#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Series"""

from typing import List, Optional
from pydantic import BaseModel


class EpisodeItem(BaseModel):
    nombre: str
    archivo: str
    tamaño: int = 0
    serie: str
    serie_normalizada: str
    temporada: int
    episodio: int
    carpeta: str


class SeriesGroup(BaseModel):
    clave: str
    serie: str
    episodios: List[EpisodeItem]
    tamaño: int = 0


class ScanRequest(BaseModel):
    folder: str


class ScanResult(BaseModel):
    duplicados: List[List[EpisodeItem]]
    huerfanos: List[EpisodeItem]
    series_sin_indexar: List[SeriesGroup]
    total_episodios: int
    sin_reconocer: int


class MoveRequest(BaseModel):
    archivo: str


class MoveBatchRequest(BaseModel):
    archivos: List[str]


class MoveBatchResult(BaseModel):
    movidos: int
    errores: List[str]


class RenameRequest(BaseModel):
    archivo: str
    nuevo_nombre: str


class IgnoreSeriesRequest(BaseModel):
    clave: str


class IgnoredSeriesList(BaseModel):
    claves: List[str]


class SavedScan(BaseModel):
    file_path: str
    scan_path: str
    scan_date: str
    total_pairs: int


class SaveRequest(BaseModel):
    folder: str
    duplicados: List[List[EpisodeItem]]
    huerfanos: List[EpisodeItem]
    series_sin_indexar: List[SeriesGroup]


class LoadRequest(BaseModel):
    file_path: str


class LoadResult(BaseModel):
    duplicados: List[List[EpisodeItem]]
    huerfanos: List[EpisodeItem]
    series_sin_indexar: List[SeriesGroup]
    total_guardado: int
    total_caidos: int
