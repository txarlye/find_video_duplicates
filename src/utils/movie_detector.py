#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidad para detectar películas duplicadas
Integrada como utilidad de la aplicación Streamlit
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any
from collections import defaultdict
from difflib import SequenceMatcher

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from src.settings.settings import settings

# Importación opcional de PLEX
try:
    from src.services.plex import PlexService
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False


class MovieDetector:
    """Clase para detectar películas duplicadas integrada con la configuración"""
    
    def __init__(self, carpeta_raiz: str = None, use_plex: bool = False):
        """
        Inicializa el detector con la carpeta raíz
        
        Args:
            carpeta_raiz: Ruta de la carpeta a analizar (opcional)
            use_plex: Si usar integración con PLEX (opcional)
        """
        self.carpeta_raiz = Path(carpeta_raiz) if carpeta_raiz else None
        self.peliculas = []
        self.duplicados = []
        self.use_plex = use_plex and PLEX_AVAILABLE
        
        # Inicializar servicio PLEX si está disponible
        self.plex_service = None
        if self.use_plex and PLEX_AVAILABLE:
            self.plex_service = PlexService()
            if not self.plex_service.is_configured():
                self.logger.warning("PLEX configurado pero credenciales no encontradas")
                self.use_plex = False
            elif not self.plex_service.connect():
                self.logger.warning("No se pudo conectar con PLEX")
                self.use_plex = False
        
        # Obtener configuración desde settings
        self.extensiones_video = set(settings.get_supported_extensions())
        self.umbral_similitud = settings.get_similarity_threshold()
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Patrones para extraer información de archivos
        self.patrones_titulo = [
            r'^(.+?)\s*\(\d{4}\)',  # Título (Año)
            r'^(.+?)\s*\[\d{4}\]',  # Título [Año]
            r'^(.+?)\s*\d{4}',      # Título Año
            r'^(.+?)(?:\s*-\s*.+)?$'  # Título - resto
        ]
        
        self.patrones_calidad = [
            r'(?:1080p|720p|480p|360p|2160p|4K)',
            r'(?:HD|FHD|UHD)',
            r'(?:BluRay|BRRip|BDRip|DVDRip|HDRip|WEBRip)',
            r'(?:x264|x265|H\.264|H\.265)'
        ]
    
    def set_carpeta_raiz(self, carpeta_raiz: str):
        """Establece la carpeta raíz a analizar"""
        self.carpeta_raiz = Path(carpeta_raiz)
        self.peliculas = []
        self.duplicados = []
    
    def set_plex_integration(self, use_plex: bool):
        """
        Activa o desactiva la integración con PLEX
        
        Args:
            use_plex: Si usar integración con PLEX
        """
        self.use_plex = use_plex and PLEX_AVAILABLE
        
        if self.use_plex and not self.plex_service:
            self.plex_service = PlexService()
            if not self.plex_service.is_configured():
                self.logger.warning("PLEX configurado pero credenciales no encontradas")
                self.use_plex = False
            elif not self.plex_service.connect():
                self.logger.warning("No se pudo conectar con PLEX")
                self.use_plex = False
        elif not self.use_plex:
            self.plex_service = None
    
    def is_plex_available(self) -> bool:
        """
        Verifica si PLEX está disponible y configurado
        
        Returns:
            bool: True si PLEX está disponible
        """
        return self.use_plex and self.plex_service is not None and self.plex_service.is_connected
    
    def get_plex_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de la conexión con PLEX
        
        Returns:
            dict: Estado de PLEX
        """
        if not self.plex_service:
            return {
                'available': False,
                'connected': False,
                'configured': False,
                'message': 'PLEX no configurado'
            }
        
        status = self.plex_service.get_connection_status()
        return {
            'available': PLEX_AVAILABLE,
            'connected': status['is_connected'],
            'configured': status['is_configured'],
            'server_info': status['server_info'],
            'libraries': status['libraries'],
            'message': 'PLEX conectado' if status['is_connected'] else 'PLEX no conectado'
        }
    
    def es_archivo_video(self, archivo: Path) -> bool:
        """Verifica si un archivo es de video"""
        return archivo.suffix.lower() in self.extensiones_video
    
    def obtener_duracion_video(self, archivo: Path) -> float:
        """
        Obtiene la duración del video en segundos
        
        Args:
            archivo: Ruta del archivo de video
            
        Returns:
            Duración en segundos, o 0 si no se puede obtener
        """
        if not MUTAGEN_AVAILABLE:
            return 0.0
        
        try:
            # Verificar que el archivo existe y es accesible
            if not archivo.exists():
                self.logger.debug(f"Archivo no existe: {archivo}")
                return 0.0
            
            # Intentar obtener duración con mutagen
            audio_file = MutagenFile(str(archivo))
            if audio_file is not None and hasattr(audio_file, 'info'):
                duration = audio_file.info.length
                if duration and duration > 0:
                    self.logger.debug(f"Duración obtenida para {archivo.name}: {duration:.1f}s")
                    return float(duration)
                else:
                    self.logger.debug(f"Duración no válida para {archivo.name}: {duration}")
            else:
                self.logger.debug(f"No se pudo cargar metadata para {archivo.name}")
                
        except Exception as e:
            self.logger.debug(f"Error obteniendo duración de {archivo.name}: {e}")
        
        return 0.0
    
    def extraer_titulo_pelicula(self, nombre_archivo: str) -> str:
        """
        Extrae el título de la película del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Título limpio de la película
        """
        # Remover extensión
        titulo = Path(nombre_archivo).stem
        
        # Aplicar patrones para extraer título
        for patron in self.patrones_titulo:
            match = re.search(patron, titulo, re.IGNORECASE)
            if match:
                titulo = match.group(1).strip()
                break
        
        # Limpiar caracteres especiales y normalizar
        titulo = re.sub(r'[._-]', ' ', titulo)
        titulo = re.sub(r'\s+', ' ', titulo)
        titulo = titulo.strip()
        
        return titulo
    
    def extraer_año(self, nombre_archivo: str) -> int:
        """
        Extrae el año de la película del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Año de la película o 0 si no se encuentra
        """
        # Buscar año en formato (YYYY) o [YYYY]
        patrones_año = [
            r'\((\d{4})\)',
            r'\[(\d{4})\]',
            r'\b(\d{4})\b'
        ]
        
        for patron in patrones_año:
            match = re.search(patron, nombre_archivo)
            if match:
                año = int(match.group(1))
                # Verificar que sea un año válido
                if 1900 <= año <= 2030:
                    return año
        
        return 0
    
    def extraer_calidad(self, nombre_archivo: str) -> str:
        """
        Extrae información de calidad del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Información de calidad encontrada
        """
        calidades = []
        
        for patron in self.patrones_calidad:
            matches = re.findall(patron, nombre_archivo, re.IGNORECASE)
            calidades.extend(matches)
        
        return ' '.join(calidades) if calidades else 'Desconocida'
    
    def normalizar_titulo(self, titulo: str) -> str:
        """
        Normaliza un título para comparación
        
        Args:
            titulo: Título a normalizar
            
        Returns:
            Título normalizado
        """
        # Convertir a minúsculas
        titulo = titulo.lower()
        
        # Remover artículos comunes
        articulos = ['el', 'la', 'los', 'las', 'un', 'una', 'the', 'a', 'an']
        palabras = titulo.split()
        palabras = [palabra for palabra in palabras if palabra not in articulos]
        
        # Remover caracteres especiales
        titulo = re.sub(r'[^\w\s]', '', ' '.join(palabras))
        
        return titulo.strip()
    
    def similitud_titulos(self, titulo1: str, titulo2: str) -> float:
        """
        Calcula la similitud entre dos títulos
        
        Args:
            titulo1: Primer título
            titulo2: Segundo título
            
        Returns:
            Porcentaje de similitud (0-1)
        """
        titulo1_norm = self.normalizar_titulo(titulo1)
        titulo2_norm = self.normalizar_titulo(titulo2)
        
        return SequenceMatcher(None, titulo1_norm, titulo2_norm).ratio()
    
    def analizar_archivo(self, archivo: Path) -> Dict:
        """
        Analiza un archivo de video y extrae su información
        
        Args:
            archivo: Ruta del archivo
            
        Returns:
            Diccionario con información de la película
        """
        nombre_archivo = archivo.name
        titulo = self.extraer_titulo_pelicula(nombre_archivo)
        año = self.extraer_año(nombre_archivo)
        calidad = self.extraer_calidad(nombre_archivo)
        # Obtener duración del video
        duracion = self.obtener_duracion_video(archivo)
        
        # Información básica del archivo
        pelicula_info = {
            'archivo': str(archivo),
            'nombre': nombre_archivo,
            'titulo': titulo,
            'año': año,
            'calidad': calidad,
            'tamaño': archivo.stat().st_size if archivo.exists() else 0,
            'carpeta': str(archivo.parent),
            'duracion': duracion,
            'has_plex_metadata': False
        }
        
        # TEMPORAL: No consultar PLEX durante escaneo inicial para velocidad
        # Los metadatos de PLEX se obtendrán solo para duplicados encontrados
        # TODO: Implementar consulta PLEX solo para duplicados
        
        return pelicula_info
    
    def escanear_carpeta(self, carpeta_raiz: str = None) -> List[Dict]:
        """
        Escanea la carpeta de manera recursiva buscando archivos de video (SIN PLEX)
        
        Args:
            carpeta_raiz: Ruta de la carpeta (opcional si ya está configurada)
            
        Returns:
            Lista de películas encontradas
        """
        if carpeta_raiz:
            self.set_carpeta_raiz(carpeta_raiz)
        
        if not self.carpeta_raiz:
            self.logger.error("No se ha especificado carpeta raíz")
            return []
        
        self.logger.info(f"🔍 Escaneando carpeta: {self.carpeta_raiz}")
        peliculas = []
        contador = 0
        
        if not self.carpeta_raiz.exists():
            self.logger.error(f"La carpeta {self.carpeta_raiz} no existe")
            return peliculas
        
        # Recorrer recursivamente
        for archivo in self.carpeta_raiz.rglob('*'):
            if archivo.is_file() and self.es_archivo_video(archivo):
                contador += 1
                
                # Mostrar archivo en miniterminal si hay callback
                if hasattr(self, 'mostrar_archivo'):
                    self.mostrar_archivo(str(archivo))
                
                # Mostrar progreso cada 100 archivos
                if contador % 100 == 0:
                    self.logger.info(f"📊 Progreso: {contador} archivos procesados...")
                    # Si hay callback de progreso, usarlo
                    if hasattr(self, 'mostrar_progreso'):
                        self.mostrar_progreso(contador, f"📊 Progreso: {contador} archivos procesados...")
                
                try:
                    pelicula = self.analizar_archivo(archivo)
                    peliculas.append(pelicula)
                    self.logger.debug(f"Encontrado: {pelicula['titulo']} ({pelicula['año']}) - {pelicula['calidad']}")
                except Exception as e:
                    self.logger.error(f"Error procesando {archivo}: {e}")
        
        self.peliculas = peliculas
        self.logger.info(f"✅ Escaneo completado: {len(peliculas)} películas encontradas de {contador} archivos")
        
        # Actualizar última ruta escaneada en configuración
        settings.update_last_scan_path(str(self.carpeta_raiz))
        
        return peliculas
    
    def encontrar_duplicados(self, umbral_similitud: float = None) -> List[List[Dict]]:
        """
        Encuentra películas duplicadas basándose en similitud de títulos y años
        
        Args:
            umbral_similitud: Umbral de similitud para considerar duplicados (0-1)
            
        Returns:
            Lista de grupos de películas duplicadas
        """
        if not self.peliculas:
            self.logger.warning("Primero debe escanear la carpeta")
            return []
        
        if umbral_similitud is None:
            umbral_similitud = self.umbral_similitud
        
        self.logger.info(f"Buscando duplicados con umbral de similitud: {umbral_similitud}")
        
        # Agrupar por año para optimizar búsqueda
        peliculas_por_año = defaultdict(list)
        for pelicula in self.peliculas:
            año = pelicula['año'] if pelicula['año'] > 0 else 'Sin año'
            peliculas_por_año[año].append(pelicula)
        
        duplicados = []
        procesadas = set()
        
        for año, peliculas_año in peliculas_por_año.items():
            for i, pelicula1 in enumerate(peliculas_año):
                if pelicula1['archivo'] in procesadas:
                    continue
                
                grupo_duplicados = [pelicula1]
                procesadas.add(pelicula1['archivo'])
                
                for j, pelicula2 in enumerate(peliculas_año[i+1:], i+1):
                    if pelicula2['archivo'] in procesadas:
                        continue
                    
                    # Calcular similitud
                    similitud = self.similitud_titulos(pelicula1['titulo'], pelicula2['titulo'])
                    
                    # Verificar si son del mismo año o años cercanos
                    años_compatibles = (
                        pelicula1['año'] == 0 or pelicula2['año'] == 0 or
                        abs(pelicula1['año'] - pelicula2['año']) <= 1
                    )
                    
                    # Verificar duración si el filtro está activado
                    duracion_compatible = True
                    if settings.get_duration_filter_enabled():
                        duracion1 = pelicula1.get('duracion', 0)
                        duracion2 = pelicula2.get('duracion', 0)
                        
                        if duracion1 > 0 and duracion2 > 0:
                            # Calcular diferencia en minutos
                            diferencia_segundos = abs(duracion1 - duracion2)
                            diferencia_minutos = diferencia_segundos / 60
                            
                            tolerancia_minutos = settings.get_duration_tolerance_minutes()
                            duracion_compatible = diferencia_minutos <= tolerancia_minutos
                            
                            if not duracion_compatible:
                                self.logger.debug(f"Descartado por duración: {pelicula1['nombre']} ({duracion1/60:.1f}min) vs {pelicula2['nombre']} ({duracion2/60:.1f}min) - Diferencia: {diferencia_minutos:.1f}min")
                    
                    if similitud >= umbral_similitud and años_compatibles and duracion_compatible:
                        grupo_duplicados.append(pelicula2)
                        procesadas.add(pelicula2['archivo'])
                
                # Si hay más de una película en el grupo, es un duplicado
                if len(grupo_duplicados) > 1:
                    duplicados.append(grupo_duplicados)
        
        self.duplicados = duplicados
        self.logger.info(f"Encontrados {len(duplicados)} grupos de duplicados")
        return duplicados
    
    def encontrar_duplicados_con_plex(self, library_id: str = None, library_name: str = None) -> List[List[Dict]]:
        """
        Encuentra duplicados usando metadatos de PLEX
        
        Args:
            library_id: ID de la biblioteca PLEX (opcional)
            
        Returns:
            Lista de grupos de películas duplicadas
        """
        if not self.is_plex_available():
            self.logger.warning("PLEX no está disponible")
            return []
        
        try:
            # Si se especifica nombre de biblioteca, buscar por nombre
            if library_name:
                libraries = self.plex_service.get_libraries()
                movie_libraries = [lib for lib in libraries if lib.get('type') == 'movie']
                
                # Buscar biblioteca por nombre
                target_library = None
                for lib in movie_libraries:
                    if lib.get('title', '').lower() == library_name.lower():
                        target_library = lib
                        break
                
                if target_library:
                    library_id = target_library.get('id')
                    self.logger.info(f"Biblioteca encontrada: {target_library.get('title')} (ID: {library_id})")
                else:
                    self.logger.warning(f"Biblioteca '{library_name}' no encontrada, usando la primera disponible")
                    library_id = None
            
            # Si no se especifica biblioteca, usar la primera disponible
            if not library_id:
                libraries = self.plex_service.get_libraries()
                movie_libraries = [lib for lib in libraries if lib.get('type') == 'movie']
                if not movie_libraries:
                    self.logger.error("No se encontraron bibliotecas de películas en PLEX")
                    return []
                library_id = movie_libraries[0]['id']
            
            # Obtener duplicados desde PLEX
            plex_duplicates = self.plex_service.detect_duplicates_with_plex(library_id)
            
            if not plex_duplicates:
                self.logger.info("PLEX no detectó duplicados")
                return []
            
            # Convertir formato de PLEX a formato interno
            duplicados = []
            for plex_group in plex_duplicates:
                grupo = []
                for plex_movie in plex_group['movies']:
                    # Crear entrada compatible con el formato interno
                    pelicula = {
                        'archivo': plex_movie.get('file_path', ''),
                        'nombre': Path(plex_movie.get('file_path', '')).name,
                        'titulo': plex_movie.get('title', ''),
                        'año': plex_movie.get('year', 0),
                        'calidad': plex_movie.get('resolution_plex', ''),
                        'tamaño': plex_movie.get('file_size', 0),
                        'carpeta': str(Path(plex_movie.get('file_path', '')).parent),
                        'duracion': plex_movie.get('duration', 0),
                        'has_plex_metadata': True,
                        'plex_detected': True,
                        'similarity_score': plex_group.get('similarity_score', 1.0)
                    }
                    
                    # Agregar metadatos adicionales de PLEX
                    pelicula.update({
                        'plex_id': plex_movie.get('plex_id'),
                        'rating_plex': plex_movie.get('rating', 0),
                        'imdb_rating': plex_movie.get('imdb_rating', 0),
                        'genres_plex': plex_movie.get('genres', []),
                        'directors_plex': plex_movie.get('directors', []),
                        'actors_plex': plex_movie.get('actors', []),
                        'studio_plex': plex_movie.get('studio', ''),
                        'summary_plex': plex_movie.get('summary', ''),
                        'view_count': plex_movie.get('view_count', 0),
                        'video_codec': plex_movie.get('video_codec', ''),
                        'audio_codec': plex_movie.get('audio_codec', ''),
                        'bitrate': plex_movie.get('bitrate', 0)
                    })
                    
                    grupo.append(pelicula)
                
                if len(grupo) > 1:
                    duplicados.append(grupo)
            
            self.duplicados = duplicados
            self.logger.info(f"PLEX detectó {len(duplicados)} grupos de duplicados")
            return duplicados
            
        except Exception as e:
            self.logger.error(f"Error detectando duplicados con PLEX: {e}")
            return []
    
    def encontrar_duplicados_hibrido(self, umbral_similitud: float = None, library_name: str = None, callback_progreso=None) -> List[List[Dict]]:
        """
        Encuentra duplicados usando estrategia optimizada:
        1. Escaneo normal de archivos (SIN PLEX - rápido)
        2. Detección de duplicados por similitud (SIN PLEX - rápido)
        3. Verificación con PLEX solo para posibles duplicados (opcional)
        
        Args:
            umbral_similitud: Umbral de similitud para considerar duplicados (0-1)
            callback_progreso: Función para mostrar progreso en tiempo real
            
        Returns:
            Lista de grupos de películas duplicadas
        """
        if not self.peliculas:
            self.logger.warning("Primero debe escanear la carpeta")
            return []
        
        if umbral_similitud is None:
            umbral_similitud = self.umbral_similitud
        
        self.logger.info(f"🔍 Paso 1: Detección rápida de duplicados por similitud (umbral: {umbral_similitud})")
        self.logger.info(f"📊 Analizando {len(self.peliculas)} películas...")
        print(f"🔍 CONSOLA: Iniciando detección de duplicados con {len(self.peliculas)} películas")
        
        # PASO 1: Detección rápida de duplicados por similitud (sin PLEX)
        duplicados_candidatos = []
        procesadas = set()
        
        for i, pelicula1 in enumerate(self.peliculas):
            if pelicula1['archivo'] in procesadas:
                continue
            
            grupo_duplicados = [pelicula1]
            procesadas.add(pelicula1['archivo'])
            
            # Mostrar progreso cada 20 películas
            if i % 20 == 0:
                mensaje = f"📊 Progreso: {i}/{len(self.peliculas)} películas procesadas..."
                self.logger.info(mensaje)
                print(f"📊 CONSOLA: {mensaje}")
                if hasattr(self, 'mostrar_progreso_streamlit'):
                    self.mostrar_progreso_streamlit(mensaje)
            
            for j, pelicula2 in enumerate(self.peliculas[i+1:], i+1):
                if pelicula2['archivo'] in procesadas:
                    continue
                
                # Calcular similitud básica (solo título y año)
                similitud = self.similitud_titulos(pelicula1['titulo'], pelicula2['titulo'])
                
                # Verificar compatibilidad básica
                if self._son_compatibles_basicos(pelicula1, pelicula2, similitud, umbral_similitud):
                    grupo_duplicados.append(pelicula2)
                    procesadas.add(pelicula2['archivo'])
            
            if len(grupo_duplicados) > 1:
                duplicados_candidatos.append(grupo_duplicados)
                mensaje = f"🎯 Duplicados encontrados: {pelicula1['titulo']} ({len(grupo_duplicados)} copias)"
                self.logger.info(mensaje)
                print(f"🎯 CONSOLA: {mensaje}")
                if hasattr(self, 'mostrar_progreso_streamlit'):
                    self.mostrar_progreso_streamlit(mensaje)
        
        self.logger.info(f"✅ Paso 1 completado: {len(duplicados_candidatos)} grupos de duplicados candidatos")
        print(f"✅ CONSOLA: Paso 1 completado: {len(duplicados_candidatos)} grupos de duplicados candidatos")
        
        # PASO 2: Verificación con PLEX solo para duplicados candidatos
        print(f"🔍 CONSOLA: Verificando PLEX disponible: {self.is_plex_available()}")
        print(f"🔍 CONSOLA: Candidatos: {len(duplicados_candidatos)}")
        
        # Mostrar primer grupo inmediatamente
        if duplicados_candidatos and callback_progreso:
            primer_grupo = duplicados_candidatos[0]
            callback_progreso({
                'tipo': 'primer_grupo',
                'grupo': primer_grupo,
                'total_grupos': len(duplicados_candidatos)
            })
        
        if self.is_plex_available() and duplicados_candidatos:
            mensaje = f"🔍 Paso 2: Verificando {len(duplicados_candidatos)} grupos con PLEX..."
            self.logger.info(mensaje)
            if hasattr(self, 'mostrar_progreso_streamlit'):
                self.mostrar_progreso_streamlit(mensaje)
            
            mensaje = f"📊 PLEX disponible: {self.plex_service.is_connected}"
            self.logger.info(mensaje)
            if hasattr(self, 'mostrar_progreso_streamlit'):
                self.mostrar_progreso_streamlit(mensaje)
            
            duplicados_verificados = self._verificar_duplicados_con_plex(duplicados_candidatos, callback_progreso)
        else:
            mensaje = "⚠️ PLEX no disponible o no hay candidatos, usando solo detección básica"
            self.logger.info(mensaje)
            if hasattr(self, 'mostrar_progreso_streamlit'):
                self.mostrar_progreso_streamlit(mensaje)
            
            mensaje = f"📊 PLEX disponible: {self.is_plex_available()}"
            self.logger.info(mensaje)
            if hasattr(self, 'mostrar_progreso_streamlit'):
                self.mostrar_progreso_streamlit(mensaje)
            
            mensaje = f"📊 Candidatos: {len(duplicados_candidatos)}"
            self.logger.info(mensaje)
            if hasattr(self, 'mostrar_progreso_streamlit'):
                self.mostrar_progreso_streamlit(mensaje)
            
            duplicados_verificados = duplicados_candidatos
        
        self.duplicados = duplicados_verificados
        self.logger.info(f"🎯 Búsqueda híbrida completada: {len(duplicados_verificados)} grupos de duplicados finales")
        return duplicados_verificados
    
    def _son_compatibles_basicos(self, pelicula1: Dict, pelicula2: Dict, similitud: float, umbral: float) -> bool:
        """
        Verifica compatibilidad básica entre dos películas (solo título y año)
        
        Args:
            pelicula1: Primera película
            pelicula2: Segunda película
            similitud: Similitud de títulos
            umbral: Umbral mínimo de similitud
            
        Returns:
            True si son compatibles
        """
        # Verificar similitud de títulos
        if similitud < umbral:
            return False
        
        # Verificar años (tolerancia de ±1 año)
        año1 = pelicula1.get('año', 0)
        año2 = pelicula2.get('año', 0)
        
        if año1 > 0 and año2 > 0:
            if abs(año1 - año2) > 1:
                return False
        
        return True
    
    def _verificar_duplicados_con_plex(self, duplicados_candidatos: List[List[Dict]], callback_progreso=None) -> List[List[Dict]]:
        """
        Verifica duplicados candidatos usando metadatos de PLEX
        
        Args:
            duplicados_candidatos: Lista de grupos de duplicados candidatos
            callback_progreso: Función para mostrar progreso en tiempo real
            
        Returns:
            Lista de duplicados verificados
        """
        print(f"🔍 CONSOLA: Iniciando verificación PLEX con {len(duplicados_candidatos)} grupos")
        duplicados_verificados = []
        
        for i, grupo in enumerate(duplicados_candidatos):
            print(f"🔍 CONSOLA: Procesando grupo {i+1}/{len(duplicados_candidatos)}: {grupo[0]['titulo']}")
            try:
                # Obtener metadatos de PLEX para cada película del grupo
                peliculas_mejoradas = []
                
                for j, pelicula in enumerate(grupo):
                    print(f"🔍 CONSOLA: Buscando en PLEX película {j+1}/{len(grupo)}: {pelicula.get('titulo', 'Sin título')}")
                    print(f"🔍 CONSOLA: Ruta: {pelicula.get('archivo', 'Sin ruta')}")
                    
                    try:
                        # Buscar en PLEX usando conexión directa a la base de datos
                        from src.services.plex.plex_database_direct import PlexDatabaseDirect
                        from src.settings.settings import settings
                        
                        db_path = settings.get_plex_database_path()
                        if db_path:
                            plex_db = PlexDatabaseDirect(db_path)
                            if plex_db.connect():
                                plex_movie = plex_db.search_movie_by_path(pelicula.get('archivo', ''))
                                plex_db.close()
                                
                                if plex_movie:
                                    print(f"✅ CONSOLA: PLEX encontrado para: {pelicula.get('titulo', 'Sin título')}")
                                else:
                                    print(f"❌ CONSOLA: PLEX NO encontrado para: {pelicula.get('titulo', 'Sin título')}")
                            else:
                                print(f"❌ CONSOLA: No se pudo conectar a PLEX DB")
                                plex_movie = None
                        else:
                            print(f"❌ CONSOLA: No se encontró ruta de PLEX DB")
                            plex_movie = None
                    except Exception as e:
                        print(f"❌ CONSOLA: Error buscando en PLEX: {e}")
                        plex_movie = None
                    
                    if plex_movie:
                        # Combinar metadatos de PLEX
                        pelicula_mejorada = {
                            **pelicula,
                            'has_plex_metadata': True,
                            'plex_metadata': plex_movie,
                            'title_plex': plex_movie.get('title', pelicula.get('titulo', '')),
                            'year_plex': plex_movie.get('year', pelicula.get('año', 0)),
                            'duration_plex': plex_movie.get('duration', 0),
                            'rating_plex': plex_movie.get('rating', 0),
                            'audience_rating': plex_movie.get('audience_rating', 0),
                            'imdb_rating': plex_movie.get('imdb_rating', 0),
                            'genres_plex': plex_movie.get('genres', []),
                            'directors_plex': plex_movie.get('directors', []),
                            'actors_plex': plex_movie.get('actors', []),
                            'studio_plex': plex_movie.get('studio', ''),
                            'summary_plex': plex_movie.get('summary', ''),
                            'content_rating': plex_movie.get('content_rating', ''),
                            'video_codec': plex_movie.get('video_codec', ''),
                            'audio_codec': plex_movie.get('audio_codec', ''),
                            'resolution_plex': plex_movie.get('resolution', ''),
                            'bitrate': plex_movie.get('bitrate', 0)
                        }
                        
                        # Usar metadatos de PLEX si están disponibles
                        if plex_movie.get('title'):
                            pelicula_mejorada['titulo'] = plex_movie['title']
                        if plex_movie.get('year'):
                            pelicula_mejorada['año'] = plex_movie['year']
                        if plex_movie.get('duration'):
                            pelicula_mejorada['duracion'] = plex_movie['duration']
                    else:
                        pelicula_mejorada = {
                            **pelicula,
                            'has_plex_metadata': False
                        }
                    
                    peliculas_mejoradas.append(pelicula_mejorada)
                
                # Verificar duración si hay metadatos de PLEX
                if any(p.get("has_plex_metadata") for p in peliculas_mejoradas):
                    duraciones = [p.get('duration_plex', 0) for p in peliculas_mejoradas if p.get('duration_plex', 0) > 0]
                    
                    if duraciones:
                        # Verificar que las duraciones sean similares (tolerancia de ±2 minutos)
                        duracion_promedio = sum(duraciones) / len(duraciones)
                        duraciones_compatibles = all(
                            abs(duracion - duracion_promedio) <= 120000  # 2 minutos en ms
                            for duracion in duraciones
                        )
                        
                        if duraciones_compatibles:
                            self.logger.info(f"✅ Duplicados verificados con PLEX: {peliculas_mejoradas[0].get('titulo', 'Unknown')}")
                            duplicados_verificados.append(peliculas_mejoradas)
                            
                            # Notificar grupo completado
                            if callback_progreso:
                                callback_progreso({
                                    'tipo': 'grupo_completado',
                                    'grupo': peliculas_mejoradas,
                                    'indice': i,
                                    'total': len(duplicados_candidatos)
                                })
                        else:
                            self.logger.info(f"❌ Duplicados descartados por duración: {peliculas_mejoradas[0].get('titulo', 'Unknown')}")
                    else:
                        # Sin duraciones de PLEX, usar grupo original
                        duplicados_verificados.append(peliculas_mejoradas)
                        
                        # Notificar grupo completado
                        if callback_progreso:
                            callback_progreso({
                                'tipo': 'grupo_completado',
                                'grupo': peliculas_mejoradas,
                                'indice': i,
                                'total': len(duplicados_candidatos)
                            })
                else:
                    # Sin metadatos de PLEX, usar grupo original
                    duplicados_verificados.append(peliculas_mejoradas)
                    
                    # Notificar grupo completado
                    if callback_progreso:
                        callback_progreso({
                            'tipo': 'grupo_completado',
                            'grupo': peliculas_mejoradas,
                            'indice': i,
                            'total': len(duplicados_candidatos)
                        })
                    
            except Exception as e:
                self.logger.warning(f"Error verificando grupo con PLEX: {e}")
                # En caso de error, usar grupo original
                duplicados_verificados.append(grupo)
        
        return duplicados_verificados
    
    def _calcular_similitud_hibrida(self, pelicula1: Dict, pelicula2: Dict) -> float:
        """
        Calcula similitud mejorada usando metadatos de PLEX
        
        Args:
            pelicula1: Primera película
            pelicula2: Segunda película
            
        Returns:
            Puntuación de similitud (0-1)
        """
        # Similitud básica de títulos
        similitud_titulo = self.similitud_titulos(pelicula1['titulo'], pelicula2['titulo'])
        
        # Si ambas tienen metadatos de PLEX, usar información adicional
        if pelicula1.get('has_plex_metadata') and pelicula2.get('has_plex_metadata'):
            # Verificar si están duplicadas en PLEX
            if (pelicula1.get('plex_id') == pelicula2.get('plex_id') and 
                pelicula1.get('plex_id') is not None):
                return 1.0  # Película duplicada en PLEX
            
            # Similitud de géneros
            generos1 = set(pelicula1.get('genres_plex', []))
            generos2 = set(pelicula2.get('genres_plex', []))
            similitud_generos = len(generos1.intersection(generos2)) / max(len(generos1.union(generos2)), 1)
            
            # Similitud de directores
            directores1 = set(pelicula1.get('directors_plex', []))
            directores2 = set(pelicula2.get('directors_plex', []))
            similitud_directores = len(directores1.intersection(directores2)) / max(len(directores1.union(directores2)), 1)
            
            # Combinar similitudes
            similitud_plex = (similitud_generos * 0.3 + similitud_directores * 0.7)
            return max(similitud_titulo, similitud_plex)
        
        return similitud_titulo
    
    def _son_compatibles(self, pelicula1: Dict, pelicula2: Dict, similitud: float, umbral: float) -> bool:
        """
        Verifica si dos películas son compatibles para ser consideradas duplicadas
        
        Args:
            pelicula1: Primera película
            pelicula2: Segunda película
            similitud: Puntuación de similitud
            umbral: Umbral mínimo
            
        Returns:
            bool: True si son compatibles
        """
        # Verificar umbral de similitud
        if similitud < umbral:
            return False
        
        # Verificar años compatibles
        años_compatibles = (
            pelicula1['año'] == 0 or pelicula2['año'] == 0 or
            abs(pelicula1['año'] - pelicula2['año']) <= 1
        )
        
        if not años_compatibles:
            return False
        
        # Verificar duración si el filtro está activado
        if settings.get_duration_filter_enabled():
            duracion1 = pelicula1.get('duracion', 0)
            duracion2 = pelicula2.get('duracion', 0)
            
            if duracion1 > 0 and duracion2 > 0:
                diferencia_segundos = abs(duracion1 - duracion2)
                diferencia_minutos = diferencia_segundos / 60
                tolerancia_minutos = settings.get_duration_tolerance_minutes()
                
                if diferencia_minutos > tolerancia_minutos:
                    return False
        
        return True
    
    def formatear_tamaño(self, bytes_size: int) -> str:
        """Formatea el tamaño en bytes a formato legible"""
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unidad}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def get_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del análisis
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.peliculas:
            return {
                'total_peliculas': 0,
                'total_duplicados': 0,
                'grupos_duplicados': 0,
                'espacio_duplicado': 0
            }
        
        total_peliculas = len(self.peliculas)
        total_duplicados = sum(len(grupo) for grupo in self.duplicados)
        grupos_duplicados = len(self.duplicados)
        
        # Calcular espacio duplicado (suma de tamaños de duplicados)
        espacio_duplicado = 0
        for grupo in self.duplicados:
            # Sumar tamaños de todos los archivos excepto el primero (considerado original)
            for pelicula in grupo[1:]:
                espacio_duplicado += pelicula['tamaño']
        
        estadisticas = {
            'total_peliculas': total_peliculas,
            'total_duplicados': total_duplicados,
            'grupos_duplicados': grupos_duplicados,
            'espacio_duplicado': espacio_duplicado,
            'espacio_duplicado_formateado': self.formatear_tamaño(espacio_duplicado)
        }
        
        # Agregar estadísticas de PLEX si está disponible
        if self.is_plex_available():
            try:
                libraries = self.plex_service.get_libraries()
                movie_libraries = [lib for lib in libraries if lib.get('type') == 'movie']
                
                if movie_libraries:
                    library_id = movie_libraries[0]['id']
                    plex_stats = self.plex_service.get_library_statistics(library_id)
                    
                    estadisticas.update({
                        'plex_available': True,
                        'plex_connected': True,
                        'plex_libraries': len(movie_libraries),
                        'plex_total_movies': plex_stats.get('total_movies', 0),
                        'plex_total_size_gb': plex_stats.get('total_size_gb', 0),
                        'plex_total_duration_hours': plex_stats.get('total_duration_hours', 0),
                        'plex_average_rating': plex_stats.get('average_rating', 0),
                        'plex_years_distribution': plex_stats.get('years_distribution', {}),
                        'plex_genres_distribution': plex_stats.get('genres_distribution', {}),
                        'plex_resolutions_distribution': plex_stats.get('resolutions_distribution', {}),
                        'plex_codecs_distribution': plex_stats.get('codecs_distribution', {})
                    })
                else:
                    estadisticas.update({
                        'plex_available': True,
                        'plex_connected': True,
                        'plex_libraries': 0,
                        'plex_message': 'No hay bibliotecas de películas en PLEX'
                    })
            except Exception as e:
                self.logger.warning(f"Error obteniendo estadísticas de PLEX: {e}")
                estadisticas.update({
                    'plex_available': True,
                    'plex_connected': False,
                    'plex_error': str(e)
                })
        else:
            estadisticas.update({
                'plex_available': False,
                'plex_connected': False
            })
        
        return estadisticas
    
    def guardar_resultados(self, archivo_salida: str = None) -> str:
        """
        Guarda los resultados en un archivo de texto
        
        Args:
            archivo_salida: Nombre del archivo de salida
            
        Returns:
            Ruta del archivo guardado
        """
        if not self.duplicados:
            self.logger.warning("No hay duplicados para guardar")
            return ""
        
        if not archivo_salida:
            archivo_salida = f"duplicados_{self.carpeta_raiz.name}.txt"
        
        output_path = Path(archivo_salida)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"REPORTE DE PELÍCULAS DUPLICADAS\n")
            f.write(f"Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Carpeta analizada: {self.carpeta_raiz}\n")
            f.write(f"Total de grupos duplicados: {len(self.duplicados)}\n")
            f.write("="*80 + "\n\n")
            
            for i, grupo in enumerate(self.duplicados, 1):
                f.write(f"GRUPO {i}\n")
                f.write(f"Título: {grupo[0]['titulo']}\n")
                f.write(f"Año: {grupo[0]['año'] if grupo[0]['año'] > 0 else 'Desconocido'}\n")
                f.write(f"Archivos ({len(grupo)}):\n")
                
                for j, pelicula in enumerate(grupo, 1):
                    f.write(f"  {j}. {pelicula['nombre']}\n")
                    f.write(f"     Ruta: {pelicula['archivo']}\n")
                    f.write(f"     Calidad: {pelicula['calidad']}\n")
                    f.write(f"     Tamaño: {self.formatear_tamaño(pelicula['tamaño'])}\n")
                
                f.write("\n" + "-"*50 + "\n\n")
        
        self.logger.info(f"Resultados guardados en: {output_path}")
        
        # Actualizar última ruta de salida en configuración
        settings.update_last_output_path(str(output_path))
        
        return str(output_path)
    
    def encontrar_duplicados_rapido_con_plex(self, callback_progreso=None):
        """
        Método optimizado: búsqueda rápida + metadatos de PLEX
        
        Args:
            callback_progreso: Función de callback para mostrar progreso
            
        Returns:
            Lista de grupos de duplicados con metadatos de PLEX
        """
        self.logger.info("🚀 Iniciando búsqueda rápida con metadatos de PLEX...")
        
        # 1. Búsqueda rápida por similitud (sin PLEX)
        self.logger.info("🔍 Paso 1: Búsqueda rápida por similitud...")
        duplicados_rapidos = self.encontrar_duplicados()
        
        if not duplicados_rapidos:
            self.logger.info("ℹ️ No se encontraron duplicados")
            return []
        
        self.logger.info(f"✅ Encontrados {len(duplicados_rapidos)} grupos de duplicados")
        
        # 2. Añadir metadatos de PLEX solo a los grupos encontrados
        if self.use_plex and self.plex_service and self.plex_service.is_connected:
            self.logger.info("🎬 Paso 2: Añadiendo metadatos de PLEX...")
            
            try:
                from src.services.plex.plex_fast_search import PlexFastSearch
                
                # Obtener ruta de la base de datos desde configuración
                db_path = settings.get_plex_database_path()
                
                if db_path:
                    enhancer = PlexFastSearch(db_path)
                    
                    if enhancer.connect():
                        duplicados_mejorados = []
                        
                        for i, grupo in enumerate(duplicados_rapidos):
                            # Notificar progreso
                            if callback_progreso:
                                callback_progreso({
                                    'tipo': 'procesando_plex',
                                    'indice': i,
                                    'total': len(duplicados_rapidos),
                                    'mensaje': f"Procesando grupo {i+1}/{len(duplicados_rapidos)} con PLEX..."
                                })
                            
                            # Añadir metadatos de PLEX
                            grupo_mejorado = enhancer.enhance_duplicate_group(grupo)
                            duplicados_mejorados.append(grupo_mejorado)
                        
                        enhancer.close()
                        self.logger.info("✅ Metadatos de PLEX añadidos exitosamente")
                        return duplicados_mejorados
                    else:
                        self.logger.warning("⚠️ No se pudo conectar con la base de datos PLEX, devolviendo duplicados sin metadatos")
                        return duplicados_rapidos
                else:
                    self.logger.warning("⚠️ Ruta de base de datos PLEX no configurada, devolviendo duplicados sin metadatos")
                    return duplicados_rapidos
                    
            except Exception as e:
                self.logger.error(f"❌ Error añadiendo metadatos de PLEX: {e}")
                return duplicados_rapidos
        else:
            self.logger.info("ℹ️ PLEX no disponible, devolviendo duplicados sin metadatos")
            return duplicados_rapidos
