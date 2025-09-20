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
        if env_path.exists():
            load_dotenv(env_path)
        
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


# Instancia global del singleton
settings = Settings()
