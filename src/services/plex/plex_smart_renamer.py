# -*- coding: utf-8 -*-
"""
Renombrador inteligente para que PLEX detecte películas
Convierte nombres de archivo a formatos que PLEX reconoce
"""

import re
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class PlexSmartRenamer:
    """Renombrador inteligente para compatibilidad con PLEX"""
    
    def __init__(self):
        self.backup_folder = None
    
    def analyze_filename(self, filename: str) -> Dict[str, str]:
        """
        Analiza un nombre de archivo y extrae información
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            dict: Información extraída del archivo
        """
        # Remover extensión
        name_without_ext = Path(filename).stem
        
        # Patrones comunes para extraer información
        patterns = {
            'title': r'^(.+?)(?:\s*\((\d{4})\))?(?:\s*-\s*(.+))?$',
            'year': r'\((\d{4})\)',
            'version': r'(?:-\s*|{)(.+?)(?:}|$)',  # Mejorado para detectar versiones
            'quality': r'(?:\.|_)(?:HD|SD|DVDRip|BRRip|WEBRip|BluRay|HDTV|WEB-DL)',
            'source': r'\[([^\]]+)\]'
        }
        
        info = {
            'original': filename,
            'title': name_without_ext,
            'year': None,
            'version': None,
            'quality': None,
            'source': None
        }
        
        # Extraer año
        year_match = re.search(patterns['year'], name_without_ext)
        if year_match:
            info['year'] = year_match.group(1)
        
        # Extraer versión (Montaje Director, Extended, etc.)
        # Buscar versiones entre llaves {Montaje Director}
        version_match = re.search(r'\{([^}]+)\}', name_without_ext)
        if version_match:
            info['version'] = version_match.group(1).strip()
        else:
            # Buscar versiones después de guión - Montaje Director
            version_match = re.search(r'-\s*(.+?)(?:\s*\((\d{4})\))?$', name_without_ext)
            if version_match:
                info['version'] = version_match.group(1).strip()
        
        # Extraer calidad
        quality_match = re.search(patterns['quality'], name_without_ext, re.IGNORECASE)
        if quality_match:
            info['quality'] = quality_match.group(0).strip('._')
        
        # Extraer fuente
        source_match = re.search(patterns['source'], name_without_ext)
        if source_match:
            info['source'] = source_match.group(1)
        
        return info
    
    def generate_plex_friendly_name(self, file_info: Dict[str, str]) -> str:
        """
        Genera un nombre compatible con PLEX usando el formato de ediciones
        
        Args:
            file_info: Información del archivo
            
        Returns:
            str: Nombre compatible con PLEX
        """
        title = file_info['title']
        year = file_info.get('year')
        version = file_info.get('version')
        quality = file_info.get('quality')
        
        # Limpiar título base
        base_title = title
        
        # Remover versión del título si está al final
        if version and base_title.endswith(f' - {version}'):
            base_title = base_title.replace(f' - {version}', '').strip()
        
        # Remover año del título si está al final
        if year and base_title.endswith(f' ({year})'):
            base_title = base_title.replace(f' ({year})', '').strip()
        
        # Remover llaves y caracteres especiales
        base_title = re.sub(r'[{}]', '', base_title)
        base_title = re.sub(r'\s+', ' ', base_title).strip()
        
        # Construir nombre compatible con PLEX
        plex_name = base_title
        
        # Añadir año si existe
        if year:
            plex_name += f' ({year})'
        
        # Añadir versión como edición PLEX si existe
        if version:
            # Limpiar versión
            clean_version = version.strip('{}')
            # Usar formato de edición PLEX: {edition-Nombre}
            plex_name += f' {{edition-{clean_version}}}'
        
        return plex_name
    
    def suggest_rename(self, file_path: str, create_folder: bool = False) -> Optional[Dict[str, str]]:
        """
        Sugiere un nuevo nombre para un archivo
        
        Args:
            file_path: Ruta del archivo
            create_folder: Si crear carpeta separada para la edición
            
        Returns:
            dict: Sugerencia de renombrado
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"❌ Archivo no encontrado: {file_path}")
                return None
            
            # Analizar archivo
            file_info = self.analyze_filename(path.name)
            
            # Generar nombre compatible con PLEX
            plex_name = self.generate_plex_friendly_name(file_info)
            
            # Construir nueva ruta
            new_filename = f"{plex_name}{path.suffix}"
            
            if create_folder and file_info.get('version'):
                # Crear carpeta separada para la edición
                folder_name = f"{plex_name.split(' {edition-')[0]} {file_info.get('version')}"
                new_path = path.parent / folder_name / new_filename
            else:
                # Misma carpeta
                new_path = path.parent / new_filename
            
            return {
                'original_path': str(path),
                'original_name': path.name,
                'suggested_name': new_filename,
                'suggested_path': str(new_path),
                'file_info': file_info,
                'plex_name': plex_name,
                'create_folder': create_folder
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando archivo: {e}")
            return None
    
    def rename_file(self, file_path: str, create_backup: bool = True) -> bool:
        """
        Renombra un archivo con el nombre sugerido
        
        Args:
            file_path: Ruta del archivo
            create_backup: Si crear backup antes de renombrar
            
        Returns:
            bool: True si el renombrado fue exitoso
        """
        try:
            suggestion = self.suggest_rename(file_path)
            if not suggestion:
                return False
            
            original_path = Path(suggestion['original_path'])
            new_path = Path(suggestion['suggested_path'])
            
            # Verificar que el nuevo nombre sea diferente
            if original_path.name == new_path.name:
                logger.info(f"ℹ️ El archivo ya tiene un nombre compatible: {original_path.name}")
                return True
            
            # Crear backup si se solicita
            if create_backup:
                backup_path = original_path.with_suffix(original_path.suffix + '.backup')
                shutil.copy2(original_path, backup_path)
                logger.info(f"📁 Backup creado: {backup_path}")
            
            # Renombrar archivo
            original_path.rename(new_path)
            logger.info(f"✅ Archivo renombrado: {original_path.name} → {new_path.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error renombrando archivo: {e}")
            return False
    
    def batch_rename_duplicates(self, duplicate_group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Renombra un grupo de duplicados para que PLEX los reconozca
        
        Args:
            duplicate_group: Grupo de duplicados
            
        Returns:
            list: Grupo con archivos renombrados
        """
        renamed_group = []
        
        for movie in duplicate_group:
            try:
                file_path = movie.get('archivo', '')
                if not file_path:
                    renamed_group.append(movie)
                    continue
                
                # Analizar archivo
                suggestion = self.suggest_rename(file_path)
                if suggestion:
                    # Actualizar información del archivo
                    movie['suggested_plex_name'] = suggestion['plex_name']
                    movie['suggested_filename'] = suggestion['suggested_name']
                    movie['rename_available'] = True
                    
                    logger.info(f"💡 Sugerencia para {Path(file_path).name}: {suggestion['suggested_name']}")
                else:
                    movie['rename_available'] = False
                
                renamed_group.append(movie)
                
            except Exception as e:
                logger.error(f"❌ Error procesando archivo: {e}")
                renamed_group.append(movie)
        
        return renamed_group


def test_smart_renamer():
    """Función de prueba para el renombrador inteligente"""
    
    renamer = PlexSmartRenamer()
    
    # Archivos de prueba
    test_files = [
        "Reanimator {Montaje Director} (1985).mkv",
        "Reanimator Montaje Director (1985).mkv",
        "El secreto de la pirámide (1985).mp4",
        "v el secreto de la piramide(1985).avi"
    ]
    
    print("🧪 Probando renombrador inteligente...")
    
    for filename in test_files:
        print(f"\n📁 Archivo: {filename}")
        
        # Analizar archivo
        file_info = renamer.analyze_filename(filename)
        print(f"   - Título: {file_info['title']}")
        print(f"   - Año: {file_info['year']}")
        print(f"   - Versión: {file_info['version']}")
        print(f"   - Calidad: {file_info['quality']}")
        
        # Generar nombre compatible
        plex_name = renamer.generate_plex_friendly_name(file_info)
        print(f"   - Nombre PLEX: {plex_name}")
        
        # Mostrar opciones de renombrado
        print(f"\n   📂 Opción 1 - Misma carpeta:")
        print(f"      {filename} → {plex_name}{Path(filename).suffix}")
        
        if file_info.get('version'):
            print(f"\n   📁 Opción 2 - Carpeta separada:")
            folder_name = f"{plex_name.split(' {edition-')[0]} {file_info.get('version')}"
            print(f"      {filename} → {folder_name}/{plex_name}{Path(filename).suffix}")


if __name__ == "__main__":
    test_smart_renamer()
