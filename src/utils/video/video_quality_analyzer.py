#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de calidad de video usando FFprobe
Extrae información técnica de archivos de video cuando Plex no está disponible
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VideoQualityInfo:
    """Información de calidad de video extraída"""
    resolution: Optional[str]  # 1920x1080, 1280x720, etc.
    width: Optional[int]
    height: Optional[int]
    bitrate: Optional[int]  # en kbps
    duration: Optional[float]  # en segundos
    duration_formatted: Optional[str]  # HH:MM:SS
    video_codec: Optional[str]  # h264, h265, etc.
    audio_codec: Optional[str]  # aac, ac3, etc.
    quality_category: str  # SD, HD, FHD, 4K
    file_size: Optional[int]  # en bytes
    fps: Optional[float]  # frames por segundo
    has_audio: bool
    has_video: bool

class VideoQualityAnalyzer:
    """Analizador de calidad de video usando FFprobe"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ffprobe_path = self._find_ffprobe()
    
    def _find_ffprobe(self) -> Optional[str]:
        """Busca ffprobe en el sistema"""
        try:
            # Intentar ejecutar ffprobe para verificar si está disponible
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'ffprobe'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Buscar en rutas comunes de Windows
        common_paths = [
            r"C:\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe",
            r"C:\tools\ffmpeg\bin\ffprobe.exe"
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        self.logger.warning("FFprobe no encontrado. Análisis de video no disponible.")
        return None
    
    def analyze_video(self, file_path: Path) -> Optional[VideoQualityInfo]:
        """
        Analiza un archivo de video y extrae información de calidad
        
        Args:
            file_path: Ruta del archivo de video
            
        Returns:
            VideoQualityInfo con la información extraída o None si falla
        """
        if not self.ffprobe_path:
            self.logger.warning("FFprobe no disponible")
            return None
        
        if not file_path.exists():
            self.logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        try:
            # Comando ffprobe para obtener información completa
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Error ejecutando ffprobe: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            return self._parse_ffprobe_output(data, file_path)
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout analizando {file_path}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando JSON de ffprobe: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error analizando video {file_path}: {e}")
            return None
    
    def _parse_ffprobe_output(self, data: Dict, file_path: Path) -> VideoQualityInfo:
        """Parsea la salida de ffprobe y extrae información de calidad"""
        
        # Información básica del archivo
        format_info = data.get('format', {})
        file_size = format_info.get('size')
        duration = float(format_info.get('duration', 0))
        bitrate = int(format_info.get('bit_rate', 0)) // 1000 if format_info.get('bit_rate') else None
        
        # Buscar streams de video y audio
        video_stream = None
        audio_stream = None
        
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video' and not video_stream:
                video_stream = stream
            elif stream.get('codec_type') == 'audio' and not audio_stream:
                audio_stream = stream
        
        # Extraer información de video
        width = height = fps = None
        video_codec = None
        
        if video_stream:
            width = video_stream.get('width')
            height = video_stream.get('height')
            video_codec = video_stream.get('codec_name')
            
            # Calcular FPS
            fps_str = video_stream.get('r_frame_rate')
            if fps_str and '/' in fps_str:
                try:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else None
                except (ValueError, ZeroDivisionError):
                    fps = None
        
        # Extraer información de audio
        audio_codec = None
        if audio_stream:
            audio_codec = audio_stream.get('codec_name')
        
        # Determinar resolución y categoría de calidad
        resolution = f"{width}x{height}" if width and height else None
        quality_category = self._determine_quality_category(width, height, bitrate)
        
        # Formatear duración
        duration_formatted = self._format_duration(duration) if duration else None
        
        return VideoQualityInfo(
            resolution=resolution,
            width=width,
            height=height,
            bitrate=bitrate,
            duration=duration,
            duration_formatted=duration_formatted,
            video_codec=video_codec,
            audio_codec=audio_codec,
            quality_category=quality_category,
            file_size=file_size,
            fps=fps,
            has_audio=audio_stream is not None,
            has_video=video_stream is not None
        )
    
    def _determine_quality_category(self, width: Optional[int], height: Optional[int], bitrate: Optional[int]) -> str:
        """Determina la categoría de calidad basada en resolución y bitrate"""
        
        if not width or not height:
            return "Desconocida"
        
        # Categorías por resolución
        if width >= 3840 or height >= 2160:  # 4K
            return "4K"
        elif width >= 1920 or height >= 1080:  # Full HD
            return "FHD"
        elif width >= 1280 or height >= 720:  # HD
            return "HD"
        elif width >= 854 or height >= 480:  # SD
            return "SD"
        else:
            # Intentar determinar por bitrate si la resolución es ambigua
            if bitrate:
                if bitrate >= 15000:  # 15 Mbps o más
                    return "FHD"
                elif bitrate >= 5000:   # 5 Mbps o más
                    return "HD"
                else:
                    return "SD"
            return "SD"
    
    def _format_duration(self, duration_seconds: float) -> str:
        """Convierte duración en segundos a formato HH:MM:SS"""
        if not duration_seconds:
            return "00:00:00"
        
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_quality_summary(self, file_path: Path) -> Dict[str, any]:
        """
        Obtiene un resumen de calidad para un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con resumen de calidad
        """
        quality_info = self.analyze_video(file_path)
        
        if not quality_info:
            return {
                'available': False,
                'error': 'No se pudo analizar el archivo'
            }
        
        return {
            'available': True,
            'resolution': quality_info.resolution,
            'quality_category': quality_info.quality_category,
            'bitrate': quality_info.bitrate,
            'duration': quality_info.duration_formatted,
            'video_codec': quality_info.video_codec,
            'audio_codec': quality_info.audio_codec,
            'file_size': quality_info.file_size,
            'fps': quality_info.fps,
            'has_audio': quality_info.has_audio,
            'has_video': quality_info.has_video
        }
    
    def is_available(self) -> bool:
        """Verifica si el analizador está disponible"""
        return self.ffprobe_path is not None
