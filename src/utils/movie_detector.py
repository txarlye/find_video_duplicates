#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidad para detectar películas duplicadas
Integrada como utilidad de la aplicación Streamlit
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import defaultdict
from difflib import SequenceMatcher

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from src.settings.settings import settings


class MovieDetector:
    """Clase para detectar películas duplicadas integrada con la configuración"""
    
    def __init__(self, carpeta_raiz: str = None):
        """
        Inicializa el detector con la carpeta raíz
        
        Args:
            carpeta_raiz: Ruta de la carpeta a analizar (opcional)
        """
        self.carpeta_raiz = Path(carpeta_raiz) if carpeta_raiz else None
        self.peliculas = []
        self.duplicados = []
        
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
    
    def _is_in_excluded_directory(self, archivo: Path, excluded_dirs: List[str]) -> bool:
        """
        Verifica si un archivo está en un directorio excluido
        
        Args:
            archivo: Ruta del archivo
            excluded_dirs: Lista de nombres de directorios a excluir
            
        Returns:
            True si el archivo está en un directorio excluido
        """
        try:
            # Obtener todas las partes del path
            path_parts = archivo.parts
            
            # Verificar si alguna parte del path coincide con los directorios excluidos
            for part in path_parts:
                if part.lower() in [dir_name.lower() for dir_name in excluded_dirs]:
                    return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Error verificando directorio excluido: {e}")
            return False
    
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
        # Deshabilitar duración temporalmente para evitar bloqueos
        duracion = 0.0  # self.obtener_duracion_video(archivo)
        
        return {
            'archivo': str(archivo),
            'nombre': nombre_archivo,
            'titulo': titulo,
            'año': año,
            'calidad': calidad,
            'tamaño': archivo.stat().st_size if archivo.exists() else 0,
            'carpeta': str(archivo.parent),
            'duracion': duracion
        }
    
    def escanear_carpeta(self, carpeta_raiz: str = None) -> List[Dict]:
        """
        Escanea la carpeta de manera recursiva buscando archivos de video
        
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
        
        self.logger.info(f"Escaneando carpeta: {self.carpeta_raiz}")
        peliculas = []
        
        if not self.carpeta_raiz.exists():
            self.logger.error(f"La carpeta {self.carpeta_raiz} no existe")
            return peliculas
        
        # Obtener directorios excluidos de la configuración
        excluded_dirs = settings.get_excluded_directories()
        self.logger.info(f"Directorios excluidos: {excluded_dirs}")
        
        # Recorrer recursivamente
        for archivo in self.carpeta_raiz.rglob('*'):
            # Verificar si el archivo está en un directorio excluido
            if self._is_in_excluded_directory(archivo, excluded_dirs):
                self.logger.debug(f"Excluyendo archivo en directorio excluido: {archivo}")
                continue
                
            if archivo.is_file() and self.es_archivo_video(archivo):
                # Mostrar archivo en miniterminal si hay callback
                if hasattr(self, 'mostrar_archivo'):
                    self.mostrar_archivo(str(archivo))
                
                try:
                    pelicula = self.analizar_archivo(archivo)
                    peliculas.append(pelicula)
                    self.logger.debug(f"Encontrado: {pelicula['titulo']} ({pelicula['año']}) - {pelicula['calidad']}")
                except Exception as e:
                    self.logger.error(f"Error procesando {archivo}: {e}")
        
        self.peliculas = peliculas
        self.logger.info(f"Total de películas encontradas: {len(peliculas)}")
        
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
        
        return {
            'total_peliculas': total_peliculas,
            'total_duplicados': total_duplicados,
            'grupos_duplicados': grupos_duplicados,
            'espacio_duplicado': espacio_duplicado,
            'espacio_duplicado_formateado': self.formatear_tamaño(espacio_duplicado)
        }
    
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
