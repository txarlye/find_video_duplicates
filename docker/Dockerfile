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

# ---- Stage 1: build del frontend (React + Vite) ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: la app de Python (FastAPI) ----
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Carlos"
LABEL description="Detector de Películas Duplicadas con IMDB, Telegram y Plex"
LABEL version="4.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCKER_CONTAINER=true
ENV API_SERVER_ADDRESS=0.0.0.0
ENV API_PORT=8000

# El programador interno de Propuestas (Configuración → 📅 Programación)
# dispara el escaneo a la hora local del contenedor — sin esto, Debian
# usa UTC y la hora configurada no coincidiría con tu hora real.
# Sobrescribible con TZ=... en docker-compose si compartes la imagen.
ENV TZ=Europe/Madrid

# Instalar dependencias del sistema (incluye ffmpeg, que usa la app para
# extraer fotogramas de comparación, y tzdata para que TZ tenga efecto)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    ffmpeg \
    tzdata \
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
COPY main.py scheduled_scan.py ./
COPY src/ ./src/

# Frontend ya construido en el stage 1 — FastAPI lo sirve directamente
# (src/api/main.py monta frontend/dist/ si existe), sin nginx.
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Directorios de datos persistentes (normalmente montados como volumen,
# pero deben existir igualmente por si alguien corre la imagen sin ellos).
# Sin usuario no-root: los volúmenes montados (DATA_PATH, LOGS_PATH,
# MOVIES_PATH...) son carpetas reales del NAS con el dueño que tengan
# en Synology, y la app ya necesita escritura ahí — para software
# personal de un solo usuario, exigir un UID concreto solo añade
# fricción (chown manual en DSM) sin aportar aislamiento real.
RUN mkdir -p /app/data /app/logs /app/scan_data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8000}/api/health || exit 1

# main.py ya detecta DOCKER_CONTAINER=true y arranca sin intentar abrir
# un navegador — mismo script que se usa en local.
CMD ["python", "main.py"]
