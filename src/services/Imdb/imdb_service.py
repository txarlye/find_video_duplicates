#!/usr/bin/env python3
"""
Servicio principal para IMDB
Reutiliza funcionalidades de Telegram para la fase inicial
"""

import logging
from typing import Dict, Any, Optional, Callable

from .imdb_manager import ImdbManager


class ImdbService:
    """Servicio principal para interactuar con IMDB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.manager = ImdbManager()
        
        # Callback para progreso
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Establece un callback para reportar el progreso de las operaciones."""
        self.progress_callback = callback
        self.manager.set_progress_callback(callback)

    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        return self.manager.is_configured()

    def test_connection(self) -> bool:
        """Prueba la conexión con IMDB."""
        return self.manager.test_connection()

    def send_message(self, message: str) -> bool:
        """Envía un mensaje (placeholder para futuras funcionalidades)."""
        return self.manager.send_message(message)

    def find_movie_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca información de una película"""
        return self.manager.find_movie_info(file_path)

    def upload_movie_with_info(self, file_path: str, movie_info: Dict[str, Any], 
                              use_telethon: bool = True) -> Dict[str, Any]:
        """Sube una película con información completa"""
        return self.manager.upload_movie_with_info(file_path, movie_info, use_telethon)

    def upload_multiple_movies(self, movies: list, use_telethon: bool = True) -> Dict[str, bool]:
        """Sube múltiples películas (reutiliza funcionalidad de Telegram)."""
        return self.manager.upload_multiple_movies(movies, use_telethon)

    def get_upload_capabilities(self) -> Dict[str, Any]:
        """Obtiene las capacidades de subida."""
        return self.manager.get_upload_capabilities()
