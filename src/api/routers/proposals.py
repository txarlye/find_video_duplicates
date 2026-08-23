#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router de Propuestas — puerto de _render_proposals_interface /
_generar_propuestas_ahora / _aplicar_propuestas_*_lote /
_descartar_propuestas_*_lote de streamlit_manager.py (línea 4138).

Genera con ProposalsService (ya puro, sin cambios) contra las carpetas
configuradas en Programación. La API no guarda sesión entre peticiones
— aplicar/descartar recibe de vuelta los objetos que el cliente ya
obtuvo de /generate, en vez de volver a generarlos (evita repetir
llamadas a la IA y cualquier deriva entre lo que ves y lo que aplicas).
"""

import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_settings, get_proposals_service, get_plex_refresh_service, get_scan_data_manager
from src.api.schemas.proposals import (
    ProposalsResponse,
    ApplyHuerfanosRequest,
    ApplyDuplicadosRequest,
    ClavesRequest,
    BatchResult,
    DismissedProposals,
    ArchivoRequest,
    ClaveRequest,
)

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


def _mover_a_debug(ruta: str, settings, scan_data_manager) -> None:
    """Misma lógica que _mover_archivo_a_debug de streamlit_manager.py, sin llamadas a st.*"""
    origen = Path(ruta)
    if not origen.exists():
        raise FileNotFoundError(f"El archivo ya no existe: {ruta}")

    if settings.get_debug_enabled():
        debug_path = Path(settings.get_debug_folder())
        debug_path.mkdir(parents=True, exist_ok=True)
        destino = debug_path / origen.name
        contador = 1
        while destino.exists():
            destino = debug_path / f"{origen.stem}_{contador}{origen.suffix}"
            contador += 1
        shutil.move(str(origen), str(destino))
        scan_data_manager.record_trash_move(str(destino), str(origen))
    else:
        os.remove(str(origen))


def _refrescar_plex(settings, plex_refresh_service) -> None:
    """Mismo criterio best-effort que _refresh_plex_after_rename — nunca rompe la petición si falla"""
    try:
        if not plex_refresh_service.is_configured():
            return
        movies_library = settings.get_plex_movies_library()
        tv_library = settings.get_plex_tv_shows_library()
        if movies_library:
            plex_refresh_service.refresh_library_by_name(movies_library)
        if tv_library and tv_library != movies_library:
            plex_refresh_service.refresh_library_by_name(tv_library)
    except Exception:
        pass


@router.post("/generate", response_model=ProposalsResponse)
def generar_propuestas(settings=Depends(get_settings), proposals_service=Depends(get_proposals_service)):
    carpetas = settings.get_automation_movie_folders()
    if not carpetas:
        raise HTTPException(
            status_code=409,
            detail='Configura al menos una carpeta en "Configuración → Programación" primero',
        )
    huerfanos = proposals_service.generar_propuestas_huerfanos(carpetas)
    duplicados = proposals_service.generar_propuestas_duplicados(carpetas)
    return ProposalsResponse(huerfanos=huerfanos, duplicados=duplicados)


@router.post("/huerfanos/apply", response_model=BatchResult)
def aplicar_huerfanos(
    body: ApplyHuerfanosRequest,
    settings=Depends(get_settings),
    plex_refresh_service=Depends(get_plex_refresh_service),
):
    aplicados = 0
    errores: List[str] = []
    for p in body.items:
        try:
            old_path = Path(p.archivo)
            new_path = old_path.parent / f"{p.nombre_sugerido}{old_path.suffix}"
            os.rename(str(old_path), str(new_path))
            aplicados += 1
        except Exception as e:
            errores.append(f"{p.archivo}: {e}")

    if aplicados:
        _refrescar_plex(settings, plex_refresh_service)

    return BatchResult(aplicados=aplicados, errores=errores)


@router.post("/huerfanos/dismiss")
def descartar_huerfanos(body: ClavesRequest, settings=Depends(get_settings)):
    for clave in body.claves:
        settings.add_dismissed_orphan_proposal(clave)
    return {"ok": True}


@router.post("/duplicados/apply", response_model=BatchResult)
def aplicar_duplicados(
    body: ApplyDuplicadosRequest,
    settings=Depends(get_settings),
    scan_data_manager=Depends(get_scan_data_manager),
):
    aplicados = 0
    errores: List[str] = []
    for p in body.items:
        try:
            _mover_a_debug(p.archivo_a_borrar, settings, scan_data_manager)
            aplicados += 1
        except Exception as e:
            errores.append(f"{p.archivo_a_borrar}: {e}")

    return BatchResult(aplicados=aplicados, errores=errores)


@router.post("/duplicados/dismiss")
def descartar_duplicados(body: ClavesRequest, settings=Depends(get_settings)):
    for clave in body.claves:
        settings.add_dismissed_duplicate_proposal(clave)
    return {"ok": True}


@router.get("/dismissed", response_model=DismissedProposals)
def obtener_descartadas(settings=Depends(get_settings)):
    return DismissedProposals(
        huerfanos=settings.get_dismissed_orphan_proposals(),
        duplicados=settings.get_dismissed_duplicate_proposals(),
    )


@router.post("/dismissed/huerfanos/remove")
def deshacer_descarte_huerfano(body: ArchivoRequest, settings=Depends(get_settings)):
    settings.remove_dismissed_orphan_proposal(body.archivo)
    return {"ok": True}


@router.post("/dismissed/duplicados/remove")
def deshacer_descarte_duplicado(body: ClaveRequest, settings=Depends(get_settings)):
    settings.remove_dismissed_duplicate_proposal(body.clave)
    return {"ok": True}
