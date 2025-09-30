"""
Servicio de Telegram usando Telethon (Cliente de Usuario)
Soporta archivos hasta 1.5GB
"""

import logging
import asyncio
from typing import Optional, Callable
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ...settings.settings import settings

class TelegramTelethonService:
    """Servicio para Telegram usando Telethon (Cliente de Usuario)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Credenciales - leer directamente del .env
        self.api_id = self._get_env_value("TELEGRAM_API_ID")
        self.api_hash = self._get_env_value("TELEGRAM_API_HASH")
        self.phone = self._get_env_value("TELEGRAM_PHONE")
        self.channel_id = self._get_env_value("TELEGRAM_CHANNEL_ID")
        
        # Cliente
        self.client: Optional[TelegramClient] = None
        self.connected = False
    
    def _get_env_value(self, key: str) -> str:
        """Lee un valor del archivo .env directamente"""
        try:
            env_path = Path(__file__).parent.parent.parent / "settings" / ".env"
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            if k == key:
                                return v
            return None
        except Exception as e:
            self.logger.error(f"Error leyendo {key}: {e}")
            return None
        
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado"""
        return all([
            self.api_id and self.api_id != 'tu_api_id',
            self.api_hash and self.api_hash != 'tu_api_hash',
            self.phone and self.phone != 'tu_telefono',
            self.channel_id and self.channel_id != 'tu_channel_id'
        ])
    
    async def connect(self) -> bool:
        """Conecta al cliente de Telegram"""
        try:
            if not self.is_configured():
                self.logger.error("Telethon no está configurado")
                return False
            
            if self.connected:
                return True
                
            # Crear cliente
            self.client = TelegramClient('session_name', int(self.api_id), self.api_hash)
            
            # Conectar
            await self.client.start(phone=self.phone)
            self.connected = True
            
            self.logger.info("Conectado a Telegram con Telethon")
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando con Telethon: {e}")
            return False
    
    async def disconnect(self):
        """Desconecta del cliente de Telegram"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            self.logger.info("Desconectado de Telegram")
    
    async def upload_file(self, file_path: str, caption: str = "", 
                         progress_callback: Optional[Callable] = None) -> bool:
        """Sube un archivo al canal"""
        try:
            if not self.connected:
                if not await self.connect():
                    return False
            
            # Verificar archivo
            if not Path(file_path).exists():
                self.logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            # Obtener información del archivo
            file_size = Path(file_path).stat().st_size
            self.logger.info(f"Subiendo archivo: {file_path} ({file_size / (1024*1024):.2f} MB)")
            
            # Subir archivo
            await self.client.send_file(
                entity=self.channel_id,
                file=file_path,
                caption=caption,
                force_document=True,  # Sin límites de tamaño
                progress_callback=progress_callback
            )
            
            self.logger.info("Archivo subido correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subiendo archivo: {e}")
            return False
    
    def upload_file_sync(self, file_path: str, caption: str = "") -> bool:
        """Wrapper síncrono para subir archivos"""
        return asyncio.run(self.upload_file(file_path, caption))
    
    async def get_channel_info(self) -> Optional[dict]:
        """Obtiene información del canal"""
        try:
            if not self.connected:
                if not await self.connect():
                    return None
            
            entity = await self.client.get_entity(self.channel_id)
            return {
                'id': entity.id,
                'title': entity.title,
                'username': getattr(entity, 'username', None)
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información del canal: {e}")
            return None
