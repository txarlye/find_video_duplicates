#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera "propuestas" para la pantalla de Automatización: nombres
sugeridos para huérfanos y recomendaciones de qué copia borrar en
duplicados, ambas ya filtradas contra la lista de descartes persistente
("no, ese no") y listas para aplicar con un clic.

La recomendación de duplicados solo se hace cuando Plex tiene indexados
ambos archivos con resolución conocida — sin eso, comparar solo por
tamaño no es un criterio fiable de qué copia es mejor, así que el par
se omite en vez de arriesgar una recomendación a ciegas.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.settings.settings import settings
from src.utils.movie_detector import MovieDetector


class ProposalsService:
    """Genera y filtra propuestas de nombres (huérfanos) y de borrado (duplicados)"""

    def __init__(self, plex_service, ai_naming_service):
        self.plex_service = plex_service
        self.ai_naming_service = ai_naming_service
        self.logger = logging.getLogger(__name__)

    def par_key(self, ruta1: str, ruta2: str) -> str:
        """
        Clave estable e independiente del orden para un par de archivos.
        Sin hashear a propósito (a diferencia de la clave de UI de
        duplicados): al guardarse en la lista de descartados, poder leer
        las dos rutas directamente ahí es más útil que un hash opaco.
        """
        a, b = sorted([ruta1, ruta2])
        return f"{a}|{b}"

    def generar_propuestas_huerfanos(self, carpetas: List[str]) -> List[Dict[str, Any]]:
        """Escanea las carpetas dadas y propone un nombre IA para cada huérfano no descartado"""
        if not self.ai_naming_service.is_configured():
            return []

        descartados = set(settings.get_dismissed_orphan_proposals())
        plex_filenames = self.plex_service.get_all_movie_filenames()
        propuestas = []

        for carpeta in carpetas:
            if not carpeta or not Path(carpeta).exists():
                continue
            try:
                detector = MovieDetector(carpeta)
                peliculas = detector.escanear_carpeta()
            except Exception as e:
                self.logger.error(f"Error escaneando '{carpeta}' para propuestas de huérfanos: {e}")
                continue

            huerfanos = [p for p in peliculas if p['nombre'].lower() not in plex_filenames]
            for h in huerfanos:
                if h['archivo'] in descartados:
                    continue
                try:
                    sugerido = self.ai_naming_service.suggest_name(h['nombre'])
                except Exception as e:
                    self.logger.error(f"Error sugiriendo nombre para '{h['nombre']}': {e}")
                    sugerido = None
                if not sugerido:
                    continue
                propuestas.append({
                    'tipo': 'huerfano',
                    'clave': h['archivo'],
                    'archivo': h['archivo'],
                    'nombre_actual': h['nombre'],
                    'nombre_sugerido': sugerido,
                    'tamaño': h.get('tamaño', 0),
                })

        return propuestas

    def generar_propuestas_duplicados(self, carpetas: List[str]) -> List[Dict[str, Any]]:
        """Escanea las carpetas dadas y propone qué copia borrar en cada duplicado no descartado"""
        descartados = set(settings.get_dismissed_duplicate_proposals())
        tolerancia_pct = settings.get_automation_size_premium_tolerance_pct()
        tolerancia_gb = settings.get_automation_size_premium_max_gb()
        propuestas = []

        for carpeta in carpetas:
            if not carpeta or not Path(carpeta).exists():
                continue
            try:
                detector = MovieDetector(carpeta)
                detector.escanear_carpeta()
                grupos = detector.encontrar_duplicados()
            except Exception as e:
                self.logger.error(f"Error escaneando '{carpeta}' para propuestas de duplicados: {e}")
                continue

            for grupo in grupos:
                for i in range(len(grupo)):
                    for j in range(i + 1, len(grupo)):
                        a, b = grupo[i], grupo[j]
                        clave = self.par_key(a['archivo'], b['archivo'])
                        if clave in descartados:
                            continue
                        try:
                            propuesta = self._evaluar_par(a, b, tolerancia_pct, tolerancia_gb)
                        except Exception as e:
                            self.logger.error(f"Error evaluando par '{a['archivo']}' / '{b['archivo']}': {e}")
                            propuesta = None
                        if propuesta:
                            propuesta['clave'] = clave
                            propuestas.append(propuesta)

        return propuestas

    def _evaluar_par(self, a: Dict, b: Dict, tolerancia_pct: float, tolerancia_gb: float) -> Optional[Dict[str, Any]]:
        """
        Compara dos archivos duplicados por resolución (Plex) y tamaño.
        Devuelve una propuesta {archivo a borrar, archivo a conservar,
        motivo} si puede juzgar con confianza, o None si no hay datos de
        resolución fiables para ambos (no arriesga una recomendación).
        """
        meta_a = self.plex_service.get_movie_metadata_by_filename(a['nombre'])
        meta_b = self.plex_service.get_movie_metadata_by_filename(b['nombre'])
        if not meta_a or not meta_b or not meta_a.get('width') or not meta_b.get('width'):
            return None

        pixeles_a = meta_a['width'] * meta_a['height']
        pixeles_b = meta_b['width'] * meta_b['height']
        tam_a = a.get('tamaño', 0)
        tam_b = b.get('tamaño', 0)

        if pixeles_a == pixeles_b:
            mejor, peor = (a, b) if tam_a <= tam_b else (b, a)
            motivo = "Misma resolución en ambas copias — la otra pesa más sin ninguna ventaja."
        else:
            mejor, peor = (a, b) if pixeles_a > pixeles_b else (b, a)
            meta_mejor = meta_a if mejor is a else meta_b
            meta_peor = meta_b if mejor is a else meta_a
            tam_mejor = mejor.get('tamaño', 0)
            tam_peor = peor.get('tamaño', 0)
            premium_gb = (tam_mejor - tam_peor) / (1024 ** 3)
            premium_pct = ((tam_mejor - tam_peor) / tam_peor * 100) if tam_peor > 0 else 0

            if premium_gb <= 0:
                motivo = (
                    f"{meta_mejor['width']}x{meta_mejor['height']} y encima pesa igual o menos "
                    "que la otra copia — no hay duda."
                )
            elif premium_pct <= tolerancia_pct and premium_gb <= tolerancia_gb:
                motivo = (
                    f"{meta_mejor['width']}x{meta_mejor['height']} frente a "
                    f"{meta_peor['width']}x{meta_peor['height']}, y solo pesa "
                    f"{premium_pct:.0f}% más ({premium_gb:.1f} GB) — compensa quedarse con la mejor."
                )
            else:
                # La mejora de calidad no compensa el espacio extra según tu
                # umbral configurado: se invierte la recomendación.
                mejor, peor = peor, mejor
                motivo = (
                    f"La copia en {meta_peor['width']}x{meta_peor['height']} pesa "
                    f"{premium_pct:.0f}% más ({premium_gb:.1f} GB) solo por la resolución — "
                    "no compensa según tu umbral configurado, mejor quedarse con la más ligera."
                )

        return {
            'tipo': 'duplicado',
            'archivo_a_borrar': peor['archivo'],
            'archivo_a_conservar': mejor['archivo'],
            'nombre_a_borrar': peor['nombre'],
            'nombre_a_conservar': mejor['nombre'],
            'tamaño_a_borrar': peor.get('tamaño', 0),
            'tamaño_a_conservar': mejor.get('tamaño', 0),
            'motivo': motivo,
        }
