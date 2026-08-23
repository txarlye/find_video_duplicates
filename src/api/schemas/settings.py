#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Configuración"""

from typing import List, Optional
from pydantic import BaseModel


class DetectionSettings(BaseModel):
    similarity_threshold: float
    excluded_directories: List[str]
    duration_filter_enabled: bool
    duration_tolerance_minutes: int


class DetectionUpdate(BaseModel):
    similarity_threshold: float
    duration_filter_enabled: bool
    duration_tolerance_minutes: int


class ExcludedDirectoryCreate(BaseModel):
    directory: str


class PlayerSettings(BaseModel):
    show_video_players: bool
    show_embedded_players: bool
    video_player_size: str
    video_start_time_seconds: int
    debug_folder: str


class PlexSettings(BaseModel):
    database_path: str
    movies_library: str
    tv_shows_library: str
    fetch_metadata: bool
    duration_filter_enabled: bool
    duration_tolerance_minutes: int
    is_configured: bool


class PlexUpdate(BaseModel):
    database_path: str
    movies_library: str
    tv_shows_library: str
    fetch_metadata: bool
    duration_filter_enabled: bool
    duration_tolerance_minutes: int


class PlexLibrary(BaseModel):
    name: str


class ActionResult(BaseModel):
    ok: bool
    detail: Optional[str] = None


class TelegramStatus(BaseModel):
    """
    Solo lectura a propósito: el bot token es un secreto y vive
    únicamente en .env, nunca en un campo editable de la UI (mismo
    criterio que TMDB/OMDb/SMTP en toda la app).
    """
    configured: bool
    channel_id: Optional[str] = None


class AutomationSettings(BaseModel):
    enabled: bool
    movie_folders: List[str]
    schedule_time: str
    email_to: str
    app_url: str
    email_message: str
    size_premium_tolerance_pct: float
    size_premium_max_gb: float
    smtp_configured: bool
    smtp_user: Optional[str] = None
    last_run_date: Optional[str] = None


class AutomationUpdate(BaseModel):
    enabled: bool
    schedule_time: str
    email_to: str
    app_url: str
    email_message: str
    size_premium_tolerance_pct: float
    size_premium_max_gb: float


class AutomationFoldersUpdate(BaseModel):
    folders: List[str]


class AiNamingSettings(BaseModel):
    enabled: bool
    provider: str  # ollama | openai | gemini
    mode: str  # suggest | auto
    ollama_url: str
    ollama_model: str
    openai_model: str
    gemini_model: str
    openai_key_configured: bool
    gemini_key_configured: bool
    tmdb_configured: bool
    omdb_configured: bool


class AiNamingUpdate(BaseModel):
    enabled: bool
    provider: str
    mode: str
    ollama_url: str
    ollama_model: str
    openai_model: str
    gemini_model: str
