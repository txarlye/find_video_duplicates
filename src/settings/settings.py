#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada de la aplicación
Implementa patrón Singleton para acceso global
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Settings:
    """
    Clase Singleton para manejo centralizado de configuración
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_config()
            Settings._initialized = True

    def _load_config(self):
        """Carga la configuración desde archivos"""
        # Cargar variables de entorno
        env_path = Path(__file__).parent / ".env"
        print(f"DEBUG: Buscando archivo .env en: {env_path}")
        print(f"DEBUG: Archivo existe: {env_path.exists()}")
        
        if env_path.exists():
            # Intentar cargar con diferentes opciones
            try:
                load_dotenv(env_path, override=True)
            except Exception as e:
                print(f"DEBUG: Error cargando .env: {e}")
        else:
            # Intentar cargar desde la raíz del proyecto
            root_env = Path(__file__).parent.parent.parent / ".env"
            if root_env.exists():
                load_dotenv(root_env, override=True)
        
        # Cargar configuración de PLEX desde archivo alternativo
        plex_config_path = Path(__file__).parent / "plex_config.txt"
        if plex_config_path.exists():
            try:
                load_dotenv(plex_config_path, override=True)
            except Exception as e:
                print(f"DEBUG: Error cargando plex_config.txt: {e}")
        
        # Cargar configuración JSON
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self._create_default_config()
            self._save_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Crea configuración por defecto"""
        return {
            "app": {
                "name": "Detector de Películas Duplicadas",
                "version": "1.0.0",
                "debug": False
            },
            "paths": {
                "last_scan_path": "",
                "last_output_path": "",
                "default_scan_path": ""
            },
            "detection": {
                "similarity_threshold": 0.8,
                "supported_extensions": [
                    ".mp4", ".avi", ".mkv", ".mov", ".wmv", 
                    ".flv", ".m4v", ".mpg", ".mpeg", ".3gp", ".webm"
                ]
            },
            "imdb": {
                "api_key": "",
                "base_url": "https://imdb-api.com",
                "language": "es"
            },
            "telegram": {
                "bot_token": "",
                "channel_id": "",
                "max_file_size": 2000000000,  # 2GB en bytes
                "upload_delay": 1  # Delay entre subidas en segundos
            },
            "ui": {
                "theme": "light",
                "page_size": 20,
                "show_advanced_options": False
            }
        }

    def _save_config(self):
        """Guarda la configuración actual"""
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de puntos
        
        Args:
            key: Clave en formato 'seccion.subseccion'
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración usando notación de puntos
        
        Args:
            key: Clave en formato 'seccion.subseccion'
            value: Valor a establecer
        """
        keys = key.split('.')
        config = self.config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Establecer el valor final
        config[keys[-1]] = value
        self._save_config()

    def get_env(self, key: str, default: str = "") -> str:
        """
        Obtiene una variable de entorno
        
        Args:
            key: Nombre de la variable de entorno
            default: Valor por defecto
            
        Returns:
            Valor de la variable de entorno
        """
        return os.getenv(key, default)

    def update_last_scan_path(self, path: str):
        """Actualiza la última ruta escaneada"""
        self.set("paths.last_scan_path", path)

    def update_last_output_path(self, path: str):
        """Actualiza la última ruta de salida"""
        self.set("paths.last_output_path", path)

    def get_last_scan_path(self) -> str:
        """Obtiene la última ruta escaneada"""
        return self.get("paths.last_scan_path", "")

    def get_last_output_path(self) -> str:
        """Obtiene la última ruta de salida"""
        return self.get("paths.last_output_path", "")

    def get_imdb_api_key(self) -> str:
        """Obtiene la API key de IMDB"""
        return self.get_env("IMDB_API_KEY") or self.get("imdb.api_key", "")

    def get_telegram_bot_token(self) -> str:
        """Obtiene el token del bot de Telegram"""
        return self.get_env("TELEGRAM_BOT_TOKEN") or self.get("telegram.bot_token", "")

    def get_telegram_channel_id(self) -> str:
        """Obtiene el ID del canal de Telegram"""
        return self.get_env("TELEGRAM_CHANNEL_ID") or self.get("telegram.channel_id", "")
    
    def get_telegram_max_file_size(self) -> int:
        """Obtiene el tamaño máximo de archivo para Telegram"""
        return self.get("telegram.max_file_size", 2000000000)  # 2GB por defecto
    
    def get_telegram_upload_delay(self) -> int:
        """Obtiene el delay entre subidas de Telegram"""
        return self.get("telegram.upload_delay", 1)
    
    def set_telegram_bot_token(self, value: str):
        """Establece el token del bot de Telegram"""
        self.set("telegram.bot_token", value)
    
    def set_telegram_channel_id(self, value: str):
        """Establece el ID del canal de Telegram"""
        self.set("telegram.channel_id", value)

    def is_debug_mode(self) -> bool:
        """Verifica si está en modo debug"""
        return self.get("app.debug", False)

    def get_supported_extensions(self) -> list:
        """Obtiene las extensiones de video soportadas"""
        return self.get("detection.supported_extensions", [])

    def get_similarity_threshold(self) -> float:
        """Obtiene el umbral de similitud"""
        return self.get("detection.similarity_threshold", 0.8)
    
    def get_duration_filter_enabled(self) -> bool:
        """Obtiene si el filtro por duración está activado"""
        return self.get("detection.duration_filter_enabled", True)
    
    def set_duration_filter_enabled(self, value: bool):
        """Establece si el filtro por duración está activado"""
        self.set("detection.duration_filter_enabled", value)
    
    def get_duration_tolerance_minutes(self) -> int:
        """Obtiene la tolerancia de duración en minutos"""
        return self.get("detection.duration_tolerance_minutes", 5)
    
    def set_duration_tolerance_minutes(self, value: int):
        """Establece la tolerancia de duración en minutos"""
        self.set("detection.duration_tolerance_minutes", value)
    
    def get_show_video_players(self) -> bool:
        """Obtiene si mostrar reproductores de video"""
        return self.get("ui.show_video_players", True)
    
    def set_show_video_players(self, value: bool):
        """Establece si mostrar reproductores de video"""
        self.set("ui.show_video_players", value)
    
    def get_video_player_size(self) -> str:
        """Obtiene el tamaño de los reproductores de video"""
        return self.get("ui.video_player_size", "medium")
    
    def set_video_player_size(self, value: str):
        """Establece el tamaño de los reproductores de video"""
        self.set("ui.video_player_size", value)
    
    def get_show_embedded_players(self) -> bool:
        """Obtiene si mostrar reproductores embebidos"""
        return self.get("ui.show_embedded_players", False)
    
    def set_show_embedded_players(self, value: bool):
        """Establece si mostrar reproductores embebidos"""
        self.set("ui.show_embedded_players", value)
    
    def get_video_start_time_seconds(self) -> int:
        """Obtiene el tiempo de inicio en segundos para los reproductores embebidos"""
        return self.get("ui.video_start_time_seconds", 900)  # 15 minutos por defecto
    
    def set_video_start_time_seconds(self, value: int):
        """Establece el tiempo de inicio en segundos para los reproductores embebidos"""
        self.set("ui.video_start_time_seconds", value)
    
    def get_debug_enabled(self) -> bool:
        """Obtiene si el modo debug está activado"""
        return self.get("debug.enabled", True)
    
    def set_debug_enabled(self, value: bool):
        """Establece si el modo debug está activado"""
        self.set("debug.enabled", value)
    
    def get_debug_folder(self) -> str:
        """Obtiene la carpeta de debug"""
        return self.get("debug.debug_folder", "\\\\DiskStation\\data\\media\\movies\\00-borrar\\debug")
    
    def set_debug_folder(self, value: str):
        """Establece la carpeta de debug"""
        self.set("debug.debug_folder", value)
    
    def get_last_scan_path(self) -> str:
        """Obtiene la última ruta de escaneo"""
        return self.get("paths.last_scan_path", "")
    
    def set_last_scan_path(self, value: str):
        """Establece la última ruta de escaneo"""
        self.set("paths.last_scan_path", value)
    
    # Métodos de IMDB
    def get_imdb_api_key(self) -> str:
        """Obtiene la API key de IMDB"""
        return os.getenv("IMDB_API_KEY", self.get("imdb.api_key", ""))
    
    def get_imdb_base_url(self) -> str:
        """Obtiene la URL base de IMDB"""
        return self.get("imdb.base_url", "https://imdb-api.com")
    
    def get_imdb_language(self) -> str:
        """Obtiene el idioma para IMDB"""
        return self.get("imdb.language", "es")
    
    def get_imdb_enabled(self) -> bool:
        """Obtiene si IMDB está habilitado"""
        return self.get("imdb.enabled", False)
    
    def set_imdb_enabled(self, value: bool):
        """Establece si IMDB está habilitado"""
        self.set("imdb.enabled", value)
    
    def get_imdb_include_poster(self) -> bool:
        """Obtiene si incluir póster de IMDB"""
        return self.get("imdb.include_poster", True)
    
    def set_imdb_include_poster(self, value: bool):
        """Establece si incluir póster de IMDB"""
        self.set("imdb.include_poster", value)
    
    def get_imdb_include_synopsis(self) -> bool:
        """Obtiene si incluir sinopsis de IMDB"""
        return self.get("imdb.include_synopsis", True)
    
    def set_imdb_include_synopsis(self, value: bool):
        """Establece si incluir sinopsis de IMDB"""
        self.set("imdb.include_synopsis", value)
    
    # Métodos de PLEX
    def get_plex_enabled(self) -> bool:
        """Obtiene si PLEX está habilitado"""
        return self.get("plex.enabled", False)
    
    def set_plex_enabled(self, value: bool):
        """Establece si PLEX está habilitado"""
        self.set("plex.enabled", value)
    
    def get_plex_use_detection(self) -> bool:
        """Obtiene si usar detección de PLEX"""
        return self.get("plex.use_plex_detection", False)
    
    def set_plex_use_detection(self, value: bool):
        """Establece si usar detección de PLEX"""
        self.set("plex.use_plex_detection", value)
    
    def get_plex_use_metadata(self) -> bool:
        """Obtiene si usar metadatos de PLEX"""
        return self.get("plex.use_plex_metadata", True)
    
    def set_plex_use_metadata(self, value: bool):
        """Establece si usar metadatos de PLEX"""
        self.set("plex.use_plex_metadata", value)
    
    def get_plex_auto_connect(self) -> bool:
        """Obtiene si conectar automáticamente a PLEX"""
        return self.get("plex.auto_connect", True)
    
    def set_plex_auto_connect(self, value: bool):
        """Establece si conectar automáticamente a PLEX"""
        self.set("plex.auto_connect", value)
    
    def get_plex_prefer_titles(self) -> bool:
        """Obtiene si preferir títulos de PLEX"""
        return self.get("plex.prefer_plex_titles", True)
    
    def set_plex_prefer_titles(self, value: bool):
        """Establece si preferir títulos de PLEX"""
        self.set("plex.prefer_plex_titles", value)
    
    def get_plex_prefer_years(self) -> bool:
        """Obtiene si preferir años de PLEX"""
        return self.get("plex.prefer_plex_years", True)
    
    def set_plex_prefer_years(self, value: bool):
        """Establece si preferir años de PLEX"""
        self.set("plex.prefer_plex_years", value)
    
    def get_plex_prefer_duration(self) -> bool:
        """Obtiene si preferir duración de PLEX"""
        return self.get("plex.prefer_plex_duration", True)
    
    def set_plex_prefer_duration(self, value: bool):
        """Establece si preferir duración de PLEX"""
        self.set("plex.prefer_plex_duration", value)
    
    def get_plex_user(self) -> str:
        """Obtiene el usuario de PLEX"""
        return os.getenv("PLEX_USER", "")
    
    def get_plex_pass(self) -> str:
        """Obtiene la contraseña de PLEX"""
        return os.getenv("PLEX_PASS", "")
    
    def get_plex_token(self) -> str:
        """Obtiene el token de PLEX"""
        return os.getenv("PLEX_TOKEN", "")
    
    def get_plex_server_ip(self) -> str:
        """Obtiene la IP del servidor PLEX"""
        return os.getenv("IP_NAS", "localhost")
    
    def get_plex_database_path(self) -> str:
        """Obtiene la ruta de la base de datos de PLEX"""
        return self.get("plex.database_path", "")
    
    def get_plex_server_url(self) -> str:
        """Obtiene la URL del servidor PLEX"""
        return self.get("plex.server_url", "http://localhost:32400")
    
    def set_plex_server_url(self, value: str):
        """Establece la URL del servidor PLEX"""
        self.set("plex.server_url", value)
    
    def get_plex_server_name(self) -> str:
        """Obtiene el nombre del servidor PLEX"""
        return self.get("plex.server_name", "Plex Media Server")
    
    def set_plex_server_name(self, value: str):
        """Establece el nombre del servidor PLEX"""
        self.set("plex.server_name", value)
    
    def get_plex_timeout(self) -> int:
        """Obtiene el timeout de conexión a PLEX"""
        return self.get("plex.timeout", 30)
    
    def set_plex_timeout(self, value: int):
        """Establece el timeout de conexión a PLEX"""
        self.set("plex.timeout", value)
    
    def get_plex_config_token(self) -> str:
        """Obtiene el token de PLEX desde configuración"""
        return self.get("plex.token", "")
    
    def set_plex_config_token(self, value: str):
        """Establece el token de PLEX en configuración"""
        self.set("plex.token", value)
    
    def get_plex_library_name(self) -> str:
        """Obtiene el nombre de la biblioteca de PLEX"""
        return self.get("plex.library_name", "Películas")
    
    def set_plex_library_name(self, value: str):
        """Establece el nombre de la biblioteca de PLEX"""
        self.set("plex.library_name", value)
    
    def get_plex_library_id(self) -> Optional[int]:
        """Obtiene el ID de la biblioteca de PLEX"""
        return self.get("plex.library_id", None)
    
    def set_plex_library_id(self, value: int):
        """Establece el ID de la biblioteca de PLEX"""
        self.set("plex.library_id", value)


# Instancia global del singleton
settings = Settings()
