#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para sugerir un nombre limpio "Título (Año)" a partir del nombre
de un archivo de vídeo, usando un modelo de IA. Soporta tres proveedores
intercambiables (elegibles desde Configuración): Ollama en local (gratis,
no requiere API key), OpenAI (ChatGPT) y Gemini.

La IA sola tiende a acertar el título pero puede inventarse el año (es
memoria del modelo, no una consulta real). Por eso, si hay una API key
de OMDb configurada, la respuesta de la IA se usa solo como término de
búsqueda: se contrasta contra los resultados reales de OMDb y se
devuelve el candidato más parecido, con el año que diga la base de
datos — no el que haya podido inventar el modelo.
"""

import re
import logging
import difflib
import requests
from typing import Optional, List, Dict

from src.settings.settings import settings


PROMPT_SISTEMA = (
    "Eres un asistente que limpia nombres de archivo de películas para "
    "organizarlas en Plex. Te doy el nombre de un archivo de vídeo y "
    "debes responder ÚNICAMENTE con el título y el año en el formato "
    "exacto 'Título (Año)', sin extensión, sin calidad, sin idioma, sin "
    "comillas ni ningún otro texto ni explicación. Si no puedes "
    "identificar la película con razonable certeza, responde "
    "exactamente: DESCONOCIDO"
)


class AINamingService:
    """Sugiere un nombre limpio 'Título (Año)' para un archivo de vídeo usando IA"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        """Verifica si hay un proveedor de IA listo para usarse"""
        if not settings.get_ai_enabled():
            return False

        provider = settings.get_ai_provider()
        if provider == "ollama":
            return True  # no requiere API key
        if provider == "openai":
            return bool(settings.get_openai_api_key())
        if provider == "gemini":
            return bool(settings.get_gemini_api_key())
        return False

    def suggest_name(self, filename: str) -> Optional[str]:
        """
        Sugiere un nombre limpio para un archivo de vídeo.

        Primero le pide a la IA una aproximación (título y año) a partir
        del nombre de archivo. Si hay una API key de OMDb configurada,
        esa aproximación se usa solo como término de búsqueda: se busca
        en OMDb de verdad y se devuelve el candidato más parecido de la
        lista de resultados, con el año real — no el que haya podido
        inventar el modelo. Sin OMDb configurado, se devuelve la
        aproximación de la IA tal cual (mejor que nada, pero sin
        contrastar).

        Args:
            filename: Nombre de archivo original (con extensión)

        Returns:
            Nombre sugerido en formato "Título (Año)" (sin extensión),
            o None si la IA no está configurada, falla, o no reconoce
            la película con suficiente certeza.
        """
        if not self.is_configured():
            return None

        provider = settings.get_ai_provider()
        try:
            if provider == "ollama":
                respuesta = self._ask_ollama(filename)
            elif provider == "openai":
                respuesta = self._ask_openai(filename)
            elif provider == "gemini":
                respuesta = self._ask_gemini(filename)
            else:
                self.logger.warning(f"Proveedor de IA desconocido: {provider}")
                return None
        except Exception as e:
            self.logger.error(f"Error consultando IA ({provider}) para '{filename}': {e}")
            return None

        aproximacion = self._validar_respuesta(respuesta)
        if not aproximacion:
            return None

        if settings.get_omdb_api_key():
            titulo_aprox, año_aprox = self._separar_titulo_año(aproximacion)
            confirmado = self._buscar_en_omdb(titulo_aprox, año_aprox)
            if confirmado:
                return confirmado
            # OMDb no encontró nada convincente: mejor no proponer un año
            # inventado por el modelo sin contrastar.
            return None

        return aproximacion

    def _validar_respuesta(self, respuesta: Optional[str]) -> Optional[str]:
        """Acepta solo respuestas con forma 'Algo (AAAA)'; descarta el resto"""
        if not respuesta:
            return None

        texto = respuesta.strip().strip('"').strip("'").strip()

        if texto.upper().startswith("DESCONOCIDO"):
            return None

        if not re.match(r"^.+\(\d{4}\)$", texto):
            return None

        return texto

    def _separar_titulo_año(self, texto: str) -> tuple:
        """Separa 'Título (Año)' en (titulo, año). El regex de _validar_respuesta ya garantiza el formato"""
        match = re.match(r"^(.+)\((\d{4})\)$", texto)
        return match.group(1).strip(), match.group(2)

    def _buscar_en_omdb(self, titulo: str, año_pista: Optional[str]) -> Optional[str]:
        """
        Busca `titulo` en OMDb (modo de búsqueda, no de lookup exacto) y
        devuelve el candidato más parecido de la lista de resultados
        reales, como "Título (Año)".
        """
        try:
            api_key = settings.get_omdb_api_key()
            response = requests.get("http://www.omdbapi.com/", params={
                "apikey": api_key,
                "s": titulo,
                "type": "movie",
            }, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("Response") != "True":
                return None

            candidatos = data.get("Search", [])
            mejor = self._elegir_mejor_candidato(titulo, año_pista, candidatos)
            if not mejor:
                return None

            return f"{mejor['Title']} ({mejor['Year']})"

        except Exception as e:
            self.logger.error(f"Error buscando '{titulo}' en OMDb: {e}")
            return None

    def _elegir_mejor_candidato(self, titulo: str, año_pista: Optional[str], candidatos: List[Dict]) -> Optional[Dict]:
        """
        Elige, de una lista de resultados de búsqueda de OMDb, el más
        convincente: combina similitud de título con la aproximación de
        la IA y cercanía al año que haya podido apuntar (sin exigirlo,
        solo como desempate).
        """
        mejores = []
        for c in candidatos:
            año_match = re.match(r"(\d{4})", c.get("Year", ""))
            if not año_match:
                continue  # descarta series/años en rango tipo "2015–2018"

            similitud = difflib.SequenceMatcher(None, titulo.lower(), c.get("Title", "").lower()).ratio()

            if año_pista:
                diferencia_años = abs(int(año_match.group(1)) - int(año_pista))
                cercania_año = max(0, 1 - diferencia_años / 5)
            else:
                cercania_año = 0.5  # sin pista de año: no penaliza ni premia

            puntuacion = similitud * 0.7 + cercania_año * 0.3
            mejores.append((puntuacion, {**c, "Year": año_match.group(1)}))

        if not mejores:
            return None

        mejores.sort(key=lambda x: x[0], reverse=True)
        mejor_puntuacion, mejor_candidato = mejores[0]

        # Umbral mínimo: si ni el mejor candidato se parece razonablemente,
        # mejor no proponer nada a que se cuele un resultado sin relación.
        if mejor_puntuacion < 0.5:
            return None

        return mejor_candidato

    def _ask_ollama(self, filename: str) -> Optional[str]:
        url = settings.get_ai_ollama_url().rstrip('/') + "/api/generate"
        model = settings.get_ai_ollama_model()

        response = requests.post(url, json={
            "model": model,
            "system": PROMPT_SISTEMA,
            "prompt": f"Archivo: {filename}",
            "stream": False,
            "options": {"temperature": 0},
        }, timeout=30)
        response.raise_for_status()

        return response.json().get("response", "")

    def _ask_openai(self, filename: str) -> Optional[str]:
        api_key = settings.get_openai_api_key()
        model = settings.get_ai_openai_model()

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": PROMPT_SISTEMA},
                    {"role": "user", "content": f"Archivo: {filename}"},
                ],
                "temperature": 0,
            },
            timeout=30,
        )
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _ask_gemini(self, filename: str) -> Optional[str]:
        api_key = settings.get_gemini_api_key()
        model = settings.get_ai_gemini_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        response = requests.post(url, json={
            "systemInstruction": {"parts": [{"text": PROMPT_SISTEMA}]},
            "contents": [{"parts": [{"text": f"Archivo: {filename}"}]}],
            "generationConfig": {"temperature": 0},
        }, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
