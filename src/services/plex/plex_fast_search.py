# -*- coding: utf-8 -*-
"""
Búsquedas rápidas en la base de datos de PLEX
Acceso directo para máxima velocidad
"""

import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PlexFastSearch:
    """Búsquedas rápidas en la base de datos de PLEX"""
    
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
    
    def search_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """Busca películas por nombre de archivo (muy rápido)"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Búsqueda optimizada por nombre de archivo
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
            WHERE mp.file LIKE ? AND mi.metadata_type = 1
            ORDER BY mi.title
            """
            
            # Buscar por nombre de archivo (flexible)
            search_pattern = f"%{filename}%"
            cursor.execute(query, (search_pattern,))
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
            
            logger.info(f"🔍 Encontradas {len(movies)} películas para '{filename}'")
            return movies
            
        except Exception as e:
            logger.error(f"❌ Error buscando por nombre: {e}")
            return []
    
    def search_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Busca películas por título (muy rápido)"""
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
            
            logger.info(f"🔍 Encontradas {len(movies)} películas para '{title}'")
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
        """Añade metadatos de PLEX a un grupo de duplicados (muy rápido)"""
        enhanced_group = []
        
        for movie in duplicate_group:
            enhanced_movie = movie.copy()
            
            # Buscar por nombre de archivo (más rápido)
            filename = Path(movie.get('archivo', '')).name
            plex_movies = self.search_by_filename(filename)
            
            if plex_movies:
                # Usar la primera coincidencia
                plex_metadata = plex_movies[0]
                
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
                elif not enhanced_movie.get('duracion') and plex_metadata.get('file_duration'):
                    enhanced_movie['duracion'] = plex_metadata['file_duration'] // 1000  # Convertir de ms a segundos
                
                logger.info(f"✅ Metadatos PLEX añadidos para: {plex_metadata.get('title', 'Sin título')}")
            else:
                enhanced_movie['has_plex_metadata'] = False
                logger.warning(f"⚠️ No se encontraron metadatos PLEX para: {filename}")
            
            enhanced_group.append(enhanced_movie)
        
        return enhanced_group
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos"""
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Películas
            cursor.execute("SELECT COUNT(*) FROM metadata_items WHERE metadata_type = 1")
            movie_count = cursor.fetchone()[0]
            
            # Archivos
            cursor.execute("SELECT COUNT(*) FROM media_parts")
            file_count = cursor.fetchone()[0]
            
            # Géneros
            cursor.execute("SELECT COUNT(*) FROM tags WHERE tag_type = 1")
            genre_count = cursor.fetchone()[0]
            
            return {
                'movies': movie_count,
                'files': file_count,
                'genres': genre_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✅ Conexión a BBDD cerrada")


def test_plex_fast_search():
    """Función de prueba para búsquedas rápidas"""
    
    # Obtener ruta de la BBDD desde configuración
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    from src.settings.settings import Settings
    settings = Settings()
    db_path = settings.get_plex_database_path()
    
    if not db_path:
        print("❌ Ruta de base de datos PLEX no configurada")
        return
    
    search = PlexFastSearch(db_path)
    
    try:
        # Conectar
        if not search.connect():
            print("❌ No se pudo conectar a la BBDD")
            return
        
        # Estadísticas
        stats = search.get_database_stats()
        print(f"📊 Estadísticas de la BBDD:")
        print(f"   - Películas: {stats.get('movies', 0)}")
        print(f"   - Archivos: {stats.get('files', 0)}")
        print(f"   - Géneros: {stats.get('genres', 0)}")
        
        # Búsqueda por nombre de archivo
        print(f"\n🔍 Buscando por nombre de archivo: 'el.ultimo.heroe'")
        movies = search.search_by_filename("el.ultimo.heroe")
        print(f"✅ Encontradas {len(movies)} películas")
        
        for movie in movies[:3]:  # Mostrar solo las primeras 3
            print(f"   - {movie['title']} ({movie['year']}) - {movie['file_path']}")
        
        # Búsqueda por título
        print(f"\n🔍 Buscando por título: 'El Libro de la Selva'")
        movies = search.search_by_title("El Libro de la Selva")
        print(f"✅ Encontradas {len(movies)} películas")
        
        for movie in movies[:3]:  # Mostrar solo las primeras 3
            print(f"   - {movie['title']} ({movie['year']}) - {movie['file_path']}")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
    finally:
        search.close()


if __name__ == "__main__":
    test_plex_fast_search()
