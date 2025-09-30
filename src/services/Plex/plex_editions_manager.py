#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor principal de ediciones de Plex
"""
import os
from typing import Dict, List, Optional, Tuple
import logging

from .plex_editions_detector import PlexEditionsDetector
from .plex_edition_creator import PlexEditionCreator
from .plex_duplicate_analyzer import PlexDuplicateAnalyzer

class PlexEditionsManager:
    """Gestor principal de ediciones de Plex"""
    
    def __init__(self, database_path: str):
        """
        Inicializa el gestor de ediciones
        
        Args:
            database_path: Ruta a la base de datos de Plex
        """
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        
        # Inicializar servicios
        self.detector = PlexEditionsDetector(database_path)
        self.creator = PlexEditionCreator()
        self.analyzer = PlexDuplicateAnalyzer()
    
    def analyze_duplicate_pair_with_editions(self, file1_path: str, file2_path: str,
                                           plex_info1: Optional[Dict], plex_info2: Optional[Dict]) -> Dict:
        """
        Analiza un par de duplicados considerando ediciones existentes
        
        Args:
            file1_path: Ruta del primer archivo
            file2_path: Ruta del segundo archivo
            plex_info1: Información de Plex del primer archivo
            plex_info2: Información de Plex del segundo archivo
            
        Returns:
            Análisis completo con recomendaciones de ediciones
        """
        try:
            # 1. Análisis básico de duplicados
            analysis = self.analyzer.analyze_duplicate_pair(file1_path, file2_path, plex_info1, plex_info2)
            
            if not analysis['same_movie']:
                return analysis
            
            # 2. Verificar ediciones existentes (con manejo de errores)
            try:
                if plex_info1 and plex_info2:
                    title = plex_info1.get('title', '')
                    year = plex_info1.get('year', '')
                    
                    if title and year:
                        existing_editions = self.detector.check_existing_editions(title, year)
                        analysis['existing_editions'] = existing_editions
                        analysis['has_existing_editions'] = len(existing_editions) > 0
            except Exception as e:
                self.logger.warning(f"Error verificando ediciones existentes: {e}")
                analysis['existing_editions'] = []
                analysis['has_existing_editions'] = False
            
            # 3. Verificar si los archivos ya tienen ediciones (con manejo de errores)
            try:
                edition1 = self.detector.check_if_file_has_edition(file1_path)
                edition2 = self.detector.check_if_file_has_edition(file2_path)
                
                analysis['file1_has_edition'] = edition1 is not None
                analysis['file2_has_edition'] = edition2 is not None
                
                if edition1:
                    analysis['file1_edition'] = edition1
                if edition2:
                    analysis['file2_edition'] = edition2
            except Exception as e:
                self.logger.warning(f"Error verificando ediciones de archivos: {e}")
                analysis['file1_has_edition'] = False
                analysis['file2_has_edition'] = False
            
            # 4. Generar recomendaciones específicas
            analysis['recommendations'] = self._generate_edition_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando par con ediciones: {e}")
            return {
                'same_movie': False,
                'recommendation': 'error',
                'message': f'Error en análisis: {e}'
            }
    
    def create_edition_for_file(self, file_path: str, movie_title: str, edition_name: str,
                               create_subfolder: bool = False) -> Optional[str]:
        """
        Crea una edición para un archivo específico
        
        Args:
            file_path: Ruta del archivo
            movie_title: Título de la película
            edition_name: Nombre de la edición
            create_subfolder: Si crear subcarpeta
            
        Returns:
            Nueva ruta del archivo o None si hay error
        """
        try:
            # Validar nombre de edición
            if not self.creator.validate_edition_name(edition_name):
                self.logger.error(f"Nombre de edición inválido: {edition_name}")
                return None
            
            # Crear edición (usar método UNC-safe para rutas de red)
            if file_path.startswith('\\\\'):
                new_path = self.creator.create_edition_file_unc_safe(file_path, movie_title, edition_name, create_subfolder)
            else:
                new_path = self.creator.create_edition_file(file_path, movie_title, edition_name, create_subfolder)
            
            if new_path:
                self.logger.info(f"Edición creada exitosamente: {new_path}")
                return new_path
            else:
                self.logger.error(f"Error creando edición para: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando edición: {e}")
            return None
    
    def get_edition_suggestions_for_movie(self, movie_title: str) -> List[str]:
        """
        Obtiene sugerencias de edición para una película específica
        
        Args:
            movie_title: Título de la película
            
        Returns:
            Lista de sugerencias
        """
        return self.creator.get_edition_suggestions(movie_title)
    
    def get_all_editions_for_movie(self, title: str, year: str) -> List[Dict]:
        """
        Obtiene todas las ediciones de una película
        
        Args:
            title: Título de la película
            year: Año de la película
            
        Returns:
            Lista de todas las ediciones
        """
        return self.detector.get_all_editions_for_movie(title, year)
    
    def _generate_edition_recommendations(self, analysis: Dict) -> List[str]:
        """
        Genera recomendaciones específicas basadas en el análisis
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        if analysis['recommendation'] == 'create_editions':
            if analysis.get('has_existing_editions', False):
                recommendations.append("Ya existen ediciones de esta película en Plex")
                recommendations.append("Considera usar un nombre de edición diferente")
            
            if analysis.get('file1_has_edition', False):
                recommendations.append("El primer archivo ya tiene una edición asignada")
            
            if analysis.get('file2_has_edition', False):
                recommendations.append("El segundo archivo ya tiene una edición asignada")
            
            if 'size_difference_percent' in analysis:
                recommendations.append(f"Archivos muy diferentes ({analysis['size_difference_percent']:.1f}% diferencia)")
                recommendations.append("Recomendado: Crear ediciones directamente")
            else:
                recommendations.append("Archivos diferentes de la misma película")
                recommendations.append("Recomendado: Crear ediciones para distinguirlos")
        
        elif analysis['recommendation'] == 'delete_duplicate':
            recommendations.append("Archivos idénticos detectados")
            recommendations.append("Recomendado: Eliminar uno de los duplicados")
        
        return recommendations
    
    def close_connections(self):
        """Cierra todas las conexiones"""
        self.detector.close_connection()
    
    def __del__(self):
        """Destructor para cerrar conexiones"""
        self.close_connections()
