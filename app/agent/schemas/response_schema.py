"""
Pydantic Schemas for Structured Responses (v2)
Inspirado en response_schema.py de bbog-bebd-gcm-ml
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class MatchCardSchema(BaseModel):
    overallScore: int = Field(..., ge=0, le=100, description="Porcentaje de compatibilidad técnica y de liderazgo")
    roleDetected: str = Field(..., description="Nombre del cargo o perfil inferido de la vacante")
    keyStrengths: list[str] = Field(default_factory=list, description="Fortalezas clave de Diego que encajan")
    alignedDeliverables: list[str] = Field(default_factory=list, description="Entregables y valor inmediato")
    mitigations: list[str] = Field(default_factory=list, description="Mitigación proactiva de posibles brechas")


class CtaLinksSchema(BaseModel):
    calendarLink: str = Field(..., description="Enlace directo a Google Calendar para agendar entrevista")
    whatsappLink: str = Field(..., description="Enlace directo a WhatsApp con mensaje pre-estructurado")
    emailLink: str = Field(..., description="Enlace mailto directo a Diego Monroy")
    phone: str = "+57 310 800 9394"
    email: str = "diego.97duran@gmail.com"


class VisualResourceSchema(BaseModel):
    type: str = "project_card"
    projectId: str
    title: str
    category: str
    badge: str
    image: str
    metric: Optional[str] = None
    flowSteps: list[dict] = Field(default_factory=list)
    ctaText: str = "Ver Arquitectura del Proyecto"


class ChatResponseSchema(BaseModel):
    success: bool = True
    response: str = Field(..., description="Respuesta textual en Markdown enriquecido")
    sessionId: str = Field(..., description="ID de sesión")
    match: Optional[MatchCardSchema] = None
    cta: Optional[CtaLinksSchema] = None
    visualResource: Optional[VisualResourceSchema] = None
    toolsUsed: list[str] = Field(default_factory=list)
    processingTimeMs: int = Field(..., description="Tiempo de procesamiento en milisegundos")
    error: Optional[str] = None
