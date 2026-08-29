#!/bin/bash
# Construye la imagen Docker y la exporta a .imagen_docker/ (gitignored)
# junto con el docker-compose.yml y env.template, listos para copiar a
# tu NAS/Portainer — equivalente a build_docker_image.bat pero para
# Linux/Mac/Git Bash, y sin el paso interactivo: aquí SIEMPRE exporta,
# porque para eso existe esta carpeta.
#
# Contexto de build = raíz del repo (este script vive ahí), receta =
# docker/Dockerfile. La imagen sigue siendo genérica: config.json y
# .env nunca se hornean dentro, se montan como volumen en tiempo de
# ejecución (ver docker/docker-compose-synology.yml).
set -e
cd "$(dirname "$0")"

IMAGE_NAME="find-video-duplicates"
TAG="latest"
OUT_DIR=".imagen_docker"

if ! command -v docker &> /dev/null; then
    echo "❌ No se encuentra 'docker' en el PATH. Instala/abre Docker Desktop primero."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker no está arrancado. Abre Docker Desktop y vuelve a intentarlo."
    exit 1
fi

echo "🐳 Construyendo imagen ${IMAGE_NAME}:${TAG}..."
echo "   (contexto = raíz del repo, receta = docker/Dockerfile — incluye el build"
echo "   del frontend React, necesita internet para 'npm ci')"
echo

docker build -f docker/Dockerfile -t "${IMAGE_NAME}:${TAG}" .

echo
echo "✅ Imagen construida correctamente."
echo

mkdir -p "$OUT_DIR"

echo "📦 Exportando ${OUT_DIR}/${IMAGE_NAME}.tar..."
docker save "${IMAGE_NAME}:${TAG}" -o "${OUT_DIR}/${IMAGE_NAME}.tar"

cp docker/docker-compose-synology.yml "${OUT_DIR}/docker-compose.yml"
cp docker/env.template "${OUT_DIR}/env.template"

echo
echo "✅ Listo en ${OUT_DIR}/:"
echo "   - ${IMAGE_NAME}.tar    → docker load -i ${IMAGE_NAME}.tar (en el host de Portainer)"
echo "   - docker-compose.yml   → pégalo como stack en Portainer, o 'docker-compose up -d'"
echo "   - env.template         → cópialo a .env junto al compose y ajusta las rutas"
echo
echo "   El .env de secretos (Telegram, TMDB, OMDb, IA...) es aparte — copia"
echo "   .env.example a .env en la carpeta donde quede el compose, con tus claves reales."
echo
echo "   Acceso: puerto publicado en 0.0.0.0 → LAN y, si tienes el paquete"
echo "   Tailscale de Synology instalado, también tu tailnet (100.x.x.x) sin"
echo "   configurar nada extra."
