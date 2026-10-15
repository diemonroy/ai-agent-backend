"""
Pydantic Schemas for Request Validation (v2)
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChatAttachment(BaseModel):
    name: str = Field(..., max_length=255)
    mimeType: str = Field(..., description="application/pdf, image/png, image/jpeg, etc.")
    content: str = Field(..., description="Base64 encoded string o texto plano extraído")
    size: Optional[int] = Field(default=None, description="Tamaño en bytes")


class RecruiterContext(BaseModel):
    company: Optional[str] = None
    roleLookingFor: Optional[str] = None
    recruiterName: Optional[str] = None
    channel: Optional[Literal["web_portfolio", "linkedin", "direct_link"]] = "web_portfolio"


class ChatRequest(BaseModel):
    message: str = Field(..., description="Pregunta o descripción de la vacante")
    sessionId: Optional[str] = Field(default=None, description="Identificador único de la sesión")
    attachments: list[ChatAttachment] = Field(default_factory=list, description="Documentos o capturas adjuntas")
    context: Optional[RecruiterContext] = None
    stream: bool = Field(default=True, description="Si debe responder en streaming SSE")
