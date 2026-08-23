#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Basura/Purgatorio — puerto de `_render_trash_interface` /
`_render_trash_table` / `_restore_from_trash` de
src/app/streamlit_manager.py (línea 4458) a la API. Misma lógica de
negocio, sin ningún cambio: solo lectura del filesystem + los métodos
de ScanDataManager ya existentes para el registro de origen de cada
archivo movido a la papelera.
"""

import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_settings, get_scan_data_manager
from src.api.schemas.trash import (
    TrashItem,
    TrashListResponse,
    LibrarySizeUpdate,
    RestoreRequest,
    RestoreResult,
)
from src.utils.series_detector import SeriesDetector

router = APIRouter(prefix="/api/trash", tags=["trash"])


@router.get("", response_model=TrashListResponse)
def listar_basura(settings=Depends(get_settings), scan_data_manager=Depends(get_scan_data_manager)):
    debug_folder = settings.get_debug_folder()
    if not debug_folder:
        raise HTTPException(status_code=409, detail="No hay carpeta de debug/purgatorio configurada")

    debug_path = Path(debug_folder)
    library_size_gb = float(settings.get_library_size_gb())

    if not debug_path.exists():
        return TrashListResponse(
            debug_folder=str(debug_path),
            exists=False,
            total_files=0,
            total_gb=0.0,
            library_size_gb=library_size_gb,
            percent_used=None,
            peliculas=[],
            episodios=[],
        )

    try:
        archivos = [f for f in debug_path.rglob("*") if f.is_file()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo la carpeta de purgatorio: {e}")

    origenes = scan_data_manager.get_trash_origins()

    episodios: List[TrashItem] = []
    peliculas: List[TrashItem] = []
    tamaño_total = 0

    entradas = []
    for f in archivos:
        try:
            tamaño = f.stat().st_size
        except OSError:
            continue
        tamaño_total += tamaño
        entradas.append((f, tamaño))

    entradas.sort(key=lambda x: x[1], reverse=True)

    for f, tamaño in entradas:
        item = TrashItem(
            nombre=f.name,
            gb=round(tamaño / (1024 ** 3), 2),
            ruta=str(f),
            origen=origenes.get(str(f)),
        )
        if SeriesDetector.PATRON_SXXEXX.search(f.name) or SeriesDetector.PATRON_NXNN.search(f.name):
            episodios.append(item)
        else:
            peliculas.append(item)

    tamaño_gb = tamaño_total / (1024 ** 3)
    percent_used = min(tamaño_gb / library_size_gb, 1.0) if library_size_gb > 0 else None

    return TrashListResponse(
        debug_folder=str(debug_path),
        exists=True,
        total_files=len(archivos),
        total_gb=round(tamaño_gb, 2),
        library_size_gb=library_size_gb,
        percent_used=percent_used,
        peliculas=peliculas,
        episodios=episodios,
    )


@router.put("/library-size")
def actualizar_tamaño_biblioteca(body: LibrarySizeUpdate, settings=Depends(get_settings)):
    settings.set_library_size_gb(body.library_size_gb)
    return {"library_size_gb": body.library_size_gb}


@router.post("/restore", response_model=RestoreResult)
def restaurar(body: RestoreRequest, scan_data_manager=Depends(get_scan_data_manager)):
    """Devuelve archivos seleccionados de la papelera a su ruta original registrada"""
    origenes = scan_data_manager.get_trash_origins()
    restaurados, sin_origen, fallidos = [], [], []

    for ruta in body.rutas:
        origen = origenes.get(ruta)
        nombre = Path(ruta).name

        if not origen:
            sin_origen.append(nombre)
            continue

        try:
            origen_path = Path(origen)
            origen_path.parent.mkdir(parents=True, exist_ok=True)

            destino_final = origen_path
            contador = 1
            while destino_final.exists():
                destino_final = origen_path.parent / f"{origen_path.stem}_restaurado_{contador}{origen_path.suffix}"
                contador += 1

            shutil.move(ruta, str(destino_final))
            scan_data_manager.forget_trash_move(ruta)
            restaurados.append(nombre)
        except Exception as e:
            fallidos.append(f"{nombre}: {e}")

    return RestoreResult(restaurados=restaurados, sin_origen=sin_origen, fallidos=fallidos)
