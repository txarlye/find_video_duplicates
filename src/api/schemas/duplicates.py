#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Duplicados"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    nombre: str
    ruta: str
    tamaño: int = 0
    duracion: float = 0
    existe: bool = True
    creado: Optional[str] = None


class DuplicatePair(BaseModel):
    clave: str
    peli1: FileInfo
    peli2: FileInfo


class ScanRequest(BaseModel):
    folder: str


class ScanResult(BaseModel):
    pares: List[DuplicatePair]
    total_peliculas: int


class PlexMetadataRequest(BaseModel):
    ruta1: str
    ruta2: str


class PlexMovieMetadata(BaseModel):
    encontrado: bool
    datos: Optional[Dict[str, Any]] = None


class PlexMetadataResponse(BaseModel):
    file1: PlexMovieMetadata
    file2: PlexMovieMetadata
    es_duplicado_plex: bool
    duracion_compatible: Optional[bool] = None
    duracion_mensaje: Optional[str] = None


class DeleteRequest(BaseModel):
    archivos: List[str]


class DeleteResult(BaseModel):
    movidos: int
    errores: List[str]


class BulkMoveRequest(BaseModel):
    archivos: List[str]
    destino: str


class BulkMoveResult(BaseModel):
    movidos: int
    errores: List[str]


class SavedScan(BaseModel):
    file_path: str
    scan_path: str
    scan_date: str
    total_pairs: int


class SaveRequest(BaseModel):
    folder: str
    pares: List[DuplicatePair]


class LoadRequest(BaseModel):
    file_path: str


class LoadResult(BaseModel):
    pares: List[DuplicatePair]
    total_guardado: int
    no_existentes: int


class EditionSuggestionsResponse(BaseModel):
    sugerencias: List[str]


class CreateEditionRequest(BaseModel):
    archivo: str
    movie_title: str
    edition_name: str
    create_subfolder: bool = False


class CreateEditionResult(BaseModel):
    ok: bool
    nueva_ruta: Optional[str] = None
    detail: Optional[str] = None
