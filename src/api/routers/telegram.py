#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Telegram — puerto de _render_telegram_tab/_render_telegram_interface/
_scan_telegram_folder/_upload_selected_videos_to_telegram y de la parte
real de _render_imdb_interface (streamlit_manager.py ~4012-5460).

La pantalla "IMDB" del Streamlit original no se porta como pantalla
aparte: era casi un calco de esta (mismo escaneo de carpeta, misma
lista con checkboxes, mismo TelegramUploader por debajo) más un modo
"Archivos Individuales" que nunca subía nada de verdad ("Simular
subida... en producción aquí se subiría realmente"). Lo único genuino
que añadía — buscar título/póster/sinopsis antes de subir — se ofrece
aquí como una casilla "enrich" en el mismo job de subida, en vez de
como una pantalla duplicada.

Tampoco se usa TelegramManager directamente en ningún sitio del
Streamlit original más allá de instanciarlo — es un envoltorio que ni
siquiera se llama (el escaneo de carpeta es un rglob manual, y la
subida ya pasa por TelegramUploader). No se porta.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_imdb_service, get_settings, get_telegram_service, get_telegram_uploader
from src.api.jobs import job_manager
from src.api.schemas.telegram import (
    ActionResult,
    ScanRequest,
    ScanResult,
    TelegramStatus,
    UploadRequest,
    VideoItem,
)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
TELETHON_MAX_MB = 1500


@router.get("/status", response_model=TelegramStatus)
def estado(telegram_service=Depends(get_telegram_service), imdb_service=Depends(get_imdb_service)):
    manager = telegram_service.manager
    return TelegramStatus(
        bot_configured=manager.bot_service.is_configured(),
        telethon_configured=manager.telethon_service.is_configured(),
        movie_info_available=imdb_service.manager.movie_finder is not None,
    )


@router.post("/test-connection", response_model=ActionResult)
def probar_conexion(telegram_service=Depends(get_telegram_service)):
    ok = telegram_service.test_connection()
    return ActionResult(ok=ok, detail=None if ok else "Telegram no está configurado (bot token/channel id o credenciales Telethon)")


@router.post("/test-message", response_model=ActionResult)
def enviar_mensaje_prueba(telegram_service=Depends(get_telegram_service)):
    ok = telegram_service.manager.bot_service.send_message("🧪 Mensaje de prueba desde la aplicación")
    return ActionResult(ok=ok, detail=None if ok else "Error enviando el mensaje — revisa TELEGRAM_BOT_TOKEN/TELEGRAM_CHANNEL_ID")


@router.post("/scan", response_model=ScanResult)
def escanear_carpeta(body: ScanRequest, settings=Depends(get_settings)):
    folder = Path(body.folder)
    if not folder.exists():
        raise HTTPException(status_code=400, detail="La carpeta especificada no existe")

    settings.add_recent_path("telegram", body.folder)

    videos: List[VideoItem] = []
    for file_path in sorted(folder.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            videos.append(VideoItem(name=file_path.name, path=str(file_path), size_mb=size_mb))

    return ScanResult(videos=videos)


def _enviar_info_pelicula(video_path: str, video_name: str, *, telegram_service, imdb_service) -> Dict[str, Any]:
    """Busca info (Plex+OMDb, vía ImdbMovieFinder) y manda póster + sinopsis antes del video. Best-effort: nunca bloquea la subida del vídeo en sí."""
    info_found = False
    poster_sent = False
    try:
        movie_info = imdb_service.find_movie_info(video_path)
        if not movie_info:
            return {"info_found": False, "poster_sent": False}
        info_found = True

        finder = imdb_service.manager.movie_finder
        bot = telegram_service.manager.bot_service

        poster_url = movie_info.get("poster")
        if finder and poster_url and poster_url != "N/A":
            poster_data = finder.get_poster_image(poster_url)
            if poster_data:
                tmp_path = Path(tempfile.gettempdir()) / f"poster_{abs(hash(video_name))}.jpg"
                tmp_path.write_bytes(poster_data)
                try:
                    poster_sent = bot.send_photo(str(tmp_path), caption=f"🎬 {movie_info.get('title', video_name)}")
                finally:
                    tmp_path.unlink(missing_ok=True)

        if finder:
            bot.send_message(finder.format_movie_message(movie_info))
    except Exception:
        pass

    return {"info_found": info_found, "poster_sent": poster_sent}


def _run_upload(
    videos: List[Any],
    enrich: bool,
    *,
    progress_cb,
    is_cancelled,
    telegram_service,
    telegram_uploader,
    imdb_service,
) -> Dict[str, Any]:
    resultados = []
    subidos = 0
    fallidos = 0
    total = len(videos)

    for i, video in enumerate(videos):
        if is_cancelled():
            break

        progress_cb((i / total) * 100 if total else 100, f"Subiendo {video.name}...")

        info_found = False
        poster_sent = False
        error = None
        try:
            if video.size_mb > TELETHON_MAX_MB:
                raise ValueError(f"Demasiado grande ({video.size_mb:.0f} MB, límite {TELETHON_MAX_MB} MB)")

            if enrich:
                info = _enviar_info_pelicula(video.path, video.name, telegram_service=telegram_service, imdb_service=imdb_service)
                info_found, poster_sent = info["info_found"], info["poster_sent"]

            success = telegram_uploader.upload_single_video(video.path, video.name, video.name)
            if success:
                subidos += 1
            else:
                fallidos += 1
                error = "Fallo al subir el vídeo"
        except Exception as e:
            fallidos += 1
            error = str(e)

        item = {"name": video.name, "success": error is None, "info_found": info_found, "poster_sent": poster_sent, "error": error}
        resultados.append(item)
        progress_cb((i + 1) / total * 100 if total else 100, f"{video.name} ({i + 1}/{total})", item=item)

    return {"subidos": subidos, "fallidos": fallidos, "resultados": resultados}


@router.post("/upload")
def subir(
    body: UploadRequest,
    telegram_service=Depends(get_telegram_service),
    telegram_uploader=Depends(get_telegram_uploader),
    imdb_service=Depends(get_imdb_service),
):
    if not telegram_service.manager.telethon_service.is_configured():
        raise HTTPException(status_code=409, detail="Telethon no está configurado (TELEGRAM_API_ID/HASH/PHONE/CHANNEL_ID en .env)")
    if not body.videos:
        raise HTTPException(status_code=400, detail="No hay vídeos seleccionados")

    job_id = job_manager.submit(
        _run_upload,
        body.videos,
        body.enrich,
        telegram_service=telegram_service,
        telegram_uploader=telegram_uploader,
        imdb_service=imdb_service,
    )
    return {"job_id": job_id}
