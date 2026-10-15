#!/usr/bin/env bash
# Script para iniciar el servidor de backend del Agente de IA

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "🚀 Iniciando Diego Monroy — Executive AI Talent Agent"
echo "=========================================================="

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual Python..."
    python3 -m venv venv
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

echo "📥 Verificando dependencias requeridas..."
pip install -q -r requirements.txt

echo "🛡️ Verificando estado de configuración y secretos..."
if [ ! -f ".env" ]; then
    echo "⚠️ Archivo .env no encontrado. Copiando desde .env.example..."
    cp .env.example .env
fi

echo "🟢 Servidor escuchando en http://0.0.0.0:8000"
echo "📖 Documentación interactiva Swagger: http://localhost:8000/docs"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
