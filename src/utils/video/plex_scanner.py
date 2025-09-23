#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escáner de PLEX para detectar películas no reconocidas
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from src.settings.settings import settings

# Importación opcional de PLEX
try:
    from src.services.plex.plex_database_direct import PlexDatabaseDirect
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False


class PlexScanner:
    """
    Clase para escanear directorios y detectar películas no reconocidas por PLEX
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.extensiones_video = [
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
            '.m4v', '.mpg', '.mpeg', '.3gp', '.webm'
        ]
    
    def escanear_directorio(self, directorio: str) -> Dict[str, Any]:
        """
        Escanea un directorio buscando películas no reconocidas por PLEX
        
        Args:
            directorio: Ruta del directorio a escanear
            
        Returns:
            dict: Resultados del escaneo
        """
        try:
            directorio_path = Path(directorio)
            if not directorio_path.exists():
                return {
                    "error": f"El directorio {directorio} no existe",
                    "peliculas_encontradas": [],
                    "peliculas_no_encontradas": [],
                    "total_archivos": 0
                }
            
            # Conectar a PLEX
            if not PLEX_AVAILABLE:
                return {
                    "error": "PLEX no está disponible",
                    "peliculas_encontradas": [],
                    "peliculas_no_encontradas": [],
                    "total_archivos": 0
                }
            
            plex_db = PlexDatabaseDirect(settings.get_plex_database_path())
            if not plex_db.connect():
                return {
                    "error": "No se pudo conectar a la base de datos de PLEX",
                    "peliculas_encontradas": [],
                    "peliculas_no_encontradas": [],
                    "total_archivos": 0
                }
            
            # Escanear archivos de video
            archivos_video = self._obtener_archivos_video(directorio_path)
            self.logger.info(f"Encontrados {len(archivos_video)} archivos de video")
            
            peliculas_encontradas = []
            peliculas_no_encontradas = []
            
            for archivo in archivos_video:
                resultado = self._verificar_pelicula_en_plex(archivo, plex_db)
                
                if resultado["encontrada"]:
                    peliculas_encontradas.append(resultado)
                else:
                    peliculas_no_encontradas.append(resultado)
            
            plex_db.close()
            
            return {
                "error": None,
                "peliculas_encontradas": peliculas_encontradas,
                "peliculas_no_encontradas": peliculas_no_encontradas,
                "total_archivos": len(archivos_video),
                "directorio": str(directorio_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error escaneando directorio: {e}")
            return {
                "error": str(e),
                "peliculas_encontradas": [],
                "peliculas_no_encontradas": [],
                "total_archivos": 0
            }
    
    def _obtener_archivos_video(self, directorio: Path) -> List[Path]:
        """
        Obtiene todos los archivos de video de un directorio
        
        Args:
            directorio: Directorio a escanear
            
        Returns:
            List[Path]: Lista de archivos de video
        """
        archivos_video = []
        
        try:
            for archivo in directorio.rglob("*"):
                if archivo.is_file() and archivo.suffix.lower() in self.extensiones_video:
                    archivos_video.append(archivo)
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos de video: {e}")
        
        return archivos_video
    
    def _verificar_pelicula_en_plex(self, archivo: Path, plex_db: PlexDatabaseDirect) -> Dict[str, Any]:
        """
        Verifica si una película está en PLEX
        
        Args:
            archivo: Archivo de video
            plex_db: Conexión a la base de datos de PLEX
            
        Returns:
            dict: Información de la verificación
        """
        try:
            nombre_archivo = archivo.name
            
            # Buscar por nombre de archivo
            resultado = plex_db.search_movie_by_path(nombre_archivo)
            
            if resultado:
                return {
                    "archivo": str(archivo),
                    "nombre": nombre_archivo,
                    "encontrada": True,
                    "titulo_plex": resultado.get('title', 'N/A'),
                    "año_plex": resultado.get('year', 'N/A'),
                    "duracion_plex": resultado.get('duration', 0),
                    "ruta_plex": resultado.get('file_path', 'N/A'),
                    "sugerencias_renombre": []
                }
            else:
                # Buscar por título extraído
                titulo_extraido = self._extraer_titulo_del_archivo(nombre_archivo)
                sugerencias = self._generar_sugerencias_renombre(nombre_archivo, titulo_extraido)
                
                return {
                    "archivo": str(archivo),
                    "nombre": nombre_archivo,
                    "encontrada": False,
                    "titulo_plex": None,
                    "año_plex": None,
                    "duracion_plex": 0,
                    "ruta_plex": None,
                    "titulo_extraido": titulo_extraido,
                    "sugerencias_renombre": sugerencias
                }
                
        except Exception as e:
            self.logger.error(f"Error verificando película {archivo}: {e}")
            return {
                "archivo": str(archivo),
                "nombre": archivo.name,
                "encontrada": False,
                "error": str(e),
                "sugerencias_renombre": []
            }
    
    def _extraer_titulo_del_archivo(self, nombre_archivo: str) -> str:
        """
        Extrae un título limpio del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            str: Título limpio
        """
        try:
            # Remover extensión
            titulo = Path(nombre_archivo).stem
            
            # Remover patrones comunes
            patrones_a_remover = [
                r'\(\d{4}\)',  # (1995)
                r'\(Spanish\)',  # (Spanish)
                r'\(DVD-Rip\)',  # (DVD-Rip)
                r'\(AVC-AC3\)',  # (AVC-AC3)
                r'\(HD\)',  # (HD)
                r'\(720p\)',  # (720p)
                r'\(1080p\)',  # (1080p)
                r'\(BluRay\)',  # (BluRay)
                r'by\.\w+',  # by.usuario
                r'\[.*?\]',  # [cualquier cosa entre corchetes]
                r'\.mkv$',  # .mkv
                r'\.mp4$',  # .mp4
                r'\.avi$',  # .avi
            ]
            
            import re
            for patron in patrones_a_remover:
                titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)
            
            # Limpiar espacios y puntos
            titulo = titulo.replace('.', ' ').strip()
            
            # Remover espacios múltiples
            titulo = re.sub(r'\s+', ' ', titulo)
            
            return titulo
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo título: {e}")
            return nombre_archivo
    
    def _generar_sugerencias_renombre(self, nombre_archivo: str, titulo_extraido: str) -> List[str]:
        """
        Genera sugerencias de renombrado para un archivo
        
        Args:
            nombre_archivo: Nombre original del archivo
            titulo_extraido: Título extraído del archivo
            
        Returns:
            List[str]: Lista de sugerencias
        """
        sugerencias = []
        
        try:
            # Obtener extensión
            extension = Path(nombre_archivo).suffix
            
            # Sugerencia 1: Título limpio
            if titulo_extraido and titulo_extraido != nombre_archivo:
                sugerencias.append(f"{titulo_extraido}{extension}")
            
            # Sugerencia 2: Título con año (si se puede extraer)
            año = self._extraer_año_del_archivo(nombre_archivo)
            if año and titulo_extraido:
                sugerencias.append(f"{titulo_extraido} ({año}){extension}")
            
            # Sugerencia 3: Título con formato estándar
            if titulo_extraido:
                titulo_formateado = titulo_extraido.replace(' ', '.').title()
                sugerencias.append(f"{titulo_formateado}{extension}")
            
            # Sugerencia 4: Título con formato estándar y año
            if año and titulo_extraido:
                titulo_formateado = titulo_extraido.replace(' ', '.').title()
                sugerencias.append(f"{titulo_formateado}.({año}){extension}")
            
        except Exception as e:
            self.logger.debug(f"Error generando sugerencias: {e}")
        
        return sugerencias[:4]  # Máximo 4 sugerencias
    
    def _extraer_año_del_archivo(self, nombre_archivo: str) -> Optional[str]:
        """
        Extrae el año del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Optional[str]: Año extraído o None
        """
        try:
            import re
            # Buscar patrones de año: (1995), 1995, [1995]
            patrones_año = [
                r'\((\d{4})\)',  # (1995)
                r'\[(\d{4})\]',  # [1995]
                r'(\d{4})',  # 1995
            ]
            
            for patron in patrones_año:
                match = re.search(patron, nombre_archivo)
                if match:
                    año = match.group(1)
                    # Verificar que sea un año válido (1900-2030)
                    if 1900 <= int(año) <= 2030:
                        return año
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo año: {e}")
            return None
    
    def renombrar_archivo(self, archivo_original: str, nuevo_nombre: str) -> Dict[str, Any]:
        """
        Renombra un archivo
        
        Args:
            archivo_original: Ruta del archivo original
            nuevo_nombre: Nuevo nombre del archivo
            
        Returns:
            dict: Resultado del renombrado
        """
        try:
            archivo_path = Path(archivo_original)
            directorio = archivo_path.parent
            nuevo_archivo = directorio / nuevo_nombre
            
            if not archivo_path.exists():
                return {
                    "exito": False,
                    "error": f"El archivo {archivo_original} no existe"
                }
            
            if nuevo_archivo.exists():
                return {
                    "exito": False,
                    "error": f"Ya existe un archivo con el nombre {nuevo_nombre}"
                }
            
            # Renombrar archivo
            archivo_path.rename(nuevo_archivo)
            
            return {
                "exito": True,
                "archivo_original": str(archivo_path),
                "archivo_nuevo": str(nuevo_archivo),
                "mensaje": f"Archivo renombrado exitosamente"
            }
            
        except Exception as e:
            self.logger.error(f"Error renombrando archivo: {e}")
            return {
                "exito": False,
                "error": str(e)
            }
