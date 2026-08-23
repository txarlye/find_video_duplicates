#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App FastAPI — sustituye gradualmente a la UI de Streamlit
(src/app/streamlit_manager.py), pantalla a pantalla. Mientras dura la
migración, este proceso corre EN PARALELO a Streamlit (puerto distinto,
ver docker/Dockerfile) — no hay ningún cambio en src/services que
rompa la app vieja.

Sirve la API bajo /api/*, WebSockets bajo /ws/* (cuando existan), y el
build estático de frontend/ en la raíz "/" (si existe — en desarrollo
sin build todavía, simplemente no se monta y solo responde la API).
"""

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.jobs import job_manager
from src.api.routers import trash as trash_router
from src.api.routers import settings as settings_router
from src.api.routers import proposals as proposals_router
from src.api.routers import orphans as orphans_router
from src.api.routers import series as series_router
from src.api.routers import telegram as telegram_router
from src.api.routers import duplicates as duplicates_router
from src.api.routers import jobs as jobs_router
from src.api.routers import video as video_router
from src.services.plex_service import PlexService
from src.services.ai_naming_service import AINamingService
from src.services.proposals_service import ProposalsService
from src.services.email_service import EmailService
from src.services.scan_scheduler import ensure_scheduler_running

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Detector de Duplicados API", version="0.1.0")

# CORS solo hace falta en desarrollo (Vite en :5173 llamando a la API en
# :8000) — en producción todo se sirve desde el mismo origen (ver mount
# de estáticos más abajo) y estos orígenes no se usan.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trash_router.router)
app.include_router(settings_router.router)
app.include_router(proposals_router.router)
app.include_router(orphans_router.router)
app.include_router(series_router.router)
app.include_router(telegram_router.router)
app.include_router(duplicates_router.router)
app.include_router(jobs_router.router)
app.include_router(video_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def _iniciar_programador_propuestas():
    """
    Mismo arranque que StreamlitAppManager.__init__ — es seguro que los
    dos procesos (Streamlit + esta API) lo llamen a la vez durante la
    convivencia: el guardado de "ya se ejecutó hoy" vive en config.json,
    no en memoria de un solo proceso (ver scan_scheduler.py).
    """
    plex_service = PlexService()
    ai_naming_service = AINamingService()
    proposals_service = ProposalsService(plex_service, ai_naming_service)
    email_service = EmailService()
    ensure_scheduler_running(proposals_service, email_service)


@app.on_event("startup")
async def _conectar_job_manager_al_loop():
    """El JobManager necesita el loop de asyncio activo para poder empujar progreso por WebSocket desde los hilos del pool"""
    job_manager.set_loop(asyncio.get_running_loop())


_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    logger.info(f"Sirviendo frontend estático desde {_frontend_dist}")
else:
    logger.info("frontend/dist no existe todavía — solo la API está activa (npm run build para servir la UI)")
