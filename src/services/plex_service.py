#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para consultar metadatos de Plex
"""

import os
import sqlite3
from pathlib import Path
from datetime import timedelta
from typing import Optional, List, Dict, Tuple
import logging

from src.settings.settings import settings


class PlexService:
    """Servicio para consultar la base de datos de Plex"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_path = None
        self._connection = None
    
    def _get_db_path(self) -> Path:
        """Obtiene la ruta de la base de datos de Plex"""
        if not self._db_path:
            db_path = settings.get_plex_database_path()
            if not db_path:
                raise ValueError("No se ha configurado la ruta de la base de datos de Plex")
            
            self._db_path = Path(db_path)
            if not self._db_path.exists():
                raise FileNotFoundError(f"Base de datos de Plex no encontrada: {self._db_path}")
        
        return self._db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos con manejo robusto de errores"""
        db_path = self._get_db_path()
        
        # Crear nueva conexión cada vez para evitar problemas de concurrencia
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Intentar conexión de solo lectura primero
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                
                # Verificar que la conexión funciona
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                return conn
                
            except sqlite3.OperationalError as e:
                if "disk I/O error" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)  # Esperar antes de reintentar
                    continue
                else:
                    # Fallback a conexión normal
                    try:
                        conn = sqlite3.connect(str(db_path))
                        conn.row_factory = sqlite3.Row
                        return conn
                    except Exception:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(0.5)
                        continue
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                import time
                time.sleep(0.5)
                continue
        
        raise Exception("No se pudo establecer conexión con la base de datos después de múltiples intentos")
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                # Ignorar errores de cierre en diferentes hilos
                pass
            finally:
                self._connection = None
    
    def _ms_to_hms(self, ms: Optional[int]) -> str:
        """Convierte milisegundos a formato h:m:s"""
        if not ms or ms <= 0:
            return "0h 0m 0s"
        td = timedelta(milliseconds=int(ms))
        h = td.seconds // 3600 + td.days * 24
        m = (td.seconds % 3600) // 60
        s = td.seconds % 60
        return f"{h}h {m}m {s}s"
    
    def get_movie_metadata_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Obtiene metadatos de una película por nombre de archivo
        
        Args:
            filename: Nombre del archivo (sin ruta)
            
        Returns:
            Diccionario con metadatos o None si no se encuentra
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            movies_library = settings.get_plex_movies_library()
            
            sql = """
            SELECT
              mi.id              AS metadata_id,
              mi.title           AS title,
              mi.original_title  AS original_title,
              mi.year            AS year,
              mi.duration        AS meta_duration_ms,
              mi.guid            AS guid,
              mi.studio          AS studio,
              mi.content_rating  AS content_rating,
              mi.rating          AS rating,
              mi.summary         AS summary,
              mi.added_at        AS added_at,
              mi.updated_at      AS updated_at,
              m.id               AS media_id,
              m.bitrate          AS bitrate,
              m.width            AS width,
              m.height           AS height,
              m.container        AS container,
              m.video_codec      AS video_codec,
              m.audio_codec      AS audio_codec,
              m.audio_channels   AS audio_channels,
              mp.id              AS part_id,
              mp.file            AS file_path,
              mp.size            AS size_bytes,
              mp.duration        AS part_duration_ms,
              ls.name            AS library_name
            FROM metadata_items mi
            JOIN media_items m        ON m.metadata_item_id = mi.id
            JOIN media_parts mp       ON mp.media_item_id   = m.id
            LEFT JOIN library_sections ls ON ls.id = mi.library_section_id
            WHERE mi.metadata_type = 1
              AND (
                    LOWER(ls.name) = LOWER(?)
                 OR  ls.name LIKE ?
                 OR  ls.name LIKE ?
              )
              AND LOWER(mp.file) LIKE '%' || LOWER(?)
            """
            
            cur.execute(sql, (
                movies_library,
                f"{movies_library}%",
                f"%{movies_library}%",
                filename
            ))
            
            rows = cur.fetchall()
            
            # Filtrar por basename exacto
            fname_lower = filename.lower()
            for r in rows:
                base = os.path.basename(r["file_path"]).lower()
                if base == fname_lower:
                    return {
                        "title": r["title"],
                        "original_title": r["original_title"],
                        "year": r["year"],
                        "guid": r["guid"],
                        "studio": r["studio"],
                        "content_rating": r["content_rating"],
                        "rating": r["rating"],
                        "summary": r["summary"],
                        "added_at": r["added_at"],
                        "updated_at": r["updated_at"],
                        "file_path": r["file_path"],
                        "size_bytes": r["size_bytes"],
                        "size_gb": round((r["size_bytes"] or 0) / (1024**3), 3),
                        "container": r["container"],
                        "video_codec": r["video_codec"],
                        "audio_codec": r["audio_codec"],
                        "audio_channels": r["audio_channels"],
                        "width": r["width"],
                        "height": r["height"],
                        "bitrate_kbps": r["bitrate"],
                        "duration_hms_meta": self._ms_to_hms(r["meta_duration_ms"]),
                        "duration_hms_part": self._ms_to_hms(r["part_duration_ms"]),
                        "duration_seconds_meta": (r["meta_duration_ms"] or 0) / 1000,
                        "duration_seconds_part": (r["part_duration_ms"] or 0) / 1000,
                        "library": r["library_name"],
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error consultando metadatos de Plex para {filename}: {e}")
            return None
    
    def get_multiple_movies_metadata(self, filenames: List[str]) -> Dict[str, Dict]:
        """
        Obtiene metadatos de múltiples películas por nombre de archivo
        
        Args:
            filenames: Lista de nombres de archivos
            
        Returns:
            Diccionario {filename: metadata} para archivos encontrados
        """
        results = {}
        
        for filename in filenames:
            metadata = self.get_movie_metadata_by_filename(filename)
            if metadata:
                results[filename] = metadata
        
        return results
    
    def check_duration_compatibility(self, metadata1: Dict, metadata2: Dict) -> Tuple[bool, str]:
        """
        Verifica si dos películas son compatibles por duración usando metadatos de Plex
        
        Args:
            metadata1: Metadatos de la primera película
            metadata2: Metadatos de la segunda película
            
        Returns:
            Tuple[bool, str]: (es_compatible, mensaje)
        """
        if not settings.get_plex_duration_filter_enabled():
            return True, "Filtro de duración desactivado"
        
        # Usar duración de metadata si está disponible, sino de part
        dur1 = metadata1.get("duration_seconds_meta", 0)
        if dur1 <= 0:
            dur1 = metadata1.get("duration_seconds_part", 0)
        
        dur2 = metadata2.get("duration_seconds_meta", 0)
        if dur2 <= 0:
            dur2 = metadata2.get("duration_seconds_part", 0)
        
        if dur1 <= 0 or dur2 <= 0:
            return True, "No se pudo obtener duración de Plex"
        
        # Calcular diferencia en minutos
        diferencia_segundos = abs(dur1 - dur2)
        diferencia_minutos = diferencia_segundos / 60
        
        tolerancia = settings.get_plex_duration_tolerance_minutes()
        
        if diferencia_minutos <= tolerancia:
            return True, f"Duración compatible (diferencia: {diferencia_minutos:.1f}min)"
        else:
            return False, f"Duración incompatible (diferencia: {diferencia_minutos:.1f}min, tolerancia: {tolerancia}min)"
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        try:
            db_path = settings.get_plex_database_path()
            return bool(db_path and Path(db_path).exists())
        except Exception:
            return False
    
    
    def get_library_info_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Obtiene información de biblioteca por nombre de archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información de biblioteca o None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Buscar solo en media_parts (más simple y robusto)
            sql = "SELECT file FROM media_parts WHERE file LIKE ?"
            
            # Buscar por nombre de archivo en la ruta
            search_term = f"%{filename}%"
            cur.execute(sql, (search_term,))
            row = cur.fetchone()
            
            if row:
                # Determinar biblioteca basándose en la ruta
                file_path = row[0]
                if '/movies/' in file_path:
                    library_name = "Películas"
                    library_type = "movie"
                elif '/tvshows/' in file_path or '/series/' in file_path:
                    library_name = "Series"
                    library_type = "show"
                else:
                    library_name = "Plex"
                    library_type = "unknown"
                
                # Si encontramos el archivo, devolver información con biblioteca
                return {
                    'library_name': library_name,
                    'library_type': library_type,
                    'title': filename.rsplit('.', 1)[0],  # Nombre sin extensión
                    'year': 'N/A',
                    'summary': f'Archivo encontrado en biblioteca "{library_name}"',
                    'studio': 'N/A',
                    'content_rating': 'N/A',
                    'rating': 'N/A',
                    'duration': 'N/A',
                    'originally_available_at': 'N/A',
                    'file_path': file_path
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de biblioteca: {e}")
            return None
    
    def get_all_movies(self) -> List[Dict]:
        """
        Obtiene todas las películas de Plex
        
        Returns:
            Lista de diccionarios con información de películas
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Consulta corregida usando metadata_items
            sql = """
            SELECT 
                mi.title,
                mi.year,
                ls.name as library_name
            FROM metadata_items mi
            JOIN library_sections ls ON mi.library_section_id = ls.id
            WHERE ls.section_type = 1 AND mi.metadata_type = 1
            ORDER BY mi.title, mi.year
            """
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            movies = []
            for row in rows:
                movies.append({
                    'title': row[0],
                    'year': row[1],
                    'library_name': row[2]
                })
            
            return movies
            
        except Exception as e:
            self.logger.error(f"Error obteniendo películas: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    def get_available_libraries(self) -> List[Dict[str, str]]:
        """
        Obtiene las bibliotecas disponibles en Plex
        
        Returns:
            Lista de diccionarios con id y nombre de bibliotecas
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            sql = """
            SELECT DISTINCT ls.id, ls.name, ls.section_type
            FROM library_sections ls
            ORDER BY ls.name
            """
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            libraries = []
            for row in rows:
                libraries.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2]
                })
            
            return libraries
            
        except Exception as e:
            self.logger.error(f"Error obteniendo bibliotecas: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM metadata_items WHERE metadata_type = 1")
            count = cur.fetchone()[0]
            self.logger.info(f"Conexión exitosa. Películas en BD: {count}")
            return True
        except Exception as e:
            self.logger.error(f"Error probando conexión: {e}")
            return False
    
    def __del__(self):
        """Destructor para cerrar conexión"""
        self.close_connection()
