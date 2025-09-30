#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para crear ediciones en Plex
"""
import os
import shutil
from typing import Optional, Dict, List
import logging

class PlexEditionCreator:
    """Creador de ediciones para Plex"""
    
    def __init__(self):
        """Inicializa el creador de ediciones"""
        self.logger = logging.getLogger(__name__)
    
    def create_edition_file(self, file_path: str, movie_title: str, edition_name: str, 
                           create_subfolder: bool = False) -> Optional[str]:
        """
        Crea una edición renombrando el archivo según las convenciones de Plex
        
        Args:
            file_path: Ruta del archivo original
            movie_title: Título de la película
            edition_name: Nombre de la edición
            create_subfolder: Si crear subcarpeta o no
            
        Returns:
            Nueva ruta del archivo o None si hay error
        """
        try:
            # Normalizar la ruta del archivo
            normalized_path = os.path.normpath(file_path)
            
            # Verificar existencia con múltiples métodos para rutas UNC
            file_exists = False
            working_path = None
            
            # Método 1: Ruta normalizada
            try:
                if os.path.exists(normalized_path):
                    file_exists = True
                    working_path = normalized_path
            except Exception:
                pass
            
            # Método 2: Ruta original
            if not file_exists:
                try:
                    if os.path.exists(file_path):
                        file_exists = True
                        working_path = file_path
                except Exception:
                    pass
            
            # Método 3: pathlib para rutas UNC
            if not file_exists:
                try:
                    from pathlib import Path
                    path_obj = Path(file_path)
                    if path_obj.exists():
                        file_exists = True
                        working_path = str(path_obj)
                except Exception:
                    pass
            
            if not file_exists:
                # Para rutas UNC, intentar continuar de todas formas
                if file_path.startswith('\\\\'):
                    self.logger.warning(f"Ruta UNC no accesible desde script: {file_path}")
                    self.logger.warning("Continuando con la ruta original (puede funcionar en Streamlit)")
                    working_path = file_path
                else:
                    self.logger.error(f"Archivo no encontrado: {file_path}")
                    return None
            
            # Usar la ruta que funciona
            file_path = working_path
            
            # Obtener directorio y nombre base
            directory = os.path.dirname(normalized_path)
            filename = os.path.basename(normalized_path)
            name, ext = os.path.splitext(filename)
            
            # Limpiar el nombre de la edición para evitar caracteres problemáticos
            clean_edition_name = self._clean_edition_name(edition_name)
            
            # Crear nuevo nombre con formato Plex: {edition-Nombre de la Edición}
            new_filename = f"{name} {{edition-{clean_edition_name}}}{ext}"
            
            # Verificar que el nuevo nombre no sea demasiado largo
            if len(new_filename) > 255:
                # Truncar el nombre si es muy largo
                max_name_length = 255 - len(ext) - len(f" {{edition-{clean_edition_name}}}")
                truncated_name = name[:max_name_length]
                new_filename = f"{truncated_name} {{edition-{clean_edition_name}}}{ext}"
            
            if create_subfolder:
                # Crear subcarpeta con el nombre de la edición
                clean_movie_title = self._clean_filename(movie_title)
                folder_name = f"{clean_movie_title} {{edition-{clean_edition_name}}}"
                new_directory = os.path.join(directory, folder_name)
                
                # Crear directorio si no existe
                os.makedirs(new_directory, exist_ok=True)
                
                # Ruta completa del nuevo archivo
                new_path = os.path.join(new_directory, new_filename)
            else:
                # Solo renombrar el archivo
                new_path = os.path.join(directory, new_filename)
            
            # Verificar que el archivo de destino no exista
            if os.path.exists(new_path):
                self.logger.error(f"El archivo de destino ya existe: {new_path}")
                return None
            
            # Renombrar archivo
            try:
                os.rename(file_path, new_path)
                self.logger.info(f"Edición creada exitosamente: {new_path}")
                return new_path
            except Exception as rename_error:
                self.logger.error(f"Error renombrando archivo: {rename_error}")
                # Intentar con ruta normalizada si falla
                try:
                    os.rename(normalized_path, new_path)
                    self.logger.info(f"Edición creada exitosamente (ruta normalizada): {new_path}")
                    return new_path
                except Exception as final_error:
                    self.logger.error(f"Error final renombrando: {final_error}")
                    return None
            
        except Exception as e:
            self.logger.error(f"Error creando edición: {e}")
            return None
    
    def create_edition_with_backup(self, file_path: str, movie_title: str, edition_name: str,
                                 create_subfolder: bool = False) -> Optional[str]:
        """
        Crea una edición con respaldo del archivo original
        
        Args:
            file_path: Ruta del archivo original
            movie_title: Título de la película
            edition_name: Nombre de la edición
            create_subfolder: Si crear subcarpeta o no
            
        Returns:
            Nueva ruta del archivo o None si hay error
        """
        try:
            # Crear respaldo
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            
            # Crear edición
            new_path = self.create_edition_file(file_path, movie_title, edition_name, create_subfolder)
            
            if new_path:
                # Eliminar respaldo si todo salió bien
                os.remove(backup_path)
                return new_path
            else:
                # Restaurar desde respaldo si falló
                shutil.move(backup_path, file_path)
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando edición con respaldo: {e}")
            return None
    
    def get_edition_suggestions(self, movie_title: str) -> List[str]:
        """
        Obtiene sugerencias de nombres de edición basadas en el título de la película
        
        Args:
            movie_title: Título de la película
            
        Returns:
            Lista de sugerencias de edición
        """
        suggestions = [
            "Edición del Director",
            "Edición Especial",
            "Edición Extendida", 
            "Edición Teatral",
            "Edición 20 Aniversario",
            "Edición 4K",
            "Edición Remasterizada",
            "Edición Sin Cortes",
            "Edición Unrated",
            "Edición Especial 25 Aniversario"
        ]
        
        # Agregar sugerencias específicas basadas en el título
        if "star wars" in movie_title.lower():
            suggestions.extend([
                "Edición Especial",
                "Edición Original",
                "Edición Teatral"
            ])
        elif "blade runner" in movie_title.lower():
            suggestions.extend([
                "Director's Cut",
                "Final Cut",
                "Theatrical Cut"
            ])
        elif "alien" in movie_title.lower():
            suggestions.extend([
                "Director's Cut",
                "Theatrical Cut"
            ])
        
        return suggestions
    
    def validate_edition_name(self, edition_name: str) -> bool:
        """
        Valida si el nombre de la edición es válido para Plex
        
        Args:
            edition_name: Nombre de la edición
            
        Returns:
            True si es válido, False si no
        """
        if not edition_name or not edition_name.strip():
            return False
        
        # Caracteres no permitidos en nombres de archivo
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        
        for char in invalid_chars:
            if char in edition_name:
                return False
        
        return True
    
    def get_edition_info_from_filename(self, file_path: str) -> Optional[Dict]:
        """
        Extrae información de edición del nombre del archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Información de la edición si existe
        """
        try:
            filename = os.path.basename(file_path)
            
            # Buscar patrón {edition-Nombre}
            if '{edition-' in filename and '}' in filename:
                start = filename.find('{edition-') + 9
                end = filename.find('}', start)
                
                if start < end:
                    edition_name = filename[start:end]
                    return {
                        'edition_name': edition_name,
                        'has_edition': True
                    }
            
            return {
                'edition_name': None,
                'has_edition': False
            }
            
        except Exception as e:
            self.logger.error(f"Error extrayendo información de edición: {e}")
            return None
    
    def _clean_edition_name(self, edition_name: str) -> str:
        """Limpia el nombre de la edición para evitar caracteres problemáticos"""
        if not edition_name:
            return "Edicion"
        
        # Caracteres problemáticos en nombres de archivo
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        
        clean_name = edition_name
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '')
        
        # Reemplazar espacios múltiples por uno solo
        clean_name = ' '.join(clean_name.split())
        
        # Limitar longitud
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        
        return clean_name.strip() or "Edicion"
    
    def _clean_filename(self, filename: str) -> str:
        """Limpia un nombre de archivo para evitar caracteres problemáticos"""
        if not filename:
            return "Archivo"
        
        # Caracteres problemáticos en nombres de archivo
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        
        clean_name = filename
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '')
        
        # Reemplazar espacios múltiples por uno solo
        clean_name = ' '.join(clean_name.split())
        
        # Limitar longitud
        if len(clean_name) > 100:
            clean_name = clean_name[:100]
        
        return clean_name.strip() or "Archivo"
    
    def create_edition_file_unc_safe(self, file_path: str, movie_title: str, edition_name: str, 
                                    create_subfolder: bool = False) -> Optional[str]:
        """
        Crea una edición con manejo seguro de rutas UNC
        
        Args:
            file_path: Ruta del archivo original
            movie_title: Título de la película
            edition_name: Nombre de la edición
            create_subfolder: Si crear subcarpeta o no
            
        Returns:
            Nueva ruta del archivo o None si hay error
        """
        try:
            # Para rutas UNC, usar la ruta original sin verificar existencia
            if file_path.startswith('\\\\'):
                self.logger.info(f"Procesando ruta UNC: {file_path}")
                return self._create_edition_with_path(file_path, movie_title, edition_name, create_subfolder)
            else:
                # Para rutas locales, usar el método normal
                return self.create_edition_file(file_path, movie_title, edition_name, create_subfolder)
                
        except Exception as e:
            self.logger.error(f"Error en creación UNC-safe: {e}")
            return None
    
    def _create_edition_with_path(self, file_path: str, movie_title: str, edition_name: str, 
                                 create_subfolder: bool = False) -> Optional[str]:
        """Crea edición con una ruta específica sin verificar existencia previa"""
        try:
            # Obtener directorio y nombre base
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            # Limpiar el nombre de la edición
            clean_edition_name = self._clean_edition_name(edition_name)
            
            # Crear nuevo nombre con formato Plex
            new_filename = f"{name} {{edition-{clean_edition_name}}}{ext}"
            
            # Verificar longitud
            if len(new_filename) > 255:
                max_name_length = 255 - len(ext) - len(f" {{edition-{clean_edition_name}}}")
                truncated_name = name[:max_name_length]
                new_filename = f"{truncated_name} {{edition-{clean_edition_name}}}{ext}"
            
            if create_subfolder:
                # Crear subcarpeta
                clean_movie_title = self._clean_filename(movie_title)
                folder_name = f"{clean_movie_title} {{edition-{clean_edition_name}}}"
                new_directory = os.path.join(directory, folder_name)
                os.makedirs(new_directory, exist_ok=True)
                new_path = os.path.join(new_directory, new_filename)
            else:
                # Solo renombrar archivo
                new_path = os.path.join(directory, new_filename)
            
            # Verificar que el destino no existe
            if os.path.exists(new_path):
                self.logger.error(f"El archivo de destino ya existe: {new_path}")
                return None
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            self.logger.info(f"Edición creada exitosamente: {new_path}")
            return new_path
            
        except Exception as e:
            self.logger.error(f"Error creando edición con ruta: {e}")
            return None
