#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fotograma de un vídeo en un instante concreto — puerto de
_render_frame_preview de streamlit_manager.py. Usa VideoFrameExtractor
(ya puro, sin cambios) para no depender de que el navegador sepa
decodificar/buscar en el archivo original.

También sirve /stream, la pieza genuinamente nueva del reproductor
embebido: Streamlit no tenía que resolverlo (st.video ya hace su
propio streaming interno), pero aquí servimos el archivo nosotros, así
que hace falta soportar Range requests a mano — sin esto, el elemento
<video> del navegador no puede buscar (seek) dentro de un archivo de
varios GB, solo reproducir desde el principio.
"""

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from src.settings.settings import settings
from src.utils.video import VideoFrameExtractor

router = APIRouter(prefix="/api/video", tags=["video"])

CHUNK_SIZE = 1024 * 1024  # 1 MB


@router.get("/frame")
def obtener_fotograma(path: str = Query(...), seconds: int = Query(None)):
    if not VideoFrameExtractor.is_available():
        raise HTTPException(status_code=503, detail="ffmpeg no disponible en el servidor")

    instante = seconds if seconds is not None else settings.get_video_start_time_seconds()
    frame = VideoFrameExtractor.extract_frame(path, instante)
    if not frame:
        raise HTTPException(status_code=404, detail=f"No se pudo extraer el fotograma en {instante}s (¿el vídeo dura menos?)")

    return Response(content=frame, media_type="image/jpeg")


@router.get("/stream")
def stream_video(request: Request, path: str = Query(...)):
    file_path = Path(path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="El archivo no existe")

    file_size = file_path.stat().st_size
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    range_header = request.headers.get("range")
    if not range_header:
        def iter_completo():
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk

        return StreamingResponse(
            iter_completo(),
            media_type=content_type,
            headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)},
        )

    try:
        unidades, rango = range_header.split("=")
        inicio_str, fin_str = rango.split("-")
        inicio = int(inicio_str) if inicio_str else 0
        fin = int(fin_str) if fin_str else file_size - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Cabecera Range no válida")

    fin = min(fin, file_size - 1)
    if inicio > fin or inicio < 0:
        raise HTTPException(status_code=416, detail="Rango fuera de los límites del archivo")

    longitud = fin - inicio + 1

    def iter_rango():
        with open(file_path, "rb") as f:
            f.seek(inicio)
            restante = longitud
            while restante > 0:
                chunk = f.read(min(CHUNK_SIZE, restante))
                if not chunk:
                    break
                restante -= len(chunk)
                yield chunk

    return StreamingResponse(
        iter_rango(),
        status_code=206,
        media_type=content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {inicio}-{fin}/{file_size}",
            "Content-Length": str(longitud),
        },
    )
