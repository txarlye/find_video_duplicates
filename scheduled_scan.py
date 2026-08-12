#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrypoint sin interfaz para el Planificador de tareas del Synology (o
cron/Task Scheduler en cualquier otro sistema). Genera las propuestas de
huérfanos/duplicados configuradas en Automatización y, si hay alguna
propuesta NUEVA desde la última vez (no solo pendiente de revisar, sino
que no se avisó ya de ella), manda un email con un enlace a la app.

No mueve, renombra ni borra nada — solo detecta y avisa. Aplicar o
descartar cada propuesta se sigue haciendo a mano desde la pantalla
🤖 Propuestas.

Uso (Planificador de tareas > Tarea programada > Script definido por el
usuario), o en Docker: docker exec find-video-duplicates python scheduled_scan.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.settings.settings import settings
from src.services.plex_service import PlexService
from src.services.ai_naming_service import AINamingService
from src.services.proposals_service import ProposalsService
from src.services.email_service import EmailService


def main():
    if not settings.get_automation_enabled():
        print("ℹ️ Automatización desactivada (Utilidades → 🤖 Propuestas → Configurar). Nada que hacer.")
        return

    carpetas = settings.get_automation_movie_folders()
    if not carpetas:
        print("ℹ️ No hay carpetas configuradas para el escaneo programado. Nada que hacer.")
        return

    plex_service = PlexService()
    ai_naming_service = AINamingService()
    proposals_service = ProposalsService(plex_service, ai_naming_service)
    email_service = EmailService()

    print(f"🔍 Analizando {len(carpetas)} carpeta(s)...")
    huerfanos = proposals_service.generar_propuestas_huerfanos(carpetas)
    duplicados = proposals_service.generar_propuestas_duplicados(carpetas)
    print(f"✅ {len(huerfanos)} propuesta(s) de nombre, {len(duplicados)} propuesta(s) de borrado pendientes")

    claves_actuales = {p['clave'] for p in huerfanos} | {p['clave'] for p in duplicados}
    claves_notificadas = set(settings.get_notified_proposal_keys())
    claves_nuevas = claves_actuales - claves_notificadas

    if not claves_nuevas:
        print("ℹ️ No hay propuestas nuevas desde el último aviso. No se envía email.")
        return

    nuevas_huerfanos = sum(1 for p in huerfanos if p['clave'] in claves_nuevas)
    nuevas_duplicados = sum(1 for p in duplicados if p['clave'] in claves_nuevas)

    if not email_service.is_configured():
        print(
            "⚠️ Hay propuestas nuevas pero el email no está configurado "
            "(SMTP_USER/SMTP_PASSWORD en .env + destinatario en Configurar automatización)."
        )
    else:
        enviado = email_service.enviar_aviso_propuestas(nuevas_huerfanos, nuevas_duplicados)
        print("📧 Email enviado." if enviado else "❌ Error enviando el email (ver log).")

    # Se marcan como notificadas independientemente de si el email se ha
    # podido enviar o no: si falló por config, reintentar cada noche con
    # las mismas propuestas no arregla el problema, solo lo esconde.
    settings.set_notified_proposal_keys(list(claves_actuales))


if __name__ == "__main__":
    main()
