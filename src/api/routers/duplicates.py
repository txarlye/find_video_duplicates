#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Duplicados — puerto de _process_scan/_render_duplicates/
_render_movie_controls/_process_pair_deletion/_get_plex_metadata_for_pair
(streamlit_manager.py ~524-2686).

No se porta el asistente de "crear edición de Plex" (renombrar según
la convención "Película {edition-Nombre}" en vez de borrar): son
varios cientos de líneas repartidas en funciones parcialmente
duplicadas entre sí en el original, para una funcionalidad secundaria
frente al flujo principal de "revisar par y borrar/mover la copia que
sobra". Con Plex ya configurado, borrar el duplicado sigue dejando la
biblioteca correcta; queda como posible ampliación futura si hace
falta de verdad.

Tampoco se porta el botón de "abrir en reproductor externo": lanzaba
un reproductor en la máquina donde corría Streamlit, algo que deja de
tener sentido en un contenedor Docker sin GUI — el reproductor
embebido (streaming con range-requests, ver routers/video.py) cubre
el mismo caso de uso desde cualquier dispositivo en la LAN/Tailscale.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.api.common import mover_a_debug, refrescar_plex
from src.api.deps import get_plex_refresh_service, get_plex_service, get_scan_data_manager, get_settings
from src.api.jobs import job_manager
from src.api.schemas.duplicates import (
    BulkMoveRequest,
    BulkMoveResult,
    DeleteRequest,
    DeleteResult,
    DuplicatePair,
    FileInfo,
    LoadRequest,
    LoadResult,
    PlexMetadataRequest,
    PlexMetadataResponse,
    PlexMovieMetadata,
    SaveRequest,
    SavedScan,
    ScanRequest,
)
from src.utils.movie_detector import MovieDetector

router = APIRouter(prefix="/api/duplicates", tags=["duplicates"])


def _file_info(archivo: Dict[str, Any]) -> FileInfo:
    ruta = archivo.get("archivo", "")
    existe = bool(ruta) and os.path.exists(ruta)
    creado = None
    if existe:
        try:
            creado = datetime.fromtimestamp(os.path.getctime(ruta)).isoformat()
        except OSError:
            pass
    return FileInfo(
        nombre=archivo.get("nombre", "N/A"),
        ruta=ruta,
        tamaño=archivo.get("tamaño", 0),
        duracion=archivo.get("duracion", 0),
        existe=existe,
        creado=creado,
    )


def _run_scan(folder: str, *, progress_cb, is_cancelled) -> Dict[str, Any]:
    progress_cb(10, "Escaneando archivos...")
    detector = MovieDetector(folder)

    contador = {"n": 0}

    def mostrar_archivo(_archivo):
        contador["n"] += 1
        if contador["n"] % 25 == 0:
            progress_cb(35, f"{contador['n']} archivo(s) escaneados...")

    detector.mostrar_archivo = mostrar_archivo
    peliculas = detector.escanear_carpeta()

    progress_cb(70, f"Buscando duplicados entre {len(peliculas)}...")
    grupos = detector.encontrar_duplicados()

    pares = []
    for grupo in grupos:
        if len(grupo) < 2:
            continue
        a1, a2 = grupo[0], grupo[1]
        pares.append(
            {
                "clave": f"{a1.get('archivo', '')}|{a2.get('archivo', '')}",
                "peli1": _file_info(a1).model_dump(),
                "peli2": _file_info(a2).model_dump(),
            }
        )

    progress_cb(100, "Completado")
    return {"pares": pares, "total_peliculas": len(peliculas)}


@router.post("/scan")
def escanear(body: ScanRequest, settings=Depends(get_settings)):
    if not Path(body.folder).exists():
        raise HTTPException(status_code=400, detail="La carpeta especificada no existe")
    settings.add_recent_path("duplicados", body.folder)
    settings.reset_pairs_counters()
    job_id = job_manager.submit(_run_scan, body.folder)
    return {"job_id": job_id}


@router.post("/plex-metadata", response_model=PlexMetadataResponse)
def metadatos_plex(body: PlexMetadataRequest, plex_service=Depends(get_plex_service)):
    meta1 = plex_service.get_movie_metadata_by_filename(os.path.basename(body.ruta1))
    meta2 = plex_service.get_movie_metadata_by_filename(os.path.basename(body.ruta2))

    es_duplicado = False
    duracion_compatible = None
    duracion_mensaje = None
    if meta1 and meta2:
        t1, y1 = meta1.get("title"), meta1.get("year")
        t2, y2 = meta2.get("title"), meta2.get("year")
        es_duplicado = bool(t1 and t1 == t2 and y1 == y2)
        duracion_compatible, duracion_mensaje = plex_service.check_duration_compatibility(meta1, meta2)

    return PlexMetadataResponse(
        file1=PlexMovieMetadata(encontrado=meta1 is not None, datos=meta1),
        file2=PlexMovieMetadata(encontrado=meta2 is not None, datos=meta2),
        es_duplicado_plex=es_duplicado,
        duracion_compatible=duracion_compatible,
        duracion_mensaje=duracion_mensaje,
    )


@router.post("/delete", response_model=DeleteResult)
def borrar(body: DeleteRequest, settings=Depends(get_settings), scan_data_manager=Depends(get_scan_data_manager)):
    movidos = 0
    errores: List[str] = []
    for archivo in body.archivos:
        try:
            mover_a_debug(archivo, settings, scan_data_manager)
            movidos += 1
        except Exception as e:
            errores.append(f"{archivo}: {e}")
    return DeleteResult(movidos=movidos, errores=errores)


@router.post("/bulk-move", response_model=BulkMoveResult)
def mover_lote(body: BulkMoveRequest, plex_refresh_service=Depends(get_plex_refresh_service), settings=Depends(get_settings)):
    import shutil

    destino = Path(body.destino)
    destino.mkdir(parents=True, exist_ok=True)

    movidos = 0
    errores: List[str] = []
    for archivo in body.archivos:
        try:
            origen = Path(archivo)
            if not origen.exists():
                errores.append(f"{archivo}: ya no existe")
                continue
            objetivo = destino / origen.name
            contador = 1
            while objetivo.exists():
                objetivo = destino / f"{origen.stem}_{contador}{origen.suffix}"
                contador += 1
            shutil.move(str(origen), str(objetivo))
            movidos += 1
        except Exception as e:
            errores.append(f"{archivo}: {e}")

    if movidos:
        refrescar_plex(settings, plex_refresh_service)

    return BulkMoveResult(movidos=movidos, errores=errores)


@router.post("/save")
def guardar(body: SaveRequest, scan_data_manager=Depends(get_scan_data_manager)):
    if not body.pares:
        raise HTTPException(status_code=400, detail="No hay pares de duplicados para guardar")
    file_path = scan_data_manager.save_scan_data(
        pairs_data=[p.model_dump() for p in body.pares],
        scan_path=body.folder,
        kind="duplicados",
    )
    return {"file_path": file_path}


@router.get("/saved", response_model=List[SavedScan])
def listar_guardados(scan_data_manager=Depends(get_scan_data_manager)):
    scans = scan_data_manager.get_available_scans(kind="duplicados")
    return [
        SavedScan(
            file_path=s["file_path"],
            scan_path=s.get("scan_path", "N/A"),
            scan_date=s.get("scan_date", "N/A"),
            total_pairs=s.get("total_pairs", 0),
        )
        for s in scans
    ]


@router.post("/load", response_model=LoadResult)
def cargar(body: LoadRequest, scan_data_manager=Depends(get_scan_data_manager)):
    scan_data = scan_data_manager.load_scan_data(body.file_path)
    guardados = scan_data.get("pairs_data", [])

    pares = []
    no_existentes = 0
    for p in guardados:
        peli1, peli2 = p.get("peli1", {}), p.get("peli2", {})
        existe1 = bool(peli1.get("ruta")) and os.path.exists(peli1["ruta"])
        existe2 = bool(peli2.get("ruta")) and os.path.exists(peli2["ruta"])
        if not existe1 or not existe2:
            no_existentes += 1
            continue
        pares.append(DuplicatePair(clave=p.get("clave", ""), peli1=FileInfo(**peli1), peli2=FileInfo(**peli2)))

    return LoadResult(pares=pares, total_guardado=len(guardados), no_existentes=no_existentes)
