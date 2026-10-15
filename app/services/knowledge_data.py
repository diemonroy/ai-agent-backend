"""
Diego Monroy Knowledge Base — Structured Domain Knowledge
Contiene todos los datos verificados, métricas de impacto, certificaciones,
respuestas a objeciones y propuesta de valor de Diego Leonardo Monroy Durán.
"""

from typing import Any

DIEGO_PROFILE: dict[str, Any] = {
    "name": "Diego Leonardo Monroy Durán",
    "headline": "Tech Lead & Solutions Architect · Cloud & GenAI Solutions",
    "location": "Bogotá D.C., Colombia",
    "phone": "+57 310 800 9394",
    "email": "diego.97duran@gmail.com",
    "linkedin": "https://linkedin.com/in/diemonroy",
    "github": "https://github.com/diemonroy",
    "portfolio": "https://diegomonroy.site",
    "experience_years": "5+ años liderando arquitectura de software y desarrollo empresarial; 8+ años en ingeniería",
    
    # Pilares de valor diferenciales
    "value_pillars": [
        {
            "pillar": "Arquitectura Limpia & Alta Disponibilidad (99.99% SLA)",
            "description": "Liderazgo técnico del CRM In-House de Banca Empresas en Banco de Bogotá (Grupo AVAL), centralizando clientes corporativos bajo Arquitectura Hexagonal y Domain-Driven Design (DDD).",
            "proof": "SLA garantizado del 99.99% en entorno de misión crítica bancaria con cero caídas no programadas."
        },
        {
            "pillar": "Inteligencia Artificial Generativa & Multi-Agent Systems",
            "description": "Diseño e implementación de sistemas agénticos con LangChain, LangGraph y bases de datos vectoriales integradas a BigQuery y LLMs (Gemini, OpenAI).",
            "proof": "Reducción del 40% en tiempos de consulta financiera y automatización de análisis de datos bancarios."
        },
        {
            "pillar": "Cloud & DevSecOps de Nivel Bancario",
            "description": "Google Cloud Certified Associate Cloud Engineer (ACE). Despliegues Zero-Downtime sobre Kubernetes (GKE), Google Cloud Run y pipelines CI/CD automatizados con escaneo SonarQube.",
            "proof": "Reducción de incidentes en producción en un 38% y cumplimiento estricto de OWASP Top 10 y PCI-DSS."
        },
        {
            "pillar": "Liderazgo Técnico, Gestión Ágil & Visión de Negocio",
            "description": "Especialista en Gerencia de Proyectos (PMI, Scrum, Kanban). Dirección de células de ingeniería, mentoría técnica, code reviews y articulación de roadmaps estratégicos con Vicepresidencias de Tecnología.",
            "proof": "Liderazgo de células de alto rendimiento con entregas predecibles en sprints continuos."
        }
    ],

    # Roles profesionales
    "experience": [
        {
            "role": "Tech Lead & Arquitecto de Software",
            "company": "Banco de Bogotá (Grupo AVAL)",
            "period": "Febrero 2022 — Presente",
            "location": "Bogotá, Colombia",
            "achievements": [
                "Lideró la arquitectura, desarrollo y puesta en marcha del CRM Corporativo de Banca Empresas.",
                "Orquestó flujos de agentes autónomos con LangChain y LangGraph integrados a BigQuery y bases de datos vectoriales, reduciendo latencia de consulta en un 40%.",
                "Estandarizó arquitecturas hexagonales desacopladas en Java (Spring Boot), Node.js y Python (FastAPI).",
                "Implementó pipelines DevSecOps con SonarQube y despliegues Zero-Downtime sobre Kubernetes y Cloud Run, reduciendo incidentes en un 38%.",
                "Aseguró cumplimiento financiero estricto bajo OWASP Top 10, autenticación OAuth2 / OIDC y auditorías de seguridad bancaria.",
                "Mentoreó a desarrolladores de software impulsando buenas prácticas, code reviews y cultura ágil."
            ]
        },
        {
            "role": "Desarrollador de Software Jr. / Ruta Digital",
            "company": "Banco de Bogotá",
            "period": "Agosto 2021 — Enero 2022",
            "location": "Bogotá, Colombia",
            "achievements": [
                "Desarrolló módulos reactivos en Angular consumiendo APIs RESTful empresariales.",
                "Implementó pruebas unitarias y de integración que garantizaron alta estabilidad funcional en el core bancario.",
                "Participó activamente en la transformación digital bancaria bajo marcos Scrum y Azure DevOps."
            ]
        }
    ],

    # Certificaciones Oficiales
    "certifications": [
        {
            "name": "Google Cloud Certified: Associate Cloud Engineer (ACE)",
            "issuer": "Google Cloud",
            "validity": "2026 — 2029",
            "badge_id": "Credly ID: 189954",
            "priority": "Alta / Clave en Cloud"
        },
        {
            "name": "AWS Academy Graduate: Cloud Foundations & Machine Learning",
            "issuer": "AWS Academy / Universidad de los Andes",
            "validity": "Julio 2022"
        },
        {
            "name": "GCP Skill Badge: Implement Load Balancing on Compute Engine",
            "issuer": "Google Cloud Skills Boost",
            "validity": "Diciembre 2025"
        },
        {
            "name": "Participante HackaPrompt GenAI & LLM Security",
            "issuer": "Microsoft & Banco de Bogotá",
            "validity": "2024"
        }
    ],

    # Educación Superior
    "education": [
        {
            "degree": "Especialización en Gerencia de Proyectos",
            "institution": "Universidad de Boyacá",
            "year": "2023",
            "focus": "Metodologías Ágiles (Scrum, Kanban), Gestión de Riesgos, Estándares PMI"
        },
        {
            "degree": "Ingeniería Mecatrónica",
            "institution": "Universidad de Boyacá",
            "year": "2022",
            "focus": "Sistemas Embebidos, Automatización de Procesos, Algoritmos, Control Inteligente"
        },
        {
            "degree": "Competencias Gerenciales I",
            "institution": "Universidad de los Andes",
            "year": "2025",
            "focus": "Liderazgo de equipos, negociación estratégica y comunicación asertiva"
        }
    ],

    # Stack Tecnológico Detallado
    "skills": {
        "cloud_and_architecture": [
            "Google Cloud Platform (GCP ACE Certified)", "AWS", "Azure",
            "Kubernetes (GKE)", "Docker", "Terraform (IaC)",
            "Clean Architecture (Hexagonal)", "Domain-Driven Design (DDD)", "Microservicios",
            "Event-Driven Architecture", "SLA 99.99%", "High-Throughput Systems"
        ],
        "generative_ai_and_data": [
            "LangChain", "LangGraph", "Multi-Agent Workflows",
            "Google Gemini API", "OpenAI GPT", "RAG Empresarial (Retrieval-Augmented Generation)",
            "Vector Databases (FAISS, Chroma, Pinecone)", "BigQuery & BigQuery ML",
            "Prompt Engineering", "Guardrails & LLM Security"
        ],
        "backend": [
            "Java (Spring Boot)", "Python (FastAPI, Flask)", "Node.js (Express, NestJS)",
            "TypeScript", "RESTful APIs", "GraphQL", "gRPC", "OAuth2 / OIDC", "JWT"
        ],
        "databases": [
            "Google Cloud BigQuery", "PostgreSQL", "MySQL", "SQL Server", "Redis (Cache & Sessions)", "MongoDB"
        ],
        "frontend": [
            "Angular (v14 a v17+ Standalone Components, Signals, RxJS)",
            "TypeScript", "JavaScript (ES6+)", "HTML5 / SCSS", "Responsive Design", "Apple HIG Dark Glass"
        ],
        "devsecops": [
            "CI/CD Pipelines (GitHub Actions, Azure DevOps, GitLab CI)",
            "SonarQube (Static Code Analysis)", "Zero-Downtime Deployments (Blue/Green, Rolling)",
            "OWASP Top 10", "PCI-DSS Banking Standards", "Git & Semantic Versioning"
        ],
        "languages": [
            {"language": "Español", "level": "Nativo"},
            {"language": "Inglés", "level": "Profesional / B2 Avanzado (Fluidez técnica y corporativa)"},
            {"language": "Portugués", "level": "Básico / A2"}
        ]
    },

    # Respuestas a Objeciones Típicas de Reclutadores
    "objection_answers": {
        "remote_work": "Diego tiene amplia experiencia trabajando en modelos 100% remotos e híbridos con células ágiles de ingeniería, gestionando comunicación asíncrona y sincronizaciones estratégicas.",
        "leadership_experience": "Diego se desempeña activamente como Tech Lead en Banco de Bogotá, liderando arquitectónicamente a ingenieros de software, definiendo estándares de código, mentoring y planificando roadmaps con Vicepresidencias.",
        "financial_regulation": "Diego está acostumbrado a trabajar bajo las regulaciones bancarias y de auditoría más estrictas (Superintendencia Financiera, OWASP, PCI-DSS, segregación de ambientes).",
        "generative_ai_depth": "A diferencia de desarrolladores que sólo consumen APIs de chat, Diego diseña arquitecturas agénticas completas con LangGraph, memoria conversacional en Redis, guardrails, trazabilidad de tokens y bases vectoriales integradas a BigQuery."
    }
}


def get_diego_knowledge_summary() -> str:
    """Retorna un texto enriquecido para ser inyectado en el System Prompt."""
    p = DIEGO_PROFILE
    pillars_text = "\n".join([f"- **{item['pillar']}**: {item['description']} (Evidencia: {item['proof']})" for item in p["value_pillars"]])
    
    certs_text = "\n".join([f"- {c['name']} ({c['issuer']}, {c['validity']})" for c in p["certifications"]])
    
    return f"""
DATOS PRINCIPALES:
- Nombre: {p['name']}
- Cargo actual: {p['headline']}
- Ubicación: {p['location']}
- Contacto: {p['email']} | {p['phone']}
- LinkedIn: {p['linkedin']} | Web: {p['portfolio']}
- Experiencia: {p['experience_years']}

PILARES DE VALOR CLAVE:
{pillars_text}

CERTIFICACIONES OFICIALES:
{certs_text}

STACK TÉCNICO DESTACADO:
- Cloud & Arquitectura: {', '.join(p['skills']['cloud_and_architecture'])}
- IA Generativa & Agentes: {', '.join(p['skills']['generative_ai_and_data'])}
- Backend & APIs: {', '.join(p['skills']['backend'])}
- Frontend: {', '.join(p['skills']['frontend'])}
- DevSecOps & Seguridad: {', '.join(p['skills']['devsecops'])}
- Idiomas: Español (Nativo), Inglés (B2 Profesional / Fluido para trabajar internacionalmente), Portugués (A2).
"""
