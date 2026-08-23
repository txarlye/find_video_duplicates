#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Huérfanos"""

from typing import List, Optional
from pydantic import BaseModel


class OrphanItem(BaseModel):
    nombre: str
    archivo: str
    tamaño: int = 0
    renombrado: bool = False


class ScanRequest(BaseModel):
    folder: str


class SuggestRequest(BaseModel):
    nombre: str


class SuggestResponse(BaseModel):
    sugerido: Optional[str] = None


class SuggestBatchItem(BaseModel):
    archivo: str
    nombre: str


class SuggestBatchRequest(BaseModel):
    items: List[SuggestBatchItem]
    scope: Optional[int] = None  # None = todos


class RenameRequest(BaseModel):
    archivo: str
    nuevo_nombre: str


class RenameBatchItem(BaseModel):
    archivo: str
    nuevo_nombre: str


class RenameBatchRequest(BaseModel):
    items: List[RenameBatchItem]


class RenameBatchResult(BaseModel):
    renombrados: int
    errores: List[str]


class SavedScan(BaseModel):
    file_path: str
    scan_path: str
    scan_date: str
    total_pairs: int


class SaveRequest(BaseModel):
    folder: str
    items: List[OrphanItem]


class LoadRequest(BaseModel):
    file_path: str


class LoadResult(BaseModel):
    items: List[OrphanItem]
    total_guardados: int
    no_existentes: int
    ya_renombrados: int
