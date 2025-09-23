#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración con PLEX para metadatos de videos
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.settings.settings import settings

# Importación opcional de PLEX
try:
    from src.services.plex.plex_database_direct import PlexDatabaseDirect
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False


class PlexVideoIntegration:
    """
    Clase para integración con PLEX para metadatos de videos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.plex_db = None
    
    def conectar_plex(self) -> bool:
        """
        Conecta a la base de datos de PLEX
        
        Returns:
            bool: True si se conectó exitosamente
        """
        if not PLEX_AVAILABLE:
            self.logger.warning("PLEX no está disponible")
            return False
        
        try:
            self.plex_db = PlexDatabaseDirect()
            if self.plex_db.connect():
                self.logger.info("✅ Conectado a PLEX")
                return True
            else:
                self.logger.warning("❌ No se pudo conectar a PLEX")
                return False
        except Exception as e:
            self.logger.error(f"Error conectando a PLEX: {e}")
            return False
    
    def desconectar_plex(self):
        """Desconecta de PLEX"""
        if self.plex_db:
            self.plex_db.close()
            self.plex_db = None
            self.logger.info("✅ Desconectado de PLEX")
    
    def buscar_video_por_archivo(self, archivo: Path) -> Optional[Dict[str, Any]]:
        """
        Busca un video en PLEX por su archivo
        
        Args:
            archivo: Ruta del archivo
            
        Returns:
            dict: Metadatos de PLEX o None
        """
        if not self.plex_db:
            if not self.conectar_plex():
                return None
        
        try:
            # Buscar por nombre de archivo
            resultados = self.plex_db.search_movie_by_path(archivo.name)
            
            if resultados:
                return resultados[0]  # Devolver el primer resultado
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando en PLEX: {e}")
            return None
    
    def obtener_metadatos_completos(self, archivo: Path) -> Dict[str, Any]:
        """
        Obtiene metadatos completos de un video desde PLEX
        
        Args:
            archivo: Ruta del archivo
            
        Returns:
            dict: Metadatos completos
        """
        if not self.plex_db:
            if not self.conectar_plex():
                return {"error": "No se pudo conectar a PLEX"}
        
        try:
            # Buscar el video
            video_data = self.buscar_video_por_archivo(archivo)
            
            if not video_data:
                return {"error": "Video no encontrado en PLEX"}
            
            # Obtener metadatos completos
            movie_id = video_data.get('id')
            if movie_id:
                metadatos_completos = self.plex_db.get_movie_metadata(movie_id)
                if metadatos_completos:
                    return {
                        "encontrado": True,
                        "metadatos": metadatos_completos,
                        "archivo_original": str(archivo)
                    }
            
            return {
                "encontrado": True,
                "metadatos": video_data,
                "archivo_original": str(archivo)
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo metadatos: {e}")
            return {"error": str(e)}
    
    def comparar_con_plex(self, archivo: Path) -> Dict[str, Any]:
        """
        Compara un archivo local con su entrada en PLEX
        
        Args:
            archivo: Ruta del archivo local
            
        Returns:
            dict: Comparación entre local y PLEX
        """
        try:
            # Obtener metadatos de PLEX
            plex_data = self.obtener_metadatos_completos(archivo)
            
            if "error" in plex_data:
                return {
                    "archivo": str(archivo),
                    "plex_disponible": False,
                    "error": plex_data["error"]
                }
            
            # Obtener información del archivo local
            info_local = {
                "nombre": archivo.name,
                "tamaño_bytes": archivo.stat().st_size if archivo.exists() else 0,
                "ruta": str(archivo)
            }
            
            # Comparar
            metadatos_plex = plex_data.get("metadatos", {})
            
            return {
                "archivo": str(archivo),
                "plex_disponible": True,
                "local": info_local,
                "plex": {
                    "titulo": metadatos_plex.get("title", "N/A"),
                    "año": metadatos_plex.get("year", "N/A"),
                    "duracion": metadatos_plex.get("duration", 0),
                    "rating": metadatos_plex.get("rating", "N/A"),
                    "estudio": metadatos_plex.get("studio", "N/A"),
                    "generos": metadatos_plex.get("genres", []),
                    "archivos": metadatos_plex.get("files", [])
                },
                "coincidencias": {
                    "nombre_similar": self._comparar_nombres(archivo.name, metadatos_plex.get("title", "")),
                    "tamaño_similar": self._comparar_tamaños(info_local["tamaño_bytes"], metadatos_plex.get("files", [])),
                    "duracion_similar": self._comparar_duraciones(archivo, metadatos_plex.get("duration", 0))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error comparando con PLEX: {e}")
            return {"error": str(e)}
    
    def _comparar_nombres(self, nombre_archivo: str, titulo_plex: str) -> bool:
        """Compara si los nombres son similares"""
        if not titulo_plex:
            return False
        
        # Lógica simple de comparación
        nombre_limpio = nombre_archivo.lower().replace(".", " ").replace("_", " ")
        titulo_limpio = titulo_plex.lower()
        
        # Verificar si el título está contenido en el nombre del archivo
        return titulo_limpio in nombre_limpio or nombre_limpio in titulo_limpio
    
    def _comparar_tamaños(self, tamaño_local: int, archivos_plex: List[Dict]) -> bool:
        """Compara si los tamaños son similares"""
        if not archivos_plex or tamaño_local == 0:
            return False
        
        # Obtener el tamaño del primer archivo de PLEX
        tamaño_plex = archivos_plex[0].get("size", 0)
        if tamaño_plex == 0:
            return False
        
        # Tolerancia del 10%
        diferencia = abs(tamaño_local - tamaño_plex)
        tolerancia = max(tamaño_local, tamaño_plex) * 0.1
        
        return diferencia <= tolerancia
    
    def _comparar_duraciones(self, archivo: Path, duracion_plex: int) -> bool:
        """Compara si las duraciones son similares"""
        if duracion_plex == 0:
            return False
        
        # Aquí podrías integrar con VideoDurationManager
        # Por ahora, retornamos False
        return False
