#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Huérfanos — puerto de _process_orphans_scan,
_render_orphans_bulk_ai_controls/_start_orphans_ai_job/
_process_orphans_ai_job_chunk, _suggest_orphan_name_ai,
_apply_orphan_rename/_rename_orphan/_apply_all_orphan_renames, y
guardado/carga (streamlit_manager.py ~línea 648-1230).

El job de IA en lote (antes trozeado a mano en st.session_state,
reejecutándose con st.rerun entre tandas de 5 para que "Detener"
pudiera reaccionar) es ahora un job de verdad en JobManager: corre en
un hilo aparte y cada sugerencia se empuja por WebSocket en cuanto está
lista, con cancelación real entre cada archivo, no solo entre tandas.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.common import refrescar_plex
from src.api.deps import get_settings, get_plex_service, get_plex_refresh_service, get_ai_naming_service, get_scan_data_manager
from src.api.jobs import job_manager
from src.api.schemas.orphans import (
    ScanRequest,
    SuggestRequest,
    SuggestResponse,
    SuggestBatchRequest,
    RenameRequest,
    OrphanItem,
    RenameBatchRequest,
    RenameBatchResult,
    SavedScan,
    SaveRequest,
    LoadRequest,
    LoadResult,
)
from src.utils.movie_detector import MovieDetector

router = APIRouter(prefix="/api/orphans", tags=["orphans"])


def _run_scan(folder: str, *, progress_cb, is_cancelled, plex_service) -> Dict[str, Any]:
    progress_cb(10, "Escaneando archivos...")
    detector = MovieDetector(folder)

    contador = {"n": 0}

    def mostrar_archivo(_archivo):
        contador["n"] += 1
        if contador["n"] % 25 == 0:
            progress_cb(30, f"{contador['n']} archivo(s) escaneados...")

    detector.mostrar_archivo = mostrar_archivo
    peliculas = detector.escanear_carpeta()

    progress_cb(70, f"Comprobando {len(peliculas)} archivo(s) contra Plex...")
    plex_filenames = plex_service.get_all_movie_filenames()
    huerfanos = [p for p in peliculas if p["nombre"].lower() not in plex_filenames]

    progress_cb(100, "Completado")
    return {
        "items": [
            {"nombre": p["nombre"], "archivo": p["archivo"], "tamaño": p.get("tamaño", 0), "renombrado": False}
            for p in huerfanos
        ],
        "total_escaneados": len(peliculas),
    }


@router.post("/scan")
def escanear(body: ScanRequest, settings=Depends(get_settings), plex_service=Depends(get_plex_service)):
    if not Path(body.folder).exists():
        raise HTTPException(status_code=400, detail="La carpeta especificada no existe")
    settings.add_recent_path("huerfanos", body.folder)
    job_id = job_manager.submit(_run_scan, body.folder, plex_service=plex_service)
    return {"job_id": job_id}


@router.post("/suggest", response_model=SuggestResponse)
def sugerir(body: SuggestRequest, ai_naming_service=Depends(get_ai_naming_service)):
    return SuggestResponse(sugerido=ai_naming_service.suggest_name(body.nombre))


def _run_suggest_batch(items: List[Any], scope: Optional[int], *, progress_cb, is_cancelled, ai_naming_service) -> Dict[str, Any]:
    pendientes = items if scope is None else items[:scope]
    total = len(pendientes)
    sugeridos = 0
    sin_sugerencia = 0
    resultados = []

    for i, item in enumerate(pendientes):
        if is_cancelled():
            break
        sugerido = ai_naming_service.suggest_name(item.nombre)
        if sugerido:
            sugeridos += 1
        else:
            sin_sugerencia += 1
        resultado_item = {"archivo": item.archivo, "sugerido": sugerido}
        resultados.append(resultado_item)
        progress_cb(
            (i + 1) / total * 100 if total else 100,
            f"{item.nombre} ({i + 1}/{total})",
            item=resultado_item,
        )

    return {"resultados": resultados, "sugeridos": sugeridos, "sin_sugerencia": sin_sugerencia, "total": total}


@router.post("/suggest-batch")
def sugerir_lote(body: SuggestBatchRequest, ai_naming_service=Depends(get_ai_naming_service)):
    if not ai_naming_service.is_configured():
        raise HTTPException(status_code=409, detail="IA no configurada correctamente (revisa proveedor/API key)")
    job_id = job_manager.submit(_run_suggest_batch, body.items, body.scope, ai_naming_service=ai_naming_service)
    return {"job_id": job_id}


@router.post("/rename", response_model=OrphanItem)
def renombrar(
    body: RenameRequest,
    settings=Depends(get_settings),
    plex_refresh_service=Depends(get_plex_refresh_service),
):
    old_path = Path(body.archivo)
    if not old_path.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no existe en esa ruta")
    new_path = old_path.parent / f"{body.nuevo_nombre}{old_path.suffix}"
    try:
        os.rename(str(old_path), str(new_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renombrando: {e}")

    refrescar_plex(settings, plex_refresh_service)
    return OrphanItem(nombre=new_path.name, archivo=str(new_path), renombrado=True)


@router.post("/rename-batch", response_model=RenameBatchResult)
def renombrar_lote(
    body: RenameBatchRequest,
    settings=Depends(get_settings),
    plex_refresh_service=Depends(get_plex_refresh_service),
):
    renombrados = 0
    errores: List[str] = []
    for item in body.items:
        try:
            old_path = Path(item.archivo)
            new_path = old_path.parent / f"{item.nuevo_nombre}{old_path.suffix}"
            os.rename(str(old_path), str(new_path))
            renombrados += 1
        except Exception as e:
            errores.append(f"{item.archivo}: {e}")

    if renombrados:
        refrescar_plex(settings, plex_refresh_service)

    return RenameBatchResult(renombrados=renombrados, errores=errores)


@router.post("/save")
def guardar(body: SaveRequest, scan_data_manager=Depends(get_scan_data_manager)):
    if not body.items:
        raise HTTPException(status_code=400, detail="No hay huérfanos para guardar")
    file_path = scan_data_manager.save_scan_data(
        pairs_data=[item.model_dump() for item in body.items],
        scan_path=body.folder,
        kind="huerfanos",
    )
    return {"file_path": file_path}


@router.get("/saved", response_model=List[SavedScan])
def listar_guardados(scan_data_manager=Depends(get_scan_data_manager)):
    scans = scan_data_manager.get_available_scans(kind="huerfanos")
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

    existentes = [h for h in guardados if h.get("archivo") and Path(h["archivo"]).exists()]
    ya_renombrados = sum(1 for h in existentes if h.get("renombrado"))

    return LoadResult(
        items=[OrphanItem(**h) for h in existentes],
        total_guardados=len(guardados),
        no_existentes=len(guardados) - len(existentes),
        ya_renombrados=ya_renombrados,
    )
