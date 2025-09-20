#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para integración con Telegram Bot API
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime

from src.settings.settings import settings


class TelegramService:
    """Servicio para interactuar con Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = settings.get_telegram_bot_token()
        self.channel_id = settings.get_telegram_channel_id()
        self.max_file_size = settings.get("telegram.max_file_size", 2000000000)  # 2GB
        self.upload_delay = settings.get("telegram.upload_delay", 1)
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MovieDetector/1.0'
        })
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        return bool(self.bot_token and self.channel_id)

    def test_connection(self) -> bool:
        """Prueba la conexión con Telegram"""
        if not self.is_configured():
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/getMe", timeout=10)
            response.raise_for_status()
            return response.json().get('ok', False)
        except Exception as e:
            self.logger.error(f"Error probando conexión con Telegram: {e}")
            return False

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envía un mensaje de texto al canal
        
        Args:
            text: Texto del mensaje
            parse_mode: Modo de parseo (HTML o Markdown)
            
        Returns:
            True si se envió correctamente
        """
        if not self.is_configured():
            self.logger.error("Telegram no está configurado")
            return False
        
        try:
            data = {
                'chat_id': self.channel_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = self.session.post(f"{self.base_url}/sendMessage", data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                self.logger.info("Mensaje enviado correctamente")
                return True
            else:
                self.logger.error(f"Error enviando mensaje: {result.get('description', 'Error desconocido')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """
        Envía una foto al canal
        
        Args:
            photo_path: Ruta de la imagen
            caption: Texto descriptivo
            
        Returns:
            True si se envió correctamente
        """
        if not self.is_configured():
            self.logger.error("Telegram no está configurado")
            return False
        
        photo_file = Path(photo_path)
        if not photo_file.exists():
            self.logger.error(f"Archivo de imagen no encontrado: {photo_path}")
            return False
        
        try:
            with open(photo_file, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.channel_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = self.session.post(
                    f"{self.base_url}/sendPhoto",
                    files=files,
                    data=data,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('ok'):
                    self.logger.info(f"Foto enviada correctamente: {photo_path}")
                    return True
                else:
                    self.logger.error(f"Error enviando foto: {result.get('description', 'Error desconocido')}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error enviando foto: {e}")
            return False

    def send_video(self, video_path: str, caption: str = "", thumbnail_path: str = None) -> bool:
        """
        Envía un video al canal
        
        Args:
            video_path: Ruta del video
            caption: Texto descriptivo
            thumbnail_path: Ruta del thumbnail (opcional)
            
        Returns:
            True si se envió correctamente
        """
        if not self.is_configured():
            self.logger.error("Telegram no está configurado")
            return False
        
        video_file = Path(video_path)
        if not video_file.exists():
            self.logger.error(f"Archivo de video no encontrado: {video_path}")
            return False
        
        # Verificar tamaño del archivo
        file_size = video_file.stat().st_size
        if file_size > self.max_file_size:
            self.logger.error(f"Archivo demasiado grande: {file_size} bytes (máximo: {self.max_file_size})")
            return False
        
        try:
            files = {'video': open(video_file, 'rb')}
            data = {
                'chat_id': self.channel_id,
                'caption': caption,
                'parse_mode': 'HTML',
                'supports_streaming': True
            }
            
            # Agregar thumbnail si existe
            if thumbnail_path and Path(thumbnail_path).exists():
                files['thumbnail'] = open(thumbnail_path, 'rb')
            
            response = self.session.post(
                f"{self.base_url}/sendVideo",
                files=files,
                data=data,
                timeout=300  # 5 minutos para videos grandes
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                self.logger.info(f"Video enviado correctamente: {video_path}")
                return True
            else:
                self.logger.error(f"Error enviando video: {result.get('description', 'Error desconocido')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando video: {e}")
            return False
        finally:
            # Cerrar archivos abiertos
            for file_obj in files.values():
                if hasattr(file_obj, 'close'):
                    file_obj.close()

    def send_document(self, document_path: str, caption: str = "") -> bool:
        """
        Envía un documento al canal
        
        Args:
            document_path: Ruta del documento
            caption: Texto descriptivo
            
        Returns:
            True si se envió correctamente
        """
        if not self.is_configured():
            self.logger.error("Telegram no está configurado")
            return False
        
        document_file = Path(document_path)
        if not document_file.exists():
            self.logger.error(f"Archivo de documento no encontrado: {document_path}")
            return False
        
        try:
            with open(document_file, 'rb') as doc:
                files = {'document': doc}
                data = {
                    'chat_id': self.channel_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = self.session.post(
                    f"{self.base_url}/sendDocument",
                    files=files,
                    data=data,
                    timeout=300
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('ok'):
                    self.logger.info(f"Documento enviado correctamente: {document_path}")
                    return True
                else:
                    self.logger.error(f"Error enviando documento: {result.get('description', 'Error desconocido')}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error enviando documento: {e}")
            return False

    def format_movie_message(self, movie_info: Dict, file_info: Dict) -> str:
        """
        Formatea un mensaje para una película
        
        Args:
            movie_info: Información de la película desde IMDB
            file_info: Información del archivo
            
        Returns:
            Mensaje formateado
        """
        # Título y año
        title = movie_info.get('title', file_info.get('titulo', 'Título desconocido'))
        year = movie_info.get('year', file_info.get('año', ''))
        
        # Información básica
        message = f"🎬 <b>{title}</b>"
        if year:
            message += f" ({year})"
        
        # Sinopsis
        plot = movie_info.get('plot', '')
        if plot:
            message += f"\n\n📖 <b>Sinopsis:</b>\n{plot}"
        
        # Detalles técnicos
        message += f"\n\n📁 <b>Archivo:</b> {file_info.get('nombre', '')}"
        
        # Calidad
        quality = file_info.get('calidad', '')
        if quality and quality != 'Desconocida':
            message += f"\n🎯 <b>Calidad:</b> {quality}"
        
        # Tamaño
        size = file_info.get('tamaño', 0)
        if size > 0:
            size_str = self._format_file_size(size)
            message += f"\n💾 <b>Tamaño:</b> {size_str}"
        
        # Información adicional de IMDB
        if movie_info.get('rating'):
            message += f"\n⭐ <b>Rating IMDB:</b> {movie_info['rating']}"
        
        if movie_info.get('genres'):
            message += f"\n🎭 <b>Géneros:</b> {movie_info['genres']}"
        
        if movie_info.get('directors'):
            message += f"\n🎬 <b>Director:</b> {movie_info['directors']}"
        
        if movie_info.get('stars'):
            message += f"\n👥 <b>Reparto:</b> {movie_info['stars']}"
        
        # Duración
        if movie_info.get('runtime'):
            message += f"\n⏱️ <b>Duración:</b> {movie_info['runtime']}"
        
        return message

    def _format_file_size(self, bytes_size: int) -> str:
        """Formatea el tamaño en bytes a formato legible"""
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unidad}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def upload_movie_to_channel(self, movie_info: Dict, file_info: Dict, 
                               poster_path: str = None) -> bool:
        """
        Sube una película completa al canal con información de IMDB
        
        Args:
            movie_info: Información de la película desde IMDB
            file_info: Información del archivo
            poster_path: Ruta del póster (opcional)
            
        Returns:
            True si se subió correctamente
        """
        if not self.is_configured():
            self.logger.error("Telegram no está configurado")
            return False
        
        try:
            # Formatear mensaje
            message = self.format_movie_message(movie_info, file_info)
            
            # Enviar póster si existe
            if poster_path and Path(poster_path).exists():
                self.logger.info("Enviando póster...")
                if not self.send_photo(poster_path, message):
                    self.logger.warning("Error enviando póster, continuando con video...")
            
            # Enviar video
            self.logger.info("Enviando video...")
            video_path = file_info.get('archivo', '')
            
            if not video_path or not Path(video_path).exists():
                self.logger.error(f"Archivo de video no encontrado: {video_path}")
                return False
            
            # Usar thumbnail si no hay póster
            thumbnail_path = poster_path if poster_path and Path(poster_path).exists() else None
            
            success = self.send_video(video_path, message, thumbnail_path)
            
            if success:
                self.logger.info(f"Película subida correctamente: {file_info.get('nombre', '')}")
                
                # Delay entre subidas
                if self.upload_delay > 0:
                    import time
                    time.sleep(self.upload_delay)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error subiendo película: {e}")
            return False

    def get_channel_info(self) -> Dict:
        """
        Obtiene información del canal
        
        Returns:
            Información del canal
        """
        if not self.is_configured():
            return {}
        
        try:
            response = self.session.get(f"{self.base_url}/getChat", 
                                      params={'chat_id': self.channel_id}, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                return result.get('result', {})
            else:
                self.logger.error(f"Error obteniendo información del canal: {result.get('description', 'Error desconocido')}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error obteniendo información del canal: {e}")
            return {}
