# -*- coding: utf-8 -*-
"""
Servicio principal de integración con PLEX Media Server
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from .plex_authenticator import PlexAuthenticator
from .plex_metadata import PlexMetadataExtractor

logger = logging.getLogger(__name__)


class PlexService:
    """Servicio principal para integración con PLEX Media Server"""
    
    def __init__(self):
        self.authenticator = PlexAuthenticator()
        self.metadata_extractor = None
        self.is_connected = False
        self.current_server = None
        self.libraries = []
    
    def connect(self, username: str = None, password: str = None, token: str = None) -> bool:
        """
        Conecta con PLEX usando credenciales o token
        
        Args:
            username: Usuario de PLEX (opcional, se obtiene de .env)
            password: Contraseña de PLEX (opcional, se obtiene de .env)
            token: Token de PLEX (opcional, se obtiene de .env)
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Obtener credenciales desde variables de entorno si no se proporcionan
            if not username:
                username = os.getenv('PLEX_USER')
            if not password:
                password = os.getenv('PLEX_PASS')
            if not token:
                token = os.getenv('PLEX_TOKEN')
            
            # Intentar con token primero (método recomendado)
            if token:
                logger.info("🔑 Intentando conectar con token de PLEX")
                return self._connect_with_token(token)
            
            # Fallback a usuario/contraseña si no hay token
            if not username or not password:
                logger.error("❌ Credenciales de PLEX no encontradas en variables de entorno")
                logger.info("💡 Agrega PLEX_TOKEN a tu archivo .env o configura PLEX_USER y PLEX_PASS")
                return False
            
            # Autenticar
            if not self.authenticator.authenticate(username, password):
                logger.error("❌ Fallo en autenticación con PLEX")
                return False
            
            # Intentar conectar directamente al servidor local primero
            # Obtener IP del NAS desde configuración
            from src.settings.settings import settings
            nas_ip = settings.get_plex_server_ip()
            
            local_servers = [
                f"http://{nas_ip}:32400",      # IP configurada en .env
                "http://DiskStation:32400",     # Nombre de tu NAS
                "http://localhost:32400",
                "http://127.0.0.1:32400"
            ]
            
            for server_url in local_servers:
                try:
                    logger.info(f"🔍 Probando servidor local: {server_url}")
                    self.metadata_extractor = PlexMetadataExtractor(server_url, self.authenticator.get_token())
                    libraries = self.metadata_extractor.get_libraries()
                    
                    if libraries:
                        self.current_server = {
                            'name': 'Servidor Local',
                            'address': server_url.replace('http://', ''),
                            'port': 32400,
                            'id': 'local',
                            'version': 'Local'
                        }
                        self.libraries = libraries
                        self.is_connected = True
                        logger.info(f"✅ Conectado a PLEX local: {server_url}")
                        return True
                except Exception as e:
                    logger.debug(f"❌ No se pudo conectar a {server_url}: {e}")
                    continue
            
            # Si no funciona con servidores locales, intentar con la API remota
            logger.info("🔍 Intentando conectar con API remota de PLEX...")
            servers = self.authenticator.get_servers()
            if not servers:
                logger.error("❌ No se encontraron servidores PLEX")
                return False
            
            # Usar el primer servidor disponible
            self.current_server = servers[0]
            server_url = f"http://{self.current_server['address']}:{self.current_server['port']}"
            
            # Crear extractor de metadatos
            self.metadata_extractor = PlexMetadataExtractor(
                server_url, 
                self.authenticator.get_token()
            )
            
            # Obtener bibliotecas
            self.libraries = self.metadata_extractor.get_libraries()
            
            self.is_connected = True
            logger.info(f"✅ Conectado a PLEX: {self.current_server['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando con PLEX: {e}")
            return False
    
    def is_configured(self) -> bool:
        """
        Verifica si PLEX está configurado
        
        Returns:
            bool: True si está configurado
        """
        username = os.getenv('PLEX_USER')
        password = os.getenv('PLEX_PASS')
        return bool(username and password)
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con PLEX
        
        Returns:
            bool: True si la conexión es exitosa
        """
        if not self.is_configured():
            return False
        
        return self.connect()
    
    def get_libraries(self) -> List[Dict[str, Any]]:
        """
        Obtiene las bibliotecas disponibles
        
        Returns:
            list: Lista de bibliotecas
        """
        if not self.is_connected:
            return []
        return self.libraries
    
    def get_movies_from_library(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene películas de una biblioteca específica
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            list: Lista de películas
        """
        if not self.is_connected or not self.metadata_extractor:
            return []
        
        return self.metadata_extractor.get_movies_from_library(library_id)
    
    def detect_duplicates_with_plex(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Detecta duplicados usando metadatos de PLEX
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            list: Lista de grupos de duplicados
        """
        if not self.is_connected or not self.metadata_extractor:
            return []
        
        return self.metadata_extractor.get_duplicates_from_plex(library_id)
    
    def get_duplicates_from_library(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene duplicados de una biblioteca específica
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            Lista de grupos de duplicados
        """
        if not self.is_connected or not self.metadata_extractor:
            return []
        
        return self.metadata_extractor.get_duplicates_from_plex(library_id)
    
    def get_library_statistics(self, library_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una biblioteca
        
        Args:
            library_id: ID de la biblioteca
            
        Returns:
            dict: Estadísticas de la biblioteca
        """
        if not self.is_connected or not self.metadata_extractor:
            return {}
        
        return self.metadata_extractor.get_library_statistics(library_id)
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del servidor
        
        Returns:
            dict: Información del servidor
        """
        return self.current_server
    
    def get_movie_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Busca una película por su ruta de archivo usando múltiples estrategias
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            dict: Metadatos de la película si se encuentra
        """
        if not self.is_connected or not self.metadata_extractor:
            return None
        
        try:
            from plexapi.server import PlexServer
            from pathlib import Path
            
            # Crear conexión con PLEX
            server_url = self.metadata_extractor.server_url
            token = self.metadata_extractor.token
            plex = PlexServer(server_url, token)
            
            # Estrategia 1: Búsqueda por ruta exacta
            logger.debug(f"🔍 Buscando por ruta exacta: {file_path}")
            movie = self._search_by_exact_path(plex, file_path)
            if movie:
                logger.debug(f"✅ Encontrado por ruta exacta: {movie.get('title', 'Unknown')}")
                return movie
            
            # Estrategia 2: Búsqueda por nombre de archivo
            filename = Path(file_path).name
            logger.debug(f"🔍 Buscando por nombre de archivo: {filename}")
            movie = self._search_by_filename(plex, filename)
            if movie:
                logger.debug(f"✅ Encontrado por nombre de archivo: {movie.get('title', 'Unknown')}")
                return movie
            
            # Estrategia 3: Búsqueda por título extraído del nombre
            title_from_filename = self._extract_title_from_filename(filename)
            if title_from_filename:
                logger.debug(f"🔍 Buscando por título extraído: {title_from_filename}")
                movie = self._search_by_title(plex, title_from_filename)
                if movie:
                    logger.debug(f"✅ Encontrado por título: {movie.get('title', 'Unknown')}")
                    return movie
            
            logger.debug(f"❌ No encontrado en PLEX: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Error buscando película por ruta: {e}")
            return None
    
    def _search_by_exact_path(self, plex, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca por ruta exacta"""
        try:
            movie_libraries = [lib for lib in plex.library.sections() if lib.type == 'movie']
            
            for library in movie_libraries:
                try:
                    movies = library.all()
                    for movie in movies:
                        if hasattr(movie, 'media') and movie.media:
                            for media in movie.media:
                                if hasattr(media, 'parts') and media.parts:
                                    for part in media.parts:
                                        if part.file and part.file.lower() == file_path.lower():
                                            return self._convert_movie_to_dict(movie, media, part)
                except Exception as e:
                    logger.debug(f"Error en biblioteca {library.title}: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error en búsqueda por ruta exacta: {e}")
        
        return None
    
    def _search_by_filename(self, plex, filename: str) -> Optional[Dict[str, Any]]:
        """Busca por nombre de archivo"""
        try:
            movie_libraries = [lib for lib in plex.library.sections() if lib.type == 'movie']
            
            for library in movie_libraries:
                try:
                    movies = library.all()
                    for movie in movies:
                        if hasattr(movie, 'media') and movie.media:
                            for media in movie.media:
                                if hasattr(media, 'parts') and media.parts:
                                    for part in media.parts:
                                        if part.file:
                                            part_filename = Path(part.file).name
                                            if part_filename.lower() == filename.lower():
                                                return self._convert_movie_to_dict(movie, media, part)
                except Exception as e:
                    logger.debug(f"Error en biblioteca {library.title}: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error en búsqueda por nombre: {e}")
        
        return None
    
    def _search_by_title(self, plex, title: str) -> Optional[Dict[str, Any]]:
        """Busca por título"""
        try:
            # Buscar en todas las bibliotecas de películas
            results = plex.search(title, mediatype='movie')
            
            if results:
                # Tomar el primer resultado que coincida
                movie = results[0]
                if hasattr(movie, 'media') and movie.media:
                    media = movie.media[0]
                    if hasattr(media, 'parts') and media.parts:
                        part = media.parts[0]
                        return self._convert_movie_to_dict(movie, media, part)
        except Exception as e:
            logger.debug(f"Error en búsqueda por título: {e}")
        
        return None
    
    def _extract_title_from_filename(self, filename: str) -> Optional[str]:
        """Extrae título del nombre de archivo"""
        try:
            from pathlib import Path
            import re
            
            # Remover extensión
            name = Path(filename).stem
            
            # Patrones comunes para extraer título
            patterns = [
                r'^(.+?)\s*\(\d{4}\)',  # Título (año)
                r'^(.+?)\s*\[.*\]',      # Título [info]
                r'^(.+?)\s*\.\d{4}',     # Título.año
                r'^(.+?)\s*-\s*',        # Título - info
            ]
            
            for pattern in patterns:
                match = re.match(pattern, name, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    # Limpiar caracteres especiales
                    title = re.sub(r'[._-]', ' ', title)
                    title = re.sub(r'\s+', ' ', title)
                    return title if len(title) > 3 else None
            
            # Si no coincide con patrones, usar el nombre completo
            clean_name = re.sub(r'[._-]', ' ', name)
            clean_name = re.sub(r'\s+', ' ', clean_name)
            return clean_name if len(clean_name) > 3 else None
            
        except Exception as e:
            logger.debug(f"Error extrayendo título: {e}")
            return None
    
    def _convert_movie_to_dict(self, movie, media, part) -> Dict[str, Any]:
        """Convierte objeto movie de plexapi a diccionario"""
        return {
            'id': movie.ratingKey,
            'title': movie.title,
            'year': movie.year,
            'duration': movie.duration,
            'file_path': part.file,
            'size': part.size,
            'resolution': media.videoResolution,
            'bitrate': media.bitrate,
            'container': media.container,
            'video_codec': media.videoCodec,
            'audio_codec': media.audioCodec,
            'added_at': movie.addedAt,
            'updated_at': movie.updatedAt,
            'rating': movie.rating,
            'genres': [g.tag for g in movie.genres] if movie.genres else [],
            'imdb_rating': getattr(movie, 'audienceRating', 0),
            'directors': [d.tag for d in movie.directors] if movie.directors else [],
            'actors': [a.tag for a in movie.actors] if movie.actors else [],
            'studio': movie.studio if hasattr(movie, 'studio') else '',
            'summary': movie.summary if hasattr(movie, 'summary') else '',
            'content_rating': movie.contentRating if hasattr(movie, 'contentRating') else ''
        }
    
    def enhance_duplicate_detection(self, file_movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mejora la detección de duplicados combinando archivos con metadatos de PLEX
        
        Args:
            file_movies: Lista de películas detectadas por archivos
            
        Returns:
            list: Lista mejorada de duplicados
        """
        if not self.is_connected:
            return file_movies
        
        # TEMPORAL: Deshabilitar búsqueda de PLEX para evitar lentitud
        # TODO: Implementar búsqueda optimizada por nombre de archivo
        logger.info("⚠️ Búsqueda de PLEX temporalmente deshabilitada para evitar lentitud")
        logger.info("💡 Usando solo análisis de archivos por ahora")
        
        enhanced_movies = []
        
        for movie in file_movies:
            # Por ahora, solo usar metadatos de archivo
            enhanced_movie = {
                **movie,
                'has_plex_metadata': False,
                'plex_metadata': None,
                'title_plex': movie.get('title', ''),
                'year_plex': movie.get('year', 0),
                'duration_plex': movie.get('duration', 0),
                'rating_plex': 0,
                'genres_plex': [],
                'imdb_rating': 0
            }
            enhanced_movies.append(enhanced_movie)
        
        return enhanced_movies
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de la conexión
        
        Returns:
            dict: Estado de la conexión
        """
        return {
            'is_connected': self.is_connected,
            'is_configured': self.is_configured(),
            'server_info': self.current_server,
            'libraries_count': len(self.libraries),
            'libraries': [lib.get('title', 'Unknown') for lib in self.libraries]
        }
    
    def _connect_with_token(self, token: str) -> bool:
        """
        Conecta con PLEX usando token de acceso
        
        Args:
            token: Token de acceso de PLEX
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Establecer token directamente
            self.authenticator.token = token
            
            # Intentar conectar directamente al servidor local primero
            # Obtener IP del NAS desde configuración
            from src.settings.settings import settings
            nas_ip = settings.get_plex_server_ip()
            
            local_servers = [
                f"http://{nas_ip}:32400",      # IP configurada en .env
                "http://DiskStation:32400",     # Nombre de tu NAS
                "http://localhost:32400",
                "http://127.0.0.1:32400"
            ]
            
            # Probar servidores locales primero (solo los más probables)
            for server_url in local_servers:
                try:
                    logger.info(f"🔍 Probando servidor local: {server_url}")
                    
                    # Crear extractor de metadatos
                    self.metadata_extractor = PlexMetadataExtractor(
                        server_url, 
                        token
                    )
                    
                    # Probar conexión obteniendo bibliotecas
                    libraries = self.metadata_extractor.get_libraries()
                    
                    if libraries:
                        self.current_server = {
                            'name': 'Servidor Local',
                            'address': server_url.replace('http://', ''),
                            'port': 32400,
                            'id': 'local',
                            'version': 'Local'
                        }
                        self.libraries = libraries
                        self.is_connected = True
                        logger.info(f"✅ Conectado a PLEX local: {server_url}")
                        return True
                        
                except Exception as e:
                    logger.debug(f"❌ No se pudo conectar a {server_url}: {e}")
                    continue
            
            # Si no funciona con servidores locales, intentar con la API remota
            logger.info("🔍 Intentando conectar con API remota de PLEX...")
            servers = self.authenticator.get_servers()
            if not servers:
                logger.error("❌ No se encontraron servidores PLEX")
                logger.info("💡 Asegúrate de que PLEX Media Server esté ejecutándose")
                return False
            
            # Usar el primer servidor disponible
            self.current_server = servers[0]
            server_url = f"http://{self.current_server['address']}:{self.current_server['port']}"
            
            # Crear extractor de metadatos
            self.metadata_extractor = PlexMetadataExtractor(
                server_url, 
                token
            )
            
            # Obtener bibliotecas
            self.libraries = self.metadata_extractor.get_libraries()
            
            self.is_connected = True
            logger.info(f"✅ Conectado a PLEX remoto: {self.current_server['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando con token PLEX: {e}")
            return False
