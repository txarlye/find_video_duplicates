#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio principal para integración con Telegram
Coordina Bot API y Telethon según necesidades
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from .Telegram.telegram_manager import TelegramManager

class TelegramService:
    """Servicio principal para interactuar con Telegram"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.manager = TelegramManager()
        
        # Callback para progreso
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Establece callback para reportar progreso"""
        self.progress_callback = callback
        self.manager.set_progress_callback(callback)

    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        return self.manager.telethon_service.is_configured() or self.manager.bot_service.is_configured()

    def test_connection(self) -> bool:
        """Prueba la conexión con Telegram"""
        return self.is_configured()
    
    def upload_movie_to_channel(self, video_info: Dict[str, Any], file_info: Dict[str, Any], 
                               poster_path: Optional[str] = None, use_telethon: bool = True) -> bool:
        """Sube una película al canal de Telegram"""
        try:
            video_path = file_info.get('archivo', '')
            video_name = file_info.get('nombre', 'Sin nombre')
            video_title = video_info.get('nombre', 'Sin título')
            video_year = video_info.get('año', '')
            
            if not video_path or not Path(video_path).exists():
                self.logger.error(f"Archivo de video no encontrado: {video_path}")
                return False
            
            # Usar el manager para subir
            return self.manager.upload_video_sync(
                video_path=video_path,
                video_name=video_name,
                video_title=video_title,
                video_year=video_year,
                use_telethon=use_telethon
            )
            
        except Exception as e:
            self.logger.error(f"Error en upload_movie_to_channel: {e}")
            return False
    
    def upload_multiple_movies(self, movies: list, use_telethon: bool = True) -> Dict[str, bool]:
        """Sube múltiples películas al canal"""
        try:
            # Preparar lista de videos
            videos = []
            for movie in movies:
                video_info = movie.get('video_info', {})
                file_info = movie.get('file_info', {})
                
                videos.append({
                    'path': file_info.get('archivo', ''),
                    'name': file_info.get('nombre', 'Sin nombre'),
                    'title': video_info.get('nombre', 'Sin título'),
                    'year': video_info.get('año', '')
                })
            
            # Usar el manager para subir múltiples videos
            return self.manager.upload_multiple_videos(videos, use_telethon=use_telethon)
            
        except Exception as e:
            self.logger.error(f"Error en upload_multiple_movies: {e}")
            return {}
        
    def format_movie_message(self, video_info: Dict[str, Any], file_info: Dict[str, Any]) -> str:
        """Formatea el mensaje para la película (compatibilidad)"""
        try:
            nombre = video_info.get('nombre', 'Sin título')
            año = video_info.get('año', '')
            archivo = file_info.get('archivo', '')
            
            # Obtener tamaño del archivo
            if archivo and Path(archivo).exists():
                size_mb = Path(archivo).stat().st_size / (1024 * 1024)
                size_text = f"{size_mb:.2f} MB"
            else:
                size_text = "Tamaño desconocido"
            
            # Crear mensaje
            message = f"🎬 **{nombre}**"
            if año:
                message += f" ({año})"
            
            message += f"\n\n📁 **Archivo:** {Path(archivo).name if archivo else 'N/A'}"
            message += f"\n📊 **Tamaño:** {size_text}"
            
            # Limitar longitud del mensaje
            if len(message) > 1024:
                message = message[:1021] + "..."
                
            return message
                
        except Exception as e:
            self.logger.error(f"Error formateando mensaje: {e}")
            return f"🎬 **{video_info.get('nombre', 'Sin título')}**"
    
    def get_upload_capabilities(self) -> Dict[str, Any]:
        """Obtiene las capacidades de subida disponibles"""
        return {
            'telethon_available': self.manager.telethon_service.is_configured(),
            'bot_available': self.manager.bot_service.is_configured(),
            'telethon_max_size': '1.5GB',
            'bot_max_size': '50MB (videos) / 2GB (documentos)',
            'recommended_method': 'telethon' if self.manager.telethon_service.is_configured() else 'bot'
        }