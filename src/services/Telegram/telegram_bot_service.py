"""
Servicio de Telegram usando Bot API
Límite de 50MB para videos, 2GB para documentos
"""

import logging
import requests
import time
from typing import Dict, Any, Optional
from pathlib import Path

from ...settings.settings import settings

class TelegramBotService:
    """Servicio para Telegram usando Bot API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Credenciales - leer directamente del .env
        self.bot_token = self._get_env_value("TELEGRAM_BOT_TOKEN")
        self.channel_id = self._get_env_value("TELEGRAM_CHANNEL_ID")
        
        # Configuración
        self.max_file_size = int(self._get_env_value("TELEGRAM_MAX_FILE_SIZE") or "52428800")  # 50MB
        self.upload_delay = int(self._get_env_value("TELEGRAM_UPLOAD_DELAY") or "2")
        
        # URLs
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
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
            self.bot_token and self.bot_token != 'tu_bot_token',
            self.channel_id and self.channel_id != 'tu_channel_id'
        ])
    
    def format_movie_message(self, video_info: Dict[str, Any], file_info: Dict[str, Any]) -> str:
        """Formatea el mensaje para la película"""
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
    
    def send_document(self, file_path: str, caption: str = "") -> bool:
        """Envía un archivo como documento"""
        try:
            if not self.is_configured():
                self.logger.error("Bot de Telegram no está configurado")
                return False
            
            # Verificar archivo
            if not Path(file_path).exists():
                self.logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            # Obtener información del archivo
            file_size = Path(file_path).stat().st_size
            self.logger.info(f"Enviando documento: {file_path} ({file_size / (1024*1024):.2f} MB)")
            
            # Preparar datos
            url = f"{self.base_url}/sendDocument"
            data = {
                'chat_id': self.channel_id,
                'caption': caption
            }
            
            # Preparar archivo
            with open(file_path, 'rb') as file:
                files = {'document': file}
                
                # Timeout dinámico basado en el tamaño
                timeout_seconds = max(300, int(file_size / (1024 * 1024)) * 2)
                
                # Enviar
                response = requests.post(
                    url, 
                    data=data, 
                    files=files, 
                    timeout=timeout_seconds
                )
                
                if response.status_code == 200:
                    self.logger.info("Documento enviado correctamente")
                    return True
                else:
                    self.logger.error(f"Error enviando documento: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error en send_document: {e}")
            return False
    
    def send_video(self, file_path: str, caption: str = "") -> bool:
        """Envía un video (límite 50MB)"""
        try:
            if not self.is_configured():
                self.logger.error("Bot de Telegram no está configurado")
                return False
            
            # Verificar archivo
            if not Path(file_path).exists():
                self.logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            # Verificar tamaño
            file_size = Path(file_path).stat().st_size
            if file_size > self.max_file_size:
                self.logger.warning(f"Archivo muy grande para sendVideo ({file_size / (1024*1024):.2f} MB), usando sendDocument")
                return self.send_document(file_path, caption)
            
            # Obtener información del archivo
            self.logger.info(f"Enviando video: {file_path} ({file_size / (1024*1024):.2f} MB)")
            
            # Preparar datos
            url = f"{self.base_url}/sendVideo"
            data = {
                'chat_id': self.channel_id,
                'caption': caption
            }
            
            # Preparar archivo
            with open(file_path, 'rb') as file:
                files = {'video': file}
                
                # Timeout dinámico
                timeout_seconds = max(300, int(file_size / (1024 * 1024)) * 2)
                
                # Enviar
                response = requests.post(
                    url, 
                    data=data, 
                    files=files, 
                    timeout=timeout_seconds
                )
                
                if response.status_code == 200:
                    self.logger.info("Video enviado correctamente")
                    return True
                else:
                    self.logger.error(f"Error enviando video: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error en send_video: {e}")
            return False
    
    def upload_movie_to_channel(self, video_info: Dict[str, Any], file_info: Dict[str, Any], 
                               poster_path: Optional[str] = None) -> bool:
        """Sube una película al canal de Telegram"""
        try:
            if not self.is_configured():
                self.logger.error("Telegram no está configurado")
                return False
            
            message = self.format_movie_message(video_info, file_info)
            
            video_path = file_info.get('archivo', '')
            if not video_path or not Path(video_path).exists():
                self.logger.error(f"Archivo de video no encontrado: {video_path}")
                return False
            
            # Decidir método de envío
            file_size = Path(video_path).stat().st_size
            
            if file_size > self.max_file_size:
                # Usar sendDocument para archivos grandes
                self.logger.info(f"Enviando archivo grande ({file_size / (1024*1024):.2f} MB) como documento...")
                success = self.send_document(video_path, message)
            else:
                # Usar sendVideo para archivos pequeños
                self.logger.info(f"Enviando video ({file_size / (1024*1024):.2f} MB)...")
                success = self.send_video(video_path, message)
            
            if success:
                self.logger.info(f"Película subida correctamente: {file_info.get('nombre', '')}")
                
                if self.upload_delay > 0:
                    time.sleep(self.upload_delay)
                
                return True
            else:
                self.logger.error("Error subiendo película")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en upload_movie_to_channel: {e}")
            return False
