#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fotograma de un vídeo en un instante concreto — puerto de
_render_frame_preview de streamlit_manager.py. Usa VideoFrameExtractor
(ya puro, sin cambios) para no depender de que el navegador sepa
decodificar/buscar en el archivo original.
"""

from fastapi import APIRouter, HTTPException, Query, Response

from src.settings.settings import settings
from src.utils.video import VideoFrameExtractor

router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/frame")
def obtener_fotograma(path: str = Query(...), seconds: int = Query(None)):
    if not VideoFrameExtractor.is_available():
        raise HTTPException(status_code=503, detail="ffmpeg no disponible en el servidor")

    instante = seconds if seconds is not None else settings.get_video_start_time_seconds()
    frame = VideoFrameExtractor.extract_frame(path, instante)
    if not frame:
        raise HTTPException(status_code=404, detail=f"No se pudo extraer el fotograma en {instante}s (¿el vídeo dura menos?)")

    return Response(content=frame, media_type="image/jpeg")
