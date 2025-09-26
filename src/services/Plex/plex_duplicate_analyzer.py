#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para análisis de duplicados con Plex
"""
import os
import hashlib
from typing import Dict, Optional, List, Tuple
import logging

class PlexDuplicateAnalyzer:
    """Analizador de duplicados con integración de Plex"""
    
    def __init__(self):
        """Inicializa el analizador de duplicados"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_duplicate_pair(self, file1_path: str, file2_path: str, 
                             plex_info1: Optional[Dict], plex_info2: Optional[Dict]) -> Dict:
        """
        Analiza un par de archivos para determinar si son duplicados
        
        Args:
            file1_path: Ruta del primer archivo
            file2_path: Ruta del segundo archivo
            plex_info1: Información de Plex del primer archivo
            plex_info2: Información de Plex del segundo archivo
            
        Returns:
            Análisis del par de archivos
        """
        try:
            # 1. Verificar si Plex los considera la misma película
            same_movie = self._check_same_movie(plex_info1, plex_info2)
            
            if not same_movie:
                return {
                    'same_movie': False,
                    'recommendation': 'different_movies',
                    'message': 'Películas diferentes según Plex'
                }
            
            # 2. Obtener información de archivos
            file_info1 = self._get_file_info(file1_path)
            file_info2 = self._get_file_info(file2_path)
            
            if not file_info1 or not file_info2:
                return {
                    'same_movie': True,
                    'recommendation': 'error',
                    'message': 'Error obteniendo información de archivos'
                }
            
            # 3. Análisis inteligente basado en tamaños
            size_analysis = self._analyze_file_sizes(file_info1, file_info2)
            
            if size_analysis['significantly_different']:
                return {
                    'same_movie': True,
                    'recommendation': 'create_editions',
                    'message': 'Misma película, archivos diferentes',
                    'size_difference_percent': size_analysis['difference_percent'],
                    'file1_size_gb': size_analysis['file1_size_gb'],
                    'file2_size_gb': size_analysis['file2_size_gb']
                }
            
            # 4. Tamaños similares - calcular hash
            hash_analysis = self._analyze_file_hashes(file1_path, file2_path)
            
            if hash_analysis['identical']:
                return {
                    'same_movie': True,
                    'recommendation': 'delete_duplicate',
                    'message': 'Mismo archivo, diferente nombre',
                    'hash_identical': True
                }
            else:
                return {
                    'same_movie': True,
                    'recommendation': 'create_editions',
                    'message': 'Misma película, archivos diferentes',
                    'hash_identical': False
                }
                
        except Exception as e:
            self.logger.error(f"Error analizando par de duplicados: {e}")
            return {
                'same_movie': False,
                'recommendation': 'error',
                'message': f'Error en análisis: {e}'
            }
    
    def _check_same_movie(self, plex_info1: Optional[Dict], plex_info2: Optional[Dict]) -> bool:
        """Verifica si Plex considera los archivos como la misma película"""
        if not plex_info1 or not plex_info2:
            return False
        
        title1 = plex_info1.get('title', '')
        title2 = plex_info2.get('title', '')
        year1 = plex_info1.get('year', '')
        year2 = plex_info2.get('year', '')
        
        return (title1 == title2 and year1 == year2 and 
                title1 != 'N/A' and year1 != 'N/A')
    
    def _get_file_info(self, file_path: str) -> Optional[Dict]:
        """Obtiene información básica del archivo"""
        try:
            normalized_path = os.path.normpath(file_path)
            
            if not os.path.exists(normalized_path):
                return None
            
            stat = os.stat(normalized_path)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'path': normalized_path
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo info del archivo {file_path}: {e}")
            return None
    
    def _analyze_file_sizes(self, file_info1: Dict, file_info2: Dict) -> Dict:
        """Analiza las diferencias de tamaño entre archivos"""
        size1 = file_info1['size']
        size2 = file_info2['size']
        
        # Calcular diferencia porcentual
        max_size = max(size1, size2)
        if max_size == 0:
            return {
                'significantly_different': False,
                'difference_percent': 0,
                'file1_size_gb': 0,
                'file2_size_gb': 0
            }
        
        difference_percent = abs(size1 - size2) / max_size * 100
        
        return {
            'significantly_different': difference_percent > 10,  # >10% diferencia
            'difference_percent': difference_percent,
            'file1_size_gb': size1 / (1024**3),
            'file2_size_gb': size2 / (1024**3)
        }
    
    def _analyze_file_hashes(self, file1_path: str, file2_path: str) -> Dict:
        """Analiza los hashes de los archivos"""
        try:
            hash1 = self._calculate_file_hash(file1_path)
            hash2 = self._calculate_file_hash(file2_path)
            
            if not hash1 or not hash2:
                return {
                    'identical': False,
                    'error': 'No se pudo calcular hash'
                }
            
            return {
                'identical': hash1 == hash2,
                'hash1': hash1,
                'hash2': hash2
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando hashes: {e}")
            return {
                'identical': False,
                'error': str(e)
            }
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calcula el hash MD5 de un archivo con indicador de progreso"""
        try:
            normalized_path = os.path.normpath(file_path)
            
            # Para rutas UNC, intentar acceso directo sin verificar existencia previa
            if file_path.startswith('\\\\'):
                self.logger.info(f"🔗 Calculando hash de ruta UNC: {file_path}")
                try:
                    hash_md5 = hashlib.md5()
                    bytes_read = 0
                    chunk_size = 8192
                    
                    # Obtener tamaño del archivo para mostrar progreso
                    try:
                        file_size = os.path.getsize(normalized_path)
                        self.logger.info(f"📊 Tamaño del archivo: {file_size / (1024*1024):.1f} MB")
                    except:
                        file_size = 0
                    
                    with open(normalized_path, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            hash_md5.update(chunk)
                            bytes_read += len(chunk)
                            
                            # Mostrar progreso cada 10MB
                            if file_size > 0 and bytes_read % (10 * 1024 * 1024) == 0:
                                progress = (bytes_read / file_size) * 100
                                self.logger.info(f"🔄 Progreso hash: {progress:.1f}% ({bytes_read / (1024*1024):.1f}MB/{file_size / (1024*1024):.1f}MB)")
                    
                    self.logger.info(f"✅ Hash calculado: {hash_md5.hexdigest()[:16]}...")
                    return hash_md5.hexdigest()
                except (OSError, IOError) as e:
                    self.logger.warning(f"⚠️ No se puede acceder a ruta UNC {file_path}: {e}")
                    return None
            else:
                # Para rutas locales, verificar existencia
                if not os.path.exists(normalized_path) or not os.path.isfile(normalized_path):
                    return None
                
                hash_md5 = hashlib.md5()
                bytes_read = 0
                chunk_size = 8192
                
                # Obtener tamaño del archivo para mostrar progreso
                try:
                    file_size = os.path.getsize(normalized_path)
                    if file_size > 50 * 1024 * 1024:  # Solo mostrar progreso para archivos > 50MB
                        self.logger.info(f"📊 Calculando hash de archivo local: {file_size / (1024*1024):.1f} MB")
                except:
                    file_size = 0
                
                with open(normalized_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        hash_md5.update(chunk)
                        bytes_read += len(chunk)
                        
                        # Mostrar progreso cada 10MB para archivos grandes
                        if file_size > 50 * 1024 * 1024 and bytes_read % (10 * 1024 * 1024) == 0:
                            progress = (bytes_read / file_size) * 100
                            self.logger.info(f"🔄 Progreso hash: {progress:.1f}% ({bytes_read / (1024*1024):.1f}MB/{file_size / (1024*1024):.1f}MB)")
                
                return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculando hash de {file_path}: {e}")
            return None
    
    def get_optimization_recommendation(self, analysis: Dict) -> str:
        """
        Obtiene una recomendación de optimización basada en el análisis
        
        Args:
            analysis: Resultado del análisis de duplicados
            
        Returns:
            Recomendación de optimización
        """
        if analysis['recommendation'] == 'create_editions':
            if 'size_difference_percent' in analysis:
                return f"Archivos muy diferentes ({analysis['size_difference_percent']:.1f}% diferencia). Crear ediciones directamente."
            else:
                return "Archivos diferentes de la misma película. Crear ediciones."
        elif analysis['recommendation'] == 'delete_duplicate':
            return "Archivos idénticos. Eliminar duplicado."
        elif analysis['recommendation'] == 'different_movies':
            return "Películas diferentes. No son duplicados."
        else:
            return "Análisis no concluyente."
