#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrypoint sin interfaz para disparar el ciclo de Propuestas desde
fuera de la app — Planificador de tareas del Synology, cron, etc.

Ya no es imprescindible: desde que existe el programador interno
(Configuración → 📅 Programación, con hora configurable), la propia app
dispara el mismo ciclo sola mientras el contenedor siga vivo. Este
script sigue siendo útil si prefieres controlar el "cuándo" desde fuera
del contenedor en vez de depender de que no se reinicie justo a la hora
programada.

No mueve, renombra ni borra nada — solo detecta y avisa. Aplicar o
descartar cada propuesta se sigue haciendo a mano desde la pantalla
🤖 Propuestas.

Uso: docker exec find-video-duplicates python scheduled_scan.py
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
from src.services.scan_scheduler import ejecutar_ciclo_propuestas


def main():
    if not settings.get_automation_enabled():
        print("ℹ️ Automatización desactivada (Configuración → 📅 Programación). Nada que hacer.")
        return

    if not settings.get_automation_movie_folders():
        print("ℹ️ No hay carpetas configuradas para el escaneo programado. Nada que hacer.")
        return

    plex_service = PlexService()
    ai_naming_service = AINamingService()
    proposals_service = ProposalsService(plex_service, ai_naming_service)
    email_service = EmailService()

    print("🔍 Analizando carpetas configuradas...")
    resumen = ejecutar_ciclo_propuestas(proposals_service, email_service)

    print(f"✅ {resumen['huerfanos']} propuesta(s) de nombre, {resumen['duplicados']} propuesta(s) de borrado pendientes")

    if not resumen['nuevas']:
        print("ℹ️ No hay propuestas nuevas desde el último aviso. No se envía email.")
    elif resumen['email_enviado']:
        print(f"📧 Email enviado ({resumen['nuevas']} propuesta(s) nueva(s)).")
    elif email_service.is_configured():
        print("❌ Había propuestas nuevas pero el email falló al enviarse (ver log).")
    else:
        print(
            f"⚠️ Hay {resumen['nuevas']} propuesta(s) nueva(s) pero el email no está configurado "
            "(SMTP_USER/SMTP_PASSWORD en .env + destinatario en Configuración → 📅 Programación)."
        )


if __name__ == "__main__":
    main()
