#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Telegram (incluye la antigua pantalla IMDB, fusionada aquí)"""

from typing import List, Optional
from pydantic import BaseModel


class TelegramStatus(BaseModel):
    bot_configured: bool
    telethon_configured: bool
    movie_info_available: bool


class ActionResult(BaseModel):
    ok: bool
    detail: Optional[str] = None


class ScanRequest(BaseModel):
    folder: str


class VideoItem(BaseModel):
    name: str
    path: str
    size_mb: float


class ScanResult(BaseModel):
    videos: List[VideoItem]


class UploadRequest(BaseModel):
    videos: List[VideoItem]
    enrich: bool = False


class UploadItemResult(BaseModel):
    name: str
    success: bool
    info_found: bool = False
    poster_sent: bool = False
    error: Optional[str] = None


class UploadResult(BaseModel):
    subidos: int
    fallidos: int
    resultados: List[UploadItemResult]
