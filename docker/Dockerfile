# ========================================
# DETECTOR DE PELÍCULAS DUPLICADAS - DOCKER
# ========================================
# Optimizado para Synology NAS
#
# El contexto de build es la RAÍZ del repo, no esta carpeta docker/ —
# así la imagen siempre lleva el código real y actual (src/, main.py),
# nunca una copia congelada. Constrúyela con build_docker_image.bat
# desde la raíz, o a mano:
#
#   docker build -f docker/Dockerfile -t find-video-duplicates:latest .
#
# La imagen NUNCA lleva datos personales horneados dentro: config.json
# y .env se excluyen del build vía .dockerignore y se montan como
# volúmenes en tiempo de ejecución (ver docker-compose-synology.yml).
# Por eso la misma imagen sirve tanto para ti como para compartirla.

FROM python:3.11-slim

# Metadatos
LABEL maintainer="Carlos"
LABEL description="Detector de Películas Duplicadas con IMDB, Telegram y Plex"
LABEL version="3.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCKER_CONTAINER=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias del sistema (incluye ffmpeg, que usa la app para
# extraer fotogramas de comparación — sin él esa función se desactiva sola)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias primero (aprovecha la cache de Docker: si solo
# cambia el código, no hace falta reinstalar todo de nuevo)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código real de la aplicación (respeta .dockerignore, que
# excluye config.json, .env, venv/, tests, etc.)
COPY main.py app_simple.py ./
COPY src/ ./src/

# Directorios de datos persistentes (normalmente montados como volumen,
# pero deben existir igualmente por si alguien corre la imagen sin ellos)
RUN mkdir -p /app/data /app/logs /app/scan_data && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# main.py ya detecta DOCKER_CONTAINER=true y arranca en modo headless,
# sin intentar abrir un navegador — mismo script que se usa en local.
CMD ["python", "main.py"]
