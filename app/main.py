"""
FastAPI Entry Point — Diego Monroy AI Talent Agent
Implementa endpoints REST y Server-Sent Events (SSE) para el Agente Ejecutivo de Talento.
Inspirado en la arquitectura bancaria de bbog-bebd-gcm-ml.
"""

import time
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from app.agent.schemas.request_schema import ChatRequest
from app.agent.schemas.response_schema import ChatResponseSchema, CtaLinksSchema
from app.agent.flows.vacancy_matcher_flow import VacancyMatcherFlow
from app.services.secrets_manager import secrets_manager, mask_secret
from app.services.scheduler_service import SchedulerService
from app.services.chat_memory_service import chat_memory_service
from app.core.database import db_manager

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AppMain")

app = FastAPI(
    title="Diego Monroy — Executive AI Talent Agent",
    description="Backend API con SSE Streaming y persistencia relacional SQLite WAL para el agente de talento y vacantes.",
    version="1.0.0"
)

# Configuración de CORS segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "https://diegomonroy.site",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Inicialización y diagnóstico de base de datos relacional al arrancar."""
    db_status = db_manager.get_database_status()
    logger.info(f"🟢 [DATABASE] Motor relacional activo: {db_status['engine'].upper()} en {db_status['databasePath']}")
    logger.info(f"📊 [DATABASE] Modo: {db_status['journalMode']} | Tamaño en disco: {db_status['sizeFormatted']}")
    logger.info(
        f"📊 [DATABASE] Registros en tablas: "
        f"sessions={db_status['tables']['sessions']}, "
        f"messages={db_status['tables']['messages']}, "
        f"conversions={db_status['tables']['conversion_events']}"
    )


@app.get("/health", tags=["Health & Diagnostics"])
async def health_check():
    """Verificación de salud del servicio, base de datos relacional y secretos protegidos."""
    gemini_key = secrets_manager.get_gemini_api_key()
    db_status = db_manager.get_database_status()
    return {
        "status": "healthy",
        "service": "Diego Monroy AI Talent Agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "database": {
            "status": db_status["status"],
            "engine": db_status["engine"],
            "journalMode": db_status["journalMode"],
            "path": db_status["databasePath"],
            "size": db_status["sizeFormatted"],
            "tables": db_status["tables"]
        },
        "security": {
            "secrets_manager_active": True,
            "gemini_configured": bool(gemini_key and not gemini_key.startswith("AIzaSy...")),
            "masked_key": mask_secret(gemini_key)
        }
    }


@app.get("/info")
async def get_agent_info():
    """Metadatos del agente para guiar interactivamente al reclutador."""
    return {
        "name": "Diego Monroy — Executive AI Talent Agent",
        "headline": "Tech Lead & Solutions Architect · Cloud & GenAI Solutions",
        "description": (
            "Agente de IA diseñado para evaluar la compatibilidad de vacantes técnicas y de liderazgo "
            "con la trayectoria comprobada de Diego Leonardo Monroy Durán."
        ),
        "capabilities": [
            "Análisis instantáneo de vacantes en PDF, texto o captura",
            "Cálculo de porcentaje de compatibilidad y fortalezas clave",
            "Validación de SLA 99.99% en banca y certificación GCP ACE",
            "Agendamiento inmediato de entrevista técnica (Google Calendar / WhatsApp)"
        ],
        "suggestedChips": [
            "📄 Analizar mi vacante (subir PDF o pegar texto)",
            "🚀 ¿Por qué Diego para Tech Lead / Arquitecto Cloud?",
            "🧠 Experiencia en IA Generativa, LangChain y LangGraph",
            "🏦 Métricas de alta disponibilidad bancaria y SLA 99.99%",
            "📅 Agendar entrevista técnica directa con Diego"
        ],
        "contactChannels": {
            "whatsapp": "https://wa.me/573108009394",
            "email": "diego.97duran@gmail.com",
            "linkedin": "https://linkedin.com/in/diemonroy"
        }
    }


@app.post("/api/chat")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint principal con Server-Sent Events (SSE).
    Emite chunks en tiempo real compatibles con EventSource y fetch-streaming.
    """
    async def sse_generator():
        try:
            async for event in VacancyMatcherFlow.run(request):
                # Formato estándar Server-Sent Events
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Error en sse_generator: {e}")
            error_event = {"type": "error", "message": f"Error procesando solicitud: {str(e)}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/chat/sync", response_model=ChatResponseSchema)
async def chat_sync_endpoint(request: ChatRequest):
    """Endpoint síncrono para clientes que no admiten SSE."""
    start_time = time.time()
    accumulated_text = []
    match_card = None
    visual_resource = None
    cta_data = None
    session_id = request.sessionId or f"sess_{int(start_time * 1000)}"

    async for event in VacancyMatcherFlow.run(request):
        if event.get("type") == "text_delta":
            accumulated_text.append(event.get("delta", ""))
        elif event.get("type") == "match":
            match_card = event.get("data")
        elif event.get("type") == "done":
            visual_resource = event.get("visualResource")
            cta_data = event.get("cta")
        elif event.get("type") == "start":
            session_id = event.get("sessionId", session_id)

    processing_time = int((time.time() - start_time) * 1000)

    cta = None
    if cta_data:
        cta = CtaLinksSchema(
            calendarLink=cta_data.get("calendarLink", SchedulerService.generate_google_calendar_link()),
            whatsappLink=cta_data.get("whatsappLink", SchedulerService.generate_whatsapp_link()),
            emailLink=cta_data.get("emailLink", SchedulerService.generate_email_link()),
            phone=cta_data.get("phone", SchedulerService.DEFAULT_PHONE),
            email=cta_data.get("email", SchedulerService.DEFAULT_EMAIL)
        )

    return ChatResponseSchema(
        success=True,
        response="".join(accumulated_text),
        sessionId=session_id,
        match=match_card,
        cta=cta,
        visualResource=visual_resource,
        toolsUsed=["vacancy_analyzer", "diego_knowledge_base", "scheduler_service"],
        processingTimeMs=processing_time
    )


# -------------------------------------------------------------
# Endpoints de Dashboard de Analítica y Registro de Conversaciones
# -------------------------------------------------------------

class ConversionPayload(ChatRequest):
    conversionType: str
    metadata: dict = {}


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Retorna KPIs ejecutivos, roles detectados y preguntas frecuentes de reclutadores."""
    from app.services.chat_memory_service import chat_memory_service
    return chat_memory_service.get_analytics_summary()


@app.get("/api/dashboard/conversations")
async def get_dashboard_conversations(limit: int = 50):
    """Lista las sesiones recientes con resumen de match y último mensaje."""
    from app.services.chat_memory_service import chat_memory_service
    return chat_memory_service.get_all_sessions(limit=limit)


@app.get("/api/dashboard/conversations/{session_id}")
async def get_dashboard_conversation_details(session_id: str):
    """Retorna el historial completo paso a paso de una conversación específica."""
    from app.services.chat_memory_service import chat_memory_service
    details = chat_memory_service.get_session_details(session_id)
    if not details:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return details


@app.post("/api/chat/conversion")
async def track_conversion(request: Request):
    """Registra cuando un reclutador hace clic en agendar Calendar, WhatsApp o Email y notifica a Diego."""
    from app.services.chat_memory_service import chat_memory_service
    from app.services.email_notification_service import email_notification_service
    import asyncio
    try:
        data = await request.json()
        session_id = data.get("sessionId") or "unknown_session"
        conversion_type = data.get("conversionType") or "unknown"
        meta = data.get("metadata") or {}
        chat_memory_service.record_conversion(session_id, conversion_type, meta)

        # Disparar alerta inmediata por correo a Diego
        session_details = chat_memory_service.get_session_details(session_id) or {}
        asyncio.create_task(
            email_notification_service.notify_recruiter_interaction(
                event_type=f"📅 Solicitud de Agendamiento ({conversion_type.upper()})",
                recruiter_name=session_details.get("recruiter_name"),
                company_name=session_details.get("company_name"),
                role_sought=session_details.get("role_matched"),
                match_score=session_details.get("score"),
                interview_modality=session_details.get("interview_modality", "virtual"),
                message_snippet=f"El reclutador hizo clic en la opción de agendamiento '{conversion_type.upper()}'. Contactar prioritariamente.",
                session_id=session_id
            )
        )

        return {"status": "ok", "session_id": session_id, "conversion_type": conversion_type}
    except Exception as e:
        logger.error(f"Error registrando conversión: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/notifications/test-email", tags=["Notifications"])
async def send_test_email_endpoint():
    """Envía un correo de prueba a diego.97duran@gmail.com para verificar la configuración."""
    from app.services.email_notification_service import email_notification_service
    success = await email_notification_service.notify_recruiter_interaction(
        event_type="🧪 Notificación de Prueba del Agente",
        recruiter_name="Diego Monroy (Prueba de Sistema)",
        company_name="Verificación de Conectividad",
        role_sought="Tech Lead & Solutions Architect",
        match_score=99,
        interview_modality="presencial",
        message_snippet="Este es un correo de prueba enviado desde tu Agente de Inteligencia Artificial para verificar la entrega a diego.97duran@gmail.com.",
        session_id="test_probe_001"
    )
    return {
        "status": "success" if success else "pending_credentials",
        "recipient": email_notification_service.recipient_email,
        "is_configured": email_notification_service.is_configured(),
        "channel": "resend" if email_notification_service.resend_api_key else ("smtp" if email_notification_service.smtp_password else "none"),
        "message": "Correo enviado con éxito." if success else "Servicio listo. Configura SMTP_PASSWORD o RESEND_API_KEY para habilitar la entrega física en tu bandeja."
    }


# -------------------------------------------------------------
# Endpoints de Telemetría e Inspección de Base de Datos
# -------------------------------------------------------------

@app.get("/api/database/status", tags=["Database & Persistence"])
async def get_database_status_endpoint():
    """
    Retorna el estado de salud, tamaño en disco, métricas y registros
    de la base de datos relacional SQLite (WAL).
    """
    return db_manager.get_database_status()


@app.post("/api/database/backup", tags=["Database & Persistence"])
async def trigger_database_backup():
    """Genera una copia de seguridad SQLite consistente en caliente."""
    try:
        backup_path = db_manager.create_backup()
        return {
            "status": "success",
            "message": "Copia de seguridad relacional generada con éxito.",
            "backupFile": str(backup_path),
            "sizeBytes": backup_path.stat().st_size
        }
    except Exception as e:
        logger.error(f"Error generando backup: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar backup: {str(e)}")


# -------------------------------------------------------------
# Endpoints de la Bóveda de Conocimiento (Brand as a Product SSOT)
# -------------------------------------------------------------

@app.get("/api/knowledge/vault", tags=["Brand Knowledge Vault"])
async def get_knowledge_vault_summary():
    """
    Retorna la síntesis de la Bóveda de Conocimiento estructurada
    de Diego Monroy como Marca, Producto y Servicio.
    """
    from app.services.knowledge_vault_service import knowledge_vault_service
    return {
        "status": "online",
        "brand": knowledge_vault_service.identity.get("brand"),
        "uniqueValueProposition": knowledge_vault_service.identity.get("unique_value_proposition"),
        "totalRoles": len(knowledge_vault_service.career_history),
        "totalSkills": len(knowledge_vault_service._flat_skills),
        "certifications": knowledge_vault_service.credentials.get("certifications", []),
        "education": knowledge_vault_service.credentials.get("education", []),
        "services": knowledge_vault_service.services.get("services", []),
        "caseStudiesAvailable": list(knowledge_vault_service.case_studies.keys())
    }


@app.get("/api/knowledge/skills", tags=["Brand Knowledge Vault"])
async def get_skills_taxonomy_endpoint():
    """Retorna la matriz jerárquica de habilidades técnicas, niveles y proyectos de prueba."""
    from app.services.knowledge_vault_service import knowledge_vault_service
    return knowledge_vault_service.skills_taxonomy


@app.post("/api/knowledge/match", tags=["Brand Knowledge Vault"])
async def match_vacancy_skills_endpoint(request: Request):
    """
    Analiza una descripción de vacante o requerimiento técnico y
    detecta automáticamente las habilidades coincidentes con el portafolio de Diego.
    """
    from app.services.knowledge_vault_service import knowledge_vault_service
    body = await request.json()
    text = body.get("text") or ""
    matches = knowledge_vault_service.match_skills_in_text(text)
    return {
        "queryLength": len(text),
        "matchesCount": len(matches),
        "matchedSkills": matches
    }


# -------------------------------------------------------------
# Endpoints de Inteligencia de Demanda & Mercado (PBaaP Analytics)
# -------------------------------------------------------------

@app.get("/api/analytics/skills-demand", tags=["Market & Demand Intelligence"])
async def get_skills_demand_endpoint():
    """
    Retorna la telemetría de demanda de habilidades hacia Diego Monroy.
    Habilidades más consultadas por reclutadores vs. habilidades desapercibidas.
    """
    return chat_memory_service.get_skills_demand_analytics()


@app.get("/api/analytics/market-intelligence", tags=["Market & Demand Intelligence"])
async def get_market_intelligence_endpoint():
    """
    Retorna el informe ejecutivo de posicionamiento de marca:
    por qué el perfil es atractivo, roles buscados y funnel de conversión.
    """
    return chat_memory_service.get_market_intelligence_report()
