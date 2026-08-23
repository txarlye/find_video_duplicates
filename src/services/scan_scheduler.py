#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ciclo de "generar propuestas + avisar por email si hay algo nuevo",
compartido entre scheduled_scan.py (invocado desde fuera, p.ej. el
Planificador de tareas del Synology) y el hilo en segundo plano que la
propia app arranca para disparar el escaneo a la hora configurada en
Configuración → 📅 Programación, sin depender de nada externo al NAS.

El hilo en segundo plano solo tiene sentido mientras el proceso de la
app siga vivo — por eso sigue siendo válido usar el Planificador de
tareas del Synology si prefieres no depender de que el contenedor no
se reinicie justo a la hora programada.
"""

import logging
import threading
import time
from datetime import datetime

from src.settings.settings import settings

logger = logging.getLogger(__name__)

_scheduler_lock = threading.Lock()
_scheduler_started = False


def ejecutar_ciclo_propuestas(proposals_service, email_service) -> dict:
    """
    Genera las propuestas de las carpetas configuradas y, si hay alguna
    NUEVA desde el último aviso, manda el email. Devuelve un resumen
    (para loguear o mostrar en la UI). No hace nada si la automatización
    está desactivada o no hay carpetas configuradas.
    """
    resumen = {'ejecutado': False, 'huerfanos': 0, 'duplicados': 0, 'nuevas': 0, 'email_enviado': False}

    if not settings.get_automation_enabled():
        return resumen

    carpetas = settings.get_automation_movie_folders()
    if not carpetas:
        return resumen

    huerfanos = proposals_service.generar_propuestas_huerfanos(carpetas)
    duplicados = proposals_service.generar_propuestas_duplicados(carpetas)
    resumen.update({'ejecutado': True, 'huerfanos': len(huerfanos), 'duplicados': len(duplicados)})

    claves_actuales = {p['clave'] for p in huerfanos} | {p['clave'] for p in duplicados}
    claves_notificadas = set(settings.get_notified_proposal_keys())
    claves_nuevas = claves_actuales - claves_notificadas
    resumen['nuevas'] = len(claves_nuevas)

    if claves_nuevas:
        nuevas_huerfanos = sum(1 for p in huerfanos if p['clave'] in claves_nuevas)
        nuevas_duplicados = sum(1 for p in duplicados if p['clave'] in claves_nuevas)
        if email_service.is_configured():
            resumen['email_enviado'] = email_service.enviar_aviso_propuestas(nuevas_huerfanos, nuevas_duplicados)
        # Se marca como notificado tanto si el email se ha podido enviar
        # como si no: reintentar cada vez con las mismas propuestas por un
        # fallo de configuración solo escondería el problema, no lo arregla.
        settings.set_notified_proposal_keys(list(claves_actuales))

    return resumen


def ensure_scheduler_running(proposals_service, email_service):
    """
    Arranca el hilo en segundo plano que dispara ejecutar_ciclo_propuestas
    a la hora configurada — pero solo una vez por proceso, con este
    guardado global (el startup de FastAPI podría llamarlo más de una vez
    según el entorno de arranque).
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    hilo = threading.Thread(
        target=_bucle_programador,
        args=(proposals_service, email_service),
        daemon=True,
        name="scan-scheduler",
    )
    hilo.start()
    logger.info("🕐 Programador de propuestas iniciado en segundo plano")


def _bucle_programador(proposals_service, email_service):
    while True:
        try:
            _comprobar_y_ejecutar_si_toca(proposals_service, email_service)
        except Exception as e:
            logger.error(f"Error en el bucle del programador de propuestas: {e}")
        time.sleep(60)


def _comprobar_y_ejecutar_si_toca(proposals_service, email_service):
    if not settings.get_automation_enabled():
        return

    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    if settings.get_automation_last_run_date() == hoy:
        return  # ya se ejecutó hoy

    if ahora.strftime("%H:%M") != settings.get_automation_schedule_time():
        return  # todavía no es la hora configurada

    logger.info("🕐 Hora programada alcanzada — generando propuestas...")
    ejecutar_ciclo_propuestas(proposals_service, email_service)
    settings.set_automation_last_run_date(hoy)
