"""
Scheduler & Conversion Intent Service
Genera enlaces directos de 1 clic para:
1. Google Calendar (creación directa del evento de entrevista técnica)
2. WhatsApp con mensaje pre-estructurado
3. Correo electrónico con resumen de la oportunidad
"""

import urllib.parse
from datetime import datetime, timedelta


class SchedulerService:
    DEFAULT_PHONE = "573108009394"
    DEFAULT_EMAIL = "diego.97duran@gmail.com"

    @classmethod
    def generate_google_calendar_link(
        cls,
        title: str = "Entrevista Técnica — Diego Monroy & Equipo de Selección",
        description: str = "Reunión técnica para evaluar compatibilidad con la vacante. Contacto: diego.97duran@gmail.com | +57 310 800 9394",
        duration_minutes: int = 30
    ) -> str:
        """
        Genera una URL de Google Calendar que abre la pantalla de creación
        con el título, invitados, descripción y duración pre-llenados.
        """
        # Fijar fecha tentativa: mañana a las 15:00 UTC (10:00 AM Colombia)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=duration_minutes)

        fmt = "%Y%m%dT%H%M%SZ"
        dates_param = f"{start_time.strftime(fmt)}/{end_time.strftime(fmt)}"

        params = {
            "action": "TEMPLATE",
            "text": title,
            "details": description,
            "dates": dates_param,
            "add": cls.DEFAULT_EMAIL,
            "location": "Google Meet / Virtual"
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    @classmethod
    def generate_whatsapp_link(cls, custom_text: str | None = None) -> str:
        """
        Genera un enlace de WhatsApp con mensaje pre-compuesto listo para enviar.
        """
        msg = custom_text or (
            "Hola Diego, estuve interactuando con tu Agente de IA en tu portafolio. "
            "Me gustaría coordinar una entrevista técnica contigo para conversar sobre una oportunidad en nuestro equipo."
        )
        encoded_msg = urllib.parse.quote(msg)
        return f"https://wa.me/{cls.DEFAULT_PHONE}?text={encoded_msg}"

    @classmethod
    def generate_email_link(cls, vacancy_title: str | None = None) -> str:
        """
        Genera un enlace mailto pre-llenado con asunto y cuerpo profesional.
        """
        subject = f"Oportunidad Profesional — {vacancy_title or 'Entrevista Técnica'}"
        body = (
            f"Hola Diego,\n\n"
            f"Revisamos tu perfil a través de tu Agente de Inteligencia Artificial y encontramos una gran afinidad con nuestra búsqueda.\n\n"
            f"Nos gustaría coordinar una llamada de 20-30 minutos para profundizar en tu experiencia como Tech Lead y Arquitecto.\n\n"
            f"Saludos cordiales."
        )
        params = {
            "subject": subject,
            "body": body
        }
        return f"mailto:{cls.DEFAULT_EMAIL}?{urllib.parse.urlencode(params)}"
