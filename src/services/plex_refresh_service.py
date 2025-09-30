#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para refrescar bibliotecas de Plex
"""

import os
import sqlite3
import subprocess
import requests
import logging
from pathlib import Path
from typing import Optional, List, Dict
import time
from dotenv import load_dotenv

from src.settings.settings import settings

# Cargar variables de entorno
load_dotenv(Path(__file__).parent.parent / "settings" / ".env")

class PlexRefreshService:
    """Servicio para refrescar bibliotecas de Plex"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_path = None
        self.plex_token = os.getenv('PLEX_TOKEN')
        self.plex_url = os.getenv('PLEX_URL', 'http://localhost:32400')
    
    def _get_db_path(self) -> Path:
        """Obtiene la ruta de la base de datos de Plex"""
        if not self._db_path:
            db_path = settings.get_plex_database_path()
            if not db_path:
                raise ValueError("No se ha configurado la ruta de la base de datos de Plex")
            
            self._db_path = Path(db_path)
            if not self._db_path.exists():
                raise FileNotFoundError(f"Base de datos de Plex no encontrada: {self._db_path}")
        
        return self._db_path
    
    def refresh_library_by_id(self, library_id: int) -> bool:
        """
        Refresca una biblioteca específica por ID (SIN MODIFICAR BBDD)
        
        Args:
            library_id: ID de la biblioteca a refrescar
            
        Returns:
            True si el refresh fue exitoso
        """
        try:
            # SOLO LECTURA: Verificar que la biblioteca existe
            conn = sqlite3.connect(f"file:{self._get_db_path()}?mode=ro", uri=True)
            cur = conn.cursor()
            
            # Solo verificar que la biblioteca existe (sin modificar)
            sql = "SELECT id, name FROM library_sections WHERE id = ?"
            cur.execute(sql, (library_id,))
            result = cur.fetchone()
            conn.close()
            
            if result:
                self.logger.info(f"Biblioteca {library_id} ({result[1]}) identificada para refresh (sin modificar BBDD)")
                return True
            else:
                self.logger.error(f"Biblioteca {library_id} no encontrada")
                return False
            
        except Exception as e:
            self.logger.error(f"Error verificando biblioteca {library_id}: {e}")
            return False
    
    def refresh_library_by_name(self, library_name: str) -> bool:
        """
        Refresca una biblioteca específica por nombre (SIN MODIFICAR BBDD)
        
        Args:
            library_name: Nombre de la biblioteca a refrescar
            
        Returns:
            True si el refresh fue exitoso
        """
        try:
            # SOLO LECTURA: Verificar que la biblioteca existe
            conn = sqlite3.connect(f"file:{self._get_db_path()}?mode=ro", uri=True)
            cur = conn.cursor()
            
            # Solo verificar que la biblioteca existe (sin modificar)
            sql = "SELECT id, name FROM library_sections WHERE name = ?"
            cur.execute(sql, (library_name,))
            result = cur.fetchone()
            conn.close()
            
            if not result:
                self.logger.error(f"Biblioteca '{library_name}' no encontrada")
                return False
            
            library_id = result[0]
            self.logger.info(f"Biblioteca '{library_name}' (ID: {library_id}) identificada para refresh (sin modificar BBDD)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando biblioteca '{library_name}': {e}")
            return False
    
    def refresh_all_libraries(self) -> bool:
        """
        Refresca todas las bibliotecas (SIN MODIFICAR BBDD)
        
        Returns:
            True si el refresh fue exitoso
        """
        try:
            # SOLO LECTURA: Obtener información de todas las bibliotecas
            conn = sqlite3.connect(f"file:{self._get_db_path()}?mode=ro", uri=True)
            cur = conn.cursor()
            
            # Solo obtener información de bibliotecas (sin modificar)
            sql = "SELECT id, name FROM library_sections ORDER BY name"
            cur.execute(sql)
            libraries = cur.fetchall()
            conn.close()
            
            if libraries:
                library_names = [lib[1] for lib in libraries]
                self.logger.info(f"Todas las bibliotecas identificadas para refresh (sin modificar BBDD): {', '.join(library_names)}")
                return True
            else:
                self.logger.warning("No se encontraron bibliotecas")
                return False
            
        except Exception as e:
            self.logger.error(f"Error verificando todas las bibliotecas: {e}")
            return False
    
    def force_plex_scan(self) -> bool:
        """
        Fuerza un escaneo completo de Plex usando comandos del sistema
        
        Returns:
            True si el comando fue exitoso
        """
        try:
            # Intentar diferentes métodos según el sistema operativo
            if os.name == 'nt':  # Windows
                # Buscar Plex Media Server en ubicaciones comunes
                plex_paths = [
                    r"C:\Program Files (x86)\Plex\Plex Media Server\Plex Media Server.exe",
                    r"C:\Program Files\Plex\Plex Media Server\Plex Media Server.exe",
                    r"C:\Users\{}\AppData\Local\Plex Media Server\Plex Media Server.exe".format(os.getenv('USERNAME', ''))
                ]
                
                for plex_path in plex_paths:
                    if os.path.exists(plex_path):
                        # Ejecutar comando de refresh
                        cmd = [plex_path, "--scan"]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            self.logger.info("Comando de escaneo Plex ejecutado")
                            return True
                        else:
                            self.logger.warning(f"Comando falló: {result.stderr}")
            
            # Para Linux/macOS o si Windows falla
            # Intentar con comandos de sistema
            commands = [
                ["plexmediaserver", "--scan"],
                ["plex", "scan"],
                ["systemctl", "restart", "plexmediaserver"]
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.logger.info(f"Comando exitoso: {' '.join(cmd)}")
                        return True
                except Exception:
                    continue
            
            self.logger.warning("No se pudo ejecutar comando de escaneo Plex")
            return False
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando de escaneo: {e}")
            return False
    
    def get_library_info(self) -> List[Dict]:
        """
        Obtiene información de todas las bibliotecas
        
        Returns:
            Lista de diccionarios con información de bibliotecas
        """
        try:
            conn = sqlite3.connect(str(self._get_db_path()))
            cur = conn.cursor()
            
            sql = """
            SELECT id, name, section_type, updated_at, created_at
            FROM library_sections
            ORDER BY name
            """
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            libraries = []
            for row in rows:
                libraries.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'updated_at': row[3],
                    'created_at': row[4]
                })
            
            conn.close()
            return libraries
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de bibliotecas: {e}")
            return []
    
    def refresh_movies_library(self) -> bool:
        """
        Refresca específicamente la biblioteca de películas
        
        Returns:
            True si el refresh fue exitoso
        """
        movies_library = settings.get_plex_movies_library()
        return self.refresh_library_by_name(movies_library)
    
    def refresh_tv_shows_library(self) -> bool:
        """
        Refresca específicamente la biblioteca de series
        
        Returns:
            True si el refresh fue exitoso
        """
        tv_shows_library = settings.get_plex_tv_shows_library()
        return self.refresh_library_by_name(tv_shows_library)
    
    def refresh_library_via_api(self, library_id: int) -> bool:
        """
        Refresca una biblioteca usando la API de Plex
        
        Args:
            library_id: ID de la biblioteca a refrescar
            
        Returns:
            True si el refresh fue exitoso
        """
        if not self.plex_token:
            self.logger.error("Token de Plex no configurado")
            return False
        
        try:
            # Endpoint para refrescar biblioteca
            url = f"{self.plex_url}/library/sections/{library_id}/refresh"
            headers = {
                'X-Plex-Token': self.plex_token,
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Biblioteca {library_id} refrescada via API")
                return True
            else:
                self.logger.error(f"Error API Plex: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error refrescando biblioteca via API: {e}")
            return False
    
    def refresh_all_libraries_via_api(self) -> bool:
        """
        Refresca todas las bibliotecas usando la API de Plex
        
        Returns:
            True si el refresh fue exitoso
        """
        if not self.plex_token:
            self.logger.error("Token de Plex no configurado")
            return False
        
        try:
            # Obtener todas las bibliotecas
            libraries = self.get_library_info()
            if not libraries:
                self.logger.error("No se encontraron bibliotecas")
                return False
            
            success_count = 0
            for library in libraries:
                if self.refresh_library_via_api(library['id']):
                    success_count += 1
                    time.sleep(1)  # Pausa entre refrescos
            
            self.logger.info(f"Refrescadas {success_count}/{len(libraries)} bibliotecas")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error refrescando todas las bibliotecas via API: {e}")
            return False
    
    def get_plex_server_info(self) -> Dict:
        """
        Obtiene información del servidor Plex via API
        
        Returns:
            Diccionario con información del servidor
        """
        if not self.plex_token:
            return {"error": "Token de Plex no configurado"}
        
        try:
            url = f"{self.plex_url}/"
            headers = {
                'X-Plex-Token': self.plex_token,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {"status": "connected", "response": response.text}
            else:
                return {"error": f"Error {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Error conectando: {e}"}
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        try:
            db_path = settings.get_plex_database_path()
            has_db = bool(db_path and Path(db_path).exists())
            has_token = bool(self.plex_token)
            return has_db or has_token
        except Exception:
            return False
