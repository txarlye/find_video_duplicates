#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestión inteligente de duración de videos
Integra lógica de PLEX y análisis de archivos
"""

import logging
from pathlib import Path
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
            archivo_busqueda = str(archivo) if archivo.is_absolute() else (nombre_archivo or archivo.name)
            duracion_plex = self._obtener_duracion_plex(archivo_busqueda)
            if duracion_plex > 0:
                self.logger.debug(f"Duración obtenida de PLEX: {duracion_plex:.1f}s")
                return duracion_plex
        
        # Fallback: usar método de análisis del archivo
        return self._obtener_duracion_archivo(archivo)
    
    def _obtener_duracion_plex(self, archivo_o_nombre: str) -> float:
        """
        Obtiene la duración desde la base de datos de PLEX
        
        Args:
            archivo_o_nombre: Ruta completa del archivo o nombre del archivo
            
        Returns:
            Duración en segundos, o 0 si no se encuentra
        """
        try:
            # Conectar a la base de datos de PLEX
            from src.settings.settings import settings
            db_path = settings.get_plex_database_path()
            if not db_path:
                self.logger.warning("No se encontró ruta de BBDD de PLEX")
                return 0.0
            
            plex_db = PlexDatabaseDirect(db_path)
            if not plex_db.connect():
                self.logger.warning("No se pudo conectar a la BBDD de PLEX")
                return 0.0
            
            resultado = None
            
            # Estrategia 1: Buscar por nombre de archivo (principal)
            nombre_archivo = Path(archivo_o_nombre).name
            self.logger.debug(f"Buscando por nombre de archivo: {nombre_archivo}")
            resultado = plex_db.search_movie_by_path(nombre_archivo)
            
            # Estrategia 2: Si no encuentra, buscar por título extraído
            if not resultado:
                titulo = self._extraer_titulo_del_archivo(nombre_archivo)
                if titulo:
                    self.logger.debug(f"Buscando por título: {titulo}")
                    resultados = plex_db.search_movie_by_title(titulo)
                    if resultados:
                        resultado = resultados[0]
            
            if resultado:
                # Obtener la duración del resultado
                duracion_ms = resultado.get('duration', 0)
                if duracion_ms and duracion_ms > 0:
                    # Convertir de milisegundos a segundos
                    duracion_segundos = duracion_ms / 1000
                    self.logger.debug(f"Duración PLEX encontrada: {duracion_segundos:.1f}s")
                    return duracion_segundos
            
            self.logger.debug(f"No se encontró duración en PLEX para: {archivo_o_nombre}")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error obteniendo duración de PLEX: {e}")
            return 0.0
        finally:
            if 'plex_db' in locals():
                plex_db.close()
    
    def _extraer_titulo_del_archivo(self, nombre_archivo: str) -> str:
        """
        Extrae un título limpio del nombre del archivo para búsqueda en PLEX
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Título limpio para búsqueda
        """
        try:
            # Remover extensión
            titulo = Path(nombre_archivo).stem
            
            # Remover patrones comunes
            patrones_a_remover = [
                r'\(\d{4}\)',  # (1996)
                r'\(Spanish\)',  # (Spanish)
                r'\(DVD-Rip\)',  # (DVD-Rip)
                r'\(AVC-AC3\)',  # (AVC-AC3)
                r'by\.ser_ismael',  # by.ser_ismael
                r'\(exploradoresp2p\)',  # (exploradoresp2p)
                r'\.mkv$',  # .mkv
                r'\.mp4$',  # .mp4
                r'\.avi$',  # .avi
            ]
            
            import re
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
        from .video import VideoFormatter
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
