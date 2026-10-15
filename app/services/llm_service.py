"""
LLM Service & Model Factory
Inicializa de forma segura el modelo LLM (Google Gemini)
empleando SecretsManager para la inyección de credenciales sin fugas.
Enfocado en respuestas cortas, estratégicas, consultivas y relacionales.
"""

import os
import re
import json
import logging
import asyncio
from typing import AsyncGenerator, Optional, Any, List, Dict
from app.services.secrets_manager import secrets_manager, mask_secret
from app.services.knowledge_data import DIEGO_PROFILE, get_diego_knowledge_summary
from app.services.scheduler_service import SchedulerService

logger = logging.getLogger("LLMService")


class LLMService:
    def __init__(self):
        self.gemini_key = secrets_manager.get_gemini_api_key()
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.has_live_llm = bool(self.gemini_key and not self.gemini_key.startswith("AIzaSy..."))
        
        if self.has_live_llm:
            logger.info(f"LLM Activo: Google Gemini ({self.model_name}) con credenciales protegidas: {mask_secret(self.gemini_key)}")
        else:
            logger.warning("No se detectó GOOGLE_GEMINI_KEY válida en Secret Manager ni en .env. Modo Fallback Heurístico Activo.")

    def get_system_prompt(self) -> str:
        from app.services.knowledge_vault_service import knowledge_vault_service
        try:
            knowledge = knowledge_vault_service.get_system_prompt_context()
        except Exception as e:
            logger.warning(f"Fallback a knowledge_data debido a: {e}")
            knowledge = get_diego_knowledge_summary()

        return f"""IDENTIDAD Y VOZ:
Estás hablando DIRECTAMENTE COMO DIEGO LEONARDO MONROY DURÁN.
Rol: Tech Lead & Solutions Architect.
Ubicación: Resides en Bogotá, Colombia (disponible para trabajo presencial en Bogotá, híbrido o remoto).

REGLA FUNDAMENTAL DE LONGITUD Y BREVEDAD:
- TUS RESPUESTAS DEBEN SER CORTAS, ESTRATÉGICAS Y AL GRANO (MÁXIMO 2 PÁRRAFOS BREVES, ENTRE 65 Y 115 PALABRAS EN TOTAL).
- ESTRICTAMENTE PROHIBIDO enviar tutoriales, listas de pasos técnicos, manuales o la solución técnica resuelta de inmediato.
- Habla como un consultor y arquitecto senior de alto impacto: seguro de sus capacidades, empático y orientado al negocio.

ESTRATEGIA CONSULTIVA — CAPTURAR INFORMACIÓN Y AJUSTAR EL PERFIL A LA VACANTE / NECESIDAD:
Tu objetivo primordial como Diego NO es regalar la solución técnica servida en bandeja. Tu objetivo es ADQUIRIR INFORMACIÓN CLAVE DEL RECLUTADOR O CLIENTE para ajustar tu perfil a la vacante o reto específico, y proponer un espacio de análisis previo:

1. **Reafirma tu conocimiento y habilidades con total seguridad**:
   - Deja siempre muy claro que TIENES el conocimiento, la experiencia y las habilidades técnicas de sobra (Tech Lead & Solutions Architect, Google Cloud Certified ACE, liderazgo en banca con 99.99% SLA en Banco de Bogotá, sistemas agénticos con LangChain/LangGraph, microservicios y nube) para liderar y resolver cualquier reto de este calibre.
2. **No des la solución de entrada; indaga su contexto**:
   - En lugar de ponerte a explicar cómo harías el software, haz 1 o 2 preguntas estratégicas para adquirir información del reclutador o cliente:
     * ¿Cuál es la vacante, rol o reto específico que necesitan cubrir?
     * ¿En qué estado actual se encuentra el negocio, el proceso o el sistema hoy?
     * ¿Qué herramientas, CRM o stack tecnológico manejan actualmente?
     * ¿Cuáles son las principales metas o dolores del negocio?
3. **Propón un análisis completo (proceso, estado y negocio)**:
   - Explica que con tus habilidades y experiencia, más un análisis completo del proceso, estado actual y objetivos del negocio, encontrarán y diseñarán juntos la solución perfecta que se acomode con total precisión a sus necesidades.
4. **Cierra invitando a agendar**:
   - Invítalo cordialmente a agendar una llamada breve (o reunión presencial si están en Bogotá) para revisar a fondo ese contexto y diseñar la propuesta ideal a su medida.

TONO GENERAL:
- Cálido, humano, de tú a tú, como dos colegas charlando en un café de ingeniería.
- Si saludan o preguntan quién eres o qué haces, responde amablemente en 1 o 2 párrafos cortos y haz UNA sola pregunta abierta amistosa al final para indagar sobre su empresa o proyecto.
- Si proponen una reunión presencial en Bogotá, confirma de inmediato que vives en Bogotá y te encanta el cara a cara para conectar con el equipo.

INFORMACIÓN TÉCNICA DE REFERENCIA (ÚSALA SOLO COMO CONTEXTO, NO RECITES TODO):
{knowledge}
"""

    async def stream_chat_response(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        attachment_text: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Genera la respuesta token a token (streaming) para SSE con memoria conversacional."""
        system_prompt = self.get_system_prompt()
        prompt_with_context = user_message
        if attachment_text:
            prompt_with_context = f"[DOCUMENTO / VACANTE ADJUNTA]:\n{attachment_text}\n\n[MENSAJE DEL CLIENTE/RECLUTADOR]:\n{user_message}"

        if self.has_live_llm:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.gemini_key)

                contents = []
                # Incluir turnos previos para coherencia conversacional
                if history:
                    for h in history[-8:]:
                        role = "user" if h.get("role") == "user" else "model"
                        txt = (h.get("content") or "").strip()
                        if txt:
                            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=txt)]))

                # Mensaje actual
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt_with_context)]))

                response_stream = client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.6,
                    )
                )

                has_emitted = False
                for chunk in response_stream:
                    if chunk.text:
                        has_emitted = True
                        yield chunk.text
                if has_emitted:
                    return
            except Exception as e:
                logger.error(f"Error en llamada a Gemini ({self.model_name}): {e}. Activando generador conversacional...")

        # Fallback Heurístico Breve y Consultivo si falla la red externa
        async for chunk in self._fallback_knowledge_stream(user_message, history, attachment_text):
            yield chunk

    async def _fallback_knowledge_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        attachment_text: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generador heurístico conversacional breve, consultivo y al punto."""
        msg_lower = (message + " " + (attachment_text or "")).lower().strip()

        # 1. Seguridad
        if any(w in msg_lower for w in ["secret", "api_key", "password", "token", "prompt", "credencial", "system prompt", "jailbreak", "claves"]):
            reply = (
                "Como arquitecto de software y certificado en Google Cloud, la seguridad es prioritaria para mí. "
                "Mis credenciales y reglas operativas están protegidas bajo prácticas DevSecOps bancarias.\n\n"
                "¿Te gustaría que conversemos sobre mi experiencia implementando seguridad y mitigación OWASP?"
            )

        # 2. Propuesta de desarrollo de agente / software / caso de negocio
        elif any(w in msg_lower for w in ["puedes desarrollar", "puedes crear", "puedes hacer", "fuerza comercial", "estrategia de venta", "desarrollar un agente", "crear un agente", "desarrollar", "construir"]):
            reply = (
                "¡Por supuesto! Cuento con todo el conocimiento técnico, el liderazgo y las habilidades necesarias en sistemas agénticos (LangChain/LangGraph), arquitecturas cloud y microservicios para liderar este tipo de proyectos con total solvencia.\n\n"
                "Más que plantear una solución a ciegas, mi prioridad es entender su contexto: ¿qué vacante o reto específico buscan cubrir, cómo opera actualmente su proceso comercial y qué herramientas o CRM tienen hoy? Con mis habilidades y un análisis completo del proceso, estado y objetivos de su negocio, encontraremos la solución que se acomode con exactitud a lo que necesitan. ¿Te parece si agendamos una llamada corta para profundizar en su escenario?"
            )

        # 3. Presencial en Bogotá
        elif any(t in msg_lower for t in ["presencial", "en persona", "en la oficina", "en nuestras oficinas", "venir a la oficina", "tomarnos un café", "en bogotá", "en bogota"]):
            reply = (
                "¡Me parecería una excelente idea! Vivo en **Bogotá**, así que tengo total disponibilidad para acercarme a sus oficinas, "
                "conocer al equipo en persona y discutir los retos de arquitectura en un tablero.\n\n"
                "¿En qué sector o sede están ubicados? Si gustas, podemos coordinar el espacio directamente por WhatsApp (+57 310 800 9394) o agendar en Google Calendar."
            )

        # 4. "¿Quién eres?"
        elif any(w in msg_lower for w in ["quien eres", "quién eres", "presentate", "preséntate", "con quien hablo", "con quién hablo"]):
            reply = (
                "¡Hola! Qué gusto saludarte. Soy **Diego Leonardo Monroy Durán**, Tech Lead y Solutions Architect radicado en Bogotá.\n\n"
                "Lidero células de ingeniería y diseño arquitecturas críticas en la nube (SLA 99.99% en Banco de Bogotá) y desarrollo sistemas agénticos con Inteligencia Artificial Generativa. ¿De qué empresa me escribes hoy?"
            )

        # 5. "¿Qué haces?"
        elif any(w in msg_lower for w in ["que haces", "qué haces", "a que te dedicas", "a qué te dedicas", "cual es tu rol"]):
            reply = (
                "En mi día a día lidero células técnicas y diseño arquitecturas escalables en la nube (GCP, AWS, Kubernetes, microservicios), "
                "y llevo la IA Generativa a producción mediante sistemas multi-agente que resuelven retos de negocio.\n\n"
                "¿En qué desafío técnico o proyecto están enfocados actualmente en tu equipo?"
            )

        # 6. Saludo cordial simple
        elif msg_lower in ["hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hey", "hi", "hello"]:
            reply = (
                "¡Hola! Qué gusto saludarte, bienvenido a mi portafolio. Soy Diego Monroy.\n\n"
                "¿Cómo estás hoy? Cuéntame, ¿de qué empresa o proyecto me visitas?"
            )

        # 7. Conversación general
        else:
            reply = (
                "Totalmente de acuerdo. Con mi experiencia como Tech Lead y Arquitecto de Soluciones Cloud e IA, "
                "me enfoco en entender el contexto del negocio antes de plantear la arquitectura técnica ideal.\n\n"
                "Cuéntame un poco más sobre el escenario que tienen en mente y con gusto lo analizamos."
            )

        for word in reply.split(" "):
            yield word + " "
            await asyncio.sleep(0.015)


llm_service = LLMService()
