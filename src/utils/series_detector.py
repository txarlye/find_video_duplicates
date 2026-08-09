#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidad para detectar episodios de serie duplicados.

A diferencia de MovieDetector (título + año, agrupados por similitud de
texto), la identidad de un episodio es su serie + temporada + número de
episodio: el agrupamiento aquí es una coincidencia exacta sobre esos tres
valores, no una comparación difusa.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from src.settings.settings import settings


class SeriesDetector:
    """Detecta episodios de serie duplicados en una carpeta"""

    # SxxExx (ej. S01E01). No puede ir pegado a otro dígito/letra a los
    # lados, para no confundirse con resoluciones u otros números.
    PATRON_SXXEXX = re.compile(r'(?<![A-Za-z0-9])[Ss](\d{1,2})[Ee](\d{1,3})(?!\d)')

    # NxNN (ej. 1x02). El episodio se limita a 2 dígitos (a diferencia de
    # SxxExx) precisamente para no confundirse con resoluciones tipo
    # "1080x720": ahí el "720" tiene 3 dígitos y no cuela.
    PATRON_NXNN = re.compile(r'(?<!\d)(\d{1,2})[xX](\d{1,2})(?!\d)')

    def __init__(self, carpeta_raiz: str = None):
        """
        Inicializa el detector con la carpeta raíz

        Args:
            carpeta_raiz: Ruta de la carpeta a analizar (opcional)
        """
        self.carpeta_raiz = Path(carpeta_raiz) if carpeta_raiz else None
        self.episodios = []
        self.duplicados = []
        self.sin_reconocer = 0

        self.extensiones_video = set(settings.get_supported_extensions())
        self.logger = logging.getLogger(__name__)

    def set_carpeta_raiz(self, carpeta_raiz: str):
        """Establece la carpeta raíz a analizar"""
        self.carpeta_raiz = Path(carpeta_raiz)
        self.episodios = []
        self.duplicados = []
        self.sin_reconocer = 0

    def _is_in_excluded_directory(self, archivo: Path, excluded_dirs: List[str]) -> bool:
        """Verifica si un archivo está en un directorio excluido (misma lógica que MovieDetector)"""
        try:
            path_parts = archivo.parts
            for part in path_parts:
                if part.lower() in [dir_name.lower() for dir_name in excluded_dirs]:
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Error verificando directorio excluido: {e}")
            return False

    def es_archivo_video(self, archivo: Path) -> bool:
        """Verifica si un archivo es de video"""
        return archivo.suffix.lower() in self.extensiones_video

    def extraer_episodio(self, nombre_archivo: str) -> Optional[Dict]:
        """
        Extrae serie, temporada y episodio del nombre de archivo.

        Args:
            nombre_archivo: Nombre del archivo (con extensión)

        Returns:
            Dict con 'serie', 'temporada', 'episodio', o None si el
            nombre no tiene un patrón de episodio reconocible (SxxExx o
            NxNN) — en ese caso no se puede tratar como episodio de serie.
        """
        nombre = Path(nombre_archivo).stem

        match = self.PATRON_SXXEXX.search(nombre)
        if not match:
            match = self.PATRON_NXNN.search(nombre)
        if not match:
            return None

        temporada = int(match.group(1))
        episodio = int(match.group(2))

        # El nombre de la serie es lo que hay antes del patrón de episodio
        serie_raw = nombre[:match.start()]
        serie = re.sub(r'[._-]', ' ', serie_raw).strip(' -')
        serie = re.sub(r'\s+', ' ', serie).strip()

        if not serie:
            return None

        return {
            'serie': serie,
            'temporada': temporada,
            'episodio': episodio,
        }

    def normalizar_serie(self, serie: str) -> str:
        """Normaliza un nombre de serie para agrupar (minúsculas, sin artículos ni símbolos)"""
        texto = serie.lower()
        articulos = ['el', 'la', 'los', 'las', 'un', 'una', 'the', 'a', 'an']
        palabras = [p for p in texto.split() if p not in articulos]
        texto = re.sub(r'[^\w\s]', '', ' '.join(palabras))
        return texto.strip()

    def analizar_archivo(self, archivo: Path) -> Optional[Dict]:
        """
        Analiza un archivo y extrae su información de episodio

        Args:
            archivo: Ruta del archivo

        Returns:
            Diccionario con información del episodio, o None si el
            nombre no tiene un patrón de episodio reconocible
        """
        info = self.extraer_episodio(archivo.name)
        if not info:
            return None

        return {
            'archivo': str(archivo),
            'nombre': archivo.name,
            'serie': info['serie'],
            'serie_normalizada': self.normalizar_serie(info['serie']),
            'temporada': info['temporada'],
            'episodio': info['episodio'],
            'tamaño': archivo.stat().st_size if archivo.exists() else 0,
            'carpeta': str(archivo.parent),
        }

    def escanear_carpeta(self, carpeta_raiz: str = None) -> List[Dict]:
        """
        Escanea la carpeta de manera recursiva buscando episodios de serie

        Args:
            carpeta_raiz: Ruta de la carpeta (opcional si ya está configurada)

        Returns:
            Lista de episodios reconocidos (los archivos sin patrón de
            episodio detectable se cuentan en self.sin_reconocer, no se
            incluyen en el resultado)
        """
        if carpeta_raiz:
            self.set_carpeta_raiz(carpeta_raiz)

        if not self.carpeta_raiz:
            self.logger.error("No se ha especificado carpeta raíz")
            return []

        if not self.carpeta_raiz.exists():
            self.logger.error(f"La carpeta {self.carpeta_raiz} no existe")
            return []

        excluded_dirs = settings.get_excluded_directories()
        episodios = []
        sin_reconocer = 0

        for archivo in self.carpeta_raiz.rglob('*'):
            if self._is_in_excluded_directory(archivo, excluded_dirs):
                continue

            if archivo.is_file() and self.es_archivo_video(archivo):
                if hasattr(self, 'mostrar_archivo'):
                    self.mostrar_archivo(str(archivo))

                try:
                    episodio = self.analizar_archivo(archivo)
                    if episodio:
                        episodios.append(episodio)
                    else:
                        sin_reconocer += 1
                except Exception as e:
                    self.logger.error(f"Error procesando {archivo}: {e}")

        self.episodios = episodios
        self.sin_reconocer = sin_reconocer
        self.logger.info(f"Episodios reconocidos: {len(episodios)} (sin patrón de episodio: {sin_reconocer})")

        return episodios

    def encontrar_duplicados(self) -> List[List[Dict]]:
        """
        Agrupa episodios por (serie normalizada, temporada, episodio) —
        coincidencia exacta, no por similitud de texto como en las
        películas. Un grupo con más de un archivo es un duplicado.

        Returns:
            Lista de grupos de episodios duplicados (cada grupo puede
            tener 2 o más archivos)
        """
        if not self.episodios:
            self.logger.warning("Primero debe escanear la carpeta")
            return []

        grupos = defaultdict(list)
        for episodio in self.episodios:
            clave = (episodio['serie_normalizada'], episodio['temporada'], episodio['episodio'])
            grupos[clave].append(episodio)

        duplicados = [grupo for grupo in grupos.values() if len(grupo) > 1]

        self.duplicados = duplicados
        self.logger.info(f"Encontrados {len(duplicados)} episodios duplicados")

        return duplicados

    def formatear_tamaño(self, bytes_size: int) -> str:
        """Formatea el tamaño en bytes a formato legible"""
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unidad}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
