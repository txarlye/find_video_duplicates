#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para obtener información de películas desde IMDB
"""

import requests
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import re

from src.settings.settings import settings


class IMDBService:
    """
    Servicio para obtener información de películas desde IMDB
    """
    
    def __init__(self):
        self.api_key = settings.get_imdb_api_key()
        self.base_url = settings.get_imdb_base_url()
        self.language = settings.get_imdb_language()
        self.logger = logging.getLogger(__name__)
        
    def verificar_configuracion(self) -> bool:
        """Verifica si la configuración de IMDB está completa"""
        # IMDB API Dev no requiere API key, es gratuita
        return True
    
    def extraer_titulo_y_ano(self, nombre_archivo: str) -> Tuple[str, Optional[int]]:
        """
        Extrae título y año del nombre del archivo
        """
        # Remover extensión
        nombre = Path(nombre_archivo).stem
        
        # Patrones comunes para extraer año
        patrones_ano = [
            r'\((\d{4})\)',  # (2024)
            r'\[(\d{4})\]',  # [2024]
            r'\.(\d{4})\.',  # .2024.
            r'(\d{4})',      # 2024
        ]
        
        ano = None
        for patron in patrones_ano:
            match = re.search(patron, nombre)
            if match:
                try:
                    ano = int(match.group(1))
                    # Verificar que el año sea razonable (1900-2030)
                    if 1900 <= ano <= 2030:
                        break
                except ValueError:
                    continue
        
        # Limpiar título removiendo año y otros patrones
        titulo = nombre
        for patron in patrones_ano:
            titulo = re.sub(patron, '', titulo)
        
        # Limpiar caracteres especiales y espacios extra
        titulo = re.sub(r'[\[\](){}]', '', titulo)
        titulo = re.sub(r'[._-]+', ' ', titulo)
        titulo = re.sub(r'\s+', ' ', titulo).strip()
        
        return titulo, ano
    
    def buscar_pelicula(self, titulo: str, ano: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Busca una película en IMDB usando la API gratuita
        """
        if not self.verificar_configuracion():
            return None
        
        try:
            # Construir query de búsqueda
            query = titulo
            if ano:
                query += f" {ano}"
            
            # Buscar película usando la API gratuita
            search_url = f"{self.base_url}/search"
            params = {
                'q': query
            }
            
            self.logger.info(f"Buscando: {query} en {search_url}")
            response = requests.get(search_url, params=params, timeout=10)
            
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response text: {response.text[:200]}...")
            
            if response.status_code != 200:
                self.logger.error(f"Error en búsqueda IMDB: {response.status_code}")
                return None
            
            data = response.json()
            if not data.get('results') or len(data['results']) == 0:
                self.logger.warning(f"No se encontraron resultados para: {titulo}")
                return None
            
            # Obtener el primer resultado (más relevante)
            movie_data = data['results'][0]
            
            # Formatear información directamente desde la búsqueda
            return self._formatear_datos_pelicula(movie_data)
            
        except Exception as e:
            self.logger.error(f"Error buscando película '{titulo}': {str(e)}")
            return None
    
    def _formatear_datos_pelicula(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea los datos de la película desde la API gratuita
        """
        try:
            # Extraer información básica
            titulo = movie_data.get('title', '')
            ano = movie_data.get('year', '')
            duracion = movie_data.get('runtime', '')
            genero = movie_data.get('genres', [])
            director = movie_data.get('director', [])
            actores = movie_data.get('cast', [])
            sinopsis = movie_data.get('plot', '')
            poster_url = movie_data.get('poster', '')
            rating = movie_data.get('rating', '')
            imdb_id = movie_data.get('id', '')
            
            # Formatear géneros
            if isinstance(genero, list):
                genero = ', '.join(genero)
            
            # Formatear directores
            if isinstance(director, list):
                director = ', '.join(director)
            
            # Formatear actores (tomar solo los primeros 3)
            if isinstance(actores, list):
                actores = ', '.join(actores[:3])
            
            # Formatear duración
            if duracion and isinstance(duracion, (int, float)):
                duracion = f"{duracion} minutos"
            
            return {
                'titulo': titulo,
                'titulo_original': titulo,  # La API gratuita no distingue entre original y traducido
                'ano': str(ano) if ano else '',
                'duracion': duracion,
                'genero': genero,
                'director': director,
                'actores': actores,
                'sinopsis': sinopsis,
                'poster_url': poster_url,
                'rating': str(rating) if rating else '',
                'id': imdb_id
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando datos de película: {str(e)}")
            return {}
    
    def formatear_informacion_telegram(self, info: Dict[str, Any], archivo_path: str) -> str:
        """
        Formatea la información de la película para Telegram
        """
        # Extraer información del archivo
        archivo = Path(archivo_path)
        nombre_archivo = archivo.name
        
        # Determinar calidad y formato
        calidad = "Desconocida"
        formato = archivo.suffix.upper().replace('.', '')
        
        # Detectar calidad en el nombre del archivo
        if '4K' in nombre_archivo.upper() or '2160P' in nombre_archivo.upper():
            calidad = "4K"
        elif '1080P' in nombre_archivo.upper() or '1080P' in nombre_archivo.upper():
            calidad = "1080p"
        elif '720P' in nombre_archivo.upper() or '720P' in nombre_archivo.upper():
            calidad = "720p"
        elif 'HD' in nombre_archivo.upper():
            calidad = "HD"
        
        # Detectar audio
        audio = "Desconocido"
        if 'ESPAÑOL' in nombre_archivo.upper() or 'CASTELLANO' in nombre_archivo.upper():
            audio = "Castellano"
        elif 'LATINO' in nombre_archivo.upper():
            audio = "Latino"
        elif 'SUB' in nombre_archivo.upper() or 'SUBS' in nombre_archivo.upper():
            audio = "Subtítulos"
        
        # Construir mensaje
        mensaje = f"🎬 **{info.get('titulo', 'Título no disponible')}**"
        
        if info.get('titulo_original') and info.get('titulo_original') != info.get('titulo'):
            mensaje += f"\n📝 Título original: {info.get('titulo_original')}"
        
        if info.get('ano'):
            mensaje += f"\n📅 Año: {info.get('ano')}"
        
        if info.get('duracion'):
            mensaje += f"\n⏱️ Duración: {info.get('duracion')}"
        
        if info.get('genero'):
            mensaje += f"\n🎭 Género: {info.get('genero')}"
        
        if info.get('director'):
            mensaje += f"\n🎬 Director: {info.get('director')}"
        
        if info.get('actores'):
            mensaje += f"\n👥 Actores: {info.get('actores')}"
        
        if info.get('rating'):
            mensaje += f"\n⭐ Rating: {info.get('rating')}/10"
        
        mensaje += f"\n\n📁 **Archivo:** {nombre_archivo}"
        mensaje += f"\n🎥 **Formato:** {formato} {calidad}"
        mensaje += f"\n🔊 **Audio:** {audio}"
        
        if info.get('sinopsis'):
            mensaje += f"\n\n📖 **Sinopsis:**\n\n{info.get('sinopsis')}"
        
        return mensaje
    
    def obtener_poster(self, info: Dict[str, Any]) -> Optional[bytes]:
        """
        Descarga el póster de la película
        """
        if not info.get('poster_url'):
            return None
        
        try:
            response = requests.get(info['poster_url'], timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            self.logger.error(f"Error descargando póster: {str(e)}")
        
        return None
