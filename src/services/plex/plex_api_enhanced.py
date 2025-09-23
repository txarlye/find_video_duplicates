# -*- coding: utf-8 -*-
"""
Servicio mejorado de PLEX usando API
Optimizado para búsquedas rápidas de metadatos
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import time

logger = logging.getLogger(__name__)


class PlexAPIEnhanced:
    """Servicio mejorado de PLEX usando API para búsquedas rápidas"""
    
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'X-Plex-Token': token,
            'Accept': 'application/json'
        })
    
    def search_movie_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca una película por su ruta de archivo"""
        try:
            # Buscar por ruta exacta
            encoded_path = quote(file_path)
            url = f"{self.server_url}/library/all?X-Plex-Token={self.token}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"❌ Error en API PLEX: {response.status_code}")
                return None
            
            # Parsear XML (PLEX devuelve XML, no JSON)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Buscar por ruta
            for video in root.findall('.//Video'):
                file_elem = video.find('Media/Part')
                if file_elem is not None:
                    plex_path = file_elem.get('file', '')
                    if file_path in plex_path or plex_path in file_path:
                        return self._parse_video_element(video)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando por ruta: {e}")
            return None
    
    def search_movie_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Busca películas por título"""
        try:
            # Buscar en la biblioteca de películas
            url = f"{self.server_url}/library/sections"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Error obteniendo secciones: {response.status_code}")
                return []
            
            # Parsear secciones
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            movies = []
            for section in root.findall('.//Directory'):
                if section.get('type') == 'movie':
                    section_key = section.get('key')
                    movies.extend(self._search_in_section(section_key, title))
            
            return movies
            
        except Exception as e:
            logger.error(f"❌ Error buscando por título: {e}")
            return []
    
    def _search_in_section(self, section_key: str, title: str) -> List[Dict[str, Any]]:
        """Busca en una sección específica"""
        try:
            # Buscar en la sección
            url = f"{self.server_url}/library/sections/{section_key}/all"
            params = {
                'X-Plex-Token': self.token,
                'title': title
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            # Parsear resultados
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            movies = []
            for video in root.findall('.//Video'):
                movies.append(self._parse_video_element(video))
            
            return movies
            
        except Exception as e:
            logger.error(f"❌ Error buscando en sección: {e}")
            return []
    
    def _parse_video_element(self, video) -> Dict[str, Any]:
        """Parsea un elemento Video de PLEX"""
        try:
            # Información básica
            title = video.get('title', '')
            year = video.get('year', '')
            duration = video.get('duration', '')
            summary = video.get('summary', '')
            rating = video.get('rating', '')
            studio = video.get('studio', '')
            
            # Archivos
            files = []
            for media in video.findall('Media'):
                for part in media.findall('Part'):
                    file_path = part.get('file', '')
                    file_size = part.get('size', '')
                    file_duration = part.get('duration', '')
                    
                    files.append({
                        'path': file_path,
                        'size': int(file_size) if file_size else 0,
                        'duration': int(file_duration) if file_duration else 0
                    })
            
            # Géneros
            genres = []
            for genre in video.findall('Genre'):
                genres.append(genre.get('tag', ''))
            
            return {
                'title': title,
                'year': int(year) if year else None,
                'duration': int(duration) if duration else None,
                'summary': summary,
                'rating': float(rating) if rating else None,
                'studio': studio,
                'genres': genres,
                'files': files
            }
            
        except Exception as e:
            logger.error(f"❌ Error parseando video: {e}")
            return {}
    
    def get_movie_metadata(self, movie_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene metadatos completos de una película"""
        try:
            url = f"{self.server_url}/library/metadata/{movie_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Error obteniendo metadatos: {response.status_code}")
                return None
            
            # Parsear metadatos
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            video = root.find('.//Video')
            if video is not None:
                return self._parse_video_element(video)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadatos: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Prueba la conexión con PLEX"""
        try:
            url = f"{self.server_url}/status/sessions"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {e}")
            return False


def test_plex_api():
    """Función de prueba para la API de PLEX"""
    # Configuración de prueba
    from src.settings.settings import settings
    server_url = settings.get_plex_server_url()
    token = ""  # Configurar en .env o config.json
    
    api = PlexAPIEnhanced(server_url, token)
    
    # Probar conexión
    if api.test_connection():
        print("✅ Conexión con PLEX exitosa")
        
        # Buscar película de prueba
        movies = api.search_movie_by_title("El Libro de la Selva")
        print(f"🎬 Películas encontradas: {len(movies)}")
        
        for movie in movies[:3]:  # Mostrar solo las primeras 3
            print(f"   - {movie['title']} ({movie['year']}) - {movie['duration']}ms")
    else:
        print("❌ No se pudo conectar con PLEX")


if __name__ == "__main__":
    test_plex_api()
