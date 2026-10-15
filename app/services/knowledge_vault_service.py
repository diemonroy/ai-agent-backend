"""
Knowledge Vault Service — Diego Monroy Personal Brand & Capability Engine (SSOT)
Carga, valida y expone el conocimiento estructurado de Marca, Producto y Servicio desde data/brand_knowledge/.
Provee capacidades de matching semántico de habilidades, extracción de perfiles y generación de contexto para el LLM.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("KnowledgeVaultService")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VAULT_DIR = BASE_DIR / "data" / "brand_knowledge"


class KnowledgeVaultService:
    """
    Gestor central de la Bóveda de Conocimiento (Knowledge Hub).
    Convierte a Diego Monroy en una plataforma estructurada y consultable.
    """

    def __init__(self, vault_dir: Path = VAULT_DIR):
        self.vault_dir = vault_dir
        self.identity: Dict[str, Any] = {}
        self.career_history: List[Dict[str, Any]] = []
        self.skills_taxonomy: Dict[str, Any] = {}
        self.credentials: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.case_studies: Dict[str, str] = {}
        self._flat_skills: List[Dict[str, Any]] = []

        self.reload()

    def reload(self):
        """Carga y parsea todos los archivos declarativos de la bóveda."""
        try:
            self.identity = self._load_yaml("identity.yaml")
            career_data = self._load_yaml("career_history.yaml")
            self.career_history = career_data.get("career_history", [])
            self.skills_taxonomy = self._load_yaml("skills_taxonomy.yaml")
            self.credentials = self._load_yaml("credentials_vault.yaml")
            self.services = self._load_yaml("service_offerings.yaml")
            self.case_studies = self._load_case_studies()
            self._flat_skills = self._build_flat_skills()

            logger.info(
                f"✅ Knowledge Vault cargado: {len(self.career_history)} roles, "
                f"{len(self._flat_skills)} habilidades indexadas, "
                f"{len(self.credentials.get('certifications', []))} certificaciones, "
                f"{len(self.case_studies)} casos de estudio."
            )
        except Exception as e:
            logger.error(f"Error cargando Knowledge Vault: {e}", exc_info=True)

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        path = self.vault_dir / filename
        if not path.exists():
            logger.warning(f"Archivo de bóveda no encontrado: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_case_studies(self) -> Dict[str, str]:
        case_studies = {}
        case_dir = self.vault_dir / "case_studies"
        if case_dir.exists():
            for md_file in case_dir.glob("*.md"):
                try:
                    with open(md_file, "r", encoding="utf-8") as f:
                        case_studies[md_file.stem] = f.read()
                except Exception as e:
                    logger.warning(f"No se pudo leer caso de estudio {md_file}: {e}")
        return case_studies

    def _build_flat_skills(self) -> List[Dict[str, Any]]:
        flat = []
        categories = self.skills_taxonomy.get("categories", {})
        for cat_key, cat_data in categories.items():
            cat_name = cat_data.get("category_name", cat_key)
            for skill in cat_data.get("skills", []):
                item = dict(skill)
                item["category_key"] = cat_key
                item["category_name"] = cat_name
                # Lista de términos a coincidir
                synonyms = [s.lower() for s in item.get("synonyms", [])]
                synonyms.append(item.get("name", "").lower())
                item["search_terms"] = list(set(synonyms))
                flat.append(item)
        return flat

    def match_skills_in_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Escanea un texto (descripción de vacante o pregunta de reclutador)
        y detecta qué habilidades del portafolio de Diego se mencionan.
        """
        if not text:
            return []
        text_lower = text.lower()
        matched = []

        for skill in self._flat_skills:
            for term in skill["search_terms"]:
                if term in text_lower:
                    matched.append({
                        "id": skill["id"],
                        "name": skill["name"],
                        "category": skill["category_name"],
                        "level": skill.get("level", "Avanzado"),
                        "years": skill.get("years", 3),
                        "certified": skill.get("certified", False),
                        "proof": skill.get("proof", "")
                    })
                    break
        return matched

    def get_system_prompt_context(self) -> str:
        """
        Genera el contexto unificado enriquecido para ser inyectado en el System Prompt del LLM.
        Reemplaza la versión estática anterior con datos vivos y estructurados de la bóveda.
        """
        brand = self.identity.get("brand", {})
        uvp = self.identity.get("unique_value_proposition", {})
        diffs = uvp.get("core_differentiators", [])
        diff_text = "\n".join([f"- **{d['title']}**: {d['description']} (Métrica: {d.get('metric', 'N/A')})" for d in diffs])

        certs = self.credentials.get("certifications", [])
        certs_text = "\n".join([f"- **{c['title']}** ({c['issuer']}, ID: {c.get('credential_id', 'Oficial')}, Vigencia: {c.get('issue_date', '')}-{c.get('expiration_date', '')})" for c in certs])

        edu = self.credentials.get("education", [])
        edu_text = "\n".join([f"- **{e['degree']}** — {e['institution']} ({e.get('year_graduated', '')})" for e in edu])

        exec_edu = self.credentials.get("executive_education", [])
        exec_text = "\n".join([f"- **{x['title']}** — {x['institution']} ({x.get('year', '')})" for x in exec_edu])

        skills_by_cat = {}
        for s in self._flat_skills:
            c = s["category_name"]
            skills_by_cat.setdefault(c, []).append(f"{s['name']} ({s.get('level', 'Avanzado')})")
        skills_text = "\n".join([f"- **{cat}**: {', '.join(slist)}" for cat, slist in skills_by_cat.items()])

        services = self.services.get("services", [])
        services_text = "\n".join([f"- **{srv['title']}**: {srv.get('engagement_model', '')} ({srv.get('location_mode', '')})" for srv in services])

        return f"""
IDENTIDAD & PROPUESTA ÚNICA DE VALOR (SSOT):
- Nombre: {brand.get('full_name', 'Diego Leonardo Monroy Durán')}
- Cargo actual: {brand.get('title', 'Tech Lead & Solutions Architect')} · {brand.get('sub_title', 'Cloud & GenAI Solutions')}
- Ubicación: {brand.get('location', 'Bogotá D.C., Colombia')}
- Contacto: diego.97duran@gmail.com | +57 310 800 9394
- Portfolio Web: https://diegomonroy.site | LinkedIn: https://linkedin.com/in/diemonroy
- Idiomas: Español (Nativo), Inglés (B2 Profesional / Fluido para negocios internacionales), Portugués (A2 Básico).

MANIFIESTO DE MARCA:
"{self.identity.get('brand_manifesto', '')}"

DIFERENCIADORES & CASOS DE ÉXITO CUANTIFICADOS:
{diff_text}

CERTIFICACIONES OFICIALES & ACREDITACIONES:
{certs_text}

FORMACIÓN ACADÉMICA Y EJECUTIVA:
{edu_text}
{exec_text}

MATRIZ DE CAPACIDADES Y HABILIDADES TÉCNICAS:
{skills_text}

CATÁLOGO DE SERVICIOS Y MODALIDADES DE CONTRATACIÓN:
{services_text}
"""


# Instancia Singleton
knowledge_vault_service = KnowledgeVaultService()
