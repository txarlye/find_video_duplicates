#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helpers compartidos entre routers — versiones sin Streamlit de métodos
que en streamlit_manager.py estaban acoplados a `st.*` (_mover_archivo_a_debug,
_refresh_plex_after_rename). Mismo comportamiento, solo sin pintar UI.
"""

import os
import shutil
from pathlib import Path


def mover_a_debug(ruta: str, settings, scan_data_manager) -> None:
    """Mueve un archivo a la carpeta de debug configurada (o lo borra si el modo debug está desactivado)"""
    origen = Path(ruta)
    if not origen.exists():
        raise FileNotFoundError(f"El archivo ya no existe: {ruta}")

    if settings.get_debug_enabled():
        carpeta_debug = settings.get_debug_folder()
        if not carpeta_debug or not carpeta_debug.strip():
            # Sin esto, Path("") se resuelve al directorio de trabajo
            # actual (/app dentro de Docker) — el archivo "se mueve" en
            # silencio a un sitio sin ningún volumen montado detrás, y
            # se pierde para siempre en cuanto se recrea el contenedor.
            # Mejor un error claro que una pérdida de datos silenciosa.
            raise ValueError(
                "No hay carpeta de debug configurada — ve a ⚙️ Configuración y "
                "rellena la carpeta de debug/papelera antes de borrar/mover nada"
            )

        debug_path = Path(carpeta_debug)
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


def refrescar_plex(settings, plex_refresh_service) -> None:
    """Refresca las bibliotecas de Plex tras un renombrado/movimiento — best-effort, nunca lanza"""
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
