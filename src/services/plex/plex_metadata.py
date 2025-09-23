# -*- coding: utf-8 -*-
"""
Extractor de metadatos de PLEX Media Server
"""

import requests
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PlexMetadataExtractor:
    """Extrae metadatos y estadísticas de PLEX Media Server"""
    
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.api_url = f"{self.server_url}/library"
    
    def get_libraries(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las bibliotecas de PLEX
        
        Returns:
            list: Lista de bibliotecas disponibles
        """
        try:
            url = f"{self.api_url}/sections"
            headers = {
                "X-Plex-Token": self.token,
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                libraries = []
                
                for section in data.get('MediaContainer', {}).get('Directory', []):
                    if section.get('type') in ['movie', 'show']:
                        library_info = {
                            'id': section.get('key'),
                            'title': section.get('title'),
                            'type': section.get('type'),
                            'agent': section.get('agent'),
                            'scanner': section.get('scanner'),
                            'language': section.get('language'),
                            'refreshed_at': section.get('refreshedAt'),
                            'created_at': section.get('createdAt')
                        }
                        libraries.append(library_info)
                
                logger.info(f"✅ Encontradas {len(libraries)} bibliotecas PLEX")
                return libraries
            else:
                logger.error(f"❌ Error obteniendo bibliotecas: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo bibliotecas PLEX: {e}")
            return []
    
    def get_movies_from_library(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las películas de una biblioteca específica
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            list: Lista de películas con metadatos
        """
        try:
            url = f"{self.api_url}/sections/{library_id}/all"
            headers = {
                "X-Plex-Token": self.token,
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                movies = []
                
                for item in data.get('MediaContainer', {}).get('Metadata', []):
                    if item.get('type') == 'movie':
                        movie_info = self._extract_movie_metadata(item)
                        movies.append(movie_info)
                
                logger.info(f"✅ Obtenidas {len(movies)} películas de la biblioteca {library_id}")
                return movies
            else:
                logger.error(f"❌ Error obteniendo películas: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo películas PLEX: {e}")
            return []
    
    def _extract_movie_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae metadatos de una película individual
        
        Args:
            item: Datos de la película desde PLEX
            
        Returns:
            dict: Metadatos procesados de la película
        """
        # Información básica
        metadata = {
            'plex_id': item.get('ratingKey'),
            'title': item.get('title'),
            'year': item.get('year'),
            'duration': item.get('duration', 0) // 1000,  # Convertir a segundos
            'summary': item.get('summary', ''),
            'rating': item.get('rating', 0),
            'audience_rating': item.get('audienceRating', 0),
            'content_rating': item.get('contentRating', ''),
            'studio': item.get('studio', ''),
            'added_at': item.get('addedAt'),
            'updated_at': item.get('updatedAt'),
            'view_count': item.get('viewCount', 0),
            'last_viewed': item.get('lastViewedAt'),
            'file_path': '',
            'file_size': 0,
            'video_codec': '',
            'audio_codec': '',
            'resolution': '',
            'bitrate': 0
        }
        
        # Información de archivos
        media = item.get('Media', [])
        if media:
            media_info = media[0]
            metadata['file_size'] = media_info.get('size', 0)
            metadata['bitrate'] = media_info.get('bitrate', 0)
            metadata['video_codec'] = media_info.get('videoCodec', '')
            metadata['audio_codec'] = media_info.get('audioCodec', '')
            metadata['resolution'] = media_info.get('videoResolution', '')
            
            # Obtener ruta del archivo
            parts = media_info.get('Part', [])
            if parts:
                metadata['file_path'] = parts[0].get('file', '')
        
        # Géneros
        genres = item.get('Genre', [])
        metadata['genres'] = [genre.get('tag', '') for genre in genres]
        
        # Directores
        directors = item.get('Director', [])
        metadata['directors'] = [director.get('tag', '') for director in directors]
        
        # Actores
        actors = item.get('Role', [])
        metadata['actors'] = [actor.get('tag', '') for actor in actors]
        
        # Calificaciones
        ratings = item.get('Rating', [])
        metadata['imdb_rating'] = 0
        metadata['tmdb_rating'] = 0
        
        for rating in ratings:
            if rating.get('source') == 'imdb':
                metadata['imdb_rating'] = float(rating.get('rating', 0))
            elif rating.get('source') == 'themoviedb':
                metadata['tmdb_rating'] = float(rating.get('rating', 0))
        
        return metadata
    
    def get_duplicates_from_plex(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Detecta duplicados usando python-plexapi como PlexDeDupe
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            list: Lista de grupos de duplicados
        """
        try:
            # Usar python-plexapi como PlexDeDupe
            from plexapi.server import PlexServer
            
            # Crear conexión con PLEX usando python-plexapi
            server_url = self.server_url
            plex = PlexServer(server_url, self.token)
            
            # Obtener la biblioteca
            library = plex.library.sectionByID(int(library_id))
            
            # Obtener todas las películas
            movies = library.all()
            
            # Agrupar por título y año (método de PlexDeDupe)
            title_groups = {}
            for movie in movies:
                # Usar título y año como clave
                key = f"{movie.title}_{movie.year}"
                if key not in title_groups:
                    title_groups[key] = []
                title_groups[key].append(movie)
            
            # Identificar grupos con múltiples elementos
            duplicates = []
            for key, group in title_groups.items():
                if len(group) > 1:
                    # Convertir a formato compatible
                    group_movies = []
                    for movie in group:
                        movie_info = {
                            'id': movie.ratingKey,
                            'title': movie.title,
                            'year': movie.year,
                            'duration': movie.duration,
                            'file_path': movie.media[0].parts[0].file if movie.media else '',
                            'size': movie.media[0].parts[0].size if movie.media else 0,
                            'resolution': movie.media[0].videoResolution if movie.media else '',
                            'bitrate': movie.media[0].bitrate if movie.media else 0,
                            'container': movie.media[0].container if movie.media else '',
                            'video_codec': movie.media[0].videoCodec if movie.media else '',
                            'audio_codec': movie.media[0].audioCodec if movie.media else '',
                            'added_at': movie.addedAt,
                            'updated_at': movie.updatedAt
                        }
                        group_movies.append(movie_info)
                    
                    duplicate_group = {
                        'title': group_movies[0]['title'],
                        'year': group_movies[0]['year'],
                        'count': len(group_movies),
                        'movies': group_movies,
                        'similarity_score': 1.0,
                        'plex_detected': True
                    }
                    duplicates.append(duplicate_group)
            
            logger.info(f"✅ PLEX detectó {len(duplicates)} grupos de duplicados usando python-plexapi")
            return duplicates
            
        except ImportError:
            logger.error("❌ python-plexapi no está instalado")
            logger.info("💡 Instala con: pip install python-plexapi")
            return self._find_duplicates_manually(library_id)
        except Exception as e:
            logger.error(f"❌ Error detectando duplicados con python-plexapi: {e}")
            return self._find_duplicates_manually(library_id)
    
    def _find_duplicates_manually(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Encuentra duplicados manualmente con lógica mejorada
        """
        try:
            movies = self.get_movies_from_library(library_id)
            duplicates = []
            processed = set()
            
            for i, movie1 in enumerate(movies):
                movie1_id = movie1.get('id', f"movie_{i}")
                if movie1_id in processed:
                    continue
                
                movie_duplicates = [movie1]
                processed.add(movie1_id)
                
                for j, movie2 in enumerate(movies[i+1:], i+1):
                    movie2_id = movie2.get('id', f"movie_{j}")
                    if movie2_id in processed:
                        continue
                    
                    # Usar lógica de similitud mejorada
                    if self._are_same_movie(movie1, movie2):
                        movie_duplicates.append(movie2)
                        processed.add(movie2_id)
                
                if len(movie_duplicates) > 1:
                    duplicate_group = {
                        'title': movie_duplicates[0]['title'],
                        'year': movie_duplicates[0]['year'],
                        'count': len(movie_duplicates),
                        'movies': movie_duplicates,
                        'similarity_score': 0.95,  # Alta similitud
                        'plex_detected': False
                    }
                    duplicates.append(duplicate_group)
            
            logger.info(f"✅ Análisis manual detectó {len(duplicates)} grupos de duplicados")
            return duplicates
            
        except Exception as e:
            logger.error(f"❌ Error en análisis manual: {e}")
            return []
    
    def _are_same_movie(self, movie1: Dict, movie2: Dict) -> bool:
        """
        Determina si dos películas son la misma con lógica MUY estricta
        """
        # Comparar títulos con lógica más estricta
        title1 = movie1['title'].lower().strip()
        title2 = movie2['title'].lower().strip()
        
        # Remover caracteres especiales y normalizar
        import re
        title1_clean = re.sub(r'[^\w\s]', '', title1)
        title2_clean = re.sub(r'[^\w\s]', '', title2)
        
        # LÓGICA MUY ESTRICTA: Solo considerar duplicados si:
        # 1. Títulos son prácticamente idénticos (90%+ similitud)
        # 2. Años coinciden exactamente o con diferencia de ±1 año
        # 3. Duración es muy similar (±2 minutos máximo)
        
        # Calcular similitud de títulos usando distancia de Levenshtein
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]
        
        # Calcular similitud de títulos
        max_len = max(len(title1_clean), len(title2_clean))
        if max_len == 0:
            return False
        
        distance = levenshtein_distance(title1_clean, title2_clean)
        similarity = 1 - (distance / max_len)
        
        # Solo considerar duplicados si similitud > 90%
        title_match = similarity > 0.9
        
        if not title_match:
            return False
        
        # Verificar año (tolerancia de ±1 año)
        year1 = movie1.get('year', 0)
        year2 = movie2.get('year', 0)
        
        if year1 and year2:
            year_match = abs(year1 - year2) <= 1
        else:
            year_match = True  # Si no hay año, asumir que coincide
        
        # Verificar duración (tolerancia de ±2 minutos)
        duration1 = movie1.get('duration', 0)
        duration2 = movie2.get('duration', 0)
        
        if duration1 and duration2:
            duration_match = abs(duration1 - duration2) <= 120000  # 2 minutos en ms
        else:
            duration_match = True  # Si no hay duración, asumir que coincide
        
        # Log para debugging
        if title_match and year_match and duration_match:
            logger.info(f"DUPLICADO DETECTADO: '{movie1['title']}' vs '{movie2['title']}' (similitud: {similarity:.2f})")
        
        return title_match and year_match and duration_match
    
    def get_library_statistics(self, library_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una biblioteca
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            dict: Estadísticas de la biblioteca
        """
        try:
            movies = self.get_movies_from_library(library_id)
            
            if not movies:
                return {}
            
            # Estadísticas básicas
            total_movies = len(movies)
            total_size = sum(movie.get('file_size', 0) for movie in movies)
            total_duration = sum(movie.get('duration', 0) for movie in movies)
            
            # Estadísticas por año
            years = {}
            for movie in movies:
                year = movie.get('year', 0)
                if year:
                    years[year] = years.get(year, 0) + 1
            
            # Estadísticas por género
            genres = {}
            for movie in movies:
                for genre in movie.get('genres', []):
                    genres[genre] = genres.get(genre, 0) + 1
            
            # Estadísticas de calidad
            resolutions = {}
            codecs = {}
            for movie in movies:
                res = movie.get('resolution', 'Unknown')
                codec = movie.get('video_codec', 'Unknown')
                resolutions[res] = resolutions.get(res, 0) + 1
                codecs[codec] = codecs.get(codec, 0) + 1
            
            statistics = {
                'total_movies': total_movies,
                'total_size_gb': round(total_size / (1024**3), 2),
                'total_duration_hours': round(total_duration / 3600, 2),
                'average_rating': round(sum(movie.get('rating', 0) for movie in movies) / total_movies, 2),
                'years_distribution': dict(sorted(years.items())),
                'genres_distribution': dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]),
                'resolutions_distribution': resolutions,
                'codecs_distribution': codecs,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Estadísticas calculadas para {total_movies} películas")
            return statistics
            
        except Exception as e:
            logger.error(f"❌ Error calculando estadísticas: {e}")
            return {}
