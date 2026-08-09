#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para sugerir un nombre limpio "Título (Año)" a partir del nombre
de un archivo de vídeo, usando un modelo de IA. Soporta tres proveedores
intercambiables (elegibles desde Configuración): Ollama en local (gratis,
no requiere API key), OpenAI (ChatGPT) y Gemini.
"""

import re
import logging
import requests
from typing import Optional

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

        return self._validar_respuesta(respuesta)

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
