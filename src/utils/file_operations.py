#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades para operaciones de archivos
"""

import streamlit as st
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from src.settings.settings import settings


class FileOperations:
    """Clase para operaciones de archivos"""
    
    def __init__(self):
        # Usar valores por defecto si los métodos no existen (compatibilidad)
        try:
            self.debug_mode = settings.get_debug_enabled()
        except AttributeError:
            self.debug_mode = True  # Modo debug por defecto
        
        try:
            self.debug_folder = settings.get_debug_folder()
            if not self.debug_folder:
                # Si no hay carpeta de debug configurada, usar una por defecto
                self.debug_folder = ""
        except AttributeError:
            self.debug_folder = ""
    
    def move_files(self, file_paths: List[str], destination_folder: str) -> Tuple[int, int, List[str]]:
        """
        Mueve archivos a una carpeta de destino
        
        Args:
            file_paths: Lista de rutas de archivos a mover
            destination_folder: Carpeta de destino
            
        Returns:
            Tuple[int, int, List[str]]: (archivos_movidos, errores, archivos_no_encontrados)
        """
        moved_count = 0
        error_count = 0
        not_found = []
        
        # Crear carpeta de destino si no existe
        Path(destination_folder).mkdir(parents=True, exist_ok=True)
        
        for file_path in file_paths:
            try:
                origen = Path(file_path)
                if not origen.exists():
                    not_found.append(file_path)
                    continue
                
                destino = Path(destination_folder) / origen.name
                
                # Si el archivo ya existe en destino, agregar sufijo
                counter = 1
                while destino.exists():
                    stem = origen.stem
                    suffix = origen.suffix
                    destino = Path(destination_folder) / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.move(str(origen), str(destino))
                moved_count += 1
                
            except Exception as e:
                st.error(f"❌ Error moviendo {file_path}: {e}")
                error_count += 1
        
        return moved_count, error_count, not_found
    
    def delete_files(self, file_paths: List[str]) -> Tuple[int, int, List[str]]:
        """
        Elimina archivos (o los mueve a debug si está habilitado)
        
        Args:
            file_paths: Lista de rutas de archivos a eliminar
            
        Returns:
            Tuple[int, int, List[str]]: (archivos_procesados, errores, archivos_no_encontrados)
        """
        processed_count = 0
        error_count = 0
        not_found = []
        
        for file_path in file_paths:
            try:
                origen = Path(file_path)
                if not origen.exists():
                    not_found.append(file_path)
                    continue
                
                if self.debug_mode:
                    # Modo debug: mover a carpeta debug
                    self._move_to_debug(origen)
                else:
                    # Modo normal: eliminar
                    origen.unlink()
                
                processed_count += 1
                
            except Exception as e:
                st.error(f"❌ Error procesando {file_path}: {e}")
                error_count += 1
        
        return processed_count, error_count, not_found
    
    def _move_to_debug(self, file_path: Path) -> None:
        """
        Mueve un archivo a la carpeta de debug
        
        Args:
            file_path: Ruta del archivo a mover
        """
        try:
            # Crear carpeta debug si no existe
            debug_path = Path(self.debug_folder)
            debug_path.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo a debug
            destino = debug_path / file_path.name
            
            # Si el archivo ya existe en debug, agregar sufijo
            counter = 1
            while destino.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                destino = debug_path / f"{stem}_debug_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(file_path), str(destino))
            
        except Exception as e:
            st.error(f"❌ Error moviendo a debug {file_path}: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict: Información del archivo
        """
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            return {
                "exists": False,
                "size": 0,
                "size_gb": 0.0,
                "name": path_obj.name,
                "parent": str(path_obj.parent)
            }
        
        size_bytes = path_obj.stat().st_size
        size_gb = size_bytes / (1024**3)
        
        return {
            "exists": True,
            "size": size_bytes,
            "size_gb": size_gb,
            "name": path_obj.name,
            "parent": str(path_obj.parent),
            "extension": path_obj.suffix.lower()
        }
    
    def validate_destination_folder(self, folder_path: str) -> Tuple[bool, str]:
        """
        Valida si una carpeta de destino es válida
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            Tuple[bool, str]: (es_válida, mensaje)
        """
        try:
            path_obj = Path(folder_path)
            
            # Verificar si es una ruta válida
            if not path_obj.is_absolute():
                return False, "La ruta debe ser absoluta"
            
            # Verificar si el directorio padre existe
            if not path_obj.parent.exists():
                return False, "El directorio padre no existe"
            
            # Verificar permisos de escritura
            if not os.access(path_obj.parent, os.W_OK):
                return False, "No tienes permisos de escritura en el directorio padre"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Error validando carpeta: {e}"


class FileBatchProcessor:
    """Clase para procesar lotes de archivos"""
    
    def __init__(self):
        self.file_ops = FileOperations()
    
    def process_selected_movies(self, selections: List[Dict[str, Any]], 
                              df_data: List[Dict[str, Any]], 
                              operation: str, 
                              destination: str = None) -> Dict[str, Any]:
        """
        Procesa películas seleccionadas
        
        Args:
            selections: Lista de selecciones
            df_data: Datos de las filas
            operation: Tipo de operación ('move' o 'delete')
            destination: Carpeta de destino (solo para move)
            
        Returns:
            Dict: Resultado del procesamiento
        """
        file_paths = []
        
        # Obtener rutas de archivos seleccionados
        for selection in selections:
            pair_index = selection['pair_index']
            movie_number = selection['movie_number']
            
            if pair_index < len(df_data):
                row = df_data[pair_index]
                if movie_number == 1:
                    file_paths.append(row['Ruta 1'])
                elif movie_number == 2:
                    file_paths.append(row['Ruta 2'])
        
        # Filtrar archivos que existen
        existing_files = [fp for fp in file_paths if Path(fp).exists()]
        non_existing = [fp for fp in file_paths if not Path(fp).exists()]
        
        if operation == 'move' and destination:
            # Validar carpeta de destino
            is_valid, message = self.file_ops.validate_destination_folder(destination)
            if not is_valid:
                return {
                    "success": False,
                    "message": f"Error en carpeta de destino: {message}",
                    "moved": 0,
                    "errors": 0,
                    "not_found": len(non_existing)
                }
            
            # Mover archivos
            moved, errors, not_found = self.file_ops.move_files(existing_files, destination)
            
            return {
                "success": True,
                "message": f"Operación completada",
                "moved": moved,
                "errors": errors,
                "not_found": len(not_found) + len(non_existing)
            }
        
        elif operation == 'delete':
            # Eliminar archivos
            processed, errors, not_found = self.file_ops.delete_files(existing_files)
            
            return {
                "success": True,
                "message": f"Operación completada",
                "processed": processed,
                "errors": errors,
                "not_found": len(not_found) + len(non_existing)
            }
        
        return {
            "success": False,
            "message": "Operación no válida",
            "moved": 0,
            "errors": 0,
            "not_found": 0
        }
