#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis avanzado de videos
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importación opcional de mutagen
try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class VideoAnalyzer:
    """
    Clase para análisis avanzado de videos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analizar_archivo_video(self, archivo: Path) -> Dict[str, Any]:
        """
        Analiza un archivo de video y extrae metadatos
        
        Args:
            archivo: Ruta del archivo de video
            
        Returns:
            dict: Metadatos del video
        """
        if not MUTAGEN_AVAILABLE:
            return {"error": "Mutagen no disponible"}
        
        try:
            if not archivo.exists():
                return {"error": "Archivo no encontrado"}
            
            # Cargar archivo con mutagen
            audio_file = MutagenFile(str(archivo))
            if audio_file is None:
                return {"error": "No se pudo cargar el archivo"}
            
            # Extraer información básica
            info = {
                "archivo": str(archivo),
                "nombre": archivo.name,
                "extension": archivo.suffix.lower(),
                "tamaño_bytes": archivo.stat().st_size,
                "tamaño_mb": archivo.stat().st_size / (1024 * 1024),
                "duracion_segundos": 0,
                "duracion_formateada": "N/A",
                "codec_audio": "N/A",
                "codec_video": "N/A",
                "bitrate": 0,
                "resolucion": "N/A"
            }
            
            # Obtener duración
            if hasattr(audio_file, 'info') and audio_file.info:
                if hasattr(audio_file.info, 'length') and audio_file.info.length:
                    info["duracion_segundos"] = float(audio_file.info.length)
                    info["duracion_formateada"] = self._formatear_duracion(audio_file.info.length)
                
                # Obtener bitrate
                if hasattr(audio_file.info, 'bitrate') and audio_file.info.bitrate:
                    info["bitrate"] = audio_file.info.bitrate
                
                # Obtener códec de audio
                if hasattr(audio_file.info, 'codec'):
                    info["codec_audio"] = audio_file.info.codec[0] if audio_file.info.codec else "N/A"
            
            # Obtener metadatos adicionales
            if hasattr(audio_file, 'tags') and audio_file.tags:
                info["metadatos"] = dict(audio_file.tags)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error analizando archivo: {e}")
            return {"error": str(e)}
    
    def _formatear_duracion(self, segundos: float) -> str:
        """
        Formatea duración en segundos a formato legible
        
        Args:
            segundos: Duración en segundos
            
        Returns:
            str: Duración formateada
        """
        if segundos <= 0:
            return "N/A"
        
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        
        if horas > 0:
            return f"{horas}h {minutos}m {segs}s"
        else:
            return f"{minutos}m {segs}s"
    
    def comparar_videos(self, archivo1: Path, archivo2: Path) -> Dict[str, Any]:
        """
        Compara dos archivos de video
        
        Args:
            archivo1: Primer archivo
            archivo2: Segundo archivo
            
        Returns:
            dict: Comparación detallada
        """
        info1 = self.analizar_archivo_video(archivo1)
        info2 = self.analizar_archivo_video(archivo2)
        
        if "error" in info1 or "error" in info2:
            return {
                "error": "No se pudieron analizar ambos archivos",
                "info1": info1,
                "info2": info2
            }
        
        # Comparar duraciones
        dur1 = info1.get("duracion_segundos", 0)
        dur2 = info2.get("duracion_segundos", 0)
        diferencia_duracion = abs(dur1 - dur2) if dur1 > 0 and dur2 > 0 else 0
        
        # Comparar tamaños
        size1 = info1.get("tamaño_bytes", 0)
        size2 = info2.get("tamaño_bytes", 0)
        diferencia_tamaño = abs(size1 - size2) if size1 > 0 and size2 > 0 else 0
        
        return {
            "archivo1": info1,
            "archivo2": info2,
            "comparacion": {
                "diferencia_duracion_segundos": diferencia_duracion,
                "diferencia_duracion_minutos": diferencia_duracion / 60,
                "diferencia_tamaño_bytes": diferencia_tamaño,
                "diferencia_tamaño_mb": diferencia_tamaño / (1024 * 1024),
                "duracion_similar": diferencia_duracion <= 300,  # 5 minutos
                "tamaño_similar": diferencia_tamaño <= 100 * 1024 * 1024,  # 100MB
            }
        }
    
    def detectar_calidad_video(self, archivo: Path) -> str:
        """
        Detecta la calidad del video basándose en el tamaño y duración
        
        Args:
            archivo: Ruta del archivo
            
        Returns:
            str: Calidad estimada (HD, SD, etc.)
        """
        try:
            info = self.analizar_archivo_video(archivo)
            if "error" in info:
                return "Desconocida"
            
            tamaño_mb = info.get("tamaño_mb", 0)
            duracion_minutos = info.get("duracion_segundos", 0) / 60
            
            if duracion_minutos == 0:
                return "Desconocida"
            
            # Calcular MB por minuto
            mb_por_minuto = tamaño_mb / duracion_minutos
            
            if mb_por_minuto >= 100:
                return "4K/UHD"
            elif mb_por_minuto >= 50:
                return "1080p/HD"
            elif mb_por_minuto >= 20:
                return "720p/HD"
            elif mb_por_minuto >= 10:
                return "480p/SD"
            else:
                return "360p/Low"
                
        except Exception as e:
            self.logger.error(f"Error detectando calidad: {e}")
            return "Desconocida"
