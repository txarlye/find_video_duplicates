"""
Módulo para extraer títulos reales de Plex
Separado para no romper funcionalidades existentes
"""

import sqlite3
from typing import Optional, Dict
from pathlib import Path
import logging

class PlexTitleExtractor:
    """Extractor de títulos reales de Plex"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
    
    def _get_connection(self):
        """Obtiene conexión a la base de datos"""
        return sqlite3.connect(self.database_path)
    
    def get_real_title_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Obtiene el título real de Plex por nombre de archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Dict con título real y año, o None si no se encuentra
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Consulta simplificada para obtener título real de Plex
            # Primero buscar en media_parts
            sql1 = "SELECT media_item_id FROM media_parts WHERE file LIKE ? LIMIT 1"
            search_term = f"%{filename}%"
            cur.execute(sql1, (search_term,))
            row1 = cur.fetchone()
            
            if not row1:
                return None
            
            # Luego buscar en media_items
            sql2 = "SELECT metadata_item_id FROM media_items WHERE id = ?"
            cur.execute(sql2, (row1[0],))
            row2 = cur.fetchone()
            
            if not row2:
                return None
            
            # Finalmente buscar en metadata_items
            sql3 = "SELECT title, year FROM metadata_items WHERE id = ?"
            cur.execute(sql3, (row2[0],))
            row3 = cur.fetchone()
            
            if row3 and row3[0]:  # Si encontramos título
                return {
                    'title': row3[0],  # Título real de Plex
                    'year': row3[1] or 'N/A'  # Año real de Plex
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo título real de Plex: {e}")
            return None
        finally:
            if 'conn' in locals():
                try:
                    conn.close()
                except Exception:
                    # Ignorar errores de cierre en diferentes hilos
                    pass
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            if not Path(self.database_path).exists():
                return False
            
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False
