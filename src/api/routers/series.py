#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Series — puerto de _process_series_scan/_render_series_results/
_mover_episodios_duplicados_seleccionados/_rename_series_orphan
(streamlit_manager.py ~línea 1237-1765).

El escaneo (episodios + duplicados + cruce con Plex + agrupado por
serie) va como job de JobManager igual que en Huérfanos — con carpetas
grandes tarda varios segundos y así el cliente ve progreso real en vez
de una request colgada.
"""

import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.api.common import mover_a_debug, refrescar_plex
from src.api.deps import get_settings, get_plex_service, get_plex_refresh_service, get_scan_data_manager
from src.api.jobs import job_manager
from src.api.schemas.series import (
    EpisodeItem,
    IgnoreSeriesRequest,
    IgnoredSeriesList,
    LoadRequest,
    LoadResult,
    MoveBatchRequest,
    MoveBatchResult,
    MoveRequest,
    RenameRequest,
    SaveRequest,
    SavedScan,
    ScanRequest,
)
from src.utils.series_detector import SeriesDetector

router = APIRouter(prefix="/api/series", tags=["series"])


def _run_scan(folder: str, *, progress_cb, is_cancelled, settings, plex_service) -> Dict[str, Any]:
    progress_cb(10, "Escaneando episodios...")
    detector = SeriesDetector(folder)

    contador = {"n": 0}

    def mostrar_archivo(_archivo):
        contador["n"] += 1
        if contador["n"] % 25 == 0:
            progress_cb(25, f"{contador['n']} archivo(s) escaneados...")

    detector.mostrar_archivo = mostrar_archivo
    episodios = detector.escanear_carpeta()

    if not episodios:
        progress_cb(100, "Completado")
        return {
            "duplicados": [],
            "huerfanos": [],
            "series_sin_indexar": [],
            "total_episodios": 0,
            "sin_reconocer": detector.sin_reconocer,
        }

    progress_cb(45, f"Buscando episodios duplicados entre {len(episodios)}...")
    duplicados = detector.encontrar_duplicados()

    progress_cb(65, "Comprobando episodios contra Plex...")
    plex_episodios = plex_service.get_all_episode_filenames()
    huerfanos = [e for e in episodios if e["nombre"].lower() not in plex_episodios]

    progress_cb(85, "Agrupando por serie...")
    series_locales = defaultdict(lambda: {"episodios": [], "tamaño": 0, "nombre": ""})
    for e in episodios:
        clave = e["serie_normalizada"]
        series_locales[clave]["episodios"].append(e)
        series_locales[clave]["tamaño"] += e.get("tamaño", 0)
        series_locales[clave]["nombre"] = e["serie"]

    ignoradas = set(settings.get_ignored_series())
    series_sin_indexar = [
        {
            "clave": clave,
            "serie": datos["nombre"],
            "episodios": datos["episodios"],
            "tamaño": datos["tamaño"],
        }
        for clave, datos in series_locales.items()
        if clave not in ignoradas and not any(e["nombre"].lower() in plex_episodios for e in datos["episodios"])
    ]
    series_sin_indexar.sort(key=lambda s: s["tamaño"], reverse=True)

    progress_cb(100, "Completado")
    return {
        "duplicados": duplicados,
        "huerfanos": huerfanos,
        "series_sin_indexar": series_sin_indexar,
        "total_episodios": len(episodios),
        "sin_reconocer": detector.sin_reconocer,
    }


@router.post("/scan")
def escanear(body: ScanRequest, settings=Depends(get_settings), plex_service=Depends(get_plex_service)):
    if not Path(body.folder).exists():
        raise HTTPException(status_code=400, detail="La carpeta especificada no existe")
    settings.add_recent_path("series", body.folder)
    job_id = job_manager.submit(_run_scan, body.folder, settings=settings, plex_service=plex_service)
    return {"job_id": job_id}


@router.post("/move", response_model=MoveBatchResult)
def mover(body: MoveRequest, settings=Depends(get_settings), scan_data_manager=Depends(get_scan_data_manager)):
    try:
        mover_a_debug(body.archivo, settings, scan_data_manager)
        return MoveBatchResult(movidos=1, errores=[])
    except Exception as e:
        return MoveBatchResult(movidos=0, errores=[f"{body.archivo}: {e}"])


@router.post("/move-batch", response_model=MoveBatchResult)
def mover_lote(body: MoveBatchRequest, settings=Depends(get_settings), scan_data_manager=Depends(get_scan_data_manager)):
    movidos = 0
    errores: List[str] = []
    for archivo in body.archivos:
        try:
            mover_a_debug(archivo, settings, scan_data_manager)
            movidos += 1
        except Exception as e:
            errores.append(f"{archivo}: {e}")
    return MoveBatchResult(movidos=movidos, errores=errores)


@router.post("/rename", response_model=EpisodeItem)
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
    return EpisodeItem(
        nombre=new_path.name,
        archivo=str(new_path),
        tamaño=0,
        serie="",
        serie_normalizada="",
        temporada=0,
        episodio=0,
        carpeta=str(new_path.parent),
    )


@router.get("/ignored", response_model=IgnoredSeriesList)
def series_ignoradas(settings=Depends(get_settings)):
    return IgnoredSeriesList(claves=settings.get_ignored_series())


@router.post("/ignore", response_model=IgnoredSeriesList)
def ignorar_serie(body: IgnoreSeriesRequest, settings=Depends(get_settings)):
    settings.add_ignored_series(body.clave)
    return series_ignoradas(settings)


@router.delete("/ignore/{clave}", response_model=IgnoredSeriesList)
def quitar_serie_ignorada(clave: str, settings=Depends(get_settings)):
    settings.remove_ignored_series(clave)
    return series_ignoradas(settings)


@router.post("/save")
def guardar(body: SaveRequest, scan_data_manager=Depends(get_scan_data_manager)):
    if not body.duplicados and not body.huerfanos and not body.series_sin_indexar:
        raise HTTPException(status_code=400, detail="No hay resultados de series para guardar")

    items = (
        [{"tipo": "duplicado", "grupo": [ep.model_dump() for ep in grupo]} for grupo in body.duplicados]
        + [{"tipo": "huerfano", "episodio": ep.model_dump()} for ep in body.huerfanos]
        + [{"tipo": "serie_sin_indexar", "serie": s.model_dump()} for s in body.series_sin_indexar]
    )
    file_path = scan_data_manager.save_scan_data(pairs_data=items, scan_path=body.folder, kind="series")
    return {"file_path": file_path}


@router.get("/saved", response_model=List[SavedScan])
def listar_guardados(scan_data_manager=Depends(get_scan_data_manager)):
    scans = scan_data_manager.get_available_scans(kind="series")
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
    items = scan_data.get("pairs_data", [])

    def vivos(episodios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [e for e in episodios if e.get("archivo") and Path(e["archivo"]).exists()]

    total_guardado = 0
    total_caidos = 0

    duplicados = []
    for it in items:
        if it.get("tipo") != "duplicado":
            continue
        grupo = it.get("grupo", [])
        total_guardado += len(grupo)
        vivos_grupo = vivos(grupo)
        total_caidos += len(grupo) - len(vivos_grupo)
        if len(vivos_grupo) > 1:
            duplicados.append(vivos_grupo)

    huerfanos = []
    for it in items:
        if it.get("tipo") != "huerfano":
            continue
        total_guardado += 1
        ep = it.get("episodio", {})
        if ep.get("archivo") and Path(ep["archivo"]).exists():
            huerfanos.append(ep)
        else:
            total_caidos += 1

    series_sin_indexar = []
    for it in items:
        if it.get("tipo") != "serie_sin_indexar":
            continue
        serie = it.get("serie", {})
        episodios = serie.get("episodios", [])
        total_guardado += len(episodios)
        vivos_serie = vivos(episodios)
        total_caidos += len(episodios) - len(vivos_serie)
        if vivos_serie:
            series_sin_indexar.append({**serie, "episodios": vivos_serie})

    return LoadResult(
        duplicados=duplicados,
        huerfanos=huerfanos,
        series_sin_indexar=series_sin_indexar,
        total_guardado=total_guardado,
        total_caidos=total_caidos,
    )
