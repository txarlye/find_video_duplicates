#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estado de jobs por HTTP (snapshot/fallback) y WebSocket (tiempo real)"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from src.api.jobs import job_manager

router = APIRouter(tags=["jobs"])


@router.get("/api/jobs/{job_id}")
def obtener_job(job_id: str):
    state = job_manager.get(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return state.to_dict()


@router.post("/api/jobs/{job_id}/cancel")
def cancelar_job(job_id: str):
    job_manager.cancel(job_id)
    return {"ok": True}


@router.websocket("/ws/jobs/{job_id}")
async def ws_job(websocket: WebSocket, job_id: str):
    await websocket.accept()

    state = job_manager.get(job_id)
    if not state:
        await websocket.close(code=4004)
        return

    await websocket.send_json(state.to_dict())
    if state.status in ("done", "error", "cancelled"):
        await websocket.close()
        return

    queue = job_manager.subscribe(job_id)
    try:
        while True:
            nuevo_estado = await queue.get()
            await websocket.send_json(nuevo_estado.to_dict())
            if nuevo_estado.status in ("done", "error", "cancelled"):
                # Cierre explícito: sin esto, el cliente ve la conexión
                # cortarse sin frame de cierre (p.ej. websockets de Python
                # lo trata como ConnectionClosedError) en vez de un cierre
                # limpio — solo se veía en jobs que tardan más que el
                # tiempo de conexión del WS (con el resultado ya listo al
                # conectar, el otro camino de arriba sí cerraba bien).
                await websocket.close()
                break
    except WebSocketDisconnect:
        pass
    finally:
        job_manager.unsubscribe(job_id, queue)
