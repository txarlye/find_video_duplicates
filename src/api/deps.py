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
