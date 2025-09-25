#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de conexión directa con la base de datos de Plex
Extrae metadatos usando consultas SQL directas
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PlexMovieInfo:
    """Información de película extraída de Plex"""
    title: str
    year: Optional[int]
    duration: Optional[int]  # en segundos
    summary: Optional[str]
    audio_codec: Optional[str]
    video_codec: Optional[str]
    resolution: Optional[str]
    file_size: Optional[int]
    file_path: str
    library_section: Optional[str]
    originally_available_at: Optional[str]
    added_at: Optional[str]
    updated_at: Optional[str]

class PlexDatabaseService:
    """Servicio para conectar directamente con la base de datos de Plex"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Conecta con la base de datos de Plex"""
        try:
            if not os.path.exists(self.database_path):
                self.logger.error(f"Base de datos no encontrada: {self.database_path}")
                return False
            
            self.connection = sqlite3.connect(self.database_path)
            self.logger.info("✅ Conectado a la base de datos de Plex")
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Desconecta de la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_movie_by_filename(self, filename: str) -> List[PlexMovieInfo]:
        """
        Busca información de película por nombre de archivo
        Maneja múltiples archivos asociados a la misma película
        """
        if not self.connection:
            self.logger.error("No hay conexión a la base de datos")
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Consulta optimizada para obtener metadatos completos
            query = """
            SELECT 
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.originally_available_at,
                mi.added_at,
                mi.updated_at,
                mp.file,
                mp.file_size,
                mp.audio_codec,
                mp.video_codec,
                mp.width,
                mp.height,
                ls.name as library_section
            FROM metadata_items mi
            JOIN media_items me ON mi.id = me.metadata_item_id
            JOIN media_parts mp ON me.id = mp.media_item_id
            LEFT JOIN library_sections ls ON mi.library_section_id = ls.id
            WHERE mp.file LIKE ?
            AND mi.metadata_type = 1
            ORDER BY mi.title, mp.file
            """
            
            # Buscar por nombre de archivo (sin ruta completa)
            filename_pattern = f"%{filename}%"
            cursor.execute(query, (filename_pattern,))
            results = cursor.fetchall()
            
            movies = []
            for row in results:
                title, year, duration, summary, orig_date, added, updated, file_path, file_size, audio_codec, video_codec, width, height, library_section = row
                
                # Determinar resolución
                resolution = None
                if width and height:
                    resolution = f"{width}x{height}"
                
                movie_info = PlexMovieInfo(
                    title=title or "Sin título",
                    year=year,
                    duration=duration,
                    summary=summary,
                    audio_codec=audio_codec,
                    video_codec=video_codec,
                    resolution=resolution,
                    file_size=file_size,
                    file_path=file_path,
                    library_section=library_section,
                    originally_available_at=orig_date,
                    added_at=added,
                    updated_at=updated
                )
                movies.append(movie_info)
            
            self.logger.info(f"Encontradas {len(movies)} películas para: {filename}")
            return movies
            
        except Exception as e:
            self.logger.error(f"Error buscando película por nombre: {e}")
            return []
    
    def get_movies_by_title(self, title: str) -> List[PlexMovieInfo]:
        """Busca películas por título"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.originally_available_at,
                mi.added_at,
                mi.updated_at,
                mp.file,
                mp.file_size,
                mp.audio_codec,
                mp.video_codec,
                mp.width,
                mp.height,
                ls.name as library_section
            FROM metadata_items mi
            JOIN media_items me ON mi.id = me.metadata_item_id
            JOIN media_parts mp ON me.id = mp.media_item_id
            LEFT JOIN library_sections ls ON mi.library_section_id = ls.id
            WHERE mi.title LIKE ?
            AND mi.metadata_type = 1
            ORDER BY mi.year DESC, mi.title
            """
            
            cursor.execute(query, (f"%{title}%",))
            results = cursor.fetchall()
            
            movies = []
            for row in results:
                title, year, duration, summary, orig_date, added, updated, file_path, file_size, audio_codec, video_codec, width, height, library_section = row
                
                resolution = None
                if width and height:
                    resolution = f"{width}x{height}"
                
                movie_info = PlexMovieInfo(
                    title=title or "Sin título",
                    year=year,
                    duration=duration,
                    summary=summary,
                    audio_codec=audio_codec,
                    video_codec=video_codec,
                    resolution=resolution,
                    file_size=file_size,
                    file_path=file_path,
                    library_section=library_section,
                    originally_available_at=orig_date,
                    added_at=added,
                    updated_at=updated
                )
                movies.append(movie_info)
            
            return movies
            
        except Exception as e:
            self.logger.error(f"Error buscando por título: {e}")
            return []
    
    def get_library_stats(self) -> Dict:
        """Obtiene estadísticas de la biblioteca"""
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Total de películas
            cursor.execute("SELECT COUNT(*) FROM metadata_items WHERE metadata_type = 1;")
            total_movies = cursor.fetchone()[0]
            
            # Total de archivos de video
            cursor.execute("""
                SELECT COUNT(*) FROM media_parts mp
                JOIN media_items me ON mp.media_item_id = me.id
                JOIN metadata_items mi ON me.metadata_item_id = mi.id
                WHERE mi.metadata_type = 1
            """)
            total_files = cursor.fetchone()[0]
            
            # Bibliotecas disponibles
            cursor.execute("SELECT name FROM library_sections;")
            libraries = [row[0] for row in cursor.fetchall()]
            
            return {
                'total_movies': total_movies,
                'total_files': total_files,
                'libraries': libraries
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def search_similar_files(self, filename: str, limit: int = 10) -> List[PlexMovieInfo]:
        """Busca archivos similares por nombre"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Extraer nombre base sin extensión
            base_name = Path(filename).stem
            
            query = """
            SELECT 
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.originally_available_at,
                mi.added_at,
                mi.updated_at,
                mp.file,
                mp.file_size,
                mp.audio_codec,
                mp.video_codec,
                mp.width,
                mp.height,
                ls.name as library_section
            FROM metadata_items mi
            JOIN media_items me ON mi.id = me.metadata_item_id
            JOIN media_parts mp ON me.id = mp.media_item_id
            LEFT JOIN library_sections ls ON mi.library_section_id = ls.id
            WHERE (mp.file LIKE ? OR mi.title LIKE ?)
            AND mi.metadata_type = 1
            ORDER BY mi.title
            LIMIT ?
            """
            
            pattern = f"%{base_name}%"
            cursor.execute(query, (pattern, pattern, limit))
            results = cursor.fetchall()
            
            movies = []
            for row in results:
                title, year, duration, summary, orig_date, added, updated, file_path, file_size, audio_codec, video_codec, width, height, library_section = row
                
                resolution = None
                if width and height:
                    resolution = f"{width}x{height}"
                
                movie_info = PlexMovieInfo(
                    title=title or "Sin título",
                    year=year,
                    duration=duration,
                    summary=summary,
                    audio_codec=audio_codec,
                    video_codec=video_codec,
                    resolution=resolution,
                    file_size=file_size,
                    file_path=file_path,
                    library_section=library_section,
                    originally_available_at=orig_date,
                    added_at=added,
                    updated_at=updated
                )
                movies.append(movie_info)
            
            return movies
            
        except Exception as e:
            self.logger.error(f"Error buscando archivos similares: {e}")
            return []

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
