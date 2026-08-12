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

        # Ruta de config.json: por defecto junto a este archivo (uso local
        # normal). En Docker se sobreescribe con CONFIG_PATH apuntando a un
        # volumen persistente (ver docker-compose-synology.yml) — así la
        # imagen nunca lleva datos personales horneados dentro y los
        # cambios hechos desde la UI sobreviven a recrear el contenedor.
        config_path_env = os.environ.get("CONFIG_PATH")
        self._config_path = Path(config_path_env) if config_path_env else Path(__file__).parent / "config.json"

        if self._config_path.exists():
            with open(self._config_path, 'r', encoding='utf-8') as f:
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
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, 'w', encoding='utf-8') as f:
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

    def get_smtp_host(self) -> str:
        """Servidor SMTP para el email de propuestas (por defecto Gmail)"""
        return self.get_env("SMTP_HOST", "smtp.gmail.com")

    def get_smtp_port(self) -> int:
        """Puerto SMTP (por defecto 587, STARTTLS)"""
        try:
            return int(self.get_env("SMTP_PORT", "587"))
        except ValueError:
            return 587

    def get_smtp_user(self) -> str:
        """Cuenta que envía el email de propuestas — solo desde .env, nunca en config.json"""
        return self.get_env("SMTP_USER")

    def get_smtp_password(self) -> str:
        """Contraseña de aplicación de la cuenta SMTP — solo desde .env"""
        return self.get_env("SMTP_PASSWORD")

    def get_telegram_bot_token(self) -> str:
        """Obtiene el token del bot de Telegram"""
        return self.get_env("TELEGRAM_BOT_TOKEN") or self.get("telegram.bot_token", "")

    def get_telegram_channel_id(self) -> str:
        """Obtiene el ID del canal de Telegram"""
        return self.get_env("TELEGRAM_CHANNEL_ID") or self.get("telegram.channel_id", "")

    def get_telegram_api_id(self) -> str:
        """Obtiene el API ID de Telethon (my.telegram.org), para subir archivos grandes"""
        return self.get_env("TELEGRAM_API_ID")

    def get_telegram_api_hash(self) -> str:
        """Obtiene el API Hash de Telethon (my.telegram.org)"""
        return self.get_env("TELEGRAM_API_HASH")

    def get_telegram_phone(self) -> str:
        """Obtiene el teléfono de la cuenta de Telegram usada por Telethon"""
        return self.get_env("TELEGRAM_PHONE")

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
        return self.get("ui.video_start_time_seconds", 360)  # 6 minutos por defecto (pasados los títulos de crédito)
    
    def set_video_start_time_seconds(self, value: int):
        """Establece el tiempo de inicio en segundos para los reproductores embebidos"""
        self.set("ui.video_start_time_seconds", value)
    
    def get_debug_enabled(self) -> bool:
        """
        Si el modo debug (mover a la papelera en vez de borrar) está
        activado. Forzado a True mientras la app esté en desarrollo: no
        hay forma de desactivarlo desde la UI, para que ningún borrado
        sea irreversible por accidente. El valor guardado en config.json
        se conserva sin usar por si en el futuro se decide volver a
        permitir desactivarlo.
        """
        return True
    
    def set_debug_enabled(self, value: bool):
        """Establece si el modo debug está activado"""
        self.set("debug.enabled", value)
    
    def get_debug_folder(self) -> str:
        """Obtiene la carpeta de debug"""
        return self.get("paths.debug_folder", "")
    
    def set_debug_folder(self, value: str):
        """Establece la carpeta de debug"""
        self.set("paths.debug_folder", value)
    
    def get_library_size_gb(self) -> float:
        """
        Tamaño total aproximado de la biblioteca (en GB), introducido a
        mano por el usuario — no se calcula recorriendo la red porque
        para una biblioteca de varios TB sería lento y no aporta tanto
        como para justificar la espera. Solo se usa para mostrar qué
        porcentaje representa lo purgado (pestaña Basura). 0 = sin
        configurar, no se muestra el porcentaje.
        """
        return self.get("trash.library_size_gb", 0)

    def set_library_size_gb(self, value: float):
        """Establece el tamaño total aproximado de la biblioteca (GB)"""
        self.set("trash.library_size_gb", value)

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

    # Rutas recientes por categoría (duplicados/huérfanos/series usan
    # carpetas distintas — no tiene sentido compartir una única "última
    # ruta" entre todas, como pasaba antes)
    def get_recent_paths(self, category: str) -> List[str]:
        """Obtiene hasta 5 rutas usadas recientemente para una categoría (p.ej. 'duplicados', 'huerfanos', 'series')"""
        return self.get(f"paths.recent.{category}", [])

    def add_recent_path(self, category: str, path: str):
        """Añade una ruta al principio del historial de esa categoría (máx. 5, sin duplicados)"""
        if not path:
            return
        recientes = self.get_recent_paths(category)
        if path in recientes:
            recientes.remove(path)
        recientes.insert(0, path)
        self.set(f"paths.recent.{category}", recientes[:5])

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

    # Métodos para series ignoradas en "series sin indexar" (el usuario
    # sabe que esa serie está bien aunque el nombre no case con Plex)
    def get_ignored_series(self) -> List[str]:
        """Obtiene la lista de series (normalizadas) marcadas como ignoradas"""
        return self.get("series.ignored_shows", [])

    def set_ignored_series(self, value: List[str]):
        """Establece la lista de series ignoradas"""
        self.set("series.ignored_shows", value)

    def add_ignored_series(self, serie_normalizada: str):
        """Añade una serie a la lista de ignoradas"""
        ignoradas = self.get_ignored_series()
        if serie_normalizada not in ignoradas:
            ignoradas.append(serie_normalizada)
            self.set_ignored_series(ignoradas)

    def remove_ignored_series(self, serie_normalizada: str):
        """Quita una serie de la lista de ignoradas"""
        ignoradas = self.get_ignored_series()
        if serie_normalizada in ignoradas:
            ignoradas.remove(serie_normalizada)
            self.set_ignored_series(ignoradas)

    # Métodos para "Propuestas" (automatización): escaneo programado que
    # detecta huérfanos/duplicados nuevos, avisa por email y dejar
    # revisar/aplicar/descartar cada propuesta desde la app.
    def get_automation_enabled(self) -> bool:
        """Obtiene si el escaneo programado de propuestas está activado"""
        return self.get("automation.enabled", False)

    def set_automation_enabled(self, value: bool):
        """Establece si el escaneo programado de propuestas está activado"""
        self.set("automation.enabled", value)

    def get_automation_movie_folders(self) -> List[str]:
        """
        Carpetas de películas que analiza el escaneo programado. V1 solo
        cubre películas (huérfanos + duplicados) — series queda para una
        fase posterior, no hay ajuste equivalente todavía.
        """
        return self.get("automation.movie_folders", [])

    def set_automation_movie_folders(self, value: List[str]):
        """Establece las carpetas de películas del escaneo programado"""
        self.set("automation.movie_folders", value)

    def get_automation_email_to(self) -> str:
        """Dirección a la que se envía el aviso de propuestas nuevas"""
        return self.get("automation.email_to", "")

    def set_automation_email_to(self, value: str):
        """Establece la dirección de aviso de propuestas"""
        self.set("automation.email_to", value)

    def get_automation_app_url(self) -> str:
        """
        URL base de la app (para el enlace del email — normalmente tu IP
        de Tailscale, ej. http://100.x.x.x:8501), ya que el email no
        puede adivinar por dónde vas a entrar a verla.
        """
        return self.get("automation.app_url", "")

    def set_automation_app_url(self, value: str):
        """Establece la URL base de la app para el enlace del email"""
        self.set("automation.app_url", value)

    def get_automation_size_premium_tolerance_pct(self) -> float:
        """
        % máximo de más que puede pesar la copia de mayor calidad para
        que aun así se proponga quedarse con ella (borrar la otra).
        Por defecto 50 (tu criterio: hasta un 50% más grande).
        """
        return self.get("automation.size_premium_tolerance_pct", 50)

    def set_automation_size_premium_tolerance_pct(self, value: float):
        self.set("automation.size_premium_tolerance_pct", value)

    def get_automation_size_premium_max_gb(self) -> float:
        """GB máximos de más que puede pesar la copia de mayor calidad (por defecto 10)"""
        return self.get("automation.size_premium_max_gb", 10)

    def set_automation_size_premium_max_gb(self, value: float):
        self.set("automation.size_premium_max_gb", value)

    # Descartes persistentes ("no, ese no, no me lo vuelvas a proponer") —
    # mismo patrón que series ignoradas, pero con dos listas separadas
    # porque huérfanos y duplicados se identifican de forma distinta.
    def get_dismissed_orphan_proposals(self) -> List[str]:
        """Rutas de archivo cuya propuesta de nombre se ha descartado"""
        return self.get("automation.dismissed_orphans", [])

    def add_dismissed_orphan_proposal(self, archivo: str):
        descartados = self.get_dismissed_orphan_proposals()
        if archivo not in descartados:
            descartados.append(archivo)
            self.set("automation.dismissed_orphans", descartados)

    def remove_dismissed_orphan_proposal(self, archivo: str):
        descartados = self.get_dismissed_orphan_proposals()
        if archivo in descartados:
            descartados.remove(archivo)
            self.set("automation.dismissed_orphans", descartados)

    def get_dismissed_duplicate_proposals(self) -> List[str]:
        """Claves de par (ruta1|ruta2) cuya propuesta de borrado se ha descartado"""
        return self.get("automation.dismissed_duplicates", [])

    def add_dismissed_duplicate_proposal(self, par_key: str):
        descartados = self.get_dismissed_duplicate_proposals()
        if par_key not in descartados:
            descartados.append(par_key)
            self.set("automation.dismissed_duplicates", descartados)

    def remove_dismissed_duplicate_proposal(self, par_key: str):
        descartados = self.get_dismissed_duplicate_proposals()
        if par_key in descartados:
            descartados.remove(par_key)
            self.set("automation.dismissed_duplicates", descartados)

    # Claves de propuestas ya notificadas por email — para no mandar el
    # mismo aviso cada noche mientras el usuario no las revise ni
    # descarte; en cuanto haya una propuesta nueva de verdad, sí avisa.
    def get_notified_proposal_keys(self) -> List[str]:
        return self.get("automation.notified_keys", [])

    def set_notified_proposal_keys(self, value: List[str]):
        self.set("automation.notified_keys", value)

    def get_automation_schedule_time(self) -> str:
        """Hora local (HH:MM) a la que se dispara el escaneo programado dentro de la app"""
        return self.get("automation.schedule_time", "03:00")

    def set_automation_schedule_time(self, value: str):
        self.set("automation.schedule_time", value)

    def get_automation_last_run_date(self) -> str:
        """Fecha (YYYY-MM-DD) de la última vez que se ejecutó el escaneo programado — evita disparar dos veces el mismo día"""
        return self.get("automation.last_run_date", "")

    def set_automation_last_run_date(self, value: str):
        self.set("automation.last_run_date", value)

    def get_automation_email_message(self) -> str:
        """Mensaje personalizado que se antepone al cuerpo del email de aviso (opcional)"""
        return self.get("automation.email_message", "")

    def set_automation_email_message(self, value: str):
        self.set("automation.email_message", value)

    # Métodos para sugerencia de nombres con IA (detector de huérfanos)
    def get_ai_enabled(self) -> bool:
        """Obtiene si la sugerencia de nombres con IA está activada"""
        return self.get("ai.enabled", False)

    def set_ai_enabled(self, value: bool):
        """Establece si la sugerencia de nombres con IA está activada"""
        self.set("ai.enabled", value)

    def get_ai_provider(self) -> str:
        """Obtiene el proveedor de IA: 'ollama', 'openai' o 'gemini'"""
        return self.get("ai.provider", "ollama")

    def set_ai_provider(self, value: str):
        """Establece el proveedor de IA"""
        self.set("ai.provider", value)

    def get_ai_mode(self) -> str:
        """Obtiene el modo: 'suggest' (proponer, confirmas tú) o 'auto' (renombra solo)"""
        return self.get("ai.mode", "suggest")

    def set_ai_mode(self, value: str):
        """Establece el modo de la IA"""
        self.set("ai.mode", value)

    def get_ai_ollama_url(self) -> str:
        """Obtiene la URL del servidor Ollama local"""
        return self.get("ai.ollama_url", "http://localhost:11434")

    def set_ai_ollama_url(self, value: str):
        """Establece la URL del servidor Ollama local"""
        self.set("ai.ollama_url", value)

    def get_ai_ollama_model(self) -> str:
        """Obtiene el modelo de Ollama a usar"""
        return self.get("ai.ollama_model", "qwen2.5:7b")

    def set_ai_ollama_model(self, value: str):
        """Establece el modelo de Ollama a usar"""
        self.set("ai.ollama_model", value)

    def get_ai_openai_model(self) -> str:
        """Obtiene el modelo de OpenAI a usar"""
        return self.get("ai.openai_model", "gpt-4o-mini")

    def set_ai_openai_model(self, value: str):
        """Establece el modelo de OpenAI a usar"""
        self.set("ai.openai_model", value)

    def get_ai_gemini_model(self) -> str:
        """Obtiene el modelo de Gemini a usar"""
        return self.get("ai.gemini_model", "gemini-1.5-flash")

    def set_ai_gemini_model(self, value: str):
        """Establece el modelo de Gemini a usar"""
        self.set("ai.gemini_model", value)

    def get_openai_api_key(self) -> str:
        """Obtiene la API key de OpenAI (solo por variable de entorno, nunca en config.json)"""
        return self.get_env("OPENAI_API_KEY")

    def get_gemini_api_key(self) -> str:
        """Obtiene la API key de Gemini (solo por variable de entorno, nunca en config.json)"""
        return self.get_env("GEMINI_API_KEY")


# Instancia global del singleton
settings = Settings()
