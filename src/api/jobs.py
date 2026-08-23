#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de jobs en segundo plano con progreso en tiempo real por
WebSocket — sustituye el patrón de Streamlit (job trozeado en
st.session_state, reejecutado a sí mismo con st.rerun entre tandas
pequeñas para que el botón "Detener" pueda reaccionar) por un job de
verdad: corre en un hilo aparte desde el primer momento, y el progreso
se empuja al cliente en vez de que el cliente tenga que refrescar.

Todo en memoria — sin Redis ni base de datos: esta es una app de un
solo usuario en un único contenedor, no hace falta más.
"""

import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class JobState:
    id: str
    status: str = "running"  # running | done | error | cancelled
    percent: float = 0.0
    message: str = ""
    result: Any = None
    error: Optional[str] = None
    # Últimos eventos "item" emitidos (ej. una sugerencia de IA recién
    # lista) — el cliente WS los consume y los añade a su lista local,
    # sin tener que esperar a que el job entero termine para ver algo.
    item: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JobManager:
    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: Dict[str, JobState] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._cancel_flags: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def submit(self, fn: Callable, *args, **kwargs) -> str:
        """
        Lanza fn(*args, progress_cb=..., is_cancelled=..., **kwargs) en
        un hilo del pool. fn debe devolver el resultado final (se
        publica como job.result al terminar).
        """
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = JobState(id=job_id)
            self._subscribers[job_id] = []
            self._cancel_flags[job_id] = threading.Event()

        def progress_cb(percent: float, message: str = "", item: Optional[Dict[str, Any]] = None):
            self._update(job_id, percent=percent, message=message, item=item)

        def is_cancelled() -> bool:
            return self._cancel_flags[job_id].is_set()

        def runner():
            try:
                result = fn(*args, progress_cb=progress_cb, is_cancelled=is_cancelled, **kwargs)
                if is_cancelled():
                    self._update(job_id, status="cancelled", message="Detenido", result=result, item=None)
                else:
                    self._update(job_id, status="done", percent=100, result=result, item=None)
            except Exception as e:
                logger.error(f"Error en job {job_id}: {e}")
                self._update(job_id, status="error", error=str(e), item=None)

        self._executor.submit(runner)
        return job_id

    def cancel(self, job_id: str) -> None:
        flag = self._cancel_flags.get(job_id)
        if flag:
            flag.set()

    def get(self, job_id: str) -> Optional[JobState]:
        return self._jobs.get(job_id)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._subscribers.setdefault(job_id, []).append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        with self._lock:
            subs = self._subscribers.get(job_id)
            if subs and q in subs:
                subs.remove(q)

    def _update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            for k, v in kwargs.items():
                setattr(state, k, v)
            subs = list(self._subscribers.get(job_id, []))

        if not self._loop:
            return
        for q in subs:
            self._loop.call_soon_threadsafe(q.put_nowait, state)


job_manager = JobManager()
