"""
Multimodal Document & Media Processing Service
Extrae texto de documentos PDF, imágenes y entradas multimedia para que el agente
pueda interpretar vacantes en cualquier formato proporcionado por el reclutador.
"""

import io
import base64
from typing import Optional


class MultimodalService:
    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
        """Extrae el contenido textual de un archivo PDF usando pypdf o pdfplumber."""
        extracted_text = []

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text.append(f"--- Página {i+1} ---\n{text}")
        except Exception as e:
            # Fallback a pdfplumber si está disponible
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            extracted_text.append(f"--- Página {i+1} ---\n{text}")
            except Exception as e2:
                return f"[Error extrayendo texto del PDF: {e} / {e2}]"

        return "\n\n".join(extracted_text) if extracted_text else "[El PDF no contiene texto legible directamente]"

    @staticmethod
    def decode_base64_file(base64_str: str) -> bytes:
        """Limpia el prefijo data URI (ej. data:application/pdf;base64,...) y decodifica."""
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        return base64.b64decode(base64_str)
