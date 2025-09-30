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
        """Obtiene conexión a la base de datos con manejo robusto de errores"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Intentar conexión de solo lectura primero
                conn = sqlite3.connect(f"file:{self.database_path}?mode=ro", uri=True)
                
                # Verificar que la conexión funciona
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                return conn
                
            except sqlite3.OperationalError as e:
                if "disk I/O error" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)  # Esperar antes de reintentar
                    continue
                else:
                    # Fallback a conexión normal
                    try:
                        conn = sqlite3.connect(self.database_path)
                        return conn
                    except Exception:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(0.5)
                        continue
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                import time
                time.sleep(0.5)
                continue
        
        raise Exception("No se pudo establecer conexión con la base de datos después de múltiples intentos")
    
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
            
        except sqlite3.OperationalError as e:
            if "disk I/O error" in str(e):
                self.logger.warning(f"Error de I/O en base de datos de Plex: {e}")
                # No mostrar error en la interfaz, solo en logs
                return None
            else:
                self.logger.error(f"Error de base de datos: {e}")
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
