#!/usr/bin/env bash
# ==============================================================================
# DIEGO MONROY — GOOGLE CLOUD RUN DEPLOYMENT SCRIPT
# Project ID: dm-portfolio-511707
# Architecture: Cloud Run (Serverless 0-to-N) + Secret Manager + Artifact Registry
# ==============================================================================

set -euo pipefail

# ── 1. CONFIGURACIÓN DEL PROYECTO ─────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT:-dm-portfolio-511707}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="diego-ai-agent"
REPO_NAME="diego-portfolio-repo"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"

echo "======================================================================"
echo "🚀 DESPLIEGUE A PRODUCCIÓN — DIEGO MONROY AI TALENT AGENT"
echo "======================================================================"
echo "  • Proyecto GCP:    ${PROJECT_ID}"
echo "  • Región:          ${REGION}"
echo "  • Servicio:        ${SERVICE_NAME}"
echo "  • Imagen Destino:  ${IMAGE_TAG}"
echo "======================================================================"

# ── 2. VERIFICACIÓN DE GCLOUD CLI ─────────────────────────────────────────────
if ! command -v gcloud &> /dev/null; then
    if [ -f "/Users/DMONRO1/Downloads/google-cloud-sdk/bin/gcloud" ]; then
        export PATH="/Users/DMONRO1/Downloads/google-cloud-sdk/bin:$PATH"
    fi
fi

if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: 'gcloud' CLI no está instalado o no se encuentra en el PATH."
    echo "💡 Puedes instalarlo con: brew install --cask google-cloud-sdk"
    echo "   O ejecutar este script directamente desde Google Cloud Shell en tu navegador:"
    echo "   https://shell.cloud.google.com/?project=${PROJECT_ID}"
    exit 1
fi

echo "🔐 Configurando proyecto activo en gcloud..."
gcloud config set project "${PROJECT_ID}"

# ── 3. HABILITAR SERVICIOS Y APIS NECESARIAS ──────────────────────────────────
echo "⚙️ Habilitando APIs requeridas en Google Cloud..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}"

# ── 4. CREAR REPOSITORIO DE ARTIFACT REGISTRY ────────────────────────────────
echo "📦 Verificando repositorio en Artifact Registry..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" &> /dev/null; then
    echo "  -> Creando repositorio Docker '${REPO_NAME}' en ${REGION}..."
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Repositorio de imágenes Docker para Portfolio de Diego Monroy" \
        --project="${PROJECT_ID}"
else
    echo "  -> Repositorio '${REPO_NAME}' ya existe."
fi

# ── 5. GESTIÓN DE SECRETOS EN SECRET MANAGER ─────────────────────────────────
echo "🔒 Verificando secretos en Google Cloud Secret Manager..."

# Leer llave local si existe en .env
LOCAL_GEMINI_KEY=""
if [ -f ".env" ]; then
    LOCAL_GEMINI_KEY=$(grep "^GOOGLE_GEMINI_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
fi

if ! gcloud secrets describe GOOGLE_GEMINI_KEY --project="${PROJECT_ID}" &> /dev/null; then
    echo "  -> Creando secreto 'GOOGLE_GEMINI_KEY' en Secret Manager..."
    if [ -n "${LOCAL_GEMINI_KEY}" ]; then
        echo -n "${LOCAL_GEMINI_KEY}" | gcloud secrets create GOOGLE_GEMINI_KEY \
            --data-file=- \
            --replication-policy="automatic" \
            --project="${PROJECT_ID}"
        echo "  ✅ Secreto creado e inicializado desde .env local."
    else
        echo "⚠️ No se detectó GOOGLE_GEMINI_KEY en .env local."
        echo "  -> Creando secreto vacío. Recuerda actualizarlo en GCP Console."
        echo -n "PENDIENTE_DE_CONFIGURAR" | gcloud secrets create GOOGLE_GEMINI_KEY \
            --data-file=- \
            --replication-policy="automatic" \
            --project="${PROJECT_ID}"
    fi
else
    echo "  -> Secreto 'GOOGLE_GEMINI_KEY' ya existe en Secret Manager."
fi

# ── 6. COMPILACIÓN DE LA IMAGEN DOCKER CON CLOUD BUILD ────────────────────────
echo "🔨 Compilando imagen Docker en Cloud Build (arquitectura linux/amd64 nativa)..."
gcloud builds submit --tag "${IMAGE_TAG}" . --project="${PROJECT_ID}"

# ── 7. DESPLIEGUE A CLOUD RUN ─────────────────────────────────────────────────
echo "🚀 Desplegando a Google Cloud Run..."
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Asegurar permisos del Service Account de Cloud Run para leer Secret Manager
echo "🛡️ Asignando permisos al Service Account de Cloud Run (${COMPUTE_SA})..."
gcloud secrets add-iam-policy-binding GOOGLE_GEMINI_KEY \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" > /dev/null || true

# Despliegue con escalado a cero (Costo $0 cuando no hay visitas)
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_TAG}" \
    --platform=managed \
    --region="${REGION}" \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --set-env-vars="ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID}" \
    --set-secrets="GOOGLE_GEMINI_KEY=GOOGLE_GEMINI_KEY:latest" \
    --project="${PROJECT_ID}"

# ── 8. OBTENER URL PÚBLICA ────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")

echo ""
echo "======================================================================"
echo "🎉 ¡DESPLIEGUE COMPLETADO EXITOSAMENTE!"
echo "======================================================================"
echo "  • URL Pública Backend:    ${SERVICE_URL}"
echo "  • Swagger UI (Docs):      ${SERVICE_URL}/docs"
echo "  • Health Check:           ${SERVICE_URL}/health"
echo "  • Knowledge Vault:        ${SERVICE_URL}/api/knowledge/vault"
echo "  • Costo en Reposo:        $0.00 USD (Escala a cero automáticamente)"
echo "======================================================================"
