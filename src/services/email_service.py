#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Envío del aviso por email cuando hay propuestas nuevas (huérfanos con
nombre sugerido, duplicados con una copia recomendada a borrar). Usa
smtplib de la librería estándar — sin dependencias nuevas. Pensado para
Gmail con "contraseña de aplicación" por defecto, pero cualquier SMTP
con STARTTLS sirve cambiando SMTP_HOST/SMTP_PORT en .env.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from src.settings.settings import settings


class EmailService:
    """Envía el aviso de propuestas nuevas por email"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        return bool(
            settings.get_smtp_user()
            and settings.get_smtp_password()
            and settings.get_automation_email_to()
        )

    def enviar_aviso_propuestas(self, n_huerfanos: int, n_duplicados: int) -> bool:
        """
        Envía un email corto avisando de que hay propuestas nuevas, con
        un enlace directo a la pantalla de Propuestas de la app (no un
        informe largo — el detalle se revisa dentro de la app).
        """
        if not self.is_configured():
            self.logger.warning("Email de propuestas no configurado (falta SMTP_USER/SMTP_PASSWORD/email destino)")
            return False

        app_url = settings.get_automation_app_url().rstrip('/')
        enlace = f"{app_url}/?view=propuestas" if app_url else None

        partes = []
        if n_huerfanos:
            partes.append(f"{n_huerfanos} nombre(s) sugerido(s) para huérfanos")
        if n_duplicados:
            partes.append(f"{n_duplicados} duplicado(s) con una copia recomendada a borrar")
        resumen = " y ".join(partes)

        cuerpo = f"Tienes propuestas nuevas: {resumen}.\n"
        if enlace:
            cuerpo += f"\nRevísalas aquí: {enlace}\n"
        cuerpo += "\nNo se ha movido ni renombrado nada todavía — cada propuesta se aplica o descarta a mano desde la app."

        total = n_huerfanos + n_duplicados
        mensaje = MIMEText(cuerpo, "plain", "utf-8")
        mensaje["Subject"] = f"🎬 {total} propuesta(s) nueva(s) — Detector de Duplicados"
        mensaje["From"] = settings.get_smtp_user()
        mensaje["To"] = settings.get_automation_email_to()

        try:
            with smtplib.SMTP(settings.get_smtp_host(), settings.get_smtp_port(), timeout=20) as server:
                server.starttls()
                server.login(settings.get_smtp_user(), settings.get_smtp_password())
                server.send_message(mensaje)
            self.logger.info("Email de propuestas enviado correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error enviando email de propuestas: {e}")
            return False
