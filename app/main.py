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

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AppMain")

app = FastAPI(
    title="Diego Monroy — Executive AI Talent Agent",
    description="Backend API con SSE Streaming y arquitectura limpia para el agente evaluador de talento y vacantes.",
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


@app.get("/health")
async def health_check():
    """Verificación de salud del servicio y estado de secretos protegidos."""
    gemini_key = secrets_manager.get_gemini_api_key()
    return {
        "status": "healthy",
        "service": "Diego Monroy AI Talent Agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
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
    session_id = request.sessionId or f"sess_{int(start_time * 1000)}"

    async for event in VacancyMatcherFlow.run(request):
        if event.get("type") == "text_delta":
            accumulated_text.append(event.get("delta", ""))
        elif event.get("type") == "match":
            match_card = event.get("data")
        elif event.get("type") == "start":
            session_id = event.get("sessionId", session_id)

    processing_time = int((time.time() - start_time) * 1000)

    cta = CtaLinksSchema(
        calendarLink=SchedulerService.generate_google_calendar_link(),
        whatsappLink=SchedulerService.generate_whatsapp_link(),
        emailLink=SchedulerService.generate_email_link()
    )

    return ChatResponseSchema(
        success=True,
        response="".join(accumulated_text),
        sessionId=session_id,
        match=match_card,
        cta=cta,
        toolsUsed=["vacancy_analyzer", "diego_knowledge_base", "scheduler_service"],
        processingTimeMs=processing_time
    )
