# -*- coding: utf-8 -*-
"""
Acceso directo a la base de datos de PLEX
Para PLEX en contenedor Docker en Synology
"""

import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PlexDatabaseDirect:
    """Acceso directo a la base de datos de PLEX"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> bool:
        """Conecta a la base de datos de PLEX"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"❌ Base de datos no encontrada: {self.db_path}")
                return False
            
            self.connection = sqlite3.connect(self.db_path)
            logger.info(f"✅ Conectado a BBDD PLEX: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a BBDD: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtiene información general de la base de datos"""
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Obtener tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Obtener información de películas
            cursor.execute("SELECT COUNT(*) FROM metadata_items WHERE metadata_type = 1")
            movie_count = cursor.fetchone()[0]
            
            # Obtener información de archivos
            cursor.execute("SELECT COUNT(*) FROM media_parts")
            file_count = cursor.fetchone()[0]
            
            return {
                'tables': tables,
                'movie_count': movie_count,
                'file_count': file_count,
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de BBDD: {e}")
            return {}
    
    def search_movie_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca una película por su ruta de archivo"""
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            
            # Extraer nombre del archivo de la ruta
            from pathlib import Path
            filename = Path(file_path).name
            
            # Query para buscar por nombre de archivo
            query = """
            SELECT 
                mi.id,
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.rating,
                mi.originally_available_at,
                mp.file,
                mp.size,
                mp.duration as file_duration
            FROM metadata_items mi
            JOIN media_items mei ON mi.id = mei.metadata_item_id
            JOIN media_parts mp ON mei.id = mp.media_item_id
            WHERE mp.file LIKE ?
            """
            
            # ESTRATEGIA 1: Buscar por nombre de archivo exacto
            logger.info(f"Buscando por nombre de archivo: {filename}")
            cursor.execute(query, (f"%{filename}%",))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ Encontrado por nombre de archivo: {result[1]}")
                return self._format_movie_result(result)
            
            # ESTRATEGIA 2: Buscar por nombre sin extensión
            filename_no_ext = Path(filename).stem
            logger.info(f"Buscando por nombre sin extensión: {filename_no_ext}")
            cursor.execute(query, (f"%{filename_no_ext}%",))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ Encontrado por nombre sin extensión: {result[1]}")
                return self._format_movie_result(result)
            
            # ESTRATEGIA 3: Buscar por título extraído del nombre
            title = self._extract_title_from_filename(filename)
            if title:
                logger.info(f"Buscando por título extraído: {title}")
                title_results = self.search_movie_by_title(title)
                if title_results:
                    logger.info(f"✅ Encontrado por título: {title_results[0].get('title', 'Sin título')}")
                    return title_results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando película: {e}")
            return None
    
    def search_movie_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Busca películas por título"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                mi.id,
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.rating,
                mi.originally_available_at,
                mp.file,
                mp.size,
                mp.duration as file_duration
            FROM metadata_items mi
            JOIN media_items mei ON mi.id = mei.metadata_item_id
            JOIN media_parts mp ON mei.id = mp.media_item_id
            WHERE mi.metadata_type = 1 AND mi.title LIKE ?
            ORDER BY mi.title
            """
            
            cursor.execute(query, (f"%{title}%",))
            results = cursor.fetchall()
            
            movies = []
            for result in results:
                movies.append({
                    'id': result[0],
                    'title': result[1],
                    'year': result[2],
                    'duration': result[3],
                    'summary': result[4],
                    'rating': result[5],
                    'release_date': result[6],
                    'file_path': result[7],
                    'file_size': result[8],
                    'file_duration': result[9]
                })
            
            return movies
            
        except Exception as e:
            logger.error(f"❌ Error buscando por título: {e}")
            return []
    
    def get_movie_metadata(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene metadatos completos de una película"""
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            
            # Información básica
            query = """
            SELECT 
                mi.title,
                mi.year,
                mi.duration,
                mi.summary,
                mi.rating,
                mi.originally_available_at,
                mi.content_rating,
                mi.studio,
                mi.tagline
            FROM metadata_items mi
            WHERE mi.id = ?
            """
            
            cursor.execute(query, (movie_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            metadata = {
                'title': result[0],
                'year': result[1],
                'duration': result[2],
                'summary': result[3],
                'rating': result[4],
                'release_date': result[5],
                'content_rating': result[6],
                'studio': result[7],
                'tagline': result[8]
            }
            
            # Géneros
            cursor.execute("""
                SELECT t.tag FROM taggings tg
                JOIN tags t ON tg.tag_id = t.id
                WHERE tg.metadata_item_id = ? AND t.tag_type = 1
            """, (movie_id,))
            genres = [row[0] for row in cursor.fetchall()]
            metadata['genres'] = genres
            
            # Archivos
            cursor.execute("""
                SELECT mp.file, mp.size, mp.duration
                FROM media_items mei
                JOIN media_parts mp ON mei.id = mp.media_item_id
                WHERE mei.metadata_item_id = ?
            """, (movie_id,))
            files = cursor.fetchall()
            metadata['files'] = [
                {'path': f[0], 'size': f[1], 'duration': f[2]} 
                for f in files
            ]
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadatos: {e}")
            return None
    
    def enhance_duplicate_group(self, duplicate_group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Añade metadatos de PLEX a un grupo de duplicados"""
        enhanced_group = []
        
        for movie in duplicate_group:
            enhanced_movie = movie.copy()
            
            # Buscar en PLEX por ruta de archivo
            plex_metadata = self.search_movie_by_path(movie.get('archivo', ''))
            
            if plex_metadata:
                enhanced_movie.update({
                    'plex_title': plex_metadata.get('title'),
                    'plex_year': plex_metadata.get('year'),
                    'plex_duration': plex_metadata.get('duration'),
                    'plex_summary': plex_metadata.get('summary'),
                    'plex_rating': plex_metadata.get('rating'),
                    'plex_studio': plex_metadata.get('studio'),
                    'plex_genres': plex_metadata.get('genres', []),
                    'plex_files': plex_metadata.get('files', []),
                    'has_plex_metadata': True
                })
                
                # Si no tenemos duración local, usar la de PLEX
                if not enhanced_movie.get('duracion') and plex_metadata.get('duration'):
                    enhanced_movie['duracion'] = plex_metadata['duration'] // 1000  # Convertir de ms a segundos
                
                logger.info(f"✅ Metadatos PLEX añadidos para: {plex_metadata.get('title', 'Sin título')}")
            else:
                enhanced_movie['has_plex_metadata'] = False
                logger.warning(f"⚠️ No se encontraron metadatos PLEX para: {movie.get('archivo', '')}")
            
            enhanced_group.append(enhanced_movie)
        
        return enhanced_group
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✅ Conexión a BBDD cerrada")
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """Extrae un título limpio del nombre del archivo"""
        import re
        from pathlib import Path
        
        # Remover extensión
        name = Path(filename).stem
        
        # Patrones comunes para extraer título
        patterns = [
            r'^([^\.]+)',  # Todo hasta el primer punto
            r'^([^\(]+)',  # Todo hasta el primer paréntesis
            r'^([^\-]+)',  # Todo hasta el primer guión
            r'^([^_]+)',   # Todo hasta el primer guión bajo
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name)
            if match:
                title = match.group(1).strip()
                # Limpiar caracteres especiales
                title = re.sub(r'[._-]+', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) > 2:  # Asegurar que tenga al menos 3 caracteres
                    return title
        
        return name
    
    def _format_movie_result(self, result) -> Dict[str, Any]:
        """Formatea el resultado de una película"""
        return {
            'id': result[0],
            'title': result[1],
            'year': result[2],
            'duration': result[3],
            'summary': result[4],
            'rating': result[5],
            'release_date': result[6],
            'file_path': result[7],
            'file_size': result[8],
            'file_duration': result[9]
        }


def test_plex_database_direct():
    """Función de prueba para el acceso directo a la BBDD"""
    
    # Obtener ruta desde configuración
    from src.settings.settings import settings
    db_path = settings.get_plex_database_path()
    
    db = PlexDatabaseDirect(db_path)
    
    try:
        # Conectar
        if not db.connect():
            print("❌ No se pudo conectar a la BBDD")
            return
        
        # Obtener información
        info = db.get_database_info()
        print(f"📊 Información de la BBDD:")
        print(f"   - Películas: {info.get('movie_count', 0)}")
        print(f"   - Archivos: {info.get('file_count', 0)}")
        print(f"   - Tablas: {len(info.get('tables', []))}")
        
        # Buscar película de prueba
        test_movies = db.search_movie_by_title("El Libro de la Selva")
        print(f"🎬 Películas encontradas: {len(test_movies)}")
        for movie in test_movies[:3]:  # Mostrar solo las primeras 3
            print(f"   - {movie['title']} ({movie['year']}) - {movie['file_path']}")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_plex_database_direct()
