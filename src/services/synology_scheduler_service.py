#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crea la tarea programada de Propuestas directamente en el Planificador
de tareas de DSM (Synology), vía la API web de DSM — la misma que usa
la propia interfaz de Control Panel → Planificador de tareas, para
evitar que el usuario tenga que crearla a mano.

Esta API (SYNO.Core.TaskScheduler) NO es pública ni está documentada
oficialmente por Synology; lo de aquí está basado en lo que la
comunidad ha reconstruido por ingeniería inversa y puede variar entre
versiones de DSM. Si algo falla, el código/mensaje que devuelve DSM se
propaga tal cual (ver SynologySchedulerError) — no hay forma de
probarlo en seco, hace falta contrastarlo contra un DSM real.

Requiere un usuario DSM dedicado y restringido (grupo administrators,
requisito de la propia API para gestionar tareas) — nunca la cuenta de
administrador principal: es la única credencial de esta app con
alcance de administrador sobre el NAS. Se configura con
SYNOLOGY_HOST/SYNOLOGY_PORT/SYNOLOGY_USER/SYNOLOGY_PASSWORD en .env,
nunca en config.json.
"""

import json
import logging
from typing import Any, Dict

import requests
import urllib3

from src.settings.settings import settings

# Certificado autofirmado de DSM en LAN — esperado e intencional aquí
# (uso restringido a la propia red local / Tailscale, nunca a internet).
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TASK_NAME = "Detector de Duplicados - Propuestas"
DOCKER_COMMAND = "docker exec find-video-duplicates python scheduled_scan.py"


class SynologySchedulerError(Exception):
    """Error devuelto por la API de DSM — mensaje ya pensado para mostrar tal cual al usuario"""


class SynologySchedulerService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        return bool(
            settings.get_synology_host()
            and settings.get_synology_user()
            and settings.get_synology_password()
        )

    def _base_url(self) -> str:
        host = settings.get_synology_host()
        port = settings.get_synology_port()
        return f"https://{host}:{port}/webapi"

    def _login(self) -> str:
        if not self.is_configured():
            raise SynologySchedulerError(
                "Faltan SYNOLOGY_HOST/SYNOLOGY_USER/SYNOLOGY_PASSWORD en .env"
            )
        try:
            resp = requests.get(
                f"{self._base_url()}/auth.cgi",
                params={
                    "api": "SYNO.API.Auth",
                    "version": "6",
                    "method": "login",
                    "account": settings.get_synology_user(),
                    "passwd": settings.get_synology_password(),
                    "session": "TaskScheduler",
                    "format": "sid",
                },
                timeout=15,
                verify=False,
            )
            data = resp.json()
        except Exception as e:
            raise SynologySchedulerError(f"No se pudo conectar con DSM en {self._base_url()}: {e}")

        if not data.get("success"):
            codigo = data.get("error", {}).get("code")
            raise SynologySchedulerError(
                f"Login en DSM falló (código {codigo}) — revisa SYNOLOGY_USER/SYNOLOGY_PASSWORD, "
                "que el usuario esté en el grupo administrators, y que no tenga verificación en dos "
                "pasos activada."
            )
        return data["data"]["sid"]

    def _logout(self, sid: str) -> None:
        try:
            requests.get(
                f"{self._base_url()}/auth.cgi",
                params={"api": "SYNO.API.Auth", "version": "6", "method": "logout", "session": "TaskScheduler", "_sid": sid},
                timeout=10,
                verify=False,
            )
        except Exception:
            pass

    def test_connection(self) -> Dict[str, Any]:
        """Solo inicia y cierra sesión — confirma que las credenciales funcionan, sin tocar nada"""
        sid = self._login()
        self._logout(sid)
        return {"ok": True}

    def crear_tarea_propuestas(self, hora: str) -> Dict[str, Any]:
        """
        Crea (reemplazando si ya existía) la tarea programada que
        dispara scheduled_scan.py dentro del contenedor a la hora
        indicada ("HH:MM", cada día).
        """
        try:
            hh, mm = hora.split(":")
            hora_int, minuto_int = int(hh), int(mm)
            if not (0 <= hora_int < 24 and 0 <= minuto_int < 60):
                raise ValueError
        except (ValueError, AttributeError):
            raise SynologySchedulerError(f"Hora no válida: {hora!r} (se espera HH:MM)")

        sid = self._login()
        try:
            self._eliminar_tarea_existente(sid)

            schedule = {
                "date_type": 0,  # 0 = repetir cada día de la semana indicada
                "week_day": "0,1,2,3,4,5,6",
                "hour": hora_int,
                "minute": minuto_int,
                "repeat_date": 0,
                "repeat_hour": 0,
                "repeat_hour_store_config": False,
                "repeat_min": 0,
                "repeat_min_store_config": False,
                "month": "",
                "year": "",
                "monthly_week": [],
            }

            resp = requests.get(
                f"{self._base_url()}/entry.cgi",
                params={
                    "api": "SYNO.Core.TaskScheduler",
                    "version": "1",
                    "method": "create",
                    "_sid": sid,
                    "name": TASK_NAME,
                    "real_owner": "root",
                    "owner": "root",
                    "service_type": "script",
                    "enable": "true",
                    "notify_enable": "false",
                    "notify_only_on_error": "false",
                    "script": DOCKER_COMMAND,
                    "schedule": json.dumps(schedule),
                },
                timeout=20,
                verify=False,
            )
            data = resp.json()
            if not data.get("success"):
                codigo = data.get("error", {}).get("code")
                raise SynologySchedulerError(
                    f"DSM rechazó la creación de la tarea (código {codigo}). Respuesta completa: {data}"
                )
            return {"ok": True, "detalle": data.get("data")}
        finally:
            self._logout(sid)

    def _eliminar_tarea_existente(self, sid: str) -> None:
        """
        Best-effort: busca una tarea con nuestro nombre y la borra antes
        de recrearla, para no ir acumulando duplicadas cada vez que se
        pulsa el botón. Si esto falla (p.ej. porque el "list" tiene un
        formato distinto al esperado), se sigue adelante igualmente con
        la creación — más vale una tarea duplicada que bloquear todo el
        flujo por un paso que no es crítico.
        """
        try:
            resp = requests.get(
                f"{self._base_url()}/entry.cgi",
                params={"api": "SYNO.Core.TaskScheduler", "version": "1", "method": "list", "_sid": sid},
                timeout=15,
                verify=False,
            )
            data = resp.json()
            tareas = data.get("data", {}).get("tasks", []) if data.get("success") else []
            existente = next((t for t in tareas if t.get("name") == TASK_NAME), None)
            if existente and existente.get("id") is not None:
                requests.get(
                    f"{self._base_url()}/entry.cgi",
                    params={
                        "api": "SYNO.Core.TaskScheduler",
                        "version": "1",
                        "method": "delete",
                        "_sid": sid,
                        "id": existente["id"],
                    },
                    timeout=15,
                    verify=False,
                )
        except Exception as e:
            self.logger.warning(f"No se pudo comprobar/borrar la tarea existente antes de recrearla: {e}")
