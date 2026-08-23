#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas Pydantic para el recurso Propuestas"""

from typing import List
from pydantic import BaseModel


class HuerfanoProposal(BaseModel):
    clave: str
    archivo: str
    nombre_actual: str
    nombre_sugerido: str
    tamaño: int = 0


class DuplicadoProposal(BaseModel):
    clave: str
    archivo_a_borrar: str
    archivo_a_conservar: str
    nombre_a_borrar: str
    nombre_a_conservar: str
    tamaño_a_borrar: int = 0
    tamaño_a_conservar: int = 0
    motivo: str = ""


class ProposalsResponse(BaseModel):
    huerfanos: List[HuerfanoProposal]
    duplicados: List[DuplicadoProposal]


class ApplyHuerfanosRequest(BaseModel):
    items: List[HuerfanoProposal]


class ApplyDuplicadosRequest(BaseModel):
    items: List[DuplicadoProposal]


class ClavesRequest(BaseModel):
    claves: List[str]


class BatchResult(BaseModel):
    aplicados: int
    errores: List[str]


class DismissedProposals(BaseModel):
    huerfanos: List[str]
    duplicados: List[str]


class ArchivoRequest(BaseModel):
    archivo: str


class ClaveRequest(BaseModel):
    clave: str
