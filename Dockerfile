# ==============================================================================
# DIEGO MONROY — EXECUTIVE AI TALENT AGENT (PRODUCTION DOCKERFILE)
# Target: Google Cloud Run (dm-portfolio-511707)
# Architecture: Cloud-Native, Zero-Downtime, Non-Root User (Banking-Grade)
# ==============================================================================

# Etapa 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Etapa 2: Runner final minimalista
FROM python:3.11-slim AS runner

WORKDIR /app

# Variables de entorno Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    ENVIRONMENT=production \
    PATH=/home/appuser/.local/bin:$PATH

# Instalar dependencias mínimas de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios root (estándar bancario DevSecOps)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

# Copiar paquetes de Python instalados en el builder
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copiar código del backend y herramientas
COPY --chown=appuser:appgroup app /app/app
COPY --chown=appuser:appgroup inspect_db.py /app/inspect_db.py

# Crear directorio para base de datos SQLite y backups con permisos adecuados
RUN mkdir -p /app/data/backups && chown -R appuser:appgroup /app/data

USER appuser

EXPOSE 8080

# Health check para Cloud Run y Kubernetes
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Comando de arranque optimizado para Cloud Run (toma dinámicamente la variable $PORT)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2 --proxy-headers"]
