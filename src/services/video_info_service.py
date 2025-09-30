#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para extraer información de video local
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

class VideoInfoService:
    """Servicio para extraer información de video local"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ffprobe_available = self._check_ffprobe()
    
    def _check_ffprobe(self) -> bool:
        """Verifica si ffprobe está disponible"""
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_video_info(self, file_path: str) -> Optional[Dict]:
        """
        Obtiene información completa de un archivo de video
        
        Args:
            file_path: Ruta del archivo de video
            
        Returns:
            Diccionario con información del video o None si hay error
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        # Intentar con ffprobe primero (más completo)
        if self.ffprobe_available:
            info = self._get_info_ffprobe(file_path)
            if info:
                return info
        
        # Fallback a métodos alternativos
        return self._get_info_fallback(file_path)
    
    def _get_info_ffprobe(self, file_path: str) -> Optional[Dict]:
        """Obtiene información usando ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Error ffprobe: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            return self._parse_ffprobe_data(data)
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout en ffprobe")
            return None
        except Exception as e:
            self.logger.error(f"Error en ffprobe: {e}")
            return None
    
    def _parse_ffprobe_data(self, data: Dict) -> Dict:
        """Parsea los datos de ffprobe"""
        info = {
            'duration': None,
            'width': None,
            'height': None,
            'video_codec': None,
            'audio_codecs': [],
            'audio_channels': [],
            'container': None,
            'bitrate': None,
            'fps': None,
            'resolution': None,
            'quality': None
        }
        
        try:
            # Información del formato
            format_info = data.get('format', {})
            info['container'] = format_info.get('format_name', 'N/A')
            info['bitrate'] = format_info.get('bit_rate', 'N/A')
            
            # Duración
            duration_str = format_info.get('duration')
            if duration_str:
                info['duration'] = float(duration_str)
            
            # Información de streams
            streams = data.get('streams', [])
            
            for stream in streams:
                codec_type = stream.get('codec_type')
                
                if codec_type == 'video':
                    info['width'] = stream.get('width')
                    info['height'] = stream.get('height')
                    info['video_codec'] = stream.get('codec_name', 'N/A')
                    
                    # FPS
                    fps_str = stream.get('r_frame_rate')
                    if fps_str and '/' in fps_str:
                        try:
                            num, den = fps_str.split('/')
                            info['fps'] = round(float(num) / float(den), 2)
                        except:
                            pass
                
                elif codec_type == 'audio':
                    audio_codec = stream.get('codec_name', 'N/A')
                    channels = stream.get('channels', 0)
                    
                    info['audio_codecs'].append(audio_codec)
                    info['audio_channels'].append(channels)
            
            # Formatear resolución y calidad
            if info['width'] and info['height']:
                info['resolution'] = f"{info['width']}x{info['height']}"
                info['quality'] = self._determine_quality(info['width'], info['height'])
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error parseando datos ffprobe: {e}")
            return None
    
    def _determine_quality(self, width: int, height: int) -> str:
        """Determina la calidad del video"""
        if height >= 1080:
            return "HD 1080p"
        elif height >= 720:
            return "HD 720p"
        elif height >= 480:
            return "SD 480p"
        else:
            return "SD"
    
    def _get_info_fallback(self, file_path: str) -> Optional[Dict]:
        """Método de fallback cuando ffprobe no está disponible"""
        try:
            # Información básica del archivo
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size / (1024**3)  # GB
            
            # Información básica
            info = {
                'duration': None,
                'width': None,
                'height': None,
                'video_codec': 'N/A',
                'audio_codecs': ['N/A'],
                'audio_channels': [0],
                'container': Path(file_path).suffix.lower(),
                'bitrate': 'N/A',
                'fps': None,
                'resolution': 'N/A',
                'quality': 'N/A',
                'file_size_gb': file_size
            }
            
            # Intentar con OpenCV si está disponible
            try:
                import cv2
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    info['fps'] = cap.get(cv2.CAP_PROP_FPS)
                    
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    if info['fps'] > 0:
                        info['duration'] = frame_count / info['fps']
                    
                    if info['width'] and info['height']:
                        info['resolution'] = f"{info['width']}x{info['height']}"
                        info['quality'] = self._determine_quality(info['width'], info['height'])
                    
                    cap.release()
            except ImportError:
                pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error en método fallback: {e}")
            return None
    
    def format_duration(self, seconds: float) -> str:
        """Formatea duración en horas, minutos y segundos"""
        if not seconds:
            return "N/A"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours}h {minutes}m {secs}s"
    
    def format_audio_info(self, codecs: list, channels: list) -> str:
        """Formatea información de audio"""
        if not codecs or not channels:
            return "N/A"
        
        audio_info = []
        for codec, channel_count in zip(codecs, channels):
            if channel_count > 0:
                audio_info.append(f"{codec} ({channel_count} canales)")
            else:
                audio_info.append(codec)
        
        return ", ".join(audio_info)
    
    def get_summary_info(self, file_path: str) -> Dict:
        """
        Obtiene información resumida del video para mostrar en la UI
        
        Args:
            file_path: Ruta del archivo de video
            
        Returns:
            Diccionario con información resumida
        """
        info = self.get_video_info(file_path)
        if not info:
            return {
                'duration': 'N/A',
                'resolution': 'N/A',
                'quality': 'N/A',
                'audio': 'N/A',
                'container': 'N/A'
            }
        
        return {
            'duration': self.format_duration(info.get('duration')),
            'resolution': info.get('resolution', 'N/A'),
            'quality': info.get('quality', 'N/A'),
            'audio': self.format_audio_info(
                info.get('audio_codecs', []),
                info.get('audio_channels', [])
            ),
            'container': info.get('container', 'N/A'),
            'fps': info.get('fps', 'N/A'),
            'bitrate': info.get('bitrate', 'N/A')
        }
