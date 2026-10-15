"""
Vacancy Matcher Flow & Agent Orchestration
Orquesta la extracción multimodal, evaluación de compatibilidad,
llamada al LLM y generación de enlaces de conversión a entrevista.
"""

import time
import json
from typing import AsyncGenerator, Optional
from app.agent.schemas.request_schema import ChatRequest
from app.agent.schemas.response_schema import MatchCardSchema, CtaLinksSchema
from app.agent.middleware.guardrails import GuardrailsInterceptor
from app.services.multimodal_service import MultimodalService
from app.services.scheduler_service import SchedulerService
from app.services.llm_service import llm_service
from app.services.knowledge_data import DIEGO_PROFILE


class VacancyMatcherFlow:
    @staticmethod
    def calculate_match_profile(vacancy_text: str) -> MatchCardSchema:
        """
        Calcula de forma determinística y cualitativa la compatibilidad
        con el perfil de Diego analizando palabras clave y exigencias técnicas.
        """
        text = vacancy_text.lower()
        score = 85  # Base alta por la versatilidad de Diego
        strengths = []
        deliverables = []
        mitigations = []

        # Roles inferidos
        role_detected = "Tech Lead & Solutions Architect"
        if "lead" in text or "lider" in text or "líder" in text:
            role_detected = "Tech Lead / Líder Técnico"
            score += 4
            strengths.append("Liderazgo activo de células ágiles de ingeniería en Banco de Bogotá.")
        elif "cloud" in text or "devops" in text or "gcp" in text or "aws" in text:
            role_detected = "Cloud Solutions Architect / DevSecOps Lead"
            score += 5
            strengths.append("Certificación oficial Google Cloud ACE (#189954) y despliegues Kubernetes Zero-Downtime.")
        elif "ai" in text or "ia" in text or "genai" in text or "ml" in text:
            role_detected = "AI Solutions Architect / GenAI Lead"
            score += 5
            strengths.append("Diseño de sistemas multi-agente con LangChain, LangGraph y bases vectoriales sobre BigQuery.")

        # Keywords de Cloud
        if any(k in text for k in ["gcp", "google cloud", "aws", "azure", "cloud"]):
            strengths.append("GCP ACE Certified con experiencia en Kubernetes (GKE), Cloud Run y arquitecturas distribuidas.")
            deliverables.append("Modernización e infraestructura cloud resiliente bajo estándares de costo-eficiencia.")

        # Keywords de Arquitectura & Backend
        if any(k in text for k in ["microservicios", "microservices", "hexagonal", "ddd", "spring", "java", "python", "fastapi"]):
            strengths.append("Especialista en Arquitectura Hexagonal y DDD con Java (Spring Boot) y Python (FastAPI).")
            deliverables.append("SLA garantizado de 99.99% en servicios de alta concurrencia y criticidad bancaria.")

        # Keywords de IA
        if any(k in text for k in ["langchain", "langgraph", "llm", "rag", "agente", "agent"]):
            strengths.append("Arquitectura agéntica comprobada con reducción de tiempos de respuesta en 40%.")
            deliverables.append("Implementación de asistentes y automatizaciones empresariales con trazabilidad de tokens.")

        # Mitigaciones
        if "go" in text or "golang" in text:
            mitigations.append("Fuerte dominio en concurrencia (Java/Python) con rápida adaptabilidad a microservicios en Go.")
        if not mitigations:
            mitigations.append("Capacidad comprobada de asumir ownership técnico total desde el día 1.")

        # Default strengths si la vacante fue muy corta
        if not strengths:
            strengths = [
                "Google Cloud Certified: Associate Cloud Engineer (ACE).",
                "Tech Lead bancario garantizando 99.99% de SLA en CRM Corporativo.",
                "Especialista en Gerencia de Proyectos y metodologías ágiles."
            ]
        if not deliverables:
            deliverables = [
                "Estandarización de código con reducción de incidentes en producción en un 38%.",
                "Aceleración del roadmap técnico y mentoría a desarrolladores."
            ]

        final_score = min(score, 99)

        return MatchCardSchema(
            overallScore=final_score,
            roleDetected=role_detected,
            keyStrengths=strengths[:4],
            alignedDeliverables=deliverables[:3],
            mitigations=mitigations[:2]
        )

    @classmethod
    async def run(cls, request: ChatRequest) -> AsyncGenerator[dict, None]:
        """
        Ejecuta el flujo completo y emite eventos SSE tipados:
        - {"type": "start", "sessionId": ...}
        - {"type": "step", "step": "guardrail_check"}
        - {"type": "step", "step": "multimodal_parsing"}
        - {"type": "match", "data": MatchCardSchema}
        - {"type": "text_delta", "delta": "..."}
        - {"type": "done", "cta": CtaLinksSchema}
        """
        session_id = request.sessionId or f"session_{int(time.time() * 1000)}"
        yield {"type": "start", "sessionId": session_id}

        # 1. Filtro Guardrails y Seguridad
        is_safe, sanitized_msg, warning = GuardrailsInterceptor.inspect_and_sanitize(request.message)
        if not is_safe:
            yield {"type": "warning", "message": warning}
            yield {
                "type": "text_delta",
                "delta": "🔒 **Directriz de Seguridad**: Tu consulta activó un control de protección de credenciales o de alcance. Por políticas de DevSecOps, el acceso a instrucciones de sistema y secretos internos está completamente restringido.\n\n¿Deseas que analicemos la experiencia de Diego en arquitecturas de seguridad bancaria y OWASP?"
            }
            yield {
                "type": "done",
                "cta": {
                    "calendarLink": SchedulerService.generate_google_calendar_link(),
                    "whatsappLink": SchedulerService.generate_whatsapp_link(),
                    "emailLink": SchedulerService.generate_email_link()
                }
            }
            return

        yield {"type": "step", "label": "Verificando requerimientos y archivos adjuntos..."}

        # 2. Extracción Multimodal de adjuntos
        extracted_text = ""
        if request.attachments:
            yield {"type": "step", "label": f"Procesando {len(request.attachments)} documento(s) de la vacante..."}
            for att in request.attachments:
                try:
                    if "pdf" in att.mimeType.lower():
                        pdf_bytes = MultimodalService.decode_base64_file(att.content)
                        doc_text = MultimodalService.extract_text_from_pdf_bytes(pdf_bytes)
                        extracted_text += f"\n--- Contenido de {att.name} ---\n{doc_text}\n"
                    elif "text" in att.mimeType.lower() or "plain" in att.mimeType.lower():
                        extracted_text += f"\n--- Texto adjunto {att.name} ---\n{att.content}\n"
                except Exception as e:
                    extracted_text += f"\n[Aviso: No fue posible leer el archivo {att.name}: {e}]\n"

        # 3. Match Card si hay vacante o solicitud de evaluación
        is_vacancy = bool(extracted_text) or any(w in sanitized_msg.lower() for w in ["vacante", "perfil", "busco", "oferta", "requisitos", "rol", "contratar"])
        if is_vacancy:
            yield {"type": "step", "label": "Calculando matriz de compatibilidad con Diego Monroy..."}
            match_data = cls.calculate_match_profile(extracted_text or sanitized_msg)
            yield {"type": "match", "data": match_data.model_dump()}

        # 4. Generación de Enlaces de Agendamiento
        cta = {
            "calendarLink": SchedulerService.generate_google_calendar_link(),
            "whatsappLink": SchedulerService.generate_whatsapp_link(),
            "emailLink": SchedulerService.generate_email_link(),
            "phone": SchedulerService.DEFAULT_PHONE,
            "email": SchedulerService.DEFAULT_EMAIL
        }

        # 5. Generación de respuesta LLM en Streaming
        yield {"type": "step", "label": "Redactando informe ejecutivo de valor..."}
        async for chunk in llm_service.stream_chat_response(
            user_message=sanitized_msg,
            attachment_text=extracted_text if extracted_text else None
        ):
            yield {"type": "text_delta", "delta": chunk}

        # 6. Evento de finalización
        yield {
            "type": "done",
            "sessionId": session_id,
            "cta": cta
        }
