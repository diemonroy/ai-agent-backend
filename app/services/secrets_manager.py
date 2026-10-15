"""
Enterprise Secrets Management Service
Inspirado en la arquitectura bancaria de bbog-bebd-gcm-ml:
Soporta resolución segura desde Google Cloud Secret Manager (con validación CRC32C)
o variables de entorno / .env local protegido, garantizando enmascaramiento en logs
y prevención de fugas de credenciales.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging con formato seguro
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SecretsManager")

# Cargar .env si existe en la raíz de ai-agent-backend
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)


def mask_secret(value: Optional[str], show_chars: int = 4) -> str:
    """Enmascara un secreto para su impresión segura en logs (ej. AIza...9xQ2)."""
    if not value:
        return "[NOT_SET]"
    if len(value) <= show_chars * 2:
        return "****"
    return f"{value[:show_chars]}...{value[-show_chars:]} ({len(value)} chars)"


class SecretsManager:
    _instance: Optional["SecretsManager"] = None
    _cached_secrets: dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecretsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.use_gcp = os.getenv("USE_GCP_SECRET_MANAGER", "false").lower() in ("true", "1", "yes")
        self.gcp_project = os.getenv("GCP_PROJECT")
        self.project_number = os.getenv("PROJECT_NUMBER")

    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Resuelve un secreto con la siguiente prioridad:
        1. Caché interna en memoria.
        2. Google Cloud Secret Manager (si use_gcp es True y hay credenciales GCP).
        3. Variable de entorno del sistema o archivo .env.
        """
        # 1. Caché
        if secret_name in self._cached_secrets:
            return self._cached_secrets[secret_name]

        val: Optional[str] = None

        # 2. Google Cloud Secret Manager
        if self.use_gcp and self.project_number:
            try:
                val = self._fetch_from_gcp_secret_manager(secret_name)
                if val:
                    logger.info(f"Secreto '{secret_name}' resuelto exitosamente desde GCP Secret Manager: {mask_secret(val)}")
            except Exception as e:
                logger.warning(f"No fue posible consultar GCP Secret Manager para '{secret_name}': {e}. Usando fallback local...")

        # 3. Fallback a Variables de Entorno
        if not val:
            val = os.getenv(secret_name)
            if not val and fallback_env_var:
                val = os.getenv(fallback_env_var)
            if val:
                logger.info(f"Secreto '{secret_name}' resuelto desde variables de entorno: {mask_secret(val)}")

        if val:
            self._cached_secrets[secret_name] = val
        else:
            logger.warning(f"Secreto '{secret_name}' no encontrado en ninguna fuente configurada.")

        return val

    def _fetch_from_gcp_secret_manager(self, secret_name: str) -> Optional[str]:
        """Consulta Google Cloud Secret Manager con validación de checksum CRC32C."""
        try:
            from google.cloud import secretmanager
            import google_crc32c

            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_number}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})

            # Verificación estricta de integridad de datos (patrón bbog-bebd-gcm-ml)
            crc32c = google_crc32c.Checksum()
            crc32c.update(response.payload.data)
            if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
                logger.error(f"Corrupción de datos detectada en secreto '{secret_name}' de GCP Secret Manager.")
                return None

            return response.payload.data.decode("UTF-8").strip()
        except ImportError:
            logger.warning("Librerías de Google Cloud Secret Manager no instaladas.")
            return None
        except Exception as e:
            logger.error(f"Error accediendo a GCP Secret Manager para '{secret_name}': {e}")
            return None

    def get_gemini_api_key(self) -> Optional[str]:
        """Atajo seguro para la clave de Google Gemini."""
        return self.get_secret("GOOGLE_GEMINI_KEY", fallback_env_var="GEMINI_API_KEY")

    def get_openai_api_key(self) -> Optional[str]:
        """Atajo seguro para la clave de OpenAI (si se usa)."""
        return self.get_secret("OPENAI_API_KEY")


# Singleton export
secrets_manager = SecretsManager()
