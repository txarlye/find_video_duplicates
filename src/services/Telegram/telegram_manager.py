"""
Gestor principal de Telegram que coordina diferentes servicios
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import asyncio
import time

from .telegram_telethon_service import TelegramTelethonService
from .telegram_bot_service import TelegramBotService

class TelegramManager:
    """Gestor principal para servicios de Telegram"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.telethon_service = TelegramTelethonService()
        self.bot_service = TelegramBotService()
        
        # Callback para progreso
        self.progress_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Establece callback para reportar progreso"""
        self.progress_callback = callback
        
    def _report_progress(self, message: str, progress: float = 0.0):
        """Reporta progreso si hay callback"""
        if self.progress_callback:
            self.progress_callback(message, progress)
        self.logger.info(f"Progreso: {message} ({progress:.1f}%)")
    
    async def upload_video_telethon(self, video_path: str, video_name: str, 
                                  video_title: str, video_year: str = None) -> bool:
        """Sube un video usando Telethon con progreso"""
        try:
            self._report_progress(f"Iniciando subida de {video_name}", 0.0)
            
            # Verificar archivo
            if not Path(video_path).exists():
                self._report_progress(f"Error: Archivo no encontrado", 0.0)
                return False
                
            # Obtener tamaño
            file_size = Path(video_path).stat().st_size
            self._report_progress(f"Archivo: {file_size / (1024*1024):.2f} MB", 10.0)
            
            # Conectar a Telegram
            self._report_progress("Conectando a Telegram...", 20.0)
            await self.telethon_service.connect()
            
            # Crear mensaje
            message = f"🎬 **{video_title}**"
            if video_year:
                message += f" ({video_year})"
                
            self._report_progress("Subiendo archivo...", 30.0)
            
            # Subir archivo con progreso
            success = await self.telethon_service.upload_file(
                file_path=video_path,
                caption=message,
                progress_callback=lambda current, total: self._report_progress(
                    f"Subiendo: {current/total*100:.1f}%", 
                    30 + (current/total * 60)
                )
            )
            
            if success:
                self._report_progress(f"✅ {video_name} subido correctamente", 100.0)
            else:
                self._report_progress(f"❌ Error subiendo {video_name}", 0.0)
                
            return success
            
        except Exception as e:
            self._report_progress(f"❌ Error: {e}", 0.0)
            return False
            
    async def upload_video_bot(self, video_path: str, video_name: str,
                             video_title: str, video_year: str = None) -> bool:
        """Sube un video usando Bot API con progreso"""
        try:
            self._report_progress(f"Iniciando subida de {video_name}", 0.0)
            
            # Verificar archivo
            if not Path(video_path).exists():
                self._report_progress(f"Error: Archivo no encontrado", 0.0)
                return False
                
            # Obtener tamaño
            file_size = Path(video_path).stat().st_size
            self._report_progress(f"Archivo: {file_size / (1024*1024):.2f} MB", 10.0)
            
            # Crear mensaje
            message = f"🎬 **{video_title}**"
            if video_year:
                message += f" ({video_year})"
                
            self._report_progress("Subiendo archivo...", 30.0)
            
            # Subir archivo
            success = self.bot_service.upload_movie_to_channel(
                video_info={'nombre': video_title, 'año': video_year},
                file_info={'archivo': video_path, 'nombre': video_name},
                poster_path=None
            )
            
            if success:
                self._report_progress(f"✅ {video_name} subido correctamente", 100.0)
            else:
                self._report_progress(f"❌ Error subiendo {video_name}", 0.0)
                
            return success
            
        except Exception as e:
            self._report_progress(f"❌ Error: {e}", 0.0)
            return False
    
    def upload_video_sync(self, video_path: str, video_name: str,
                         video_title: str, video_year: str = None,
                         use_telethon: bool = True) -> bool:
        """Wrapper síncrono para subir videos"""
        if use_telethon:
            return asyncio.run(self.upload_video_telethon(video_path, video_name, video_title, video_year))
        else:
            return self.upload_video_bot(video_path, video_name, video_title, video_year)
    
    async def upload_multiple_videos(self, videos: list, use_telethon: bool = True) -> Dict[str, bool]:
        """Sube múltiples videos con progreso"""
        results = {}
        total = len(videos)
        
        for i, video in enumerate(videos):
            self._report_progress(f"Video {i+1}/{total}: {video.get('name', 'Sin nombre')}", 
                                (i/total) * 100)
            
            if use_telethon:
                success = await self.upload_video_telethon(
                    video['path'], video['name'], video['title'], video.get('year')
                )
            else:
                success = self.upload_video_bot(
                    video['path'], video['name'], video['title'], video.get('year')
                )
                
            results[video['name']] = success
            
            # Pausa entre subidas
            if i < total - 1:
                self._report_progress("Esperando 5 segundos...", ((i+1)/total) * 100)
                await asyncio.sleep(5)
        
        return results
