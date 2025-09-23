#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clases para manejo de videos y reproductores
"""

import streamlit as st
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from src.settings.settings import settings

# Importación opcional de PLEX
try:
    from src.services.plex.plex_database_direct import PlexDatabaseDirect
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False

# Importación opcional de mutagen
try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


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
                "status": "🟢 Carpeta duplicada",
                "level": "duplicate"
            }
        else:
            return {
                "status": "🔴 Carpetas diferentes",
                "level": "different",
                "path1": str(ruta1),
                "path2": str(ruta2)
            }


class VideoDurationManager:
    """
    Clase para manejar la obtención inteligente de duración de videos
    Integra lógica de PLEX y análisis de archivos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def obtener_duracion_inteligente(self, archivo: Path, nombre_archivo: str = None) -> float:
        """
        Obtiene la duración del video usando la lógica configurada:
        - Si está marcada "Preferir duración de PLEX": consulta la BBDD de PLEX
        - Si no: usa el método de análisis del archivo
        
        Args:
            archivo: Ruta del archivo de video
            nombre_archivo: Nombre del archivo (opcional, para búsqueda en PLEX)
            
        Returns:
            Duración en segundos, o 0 si no se puede obtener
        """
        # Verificar configuración de PLEX
        if (settings.get_plex_prefer_duration() and 
            settings.get_plex_enabled() and 
            PLEX_AVAILABLE):
            
            # Intentar obtener duración de PLEX
            duracion_plex = self._obtener_duracion_plex(nombre_archivo or archivo.name)
            if duracion_plex > 0:
                self.logger.debug(f"Duración obtenida de PLEX: {duracion_plex:.1f}s")
                return duracion_plex
        
        # Fallback: usar método de análisis del archivo
        return self._obtener_duracion_archivo(archivo)
    
    def _obtener_duracion_plex(self, nombre_archivo: str) -> float:
        """
        Obtiene la duración desde la base de datos de PLEX
        
        Args:
            nombre_archivo: Nombre del archivo a buscar
            
        Returns:
            Duración en segundos, o 0 si no se encuentra
        """
        try:
            # Obtener ruta de BBDD desde settings
            from src.settings.settings import settings
            db_path = settings.get_plex_database_path()
            if not db_path:
                self.logger.warning("No se encontró ruta de BBDD de PLEX")
                return 0.0
            
            # Conectar a la base de datos de PLEX
            plex_db = PlexDatabaseDirect(db_path)
            if not plex_db.connect():
                self.logger.warning("No se pudo conectar a la BBDD de PLEX")
                return 0.0
            
            # Buscar por nombre de archivo
            resultado = plex_db.search_movie_by_path(nombre_archivo)
            
            if resultado:
                # Obtener la duración del resultado
                duracion_ms = resultado.get('duration', 0)
                if duracion_ms and duracion_ms > 0:
                    # Convertir de milisegundos a segundos
                    duracion_segundos = duracion_ms / 1000
                    self.logger.debug(f"Duración PLEX encontrada: {duracion_segundos:.1f}s")
                    return duracion_segundos
            
            # Si no se encuentra por nombre, intentar por título limpio
            titulo_limpio = self._extraer_titulo_del_archivo(nombre_archivo)
            if titulo_limpio and titulo_limpio != nombre_archivo:
                resultados_titulo = plex_db.search_movie_by_title(titulo_limpio)
                if resultados_titulo:
                    # Usar el primer resultado
                    duracion_ms = resultados_titulo[0].get('duration', 0)
                    if duracion_ms and duracion_ms > 0:
                        duracion_segundos = duracion_ms / 1000
                        self.logger.debug(f"Duración PLEX encontrada por título: {duracion_segundos:.1f}s")
                        return duracion_segundos
            
            self.logger.debug(f"No se encontró duración en PLEX para: {nombre_archivo}")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error obteniendo duración de PLEX: {e}")
            return 0.0
        finally:
            if 'plex_db' in locals():
                plex_db.close()
    
    def _extraer_titulo_del_archivo(self, nombre_archivo: str) -> str:
        """
        Extrae un título limpio del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            str: Título limpio
        """
        try:
            # Remover extensión
            titulo = Path(nombre_archivo).stem
            
            # Remover patrones comunes
            import re
            patrones_a_remover = [
                r'\(\d{4}\)',  # (1995)
                r'\(Spanish\)',  # (Spanish)
                r'\(DVD-Rip\)',  # (DVD-Rip)
                r'\(AVC-AC3\)',  # (AVC-AC3)
                r'\(HD\)',  # (HD)
                r'\(720p\)',  # (720p)
                r'\(1080p\)',  # (1080p)
                r'\(BluRay\)',  # (BluRay)
                r'by\.\w+',  # by.usuario
                r'\[.*?\]',  # [cualquier cosa entre corchetes]
                r'\.mkv$',  # .mkv
                r'\.mp4$',  # .mp4
                r'\.avi$',  # .avi
            ]
            
            for patron in patrones_a_remover:
                titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)
            
            # Limpiar espacios y puntos
            titulo = titulo.replace('.', ' ').strip()
            
            # Remover espacios múltiples
            titulo = re.sub(r'\s+', ' ', titulo)
            
            return titulo
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo título: {e}")
            return nombre_archivo
    
    def _obtener_duracion_archivo(self, archivo: Path) -> float:
        """
        Obtiene la duración del video analizando el archivo directamente
        
        Args:
            archivo: Ruta del archivo de video
            
        Returns:
            Duración en segundos, o 0 si no se puede obtener
        """
        if not MUTAGEN_AVAILABLE:
            self.logger.warning("Mutagen no disponible para análisis de archivos")
            return 0.0
        
        try:
            # Verificar que el archivo existe y es accesible
            if not archivo.exists():
                self.logger.debug(f"Archivo no existe: {archivo}")
                return 0.0
            
            # Intentar obtener duración con mutagen
            audio_file = MutagenFile(str(archivo))
            if audio_file is not None and hasattr(audio_file, 'info'):
                duration = audio_file.info.length
                if duration and duration > 0:
                    self.logger.debug(f"Duración obtenida del archivo: {duration:.1f}s")
                    return float(duration)
                else:
                    self.logger.debug(f"Duración no válida del archivo: {duration}")
            else:
                self.logger.debug(f"No se pudo cargar metadata del archivo")
                
        except Exception as e:
            self.logger.debug(f"Error obteniendo duración del archivo: {e}")
        
        return 0.0
    
    def obtener_duracion_formateada(self, archivo: Path, nombre_archivo: str = None) -> str:
        """
        Obtiene la duración formateada del video
        
        Args:
            archivo: Ruta del archivo de video
            nombre_archivo: Nombre del archivo (opcional)
            
        Returns:
            Duración formateada (ej: "1h 30m 45s") o "N/A"
        """
        duracion_segundos = self.obtener_duracion_inteligente(archivo, nombre_archivo)
        return VideoFormatter.format_duration(duracion_segundos)
    
    def comparar_duraciones_inteligente(self, archivo1: Path, archivo2: Path, 
                                      nombre1: str = None, nombre2: str = None) -> dict:
        """
        Compara las duraciones de dos videos usando la lógica inteligente
        
        Args:
            archivo1: Primer archivo de video
            archivo2: Segundo archivo de video
            nombre1: Nombre del primer archivo (opcional)
            nombre2: Nombre del segundo archivo (opcional)
            
        Returns:
            dict: Información de la comparación
        """
        duracion1 = self.obtener_duracion_inteligente(archivo1, nombre1)
        duracion2 = self.obtener_duracion_inteligente(archivo2, nombre2)
        
        if duracion1 > 0 and duracion2 > 0:
            diferencia_segundos = abs(duracion1 - duracion2)
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
                "duration1_seconds": duracion1,
                "duration2_seconds": duracion2,
                "can_compare": True
            }
        else:
            return {
                "status": "⚠️ No se pudo comparar duración",
                "level": "unknown",
                "difference_minutes": 0,
                "duration1_seconds": duracion1,
                "duration2_seconds": duracion2,
                "can_compare": False
            }
