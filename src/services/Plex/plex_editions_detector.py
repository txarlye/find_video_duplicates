#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para detectar ediciones existentes en Plex
"""
import sqlite3
import os
from typing import List, Dict, Optional
import logging

class PlexEditionsDetector:
    """Detector de ediciones existentes en Plex"""
    
    def __init__(self, database_path: str):
        """
        Inicializa el detector de ediciones
        
        Args:
            database_path: Ruta a la base de datos de Plex
        """
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        self._connection = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        try:
            # Siempre crear una nueva conexión para evitar problemas de hilos
            if self._connection:
                try:
                    self._connection.close()
                except:
                    pass
            
            # Verificar que el archivo existe
            if not os.path.exists(self.database_path):
                raise FileNotFoundError(f"Base de datos no encontrada: {self.database_path}")
            
            # Crear nueva conexión
            self._connection = sqlite3.connect(self.database_path, timeout=30.0)
            self._connection.row_factory = sqlite3.Row
            
            # Verificar que la base de datos no esté corrupta
            try:
                self._connection.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            except sqlite3.DatabaseError as e:
                self.logger.error(f"Base de datos corrupta: {e}")
                raise
            
            return self._connection
            
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")
            raise
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                # Ignorar errores de cierre en diferentes hilos
                pass
            finally:
                self._connection = None
    
    def check_existing_editions(self, title: str, year: str) -> List[Dict]:
        """
        Verifica si Plex ya tiene ediciones de esta película
        
        Args:
            title: Título de la película
            year: Año de la película
            
        Returns:
            Lista de ediciones existentes
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            sql = """
            SELECT id, title, year, edition_title, summary, originally_available_at
            FROM metadata_items 
            WHERE title = ? AND year = ?
            ORDER BY 
                CASE 
                    WHEN edition_title IS NULL THEN 0 
                    ELSE 1 
                END,
                edition_title
            """
            
            cur.execute(sql, (title, year))
            results = cur.fetchall()
            
            editions = []
            for row in results:
                edition_name = row[3] if row[3] else 'Original'
                editions.append({
                    'id': row[0],
                    'title': row[1], 
                    'year': row[2],
                    'edition': edition_name,
                    'summary': row[4],
                    'release_date': row[5]
                })
            
            return editions
            
        except Exception as e:
            self.logger.error(f"Error verificando ediciones existentes: {e}")
            return []
    
    def get_edition_info(self, metadata_item_id: int) -> Optional[Dict]:
        """
        Obtiene información detallada de una edición específica
        
        Args:
            metadata_item_id: ID del item de metadatos
            
        Returns:
            Información de la edición o None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            sql = """
            SELECT id, title, year, edition_title, summary, originally_available_at,
                   studio, content_rating, rating, duration
            FROM metadata_items 
            WHERE id = ?
            """
            
            cur.execute(sql, (metadata_item_id,))
            row = cur.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'year': row[2],
                    'edition': row[3],
                    'summary': row[4],
                    'release_date': row[5],
                    'studio': row[6],
                    'content_rating': row[7],
                    'rating': row[8],
                    'duration': row[9]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de edición: {e}")
            return None
    
    def check_if_file_has_edition(self, file_path: str) -> Optional[Dict]:
        """
        Verifica si un archivo específico ya tiene una edición asignada en Plex
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Información de la edición si existe, None si no
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                self.logger.warning(f"Archivo no encontrado: {file_path}")
                return None
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Buscar el archivo en media_parts con una consulta más robusta
            filename = os.path.basename(file_path)
            search_term = f"%{filename}%"
            
            # Consulta simplificada para evitar problemas de base de datos
            sql = """
            SELECT mp.media_item_id, mi.metadata_item_id, mdi.title, mdi.year, mdi.edition_title
            FROM media_parts mp
            LEFT JOIN media_items mi ON mp.media_item_id = mi.id
            LEFT JOIN metadata_items mdi ON mi.metadata_item_id = mdi.id
            WHERE mp.file LIKE ?
            LIMIT 1
            """
            
            cur.execute(sql, (search_term,))
            row = cur.fetchone()
            
            if row and row[4]:  # Si tiene edition_title
                return {
                    'id': row[1],
                    'title': row[2],
                    'year': row[3],
                    'edition': row[4]
                }
            
            return None
            
        except sqlite3.DatabaseError as e:
            self.logger.error(f"Error de base de datos verificando edición: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error verificando edición del archivo: {e}")
            return None
    
    def get_all_editions_for_movie(self, title: str, year: str) -> List[Dict]:
        """
        Obtiene todas las ediciones de una película específica
        
        Args:
            title: Título de la película
            year: Año de la película
            
        Returns:
            Lista de todas las ediciones
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            sql = """
            SELECT id, title, year, edition_title, summary, originally_available_at,
                   studio, content_rating, rating, duration
            FROM metadata_items 
            WHERE title = ? AND year = ?
            ORDER BY 
                CASE 
                    WHEN edition_title IS NULL THEN 0 
                    ELSE 1 
                END,
                edition_title
            """
            
            cur.execute(sql, (title, year))
            results = cur.fetchall()
            
            editions = []
            for row in results:
                editions.append({
                    'id': row[0],
                    'title': row[1],
                    'year': row[2],
                    'edition': row[3] or 'Original',
                    'summary': row[4],
                    'release_date': row[5],
                    'studio': row[6],
                    'content_rating': row[7],
                    'rating': row[8],
                    'duration': row[9]
                })
            
            return editions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo todas las ediciones: {e}")
            return []
