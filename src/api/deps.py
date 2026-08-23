#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Providers singleton para la API — mismos objetos de servicio que ya
usaba StreamlitAppManager, para no duplicar estado ni reconstruirlos en
cada petición. FastAPI los inyecta vía Depends(...).
"""

from functools import lru_cache

from src.settings.settings import settings as _settings
from src.services.scan_data_manager import ScanDataManager
from src.services.plex_service import PlexService
from src.services.plex_refresh_service import PlexRefreshService
from src.services.ai_naming_service import AINamingService
from src.services.proposals_service import ProposalsService
from src.services.email_service import EmailService
from src.services.telegram_service import TelegramService
from src.services.Telegram.telegram_uploader import TelegramUploader
from src.services.Imdb.imdb_service import ImdbService
from src.services.video_info_service import VideoInfoService
from src.services.synology_scheduler_service import SynologySchedulerService


def get_settings():
    return _settings


@lru_cache
def get_scan_data_manager() -> ScanDataManager:
    return ScanDataManager()


@lru_cache
def get_plex_service() -> PlexService:
    return PlexService()


@lru_cache
def get_plex_refresh_service() -> PlexRefreshService:
    return PlexRefreshService()


@lru_cache
def get_ai_naming_service() -> AINamingService:
    return AINamingService()


@lru_cache
def get_proposals_service() -> ProposalsService:
    return ProposalsService(get_plex_service(), get_ai_naming_service())


@lru_cache
def get_email_service() -> EmailService:
    return EmailService()


@lru_cache
def get_telegram_service() -> TelegramService:
    return TelegramService()


@lru_cache
def get_telegram_uploader() -> TelegramUploader:
    return TelegramUploader()


@lru_cache
def get_imdb_service() -> ImdbService:
    return ImdbService()


@lru_cache
def get_video_info_service() -> VideoInfoService:
    return VideoInfoService()


@lru_cache
def get_synology_scheduler_service() -> SynologySchedulerService:
    return SynologySchedulerService()
