# -*- coding: utf-8 -*-
"""
Autenticador para PLEX Media Server
"""

import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PlexAuthenticator:
    """Maneja la autenticación con PLEX Media Server"""
    
    def __init__(self):
        self.base_url = "https://plex.tv"
        self.api_url = "https://plex.tv/api/v2"
        self.token = None
        self.server_info = None
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Autentica con PLEX usando usuario y contraseña
        
        Args:
            username: Usuario de PLEX
            password: Contraseña de PLEX
            
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Método 1: Intentar autenticación con usuario/contraseña (método legacy)
            auth_url = f"{self.base_url}/api/v2/users/signin"
            
            auth_data = {
                "login": username,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Plex-Client-Identifier": "movie-duplicate-detector",
                "X-Plex-Product": "Movie Duplicate Detector",
                "X-Plex-Version": "1.0.0"
            }
            
            response = requests.post(auth_url, json=auth_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                auth_result = response.json()
                self.token = auth_result.get('authToken')
                
                if self.token:
                    logger.info("✅ Autenticación con PLEX exitosa (método legacy)")
                    return True
                else:
                    logger.error("❌ No se pudo obtener token de PLEX")
                    return False
            elif response.status_code == 201:
                # Error 201: Credenciales incorrectas o método no soportado
                logger.warning("⚠️ Método de autenticación con usuario/contraseña no soportado")
                logger.info("💡 PLEX requiere token de acceso. Ve a PLEX → Configuración → Red → Acceso remoto para obtener tu token")
                return False
            else:
                logger.error(f"❌ Error de autenticación PLEX: {response.status_code}")
                logger.info(f"💡 Respuesta del servidor: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en autenticación PLEX: {e}")
            return False
    
    def get_servers(self) -> Optional[list]:
        """
        Obtiene la lista de servidores PLEX del usuario
        
        Returns:
            list: Lista de servidores disponibles
        """
        if not self.token:
            logger.error("❌ No hay token de autenticación")
            return None
        
        try:
            servers_url = f"{self.api_url}/resources"
            headers = {
                "X-Plex-Token": self.token,
                "Accept": "application/json"
            }
            
            response = requests.get(servers_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                servers = []
                
                for resource in data.get('MediaContainer', {}).get('Device', []):
                    if resource.get('provides') == 'server':
                        server_info = {
                            'name': resource.get('name', 'Unknown'),
                            'address': resource.get('connections', [{}])[0].get('uri', ''),
                            'port': resource.get('connections', [{}])[0].get('port', 32400),
                            'id': resource.get('clientIdentifier', ''),
                            'version': resource.get('productVersion', 'Unknown')
                        }
                        servers.append(server_info)
                
                logger.info(f"✅ Encontrados {len(servers)} servidores PLEX")
                return servers
            elif response.status_code == 400:
                logger.error("❌ Error 400: Token de PLEX inválido o expirado")
                logger.info("💡 Verifica que tu token de PLEX sea correcto y no haya expirado")
                logger.info(f"💡 Respuesta del servidor: {response.text[:200]}")
                return None
            elif response.status_code == 401:
                logger.error("❌ Error 401: Token de PLEX no autorizado")
                logger.info("💡 El token no tiene permisos para acceder a los servidores")
                return None
            else:
                logger.error(f"❌ Error obteniendo servidores: {response.status_code}")
                logger.info(f"💡 Respuesta del servidor: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo servidores PLEX: {e}")
            return None
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del servidor PLEX
        
        Returns:
            dict: Información del servidor
        """
        return self.server_info
    
    def is_authenticated(self) -> bool:
        """
        Verifica si está autenticado
        
        Returns:
            bool: True si está autenticado
        """
        return self.token is not None
    
    def get_token(self) -> Optional[str]:
        """
        Obtiene el token de autenticación
        
        Returns:
            str: Token de autenticación
        """
        return self.token
