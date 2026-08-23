#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Configuración — un único recurso por sección (antes repartido
entre pestañas del sidebar de Streamlit y una copia con key_prefix en
la página completa de Utilidades; aquí solo hay una vez cada cosa).

Puerto de _render_detection_tab/_render_configuration_tab/_render_plex_tab
(src/app/streamlit_manager.py:180-496) y _render_automation_config
(línea 4252). El tab de Telegram se reduce a un estado de solo lectura
a propósito (el bot token es un secreto, vive solo en .env — mismo
criterio que TMDB/OMDb/SMTP en el resto de la app); el de IMDB no se
porta: en el original nunca llegó a guardar nada de verdad (placeholder
sin terminar).
"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_settings, get_plex_service, get_plex_refresh_service, get_email_service
from src.api.schemas.settings import (
    DetectionSettings,
    DetectionUpdate,
    ExcludedDirectoryCreate,
    PlayerSettings,
    PlexSettings,
    PlexUpdate,
    PlexLibrary,
    ActionResult,
    TelegramStatus,
    AutomationSettings,
    AutomationUpdate,
    AutomationFoldersUpdate,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------- Detección ----------

@router.get("/detection", response_model=DetectionSettings)
def obtener_deteccion(settings=Depends(get_settings)):
    return DetectionSettings(
        similarity_threshold=settings.get_similarity_threshold(),
        excluded_directories=settings.get_excluded_directories(),
        duration_filter_enabled=settings.get_duration_filter_enabled(),
        duration_tolerance_minutes=settings.get_duration_tolerance_minutes(),
    )


@router.put("/detection", response_model=DetectionSettings)
def guardar_deteccion(body: DetectionUpdate, settings=Depends(get_settings)):
    settings.set_similarity_threshold(body.similarity_threshold)
    settings.set_duration_filter_enabled(body.duration_filter_enabled)
    settings.set_duration_tolerance_minutes(body.duration_tolerance_minutes)
    return obtener_deteccion(settings)


@router.post("/detection/excluded-directories", response_model=DetectionSettings)
def añadir_directorio_excluido(body: ExcludedDirectoryCreate, settings=Depends(get_settings)):
    settings.add_excluded_directory(body.directory)
    return obtener_deteccion(settings)


@router.delete("/detection/excluded-directories/{directory}", response_model=DetectionSettings)
def quitar_directorio_excluido(directory: str, settings=Depends(get_settings)):
    settings.remove_excluded_directory(directory)
    return obtener_deteccion(settings)


# ---------- Reproductores y Debug ----------

@router.get("/players", response_model=PlayerSettings)
def obtener_reproductores(settings=Depends(get_settings)):
    return PlayerSettings(
        show_video_players=settings.get_show_video_players(),
        show_embedded_players=settings.get_show_embedded_players(),
        video_player_size=settings.get_video_player_size(),
        video_start_time_seconds=settings.get_video_start_time_seconds(),
        debug_folder=settings.get_debug_folder(),
    )


@router.put("/players", response_model=PlayerSettings)
def guardar_reproductores(body: PlayerSettings, settings=Depends(get_settings)):
    settings.set_show_video_players(body.show_video_players)
    settings.set_show_embedded_players(body.show_embedded_players)
    settings.set_video_player_size(body.video_player_size)
    settings.set_video_start_time_seconds(body.video_start_time_seconds)
    settings.set_debug_folder(body.debug_folder)
    return obtener_reproductores(settings)


# ---------- Plex ----------

@router.get("/plex", response_model=PlexSettings)
def obtener_plex(settings=Depends(get_settings), plex_service=Depends(get_plex_service)):
    return PlexSettings(
        database_path=settings.get_plex_database_path(),
        movies_library=settings.get_plex_movies_library(),
        tv_shows_library=settings.get_plex_tv_shows_library(),
        fetch_metadata=settings.get_plex_fetch_metadata(),
        duration_filter_enabled=settings.get_plex_duration_filter_enabled(),
        duration_tolerance_minutes=settings.get_plex_duration_tolerance_minutes(),
        is_configured=plex_service.is_configured(),
    )


@router.put("/plex", response_model=PlexSettings)
def guardar_plex(body: PlexUpdate, settings=Depends(get_settings), plex_service=Depends(get_plex_service)):
    settings.set_plex_database_path(body.database_path)
    settings.set_plex_movies_library(body.movies_library)
    settings.set_plex_tv_shows_library(body.tv_shows_library)
    settings.set_plex_fetch_metadata(body.fetch_metadata)
    settings.set_plex_duration_filter_enabled(body.duration_filter_enabled)
    settings.set_plex_duration_tolerance_minutes(body.duration_tolerance_minutes)
    return obtener_plex(settings, plex_service)


@router.get("/plex/libraries", response_model=list[PlexLibrary])
def listar_bibliotecas_plex(plex_service=Depends(get_plex_service)):
    return [PlexLibrary(name=lib["name"]) for lib in plex_service.get_available_libraries()]


@router.post("/plex/test-connection", response_model=ActionResult)
def probar_conexion_plex(plex_service=Depends(get_plex_service)):
    ok = plex_service.test_connection()
    return ActionResult(ok=ok, detail=None if ok else "Error de conexión")


@router.post("/plex/refresh-movies", response_model=ActionResult)
def refrescar_peliculas_plex(plex_refresh_service=Depends(get_plex_refresh_service)):
    ok = plex_refresh_service.refresh_movies_library()
    return ActionResult(ok=ok, detail=None if ok else "Error refrescando películas")


@router.post("/plex/refresh-tv", response_model=ActionResult)
def refrescar_series_plex(plex_refresh_service=Depends(get_plex_refresh_service)):
    ok = plex_refresh_service.refresh_tv_shows_library()
    return ActionResult(ok=ok, detail=None if ok else "Error refrescando series")


@router.post("/plex/refresh-all", response_model=ActionResult)
def refrescar_todo_plex(plex_refresh_service=Depends(get_plex_refresh_service)):
    ok = plex_refresh_service.refresh_all_libraries_via_api()
    return ActionResult(ok=ok, detail=None if ok else "Error refrescando bibliotecas vía API")


@router.get("/plex/server-info")
def info_servidor_plex(plex_refresh_service=Depends(get_plex_refresh_service)):
    info = plex_refresh_service.get_plex_server_info()
    if "error" in info:
        raise HTTPException(status_code=502, detail=info["error"])
    return info


# ---------- Telegram (solo lectura — el bot token vive en .env) ----------

@router.get("/telegram", response_model=TelegramStatus)
def obtener_estado_telegram(settings=Depends(get_settings)):
    return TelegramStatus(
        configured=bool(settings.get_telegram_bot_token()),
        channel_id=settings.get_telegram_channel_id() or None,
    )


# ---------- Automatización (Programación de Propuestas) ----------

@router.get("/automation", response_model=AutomationSettings)
def obtener_automatizacion(settings=Depends(get_settings)):
    return AutomationSettings(
        enabled=settings.get_automation_enabled(),
        movie_folders=settings.get_automation_movie_folders(),
        schedule_time=settings.get_automation_schedule_time(),
        email_to=settings.get_automation_email_to(),
        app_url=settings.get_automation_app_url(),
        email_message=settings.get_automation_email_message(),
        size_premium_tolerance_pct=settings.get_automation_size_premium_tolerance_pct(),
        size_premium_max_gb=settings.get_automation_size_premium_max_gb(),
        smtp_configured=bool(settings.get_smtp_user()),
        smtp_user=settings.get_smtp_user() or None,
        last_run_date=settings.get_automation_last_run_date() or None,
    )


@router.put("/automation", response_model=AutomationSettings)
def guardar_automatizacion(body: AutomationUpdate, settings=Depends(get_settings)):
    settings.set_automation_enabled(body.enabled)
    settings.set_automation_schedule_time(body.schedule_time)
    settings.set_automation_email_to(body.email_to)
    settings.set_automation_app_url(body.app_url)
    settings.set_automation_email_message(body.email_message)
    settings.set_automation_size_premium_tolerance_pct(body.size_premium_tolerance_pct)
    settings.set_automation_size_premium_max_gb(body.size_premium_max_gb)
    return obtener_automatizacion(settings)


@router.put("/automation/folders", response_model=AutomationSettings)
def guardar_carpetas_automatizacion(body: AutomationFoldersUpdate, settings=Depends(get_settings)):
    settings.set_automation_movie_folders(body.folders)
    return obtener_automatizacion(settings)


@router.post("/automation/test-email", response_model=ActionResult)
def probar_email_automatizacion(email_service=Depends(get_email_service)):
    ok = email_service.enviar_aviso_propuestas(1, 1)
    return ActionResult(ok=ok, detail=None if ok else "Revisa SMTP_USER/SMTP_PASSWORD en .env y el log")


# ---------- Rutas recientes (usado por las pantallas de escaneo) ----------

@router.get("/recent-paths/{category}", response_model=list[str])
def obtener_rutas_recientes(category: str, settings=Depends(get_settings)):
    return settings.get_recent_paths(category)
