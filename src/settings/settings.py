#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada de la aplicación
Implementa patrón Singleton para acceso global
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
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
        # Cargar variables de entorno desde la raíz del proyecto
        env_path = Path(__file__).parent.parent.parent / ".env"
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
                "max_file_size": 5000000000,  # 2GB en bytes
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

    def get_omdb_api_key(self) -> str:
        """Obtiene la API key de OMDb"""
        return self.get_env("OMDB_API_KEY") or self.get("omdb.api_key", "")

    def get_tmdb_api_key(self) -> str:
        """Obtiene la API key de TMDB"""
        return self.get_env("TMDB_API_KEY") or self.get("tmdb.api_key", "")

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
        return self.get("paths.debug_folder", "")
    
    def set_debug_folder(self, value: str):
        """Establece la carpeta de debug"""
        self.set("paths.debug_folder", value)
    
    def get_plex_database_path(self) -> str:
        """Obtiene la ruta de la base de datos de Plex"""
        return self.get("plex.database_path", "")
    
    def set_plex_database_path(self, value: str):
        """Establece la ruta de la base de datos de Plex"""
        self.set("plex.database_path", value)
    
    def get_movies_folder(self) -> str:
        """Obtiene la carpeta de películas"""
        return self.get("paths.movies_folder", "")
    
    def set_movies_folder(self, value: str):
        """Establece la carpeta de películas"""
        self.set("paths.movies_folder", value)
    
    def get_selected_movies_folder(self) -> str:
        """Obtiene la carpeta de películas seleccionadas"""
        return self.get("paths.selected_movies_folder", "")
    
    def set_selected_movies_folder(self, value: str):
        """Establece la carpeta de películas seleccionadas"""
        self.set("paths.selected_movies_folder", value)
    
    def get_last_scan_path(self) -> str:
        """Obtiene la última ruta de escaneo"""
        return self.get("paths.last_scan_path", "")
    
    def set_last_scan_path(self, value: str):
        """Establece la última ruta de escaneo"""
        self.set("paths.last_scan_path", value)
    
    # Métodos para configuración de Plex (ya definidos arriba)
    
    def get_plex_movies_library(self) -> str:
        """Obtiene el nombre de la biblioteca de películas en Plex"""
        return self.get("plex.libraries.movies", "Películas")
    
    def set_plex_movies_library(self, value: str):
        """Establece el nombre de la biblioteca de películas en Plex"""
        self.set("plex.libraries.movies", value)
    
    def get_plex_tv_shows_library(self) -> str:
        """Obtiene el nombre de la biblioteca de series en Plex"""
        return self.get("plex.libraries.tv_shows", "Series")
    
    def set_plex_tv_shows_library(self, value: str):
        """Establece el nombre de la biblioteca de series en Plex"""
        self.set("plex.libraries.tv_shows", value)
    
    def get_plex_fetch_metadata(self) -> bool:
        """Obtiene si se deben traer metadatos de Plex"""
        return self.get("plex.fetch_metadata", True)
    
    def set_plex_fetch_metadata(self, value: bool):
        """Establece si se deben traer metadatos de Plex"""
        self.set("plex.fetch_metadata", value)
    
    def get_plex_duration_filter_enabled(self) -> bool:
        """Obtiene si el filtro por duración de Plex está activado"""
        return self.get("plex.duration_filter_enabled", True)
    
    def set_plex_duration_filter_enabled(self, value: bool):
        """Establece si el filtro por duración de Plex está activado"""
        self.set("plex.duration_filter_enabled", value)
    
    def get_plex_duration_tolerance_minutes(self) -> int:
        """Obtiene la tolerancia de duración en minutos para Plex"""
        return self.get("plex.duration_tolerance_minutes", 5)
    
    def set_plex_duration_tolerance_minutes(self, value: int):
        """Establece la tolerancia de duración en minutos para Plex"""
        self.set("plex.duration_tolerance_minutes", value)
    
    # Métodos para manejo temporal de pares de duplicados
    def get_total_pairs(self) -> int:
        """Obtiene el total de pares de duplicados actual"""
        return self.get("runtime.total_pairs", 0)
    
    def set_total_pairs(self, value: int):
        """Establece el total de pares de duplicados"""
        self.set("runtime.total_pairs", value)
    
    def get_pairs_deleted(self) -> int:
        """Obtiene el número de pares eliminados"""
        return self.get("runtime.pairs_deleted", 0)
    
    def set_pairs_deleted(self, value: int):
        """Establece el número de pares eliminados"""
        self.set("runtime.pairs_deleted", value)
    
    def increment_pairs_deleted(self):
        """Incrementa el contador de pares eliminados"""
        current = self.get_pairs_deleted()
        self.set_pairs_deleted(current + 1)
    
    def get_pairs_remaining(self) -> int:
        """Obtiene el número de pares restantes"""
        return self.get_total_pairs() - self.get_pairs_deleted()
    
    def reset_pairs_counters(self):
        """Resetea los contadores de pares"""
        self.set_total_pairs(0)
        self.set_pairs_deleted(0)
    
    # Métodos para configuración de hash
    def get_hash_calculation_enabled(self) -> bool:
        """Obtiene si el cálculo de hash está habilitado"""
        return self.get("plex.hash_calculation_enabled", False)
    
    def set_hash_calculation_enabled(self, value: bool):
        """Establece si el cálculo de hash está habilitado"""
        self.set("plex.hash_calculation_enabled", value)
    
    def get_hash_calculation_warning(self) -> str:
        """Obtiene el mensaje de advertencia para el cálculo de hash"""
        return self.get("plex.hash_calculation_warning", "⚠️ El cálculo de hash puede tardar 5+ minutos para archivos grandes")
    
    # Métodos para directorios excluidos
    def get_excluded_directories(self) -> List[str]:
        """Obtiene la lista de directorios excluidos del escaneo"""
        return self.get("detection.excluded_directories", ["debug", "00-borrar", "temp", "temporary", "backup", "backups"])
    
    def set_excluded_directories(self, value: List[str]):
        """Establece la lista de directorios excluidos del escaneo"""
        self.set("detection.excluded_directories", value)
    
    def add_excluded_directory(self, directory: str):
        """Agrega un directorio a la lista de excluidos"""
        excluded = self.get_excluded_directories()
        if directory not in excluded:
            excluded.append(directory)
            self.set_excluded_directories(excluded)
    
    def remove_excluded_directory(self, directory: str):
        """Remueve un directorio de la lista de excluidos"""
        excluded = self.get_excluded_directories()
        if directory in excluded:
            excluded.remove(directory)
            self.set_excluded_directories(excluded)


# Instancia global del singleton
settings = Settings()
