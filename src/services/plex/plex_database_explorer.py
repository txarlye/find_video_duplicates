# -*- coding: utf-8 -*-
"""
Explorador de la base de datos de PLEX
Para PLEX corriendo en contenedor Docker
"""

import sqlite3
import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PlexDatabaseExplorer:
    """Explora la base de datos de PLEX directamente"""
    
    def __init__(self):
        self.db_path = None
        self.connection = None
        self.container_id = None
    
    def find_plex_container(self) -> Optional[str]:
        """Encuentra el contenedor de PLEX"""
        try:
            # Buscar contenedores de PLEX
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.ID}}\t{{.Names}}\t{{.Image}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Saltar header
                for line in lines:
                    if 'plex' in line.lower():
                        container_id = line.split('\t')[0]
                        logger.info(f"🎯 Contenedor PLEX encontrado: {container_id}")
                        return container_id
            
            logger.warning("⚠️ No se encontró contenedor de PLEX")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando contenedor PLEX: {e}")
            return None
    
    def copy_database_from_container(self, container_id: str) -> Optional[str]:
        """Copia la base de datos del contenedor al sistema local"""
        try:
            # Ruta de la BBDD en el contenedor
            container_db_path = "/config/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"
            
            # Ruta local para la copia
            local_db_path = "./plex_database.db"
            
            # Copiar la BBDD
            logger.info(f"📋 Copiando BBDD de PLEX desde contenedor {container_id}...")
            result = subprocess.run(
                ["docker", "cp", f"{container_id}:{container_db_path}", local_db_path],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✅ BBDD copiada a: {local_db_path}")
                return local_db_path
            else:
                logger.error(f"❌ Error copiando BBDD: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error copiando BBDD: {e}")
            return None
    
    def connect_to_database(self, db_path: str) -> bool:
        """Conecta a la base de datos de PLEX"""
        try:
            if not os.path.exists(db_path):
                logger.error(f"❌ Base de datos no encontrada: {db_path}")
                return False
            
            self.connection = sqlite3.connect(db_path)
            self.db_path = db_path
            logger.info(f"✅ Conectado a BBDD PLEX: {db_path}")
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
            
            # Buscar por ruta de archivo
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
            
            cursor.execute(query, (f"%{file_path}%",))
            result = cursor.fetchone()
            
            if result:
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
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✅ Conexión a BBDD cerrada")


def test_plex_database():
    """Función de prueba para explorar la BBDD de PLEX"""
    explorer = PlexDatabaseExplorer()
    
    try:
        # 1. Encontrar contenedor
        container_id = explorer.find_plex_container()
        if not container_id:
            print("❌ No se encontró contenedor de PLEX")
            return
        
        # 2. Copiar BBDD
        db_path = explorer.copy_database_from_container(container_id)
        if not db_path:
            print("❌ No se pudo copiar la BBDD")
            return
        
        # 3. Conectar
        if not explorer.connect_to_database(db_path):
            print("❌ No se pudo conectar a la BBDD")
            return
        
        # 4. Obtener información
        info = explorer.get_database_info()
        print(f"📊 Información de la BBDD:")
        print(f"   - Películas: {info.get('movie_count', 0)}")
        print(f"   - Archivos: {info.get('file_count', 0)}")
        print(f"   - Tablas: {len(info.get('tables', []))}")
        
        # 5. Buscar película de prueba
        test_movies = explorer.search_movie_by_title("El Libro de la Selva")
        print(f"🎬 Películas encontradas: {len(test_movies)}")
        for movie in test_movies[:3]:  # Mostrar solo las primeras 3
            print(f"   - {movie['title']} ({movie['year']}) - {movie['file_path']}")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        explorer.close()


if __name__ == "__main__":
    test_plex_database()
