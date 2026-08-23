#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Basura/Purgatorio"""

from typing import List, Optional
from pydantic import BaseModel


class TrashItem(BaseModel):
    nombre: str
    gb: float
    ruta: str
    origen: Optional[str] = None


class TrashListResponse(BaseModel):
    debug_folder: str
    exists: bool
    total_files: int
    total_gb: float
    library_size_gb: float
    percent_used: Optional[float] = None
    peliculas: List[TrashItem]
    episodios: List[TrashItem]


class LibrarySizeUpdate(BaseModel):
    library_size_gb: float


class RestoreRequest(BaseModel):
    rutas: List[str]


class RestoreResult(BaseModel):
    restaurados: List[str]
    sin_origen: List[str]
    fallidos: List[str]
