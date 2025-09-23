# -*- coding: utf-8 -*-
"""
Integración optimizada con PLEX
Búsqueda rápida + metadatos de PLEX
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class PlexIntegrationOptimized:
    """Integración optimizada con PLEX para búsquedas rápidas"""
    
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'X-Plex-Token': token,
            'Accept': 'application/json'
        })
    
    def enhance_duplicate_group(self, duplicate_group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Añade metadatos de PLEX a un grupo de duplicados"""
        enhanced_group = []
        
        for movie in duplicate_group:
            enhanced_movie = movie.copy()
            
            # Buscar en PLEX por ruta de archivo
            plex_metadata = self._search_by_file_path(movie.get('archivo', ''))
            
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
    
    def _search_by_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca una película por su ruta de archivo"""
        try:
            # Obtener todas las secciones de películas
            sections_url = f"{self.server_url}/library/sections"
            response = self.session.get(sections_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Error obteniendo secciones: {response.status_code}")
                return None
            
            # Parsear secciones
            root = ET.fromstring(response.content)
            
            for section in root.findall('.//Directory'):
                if section.get('type') == 'movie':
                    section_key = section.get('key')
                    metadata = self._search_in_section_by_path(section_key, file_path)
                    if metadata:
                        return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando por ruta: {e}")
            return None
    
    def _search_in_section_by_path(self, section_key: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca en una sección específica por ruta"""
        try:
            # Obtener todos los elementos de la sección
            url = f"{self.server_url}/library/sections/{section_key}/all"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # Parsear resultados
            root = ET.fromstring(response.content)
            
            for video in root.findall('.//Video'):
                # Buscar en los archivos de este video
                for media in video.findall('Media'):
                    for part in media.findall('Part'):
                        plex_file_path = part.get('file', '')
                        
                        # Comparar rutas (flexible)
                        if self._paths_match(file_path, plex_file_path):
                            return self._parse_video_element(video)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando en sección: {e}")
            return None
    
    def _paths_match(self, local_path: str, plex_path: str) -> bool:
        """Compara si dos rutas corresponden al mismo archivo"""
        try:
            # Normalizar rutas
            local_normalized = local_path.replace('\\', '/').lower()
            plex_normalized = plex_path.replace('\\', '/').lower()
            
            # Comparar nombres de archivo
            local_filename = local_normalized.split('/')[-1]
            plex_filename = plex_normalized.split('/')[-1]
            
            # Comparar por nombre de archivo
            if local_filename == plex_filename:
                return True
            
            # Comparar por ruta parcial
            if local_normalized in plex_normalized or plex_normalized in local_normalized:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error comparando rutas: {e}")
            return False
    
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
    
    def test_connection(self) -> bool:
        """Prueba la conexión con PLEX"""
        try:
            url = f"{self.server_url}/status/sessions"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {e}")
            return False


def enhance_duplicates_with_plex_optimized(duplicate_groups: List[List[Dict[str, Any]]], 
                                          server_url: str, token: str) -> List[List[Dict[str, Any]]]:
    """
    Función de conveniencia para añadir metadatos de PLEX a grupos de duplicados
    
    Args:
        duplicate_groups: Lista de grupos de duplicados
        server_url: URL del servidor PLEX
        token: Token de autenticación PLEX
        
    Returns:
        Lista de grupos de duplicados con metadatos de PLEX
    """
    enhancer = PlexIntegrationOptimized(server_url, token)
    
    if not enhancer.test_connection():
        logger.warning("⚠️ No se pudo conectar con PLEX, devolviendo duplicados sin metadatos")
        return duplicate_groups
    
    enhanced_groups = []
    
    for group in duplicate_groups:
        enhanced_group = enhancer.enhance_duplicate_group(group)
        enhanced_groups.append(enhanced_group)
    
    return enhanced_groups


if __name__ == "__main__":
    # Prueba de la función
    test_groups = [
        [
            {
                'archivo': '/path/to/movie1.avi',
                'titulo': 'Movie Title',
                'duracion': 7200
            }
        ]
    ]
    
    # Configuración de prueba
    from src.settings.settings import settings
    server_url = settings.get_plex_server_url()
    token = ""  # Configurar en .env o config.json
    
    enhanced = enhance_duplicates_with_plex_optimized(test_groups, server_url, token)
    print(f"Grupos mejorados: {len(enhanced)}")
