"""
Email Notification Service — Diego Monroy AI Talent Agent
Envía alertas en tiempo real a diego.97duran@gmail.com cuando:
1. Un reclutador solicita agendamiento o entrevista (presencial en Bogotá o virtual).
2. Se evalúa una vacante con alto match (>80%).
3. Un reclutador deja sus datos de contacto en el chat.

Soporta dos canales de transporte:
- Opción 1: SMTP de Gmail (smtp.gmail.com:587) con Contraseña de Aplicación.
- Opción 2: Resend API (vía HTTP con RESEND_API_KEY).
"""

import os
import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("EmailNotificationService")


class EmailNotificationService:
    def __init__(self):
        self.recipient_email = os.getenv("RECRUITER_CONTACT_EMAIL", "diego.97duran@gmail.com")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", self.recipient_email)
        self.smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or ""
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")

    def is_configured(self) -> bool:
        """Indica si hay algún canal de correo configurado para envío en vivo."""
        return bool(self.smtp_password or self.resend_api_key)

    def _build_html_template(
        self,
        event_type: str,
        recruiter_name: Optional[str],
        company_name: Optional[str],
        role_sought: Optional[str],
        match_score: Optional[int],
        interview_modality: str,
        message_snippet: str,
        session_id: str,
        contact_info: Optional[str] = None
    ) -> str:
        date_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        score_badge = ""
        if match_score:
            color = "#10B981" if match_score >= 85 else "#38BDF8"
            score_badge = f"""
            <div style="background-color: {color}15; border: 1px solid {color}; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; display: inline-block;">
                <span style="font-size: 26px; font-weight: 800; color: {color};">{match_score}%</span>
                <span style="font-size: 13px; color: #94A3B8; margin-left: 8px;">Afinidad Calculada con Diego</span>
            </div>
            """

        recruiter_display = recruiter_name or "Reclutador / Empresa (Contacto en chat)"
        company_display = company_name or "No especificada"
        role_display = role_sought or "Tech Lead & Solutions Architect"
        modality_icon = "🏢" if interview_modality == "presencial" else "💻"
        modality_text = "Presencial en Bogotá" if interview_modality == "presencial" else "Virtual (Meet / Teams)"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nueva Alerta de Reclutador — Diego Monroy AI</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0F172A; color: #F8FAFC; margin: 0; padding: 30px 15px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1E293B; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%); padding: 24px 28px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #E2E8F0; font-weight: 700; margin-bottom: 6px;">
                        Diego Monroy · AI Talent Agent Alert
                    </div>
                    <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #FFFFFF;">
                        {event_type}
                    </h1>
                </div>

                <!-- Body -->
                <div style="padding: 28px;">
                    {score_badge}

                    <div style="background-color: #0F172A; border-radius: 10px; padding: 18px; margin-bottom: 22px; border: 1px solid #334155;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr>
                                <td style="padding: 6px 0; color: #94A3B8; width: 35%;">👤 Reclutador:</td>
                                <td style="padding: 6px 0; font-weight: 600; color: #F1F5F9;">{recruiter_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94A3B8;">🏢 Empresa:</td>
                                <td style="padding: 6px 0; font-weight: 600; color: #38BDF8;">{company_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94A3B8;">🎯 Rol Buscado:</td>
                                <td style="padding: 6px 0; font-weight: 600; color: #F1F5F9;">{role_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94A3B8;">📍 Modalidad:</td>
                                <td style="padding: 6px 0; font-weight: 600; color: #F59E0B;">{modality_icon} {modality_text}</td>
                            </tr>
                            {f'<tr><td style="padding: 6px 0; color: #94A3B8;">📞 Contacto:</td><td style="padding: 6px 0; font-weight: 600; color: #10B981;">{contact_info}</td></tr>' if contact_info else ''}
                            <tr>
                                <td style="padding: 6px 0; color: #94A3B8;">🕒 Fecha y Hora:</td>
                                <td style="padding: 6px 0; color: #CBD5E1;">{date_str}</td>
                            </tr>
                        </table>
                    </div>

                    <!-- Mensaje o extracto -->
                    <div style="margin-bottom: 25px;">
                        <div style="font-size: 12px; text-transform: uppercase; font-weight: 700; color: #94A3B8; margin-bottom: 8px;">
                            💬 Extracto del Requerimiento / Conversación:
                        </div>
                        <div style="background-color: #0F172A; border-left: 4px solid #38BDF8; padding: 14px 16px; border-radius: 4px; font-size: 13px; line-height: 1.6; color: #CBD5E1; font-style: italic;">
                            "{message_snippet}"
                        </div>
                    </div>

                    <!-- Botones de Acción -->
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://wa.me/573108009394" style="background-color: #25D366; color: #FFFFFF; text-decoration: none; padding: 12px 22px; border-radius: 8px; font-weight: 700; font-size: 14px; display: inline-block; margin-right: 10px;">
                            📱 Responder por WhatsApp
                        </a>
                        <a href="https://diegomonroy.site" style="background-color: #38BDF8; color: #0F172A; text-decoration: none; padding: 12px 22px; border-radius: 8px; font-weight: 700; font-size: 14px; display: inline-block;">
                            🌐 Ver Tablero PBaaP
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #0F172A; padding: 16px 28px; border-top: 1px solid #334155; font-size: 11px; color: #64748B; text-align: center;">
                    Enviado automáticamente por el Agente de IA de Diego Monroy · Sesión: <code>{session_id}</code>
                </div>
            </div>
        </body>
        </html>
        """

    def send_via_smtp(self, subject: str, html_body: str) -> bool:
        """Envía el correo vía SMTP seguro (TLS port 587)."""
        if not self.smtp_password:
            logger.warning("SMTP_PASSWORD no configurado. El correo no pudo enviarse por SMTP.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Diego Monroy AI Agent <{self.smtp_user}>"
            msg["To"] = self.recipient_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Notificación por correo enviada con éxito a {self.recipient_email} vía SMTP.")
            return True
        except Exception as e:
            logger.error(f"Error enviando correo vía SMTP a {self.recipient_email}: {e}")
            return False

    async def send_via_resend(self, subject: str, html_body: str) -> bool:
        """Envía el correo vía Resend API (HTTP REST)."""
        if not self.resend_api_key:
            return False

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "Diego Monroy AI <onboarding@resend.dev>",
                        "to": [self.recipient_email],
                        "subject": subject,
                        "html": html_body
                    }
                )
                if res.status_code in (200, 201):
                    logger.info(f"Notificación por correo enviada con éxito a {self.recipient_email} vía Resend.")
                    return True
                else:
                    logger.error(f"Error en Resend API ({res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Fallo al conectar con Resend API: {e}")
            return False

    async def notify_recruiter_interaction(
        self,
        event_type: str = "🎯 Nueva Consulta de Reclutador",
        recruiter_name: Optional[str] = None,
        company_name: Optional[str] = None,
        role_sought: Optional[str] = None,
        match_score: Optional[int] = None,
        interview_modality: str = "virtual",
        message_snippet: str = "",
        session_id: str = "unknown",
        contact_info: Optional[str] = None
    ) -> bool:
        """
        Orquesta el envío de la notificación a diego.97duran@gmail.com de manera
        resiliente y sin bloquear el hilo principal.
        """
        # Recortar el snippet si es muy largo
        snippet = (message_snippet[:280] + "...") if len(message_snippet) > 280 else message_snippet

        empresa_text = f"[{company_name}] " if company_name else ""
        subject = f"🚀 {empresa_text}{event_type} — Diego Monroy AI Agent"

        html_content = self._build_html_template(
            event_type=event_type,
            recruiter_name=recruiter_name,
            company_name=company_name,
            role_sought=role_sought,
            match_score=match_score,
            interview_modality=interview_modality,
            message_snippet=snippet,
            session_id=session_id,
            contact_info=contact_info
        )

        # 1. Intentar por Resend si está disponible
        if self.resend_api_key:
            resend_ok = await self.send_via_resend(subject, html_content)
            if resend_ok:
                return True

        # 2. Intentar por SMTP en hilo separado (para no bloquear el bucle de eventos)
        if self.smtp_password:
            loop = asyncio.get_event_loop()
            smtp_ok = await loop.run_in_executor(None, self.send_via_smtp, subject, html_content)
            if smtp_ok:
                return True

        logger.info(
            f"[PENDIENTE DE CONFIGURACIÓN] Notificación lista para {self.recipient_email}: "
            f"'{subject}' (Configura SMTP_PASSWORD o RESEND_API_KEY en .env o GCP Secret Manager para envío en vivo)."
        )
        return False


# Instancia singleton del servicio
email_notification_service = EmailNotificationService()
