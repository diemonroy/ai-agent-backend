"""
Vacancy Matcher Flow & Agent Orchestration
Orquesta la extracción multimodal, evaluación de compatibilidad,
llamada al LLM y generación de enlaces de conversión a entrevista.
"""

import time
import re
import json
from typing import AsyncGenerator, Optional
from app.agent.schemas.request_schema import ChatRequest
from app.agent.schemas.response_schema import MatchCardSchema, CtaLinksSchema
from app.agent.middleware.guardrails import GuardrailsInterceptor
from app.services.multimodal_service import MultimodalService
from app.services.scheduler_service import SchedulerService
from app.services.llm_service import llm_service
from app.services.knowledge_data import DIEGO_PROFILE
from app.services.chat_memory_service import chat_memory_service


class VacancyMatcherFlow:
    @staticmethod
    def extract_lead_context(user_msg: str, extracted_text: str = "") -> dict:
        """
        Extrae heurísticamente el nombre del reclutador, la empresa, 
        el interés principal y si propuso una entrevista presencial o virtual.
        """
        combined = (user_msg + " " + extracted_text).strip()
        combined_lower = combined.lower()

        # 1. Detección de Nombre del Reclutador
        recruiter_name = None
        name_patterns = [
            r"(?:soy|me llamo|mi nombre es|hablas con|te escribe|te saluda|un gusto,\s*soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)",
            r"(?:soy|me llamo|mi nombre es|hablas con)\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)"
        ]
        for pat in name_patterns:
            match = re.search(pat, combined, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip().title()
                if candidate.lower() not in ["un", "una", "el", "la", "de", "del", "en", "ingeniero", "reclutador", "tech", "lead", "desarrollador"]:
                    recruiter_name = candidate
                    break

        # 2. Detección de Empresa
        company_name = None
        known_companies = r"(bancolombia|mercado\s*libre|rappi|globant|nubank|banco\s*de\s*bogot[aá]|banco\s*davivienda|davivienda|bbva|falabella|accenture|epam|sophos|credivalores|scotiabank|nequi|daviplata|bold)"
        known_match = re.search(known_companies, combined, re.IGNORECASE)
        if known_match:
            company_name = known_match.group(1).strip().title()
        else:
            generic_patterns = [
                r"(?:de|en|desde)\s+(?:la empresa|el banco|la startup|la fintech|la consultora)\s+([A-ZÁÉÍÓÚÑ][\w&]{1,20}(?:\s+[A-ZÁÉÍÓÚÑ][\w&]{1,20})?)",
                r"(?:de|en|desde)\s+([A-ZÁÉÍÓÚÑ][\w&]{1,20}(?:\s+[A-ZÁÉÍÓÚÑ][\w&]{1,20})?)"
            ]
            for pat in generic_patterns:
                match = re.search(pat, combined)
                if match:
                    cand = match.group(1).strip().title()
                    if cand.lower() not in ["un", "una", "este", "esta", "mi", "tu", "nuestro", "bogota", "bogotá", "colombia", "equipo", "proyecto", "oficina", "aquí", "aqui"]:
                        company_name = cand
                        break

        # 3. Detección de Modalidad de Entrevista (Presencial vs Virtual)
        interview_modality = "virtual"
        presencial_triggers = [
            "presencial", "en persona", "en la oficina", "en nuestras oficinas", 
            "en las oficinas", "nos vemos en persona", "venir a la oficina", 
            "tomarnos un café", "en bogotá", "en bogota", "sede presencial", "física"
        ]
        if any(trigger in combined_lower for trigger in presencial_triggers):
            interview_modality = "presencial"

        # 4. Aspecto que le gustó / Fit
        liked_aspect = None
        if "sla" in combined_lower or "99.99" in combined_lower or "banco" in combined_lower:
            liked_aspect = "Arquitectura Resiliente & SLA 99.99%"
        elif "cloud" in combined_lower or "gcp" in combined_lower or "kubernetes" in combined_lower or "gke" in combined_lower:
            liked_aspect = "Google Cloud Certified ACE & Kubernetes"
        elif "ia" in combined_lower or "ai" in combined_lower or "genai" in combined_lower or "langchain" in combined_lower or "langgraph" in combined_lower:
            liked_aspect = "Inteligencia Artificial Generativa & LangGraph"
        elif "tech lead" in combined_lower or "liderazgo" in combined_lower or "lider" in combined_lower or "célula" in combined_lower:
            liked_aspect = "Liderazgo de Células de Alto Desempeño"
        elif "backend" in combined_lower or "java" in combined_lower or "spring" in combined_lower or "hexagonal" in combined_lower:
            liked_aspect = "Backend Mission-Critical & Arquitectura Hexagonal"

        return {
            "recruiter_name": recruiter_name,
            "company_name": company_name,
            "interview_modality": interview_modality,
            "liked_aspect": liked_aspect
        }

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

        # Coincidencias automáticas desde la Bóveda de Conocimiento (Knowledge Vault)
        from app.services.knowledge_vault_service import knowledge_vault_service
        try:
            matched_vault = knowledge_vault_service.match_skills_in_text(vacancy_text)
            for s in matched_vault[:3]:
                if s.get("proof"):
                    strengths.append(f"{s['name']}: {s['proof']}")
                score += 2
        except Exception as e:
            logger.warning(f"Error extrayendo habilidades de la bóveda: {e}")

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

        # Registrar mensaje del usuario en Memcache y Base de Datos
        att_name = request.attachments[0].name if request.attachments else None
        chat_memory_service.record_message(
            session_id=session_id,
            sender="user",
            content=sanitized_msg,
            attachment_name=att_name
        )

        if not is_safe:
            yield {"type": "warning", "message": warning}
            guardrail_resp = (
                "🔒 **Directriz de Seguridad**: Tu consulta activó un control de protección de credenciales o de alcance. "
                "Por políticas de DevSecOps, el acceso a instrucciones de sistema y secretos internos está completamente blindado.\n\n"
                "¿Deseas que analicemos mi experiencia en arquitecturas de seguridad bancaria y OWASP?"
            )
            chat_memory_service.record_message(session_id, "diego", guardrail_resp)
            yield {
                "type": "text_delta",
                "delta": guardrail_resp
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

        # 3. Extracción de contexto cualificado del reclutador y modalidad (Presencial / Virtual)
        lead_ctx = cls.extract_lead_context(sanitized_msg, extracted_text)
        chat_memory_service.update_session_lead_context(
            session_id=session_id,
            recruiter_name=lead_ctx["recruiter_name"],
            company_name=lead_ctx["company_name"],
            liked_aspect=lead_ctx["liked_aspect"],
            interview_modality=lead_ctx["interview_modality"]
        )

        # 4. Match Card si hay vacante o solicitud de evaluación
        is_vacancy = bool(extracted_text) or any(w in sanitized_msg.lower() for w in ["vacante", "perfil", "busco", "oferta", "requisitos", "rol", "contratar"])
        if is_vacancy:
            yield {"type": "step", "label": "Calculando matriz de compatibilidad con Diego Monroy..."}
            match_data = cls.calculate_match_profile(extracted_text or sanitized_msg)
            chat_memory_service.update_session_match(
                session_id=session_id,
                role=match_data.roleDetected,
                score=match_data.overallScore
            )
            # Registrar insight cualitativo de mercado y habilidades requeridas (PBaaP)
            try:
                from app.services.knowledge_vault_service import knowledge_vault_service
                chat_memory_service.db.record_market_insight(
                    session_id=session_id,
                    company_name=lead_ctx.get("company_name"),
                    role_sought=match_data.roleDetected,
                    match_score=match_data.overallScore,
                    attractiveness_reasons=match_data.keyStrengths,
                    objections_or_questions=match_data.mitigations
                )
                vac_skills = knowledge_vault_service.match_skills_in_text(extracted_text or sanitized_msg)
                for vs in vac_skills:
                    chat_memory_service.db.record_skill_demand(
                        session_id=session_id,
                        skill_id=vs["id"],
                        skill_name=vs["name"],
                        category=vs["category"],
                        inquiry_type="vacancy_requirement",
                        company_name=lead_ctx.get("company_name")
                    )

                # Despacho en segundo plano de alerta por correo a Diego
                import asyncio
                from app.services.email_notification_service import email_notification_service
                asyncio.create_task(
                    email_notification_service.notify_recruiter_interaction(
                        event_type="📋 Evaluación de Vacante Técnica",
                        recruiter_name=lead_ctx.get("recruiter_name"),
                        company_name=lead_ctx.get("company_name"),
                        role_sought=match_data.roleDetected,
                        match_score=match_data.overallScore,
                        interview_modality=lead_ctx.get("interview_modality", "virtual"),
                        message_snippet=extracted_text or sanitized_msg,
                        session_id=session_id
                    )
                )
            except Exception as ex:
                logger.debug(f"Aviso registrando telemetría de vacante: {ex}")

            yield {"type": "match", "data": match_data.model_dump()}

        # 5. Generación de Enlaces de Agendamiento
        cta = {
            "calendarLink": SchedulerService.generate_google_calendar_link(),
            "whatsappLink": SchedulerService.generate_whatsapp_link(),
            "emailLink": SchedulerService.generate_email_link(),
            "phone": SchedulerService.DEFAULT_PHONE,
            "email": SchedulerService.DEFAULT_EMAIL,
            "interviewModality": lead_ctx["interview_modality"]
        }

        # 6. Generación de respuesta LLM en Streaming con memoria relacional
        yield {"type": "step", "label": "Redactando análisis ejecutivo..."}
        
        # Obtener historial previo para coherencia conversacional continua
        history_msgs = chat_memory_service.get_conversation_history(session_id, limit=8)
        # Excluir el mensaje recién guardado para que no se duplique en el prompt
        if history_msgs and history_msgs[-1].get("content") == sanitized_msg:
            previous_history = history_msgs[:-1]
        else:
            previous_history = history_msgs

        full_agent_response = ""
        async for chunk in llm_service.stream_chat_response(
            user_message=sanitized_msg,
            history=previous_history,
            attachment_text=extracted_text if extracted_text else None
        ):
            full_agent_response += chunk
            yield {"type": "text_delta", "delta": chunk}

        # Registrar la respuesta final en Memcache y Base de Datos
        chat_memory_service.record_message(
            session_id=session_id,
            sender="diego",
            content=full_agent_response
        )

        # 7. Evento de finalización
        yield {
            "type": "done",
            "sessionId": session_id,
            "cta": cta,
            "leadContext": lead_ctx
        }
