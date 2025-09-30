#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades para manejo de videos y reproductores
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional, Tuple
from src.settings.settings import settings


class VideoPlayer:
    """Clase para manejar reproductores de video"""
    
    def __init__(self):
        self.max_file_size_mb = 2000  # Límite por defecto
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Obtiene el tamaño del archivo en MB"""
        try:
            return Path(file_path).stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def can_play_embedded(self, file_path: str) -> Tuple[bool, str]:
        """
        Verifica si un archivo puede ser reproducido embebido
        
        Returns:
            Tuple[bool, str]: (puede_reproducir, mensaje)
        """
        if not Path(file_path).exists():
            return False, "Archivo no encontrado"
        
        file_size_mb = self.get_file_size_mb(file_path)
        
        if file_size_mb > self.max_file_size_mb:
            return False, f"Video muy grande ({file_size_mb:.1f}MB) - Solo reproductor externo"
        
        return True, "OK"
    
    def render_embedded_player(self, file_path: str, key: str) -> bool:
        """
        Renderiza un reproductor embebido de Streamlit
        
        Args:
            file_path: Ruta del archivo de video
            key: Clave única para el componente
            
        Returns:
            bool: True si se pudo renderizar, False en caso contrario
        """
        try:
            can_play, message = self.can_play_embedded(file_path)
            
            if not can_play:
                st.warning(f"⚠️ {message}")
                return False
            
            # Renderizar reproductor embebido
            st.video(file_path, start_time=0)
            return True
            
        except Exception as e:
            st.warning(f"⚠️ Error cargando video: {e}")
            return False
    
    def render_external_player_button(self, file_path: str, key: str, label: str = "🔗 Abrir en Reproductor") -> bool:
        """
        Renderiza un botón para abrir el video en reproductor externo
        
        Args:
            file_path: Ruta del archivo de video
            key: Clave única para el botón
            label: Texto del botón
            
        Returns:
            bool: True si se presionó el botón
        """
        if st.button(label, key=key):
            st.info(f"🔗 Abriendo: {file_path}")
            try:
                os.startfile(file_path)
                return True
            except Exception as e:
                st.warning(f"⚠️ No se pudo abrir automáticamente: {e}")
                return False
        return False
    
    def render_video_info(self, file_path: str, title: str, size_gb: float, duration: str) -> None:
        """
        Renderiza la información de un video
        
        Args:
            file_path: Ruta del archivo
            title: Título de la película
            size_gb: Tamaño en GB
            duration: Duración formateada
        """
        # Título con estilo
        st.markdown(f"<h3 style='color: #1f77b4; margin-bottom: 10px;'>🎬 {title}</h3>", unsafe_allow_html=True)
        
        # Información del video
        st.write(f"📊 Tamaño: {size_gb:.2f} GB")
        st.write(f"⏱️ Duración: {duration}")
        
        if Path(file_path).exists():
            # Información del archivo
            archivo_info = Path(file_path)
            st.write(f"📁 Ruta: {archivo_info.parent}")
            st.write(f"📄 Archivo: {archivo_info.name}")
        else:
            st.warning("⚠️ Archivo no encontrado")
            st.write(f"📁 Ruta: {file_path}")
    
    def render_video_section(self, file_path: str, title: str, size_gb: float, duration: str, 
                           video_key: str, button_key: str) -> None:
        """
        Renderiza una sección completa de video con reproductor y controles
        
        Args:
            file_path: Ruta del archivo de video
            title: Título de la película
            size_gb: Tamaño en GB
            duration: Duración formateada
            video_key: Clave para el reproductor
            button_key: Clave para el botón
        """
        # Información del video
        self.render_video_info(file_path, title, size_gb, duration)
        
        # Reproductor embebido si está habilitado
        if settings.get_show_embedded_players():
            self.render_embedded_player(file_path, video_key)
        
        # Botón de reproductor externo
        self.render_external_player_button(file_path, button_key)


class VideoFormatter:
    """Clase para formatear información de videos"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Formatea la duración en segundos a formato legible
        
        Args:
            seconds: Duración en segundos
            
        Returns:
            str: Duración formateada (ej: "1h 30m 45s")
        """
        if seconds <= 0:
            return "N/A"
        
        horas = int(seconds // 3600)
        minutos = int((seconds % 3600) // 60)
        segs = int(seconds % 60)
        
        if horas > 0:
            return f"{horas}h {minutos}m {segs}s"
        else:
            return f"{minutos}m {segs}s"
    
    @staticmethod
    def format_size_gb(size_bytes: int) -> str:
        """
        Formatea el tamaño en bytes a GB
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            str: Tamaño formateado en GB
        """
        return f"{size_bytes / (1024**3):.2f}"
    
    @staticmethod
    def parse_duration_string(duration_str: str) -> int:
        """
        Parsea una cadena de duración a segundos
        
        Args:
            duration_str: Cadena de duración (ej: "1h 30m 45s")
            
        Returns:
            int: Duración en segundos
        """
        if duration_str == "N/A":
            return 0
        
        import re
        # Formato: "1h 30m 45s" o "30m 45s"
        match = re.match(r'(?:(\d+)h\s+)?(?:(\d+)m\s+)?(?:(\d+)s)?', duration_str)
        if match:
            horas = int(match.group(1) or 0)
            minutos = int(match.group(2) or 0)
            segundos = int(match.group(3) or 0)
            return horas * 3600 + minutos * 60 + segundos
        return 0


class VideoComparison:
    """Clase para comparar videos y mostrar análisis"""
    
    def __init__(self):
        self.formatter = VideoFormatter()
    
    def compare_durations(self, duration1_str: str, duration2_str: str) -> dict:
        """
        Compara las duraciones de dos videos
        
        Args:
            duration1_str: Duración del primer video
            duration2_str: Duración del segundo video
            
        Returns:
            dict: Información de la comparación
        """
        dur1 = self.formatter.parse_duration_string(duration1_str)
        dur2 = self.formatter.parse_duration_string(duration2_str)
        
        if dur1 > 0 and dur2 > 0:
            diferencia_segundos = abs(dur1 - dur2)
            diferencia_minutos = diferencia_segundos / 60
            
            # Determinar nivel de similitud
            if diferencia_minutos <= 2:
                status = "🟢 Duración muy similar"
                level = "high"
            elif diferencia_minutos <= 5:
                status = "🟡 Duración similar"
                level = "medium"
            else:
                status = "🔴 Duración muy diferente"
                level = "low"
            
            return {
                "status": status,
                "level": level,
                "difference_minutes": diferencia_minutos,
                "can_compare": True
            }
        else:
            return {
                "status": "⚠️ No se pudo comparar duración",
                "level": "unknown",
                "difference_minutes": 0,
                "can_compare": False
            }
    
    def compare_sizes(self, size1_gb: float, size2_gb: float) -> dict:
        """
        Compara los tamaños de dos videos
        
        Args:
            size1_gb: Tamaño del primer video en GB
            size2_gb: Tamaño del segundo video en GB
            
        Returns:
            dict: Información de la comparación
        """
        if size1_gb > size2_gb:
            diferencia = ((size1_gb - size2_gb) / size1_gb) * 100
            return {
                "status": f"🔴 Video 1 es {diferencia:.1f}% más grande",
                "level": "different"
            }
        elif size2_gb > size1_gb:
            diferencia = ((size2_gb - size1_gb) / size2_gb) * 100
            return {
                "status": f"🔴 Video 2 es {diferencia:.1f}% más grande",
                "level": "different"
            }
        else:
            return {
                "status": "🟢 Mismo tamaño",
                "level": "same"
            }
    
    def compare_paths(self, path1: str, path2: str) -> dict:
        """
        Compara las rutas de dos videos
        
        Args:
            path1: Ruta del primer video
            path2: Ruta del segundo video
            
        Returns:
            dict: Información de la comparación
        """
        ruta1 = Path(path1).parent
        ruta2 = Path(path2).parent
        
        if ruta1 == ruta2:
            return {
                "status": "🟢 Misma carpeta",
                "level": "same"
            }
        else:
            return {
                "status": "🔴 Carpetas diferentes",
                "level": "different",
                "path1": str(ruta1),
                "path2": str(ruta2)
            }
