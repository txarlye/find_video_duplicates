#!/usr/bin/env python3
"""
Módulo para subir videos a Telegram usando Telethon
Basado en el test que funcionó correctamente
"""

import asyncio
import time
import logging
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ...settings.settings import settings


class TelegramUploader:
    """Clase para subir videos a Telegram usando Telethon"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None

    def _get_telegram_credentials(self):
        """
        Obtiene las credenciales de Telethon vía settings.py. Antes leía
        directamente src/settings/.env (un fichero que nunca ha existido:
        el .env real vive en la raíz del proyecto), así que esto no
        encontraba nunca las credenciales aunque estuvieran bien puestas.
        """
        credentials = {
            'TELEGRAM_API_ID': settings.get_telegram_api_id(),
            'TELEGRAM_API_HASH': settings.get_telegram_api_hash(),
            'TELEGRAM_PHONE': settings.get_telegram_phone(),
            'TELEGRAM_CHANNEL_ID': settings.get_telegram_channel_id(),
        }

        if not all(credentials.values()):
            return None

        return credentials
    
    async def _ensure_connected(self):
        """Asegura que el cliente esté conectado"""
        if self.client is None or not self.client.is_connected():
            creds = self._get_telegram_credentials()
            
            if not creds:
                self.logger.error("❌ No se pudieron obtener las credenciales de Telegram")
                return False
            
            # Crear cliente (usar el mismo nombre de sesión que el test)
            self.client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
            
            # Conectar
            await self.client.start(phone=creds['TELEGRAM_PHONE'])
            self.logger.info("✅ Conectado a Telegram")
        
        return True
    
    async def _upload_single_video_async(self, video_path, video_name, video_title, video_year=None):
        """Sube un video usando Telethon - Mismo sistema que el test que funcionó"""
        try:
            # Asegurar conexión
            if not await self._ensure_connected():
                return False
            
            # Verificar que el archivo existe
            if not Path(video_path).exists():
                self.logger.error(f"❌ Archivo no encontrado: {video_path}")
                return False
            
            # Obtener tamaño del archivo
            file_size = Path(video_path).stat().st_size
            self.logger.info(f"📊 Tamaño: {file_size / (1024*1024):.2f} MB")
            
            # Subir archivo
            self.logger.info("📤 Subiendo archivo...")
            
            # Crear mensaje
            message = f"🎬 **{video_title}**"
            if video_year:
                message += f" ({video_year})"
            
            # Obtener credenciales para el channel ID
            creds = self._get_telegram_credentials()
            if not creds:
                self.logger.error("❌ Faltan credenciales de Telethon (API ID/Hash/teléfono/canal)")
                return False

            # Subir como documento (sin el límite de 50MB del Bot API)
            await self.client.send_file(
                entity=creds['TELEGRAM_CHANNEL_ID'],
                file=video_path,
                caption=message,
                force_document=True
            )
            
            self.logger.info("✅ Video subido correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error: {e}")
            return False
    
    def upload_single_video(self, video_path, video_name, video_title, video_year=None):
        """Wrapper síncrono para subir un video"""
        return asyncio.run(self._upload_single_video_async(video_path, video_name, video_title, video_year))
    
    def upload_multiple_videos(self, videos, progress_callback=None):
        """Sube múltiples videos con progreso usando sesión persistente"""
        async def _upload_all():
            results = []
            
            # Asegurar conexión una sola vez
            if not await self._ensure_connected():
                return [False] * len(videos)
            
            for i, video in enumerate(videos):
                try:
                    # Actualizar progreso si hay callback
                    if progress_callback:
                        progress = (i / len(videos)) * 100
                        progress_callback(f"Subiendo {video['name']}...", progress)
                    
                    # Subir video usando la sesión persistente
                    success = await self._upload_single_video_async(
                        video['path'],
                        video['name'],
                        video.get('title', video['name']),
                        video.get('year', '')
                    )
                    
                    results.append(success)
                    
                    # Pausa entre videos (como en el test)
                    if i < len(videos) - 1:
                        time.sleep(2)
                        
                except Exception as e:
                    self.logger.error(f"❌ Error subiendo {video['name']}: {e}")
                    results.append(False)
            
            return results
        
        # Ejecutar la función asíncrona
        return asyncio.run(_upload_all())
    
    async def disconnect(self):
        """Desconecta el cliente de Telegram"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            self.logger.info("🔌 Desconectado de Telegram")
