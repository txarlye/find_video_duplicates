#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para integración con la API de IMDB
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from src.settings.settings import settings


class IMDBService:
    """Servicio para obtener información de películas desde IMDB"""
    
    def __init__(self):
        self.api_key = settings.get_imdb_api_key()
        self.base_url = settings.get("imdb.base_url", "https://imdb-api.com")
        self.language = settings.get("imdb.language", "es")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MovieDetector/1.0'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 segundo entre requests
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)

    def _rate_limit(self):
        """Aplica rate limiting para evitar exceder límites de API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Realiza una petición a la API de IMDB
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la petición
            
        Returns:
            Respuesta de la API o None si hay error
        """
        if not self.api_key:
            self.logger.error("API key de IMDB no configurada")
            return None
        
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['apiKey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en petición a IMDB: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error inesperado en IMDB: {e}")
            return None

    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """
        Busca una película por título
        
        Args:
            title: Título de la película
            year: Año de la película (opcional)
            
        Returns:
            Lista de resultados de búsqueda
        """
        self.logger.info(f"Buscando película: {title} ({year})")
        
        params = {
            'expression': title,
            'language': self.language
        }
        
        if year:
            params['expression'] = f"{title} {year}"
        
        response = self._make_request('API/SearchMovie', params)
        
        if not response or 'results' not in response:
            return []
        
        return response['results']

    def get_movie_details(self, movie_id: str) -> Optional[Dict]:
        """
        Obtiene detalles completos de una película
        
        Args:
            movie_id: ID de la película en IMDB
            
        Returns:
            Detalles de la película o None si hay error
        """
        self.logger.info(f"Obteniendo detalles de película: {movie_id}")
        
        response = self._make_request('API/Title', {
            'id': movie_id,
            'language': self.language
        })
        
        return response

    def get_movie_poster(self, movie_id: str) -> Optional[str]:
        """
        Obtiene la URL del póster de una película
        
        Args:
            movie_id: ID de la película en IMDB
            
        Returns:
            URL del póster o None si hay error
        """
        details = self.get_movie_details(movie_id)
        
        if not details or 'image' not in details:
            return None
        
        return details['image']

    def find_best_match(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Encuentra la mejor coincidencia para una película
        
        Args:
            title: Título de la película
            year: Año de la película
            
        Returns:
            Mejor coincidencia encontrada
        """
        results = self.search_movie(title, year)
        
        if not results:
            return None
        
        # Si hay año, priorizar resultados del mismo año
        if year:
            for result in results:
                if 'description' in result and str(year) in result['description']:
                    return result
        
        # Retornar el primer resultado (más relevante)
        return results[0]

    def get_movie_info(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Obtiene información completa de una película
        
        Args:
            title: Título de la película
            year: Año de la película
            
        Returns:
            Información completa de la película
        """
        # Buscar la película
        match = self.find_best_match(title, year)
        
        if not match:
            return None
        
        # Obtener detalles completos
        details = self.get_movie_details(match['id'])
        
        if not details:
            return None
        
        # Formatear información
        return self._format_movie_info(details)

    def _format_movie_info(self, details: Dict) -> Dict:
        """
        Formatea la información de la película para uso interno
        
        Args:
            details: Detalles raw de IMDB
            
        Returns:
            Información formateada
        """
        return {
            'id': details.get('id', ''),
            'title': details.get('title', ''),
            'original_title': details.get('originalTitle', ''),
            'year': details.get('year', ''),
            'runtime': details.get('runtimeStr', ''),
            'plot': details.get('plot', ''),
            'genres': details.get('genres', ''),
            'directors': details.get('directors', ''),
            'writers': details.get('writers', ''),
            'stars': details.get('stars', ''),
            'rating': details.get('imDbRating', ''),
            'votes': details.get('imDbRatingVotes', ''),
            'poster_url': details.get('image', ''),
            'languages': details.get('languages', ''),
            'countries': details.get('countries', ''),
            'content_rating': details.get('contentRating', ''),
            'release_date': details.get('releaseDate', ''),
            'awards': details.get('awards', ''),
            'box_office': details.get('boxOffice', ''),
            'company': details.get('company', ''),
            'tagline': details.get('tagline', '')
        }

    def download_poster(self, poster_url: str, output_path: Path) -> bool:
        """
        Descarga el póster de una película
        
        Args:
            poster_url: URL del póster
            output_path: Ruta donde guardar el póster
            
        Returns:
            True si se descargó correctamente
        """
        if not poster_url:
            return False
        
        try:
            self._rate_limit()
            response = self.session.get(poster_url, timeout=30)
            response.raise_for_status()
            
            # Crear directorio si no existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar imagen
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Póster descargado: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error descargando póster: {e}")
            return False

    def is_api_configured(self) -> bool:
        """Verifica si la API está configurada correctamente"""
        return bool(self.api_key)

    def test_connection(self) -> bool:
        """Prueba la conexión con la API"""
        if not self.is_api_configured():
            return False
        
        try:
            # Buscar una película conocida para probar
            response = self._make_request('API/SearchMovie', {
                'expression': 'The Matrix',
                'language': self.language
            })
            return response is not None and 'results' in response
        except Exception:
            return False
