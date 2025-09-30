#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para buscar información de películas en Plex e IMDB
"""

import os
import sqlite3
import requests
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
import json

class ImdbMovieFinder:
    """Buscador de información de películas en Plex e IMDB"""
    
    def __init__(self, plex_database_path: str, omdb_api_key: str = None):
        """
        Inicializa el buscador de películas
        
        Args:
            plex_database_path: Ruta a la base de datos de Plex
            omdb_api_key: Clave API de OMDB (opcional)
        """
        self.plex_database_path = plex_database_path
        self.omdb_api_key = omdb_api_key
        self.logger = logging.getLogger(__name__)
        
        # URLs de APIs
        self.omdb_url = "http://www.omdbapi.com/"
        self.tmdb_url = "https://api.themoviedb.org/3/"
        
    def find_movie_by_filename(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Busca información de una película por nombre de archivo
        
        Args:
            file_path: Ruta del archivo de video
            
        Returns:
            Diccionario con información de la película o None
        """
        try:
            filename = os.path.basename(file_path)
            self.logger.info(f"Buscando información para: {filename}")
            
            # 1. Buscar en Plex primero
            plex_info = self._search_in_plex(filename)
            
            # 2. Si encontramos info en Plex, usarla como base
            if plex_info:
                self.logger.info(f"Información encontrada en Plex: {plex_info.get('title', 'N/A')}")
                
                # 3. Buscar información adicional en IMDB/OMDB
                imdb_info = self._search_in_imdb(plex_info.get('title', ''), plex_info.get('year', ''))
                
                # 4. Combinar información
                combined_info = self._combine_movie_info(plex_info, imdb_info)
                return combined_info
            else:
                # 5. Si no hay info en Plex, intentar extraer del nombre del archivo
                extracted_info = self._extract_info_from_filename(filename)
                if extracted_info:
                    imdb_info = self._search_in_imdb(extracted_info.get('title', ''), extracted_info.get('year', ''))
                    combined_info = self._combine_movie_info(extracted_info, imdb_info)
                    return combined_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando información de película: {e}")
            return None
    
    def _search_in_plex(self, filename: str) -> Optional[Dict[str, Any]]:
        """Busca información de la película en la base de datos de Plex"""
        try:
            if not os.path.exists(self.plex_database_path):
                self.logger.warning("Base de datos de Plex no encontrada")
                return None
            
            # Conectar a la base de datos de Plex (solo lectura)
            conn = sqlite3.connect(f"file:{self.plex_database_path}?mode=ro", uri=True)
            cur = conn.cursor()
            
            # Buscar por nombre de archivo en media_parts
            sql = """
            SELECT 
                mi.title,
                mi.year,
                mi.summary,
                mi.rating,
                mi.duration,
                mi.studio,
                ls.name as library_name,
                mp.file
            FROM media_items mi
            JOIN library_sections ls ON mi.library_section_id = ls.id
            JOIN media_parts mp ON mi.id = mp.media_item_id
            WHERE mp.file LIKE ? AND ls.section_type = 1
            ORDER BY mi.title
            """
            
            # Buscar con diferentes patrones
            search_patterns = [
                f"%{filename}%",
                f"%{os.path.splitext(filename)[0]}%",
                f"%{filename.replace(' ', '%')}%"
            ]
            
            for pattern in search_patterns:
                cur.execute(sql, (pattern,))
                result = cur.fetchone()
                if result:
                    conn.close()
                    return {
                        'title': result[0],
                        'year': result[1],
                        'summary': result[2],
                        'rating': result[3],
                        'duration': result[4],
                        'studio': result[5],
                        'library_name': result[6],
                        'file_path': result[7],
                        'source': 'plex'
                    }
            
            conn.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando en Plex: {e}")
            return None
    
    def _search_in_imdb(self, title: str, year: str = None) -> Optional[Dict[str, Any]]:
        """Busca información adicional en IMDB/OMDB"""
        try:
            if not self.omdb_api_key:
                self.logger.warning("API key de OMDB no configurada")
                return None
            
            # Construir parámetros de búsqueda
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'plot': 'full'
            }
            
            if year:
                params['y'] = year
            
            # Realizar búsqueda
            response = requests.get(self.omdb_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') == 'True':
                return {
                    'imdb_id': data.get('imdbID'),
                    'imdb_rating': data.get('imdbRating'),
                    'imdb_votes': data.get('imdbVotes'),
                    'plot': data.get('Plot'),
                    'poster': data.get('Poster'),
                    'genre': data.get('Genre'),
                    'director': data.get('Director'),
                    'actors': data.get('Actors'),
                    'awards': data.get('Awards'),
                    'source': 'imdb'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando en IMDB: {e}")
            return None
    
    def _extract_info_from_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Extrae información básica del nombre del archivo"""
        try:
            # Remover extensión
            name_without_ext = os.path.splitext(filename)[0]
            
            # Patrones comunes para extraer año
            import re
            year_match = re.search(r'\((\d{4})\)', name_without_ext)
            year = year_match.group(1) if year_match else None
            
            # Remover año del título
            title = re.sub(r'\(\d{4}\)', '', name_without_ext).strip()
            
            # Limpiar caracteres especiales
            title = re.sub(r'[._-]', ' ', title)
            title = ' '.join(title.split())  # Remover espacios múltiples
            
            return {
                'title': title,
                'year': year,
                'source': 'filename'
            }
            
        except Exception as e:
            self.logger.error(f"Error extrayendo información del archivo: {e}")
            return None
    
    def _combine_movie_info(self, plex_info: Dict, imdb_info: Dict) -> Dict[str, Any]:
        """Combina información de Plex e IMDB"""
        combined = {}
        
        # Información de Plex (prioridad)
        if plex_info:
            combined.update(plex_info)
        
        # Información de IMDB (complementaria)
        if imdb_info:
            combined.update({
                'imdb_id': imdb_info.get('imdb_id'),
                'imdb_rating': imdb_info.get('imdb_rating'),
                'imdb_votes': imdb_info.get('imdb_votes'),
                'plot': imdb_info.get('plot') or combined.get('summary'),
                'poster': imdb_info.get('poster'),
                'genre': imdb_info.get('genre'),
                'director': imdb_info.get('director'),
                'actors': imdb_info.get('actors'),
                'awards': imdb_info.get('awards')
            })
        
        # Asegurar que tenemos al menos título
        if not combined.get('title'):
            combined['title'] = 'Película Desconocida'
        
        return combined
    
    def get_poster_image(self, poster_url: str) -> Optional[bytes]:
        """Descarga la imagen del póster"""
        try:
            if not poster_url or poster_url == 'N/A':
                return None
            
            response = requests.get(poster_url, timeout=10)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error descargando póster: {e}")
            return None
    
    def format_movie_message(self, movie_info: Dict[str, Any]) -> str:
        """Formatea la información de la película para envío"""
        try:
            title = movie_info.get('title', 'Película Desconocida')
            year = movie_info.get('year', '')
            rating = movie_info.get('imdb_rating', movie_info.get('rating', ''))
            plot = movie_info.get('plot', movie_info.get('summary', ''))
            director = movie_info.get('director', '')
            actors = movie_info.get('actors', '')
            genre = movie_info.get('genre', '')
            
            message = f"🎬 **{title}**"
            if year:
                message += f" ({year})"
            
            message += "\n\n"
            
            if rating:
                message += f"⭐ **Rating:** {rating}\n"
            
            if director:
                message += f"🎭 **Director:** {director}\n"
            
            if actors:
                message += f"👥 **Actores:** {actors}\n"
            
            if genre:
                message += f"🎭 **Género:** {genre}\n"
            
            if plot:
                message += f"\n📖 **Sinopsis:**\n{plot}\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formateando mensaje: {e}")
            return f"🎬 {movie_info.get('title', 'Película Desconocida')}"
