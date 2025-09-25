#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio optimizado para extraer metadatos de Plex
Usa consultas rápidas y manejo eficiente de la base de datos
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class FastPlexInfo:
    """Información rápida de película de Plex"""
    title: str
    year: Optional[int]
    filename: str
    audio_codec: Optional[str]
    video_codec: Optional[str]
    duration: Optional[int]
    duration_formatted: Optional[str]  # Formato HH:MM:SS
    # Información de calidad
    resolution: Optional[str]  # 1080p, 720p, 4K, etc.
    bitrate: Optional[int]  # Bitrate en kbps
    quality_category: Optional[str]  # SD, HD, FHD, 4K
    file_size: Optional[int]  # Tamaño en bytes

class PlexFastMetadata:
    """Servicio rápido para metadatos de Plex"""
    
    def __init__(self, database_path: str, library_name: str = "Peliculas"):
        self.database_path = database_path
        self.library_name = library_name
        self.library_id = None
        self.logger = logging.getLogger(__name__)
    
    def _format_duration(self, duration_seconds: Optional[int]) -> Optional[str]:
        """Convierte duración en segundos a formato HH:MM:SS"""
        if not duration_seconds:
            return None

        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _determine_quality_category(self, resolution: Optional[str], bitrate: Optional[int]) -> str:
        """Determina la categoría de calidad basada en resolución y bitrate"""
        if not resolution:
            return "Desconocida"
        
        resolution_lower = resolution.lower()
        
        # Categorías por resolución
        if "4k" in resolution_lower or "2160" in resolution_lower:
            return "4K"
        elif "1080" in resolution_lower or "fhd" in resolution_lower:
            return "FHD"
        elif "720" in resolution_lower or "hd" in resolution_lower:
            return "HD"
        elif "480" in resolution_lower or "sd" in resolution_lower:
            return "SD"
        else:
            # Intentar determinar por bitrate si no hay resolución clara
            if bitrate:
                if bitrate >= 15000:  # 15 Mbps o más
                    return "FHD"
                elif bitrate >= 5000:   # 5 Mbps o más
                    return "HD"
                else:
                    return "SD"
            return "Desconocida"
    
    def _get_library_id(self, cursor) -> Optional[int]:
        """Obtiene el ID de la biblioteca por nombre"""
        if self.library_id:
            return self.library_id
        
        try:
            cursor.execute("SELECT id FROM library_sections WHERE name = ?", (self.library_name,))
            result = cursor.fetchone()
            if result:
                self.library_id = result[0]
                return self.library_id
        except Exception as e:
            self.logger.error(f"Error obteniendo ID de biblioteca: {e}")
        
        return None
    
    def get_movie_info_by_filename(self, filename: str) -> List[FastPlexInfo]:
        """
        Obtiene información rápida de película por nombre de archivo
        Optimizado para consultas rápidas
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Obtener ID de la biblioteca
            library_id = self._get_library_id(cursor)
            if not library_id:
                self.logger.warning(f"No se encontró la biblioteca '{self.library_name}'")
                conn.close()
                return []
            
            # Consulta optimizada - incluyendo información de calidad
            query = """
            SELECT
                mi.title,
                mi.year,
                mp.file,
                mi.duration,
                me.bitrate,
                me.video_codec,
                me.audio_codec,
                me.video_resolution,
                mp.size
            FROM metadata_items mi
            JOIN media_items me ON mi.id = me.metadata_item_id
            JOIN media_parts mp ON me.id = mp.media_item_id
            WHERE mp.file LIKE ?
            AND mi.metadata_type = 1
            AND mi.library_section_id = ?
            LIMIT 10
            """
            
            # Buscar por nombre de archivo
            cursor.execute(query, (f"%{filename}%", library_id))
            results = cursor.fetchall()
            
            movies = []
            for row in results:
                title, year, file_path, duration, bitrate, video_codec, audio_codec, resolution, file_size = row
                
                # Determinar categoría de calidad
                quality_category = self._determine_quality_category(resolution, bitrate)
                
                movies.append(FastPlexInfo(
                    title=title or "Sin título",
                    year=year,
                    filename=Path(file_path).name,
                    audio_codec=audio_codec,
                    video_codec=video_codec,
                    duration=duration,
                    duration_formatted=self._format_duration(duration),
                    resolution=resolution,
                    bitrate=bitrate,
                    quality_category=quality_category,
                    file_size=file_size
                ))
            
            conn.close()
            return movies
            
        except Exception as e:
            self.logger.error(f"Error en consulta rápida: {e}")
            return []
    
    def search_by_title_fragment(self, title_fragment: str, limit: int = 5) -> List[FastPlexInfo]:
        """Busca por fragmento de título"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Obtener ID de la biblioteca
            library_id = self._get_library_id(cursor)
            if not library_id:
                self.logger.warning(f"No se encontró la biblioteca '{self.library_name}'")
                conn.close()
                return []
            
            query = """
            SELECT 
                mi.title,
                mi.year,
                mp.file,
                mi.duration,
                me.bitrate,
                me.video_codec,
                me.audio_codec,
                me.video_resolution,
                mp.size
            FROM metadata_items mi
            JOIN media_items me ON mi.id = me.metadata_item_id
            JOIN media_parts mp ON me.id = mp.media_item_id
            WHERE mi.title LIKE ?
            AND mi.metadata_type = 1
            AND mi.library_section_id = ?
            ORDER BY mi.year DESC
            LIMIT ?
            """
            
            cursor.execute(query, (f"%{title_fragment}%", library_id, limit))
            results = cursor.fetchall()
            
            movies = []
            for row in results:
                title, year, file_path, duration, bitrate, video_codec, audio_codec, resolution, file_size = row
                
                # Determinar categoría de calidad
                quality_category = self._determine_quality_category(resolution, bitrate)
                
                movies.append(FastPlexInfo(
                    title=title or "Sin título",
                    year=year,
                    filename=Path(file_path).name,
                    audio_codec=audio_codec,
                    video_codec=video_codec,
                    duration=duration,
                    duration_formatted=self._format_duration(duration),
                    resolution=resolution,
                    bitrate=bitrate,
                    quality_category=quality_category,
                    file_size=file_size
                ))
            
            conn.close()
            return movies
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda por título: {e}")
            return []
    
    def get_quick_stats(self) -> Dict:
        """Obtiene estadísticas rápidas"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Contar películas
            cursor.execute("SELECT COUNT(*) FROM metadata_items WHERE metadata_type = 1;")
            total_movies = cursor.fetchone()[0]
            
            # Contar archivos
            cursor.execute("""
                SELECT COUNT(*) FROM media_parts mp
                JOIN media_items me ON mp.media_item_id = me.id
                JOIN metadata_items mi ON me.metadata_item_id = mi.id
                WHERE mi.metadata_type = 1
            """)
            total_files = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_movies': total_movies,
                'total_files': total_files
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total_movies': 0, 'total_files': 0}
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            if not os.path.exists(self.database_path):
                return False
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Consulta simple
            cursor.execute("SELECT COUNT(*) FROM metadata_items LIMIT 1;")
            cursor.fetchone()
            
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error en prueba de conexión: {e}")
            return False
