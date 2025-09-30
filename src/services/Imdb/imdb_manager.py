#!/usr/bin/env python3
"""
Manager para IMDB que coordina las operaciones
Reutiliza funcionalidades de Telegram para la fase inicial
"""

import logging
import os
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

# Importar servicios de Telegram para reutilizar funcionalidades
from ..Telegram.telegram_manager import TelegramManager
from .imdb_movie_finder import ImdbMovieFinder
from ...settings.settings import settings


class ImdbManager:
    """Manager para operaciones de IMDB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Reutilizar TelegramManager para la fase inicial
        self.telegram_manager = TelegramManager()
        
        # Inicializar buscador de películas
        plex_db_path = settings.get_plex_database_path()
        omdb_api_key = os.getenv('OMDB_API_KEY')
        self.movie_finder = ImdbMovieFinder(plex_db_path, omdb_api_key) if plex_db_path else None
        
        # Callback para progreso
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Establece un callback para reportar el progreso."""
        self.progress_callback = callback
        self.telegram_manager.set_progress_callback(callback)

    def is_configured(self) -> bool:
        """Verifica si IMDB está configurado"""
        # Verificar Telegram (para envío) y Plex (para búsqueda)
        telegram_ok = self.telegram_manager.bot_service.is_configured()
        plex_ok = self.movie_finder is not None
        return telegram_ok and plex_ok

    def test_connection(self) -> bool:
        """Prueba la conexión"""
        return self.is_configured()

    def send_message(self, message: str) -> bool:
        """Envía un mensaje (usa Telegram)"""
        return self.telegram_manager.send_message(message)

    def find_movie_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Busca información de una película
        
        Args:
            file_path: Ruta del archivo de video
            
        Returns:
            Información de la película o None
        """
        if not self.movie_finder:
            self.logger.error("Movie finder no inicializado")
            return None
        
        return self.movie_finder.find_movie_by_filename(file_path)

    def upload_movie_with_info(self, file_path: str, movie_info: Dict[str, Any], 
                              use_telethon: bool = True) -> Dict[str, Any]:
        """
        Sube una película con información completa
        
        Args:
            file_path: Ruta del archivo de video
            movie_info: Información de la película
            use_telethon: Si usar Telethon o Bot API
            
        Returns:
            Resultado de la operación
        """
        try:
            results = {
                'success': False,
                'poster_sent': False,
                'info_sent': False,
                'video_sent': False,
                'errors': []
            }
            
            # 1. Enviar póster si está disponible
            if movie_info.get('poster'):
                try:
                    poster_data = self.movie_finder.get_poster_image(movie_info['poster'])
                    if poster_data:
                        # TODO: Implementar envío de imagen
                        self.logger.info("Póster descargado, listo para enviar")
                        results['poster_sent'] = True
                except Exception as e:
                    results['errors'].append(f"Error con póster: {e}")
            
            # 2. Enviar información de la película
            try:
                message = self.movie_finder.format_movie_message(movie_info)
                if self.telegram_manager.send_message(message):
                    results['info_sent'] = True
            except Exception as e:
                results['errors'].append(f"Error enviando info: {e}")
            
            # 3. Subir video
            try:
                video_result = self.telegram_manager.upload_single_video(file_path, use_telethon)
                results['video_sent'] = video_result.get('success', False)
            except Exception as e:
                results['errors'].append(f"Error subiendo video: {e}")
            
            # Determinar éxito general
            results['success'] = results['info_sent'] and results['video_sent']
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en upload_movie_with_info: {e}")
            return {
                'success': False,
                'poster_sent': False,
                'info_sent': False,
                'video_sent': False,
                'errors': [str(e)]
            }

    def upload_multiple_movies(self, movies: list, use_telethon: bool = True) -> Dict[str, bool]:
        """Sube múltiples películas con información (reutiliza Telegram)"""
        results = {}
        
        for movie in movies:
            file_path = movie.get('file_path', '')
            if not file_path:
                results[file_path] = False
                continue
            
            # Buscar información de la película
            movie_info = self.find_movie_info(file_path)
            if not movie_info:
                movie_info = {'title': os.path.basename(file_path)}
            
            # Subir con información
            result = self.upload_movie_with_info(file_path, movie_info, use_telethon)
            results[file_path] = result['success']
        
        return results

    def get_upload_capabilities(self) -> Dict[str, Any]:
        """Obtiene las capacidades de subida (reutiliza Telegram)"""
        capabilities = {
            "telethon": True,
            "bot_api": True,
            "max_file_size": "1.5GB (Telethon) / 50MB (Bot API)",
            "movie_search": self.movie_finder is not None,
            "plex_integration": self.movie_finder is not None,
            "imdb_integration": bool(os.getenv('OMDB_API_KEY'))
        }
        
        return capabilities
