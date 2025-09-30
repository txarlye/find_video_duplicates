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


class TelegramUploader:
    """Clase para subir videos a Telegram usando Telethon"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
    
    def _get_telegram_credentials(self):
        """Obtiene las credenciales del archivo .env"""
        env_path = Path("src/settings/.env")
        credentials = {}
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if value not in ['tu_api_id', 'tu_api_hash', 'tu_telefono', 'tu_channel_id', 'tu_bot_token']:
                            if key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'TELEGRAM_CHANNEL_ID']:
                                credentials[key] = value
        
        return credentials if len(credentials) == 4 else None
    
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
            
            # Subir como documento (sin límites de tamaño)
            # Usar el enlace del canal en lugar del ID numérico
            channel_link = "https://t.me/+rksOxiM7PrdjYWFk"
            await self.client.send_file(
                entity=channel_link,
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
