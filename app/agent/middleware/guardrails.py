"""
Guardrails & Security Middleware
Filtro de seguridad contra inyecciones de prompt, exfiltración de secretos
y desvío del alcance del producto (Diego Monroy).
"""

import re
from typing import Tuple


class GuardrailsInterceptor:
    # Patrones de inyección de prompt conocidos
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"olvida\s+(todas\s+las\s+)?instrucciones\s+anteriores",
        r"act\s+as\s+dan",
        r"jailbreak",
        r"modo\s+desarrollador",
        r"developer\s+mode",
        r"system\s+prompt",
        r"reveal\s+(your\s+)?(prompt|secrets|api_key|keys)",
        r"dime\s+(tus\s+)?(secretos|claves|llaves|api_key|variables)",
        r"mu[eé]strame\s+tu\s+prompt",
    ]

    # Patrones de exfiltración de credenciales
    SECRET_EXFILTRATION_PATTERNS = [
        r"api[-_]?key",
        r"secret[-_]?manager",
        r"bearer\s+[a-zA-Z0-9_\-\.]+",
        r"password",
        r"contrase[ñn]a",
        r"token",
        r"aiza[0-9a-za-z-_]{35}",
    ]

    @classmethod
    def inspect_and_sanitize(cls, message: str) -> Tuple[bool, str, str | None]:
        """
        Analiza el mensaje entrante.
        Retorna: (is_safe: bool, sanitized_message: str, warning_reason: str | None)
        """
        lowered = message.lower()

        # 1. Chequeo de inyección
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                return (
                    False,
                    message,
                    "Intento de inyección de prompt o violación de instrucciones del sistema detectado."
                )

        # 2. Chequeo de intento de pedir secretos
        for pattern in cls.SECRET_EXFILTRATION_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE) and any(w in lowered for w in ["dime", "muéstrame", "show", "print", "reveal", "cuál es", "cual es"]):
                return (
                    False,
                    message,
                    "Intento de exfiltración de credenciales o secretos internos bloqueado por seguridad."
                )

        # 3. Limpieza de caracteres de control
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", message).strip()
        return (True, sanitized, None)
