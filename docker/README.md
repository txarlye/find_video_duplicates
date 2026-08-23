# 🐳 Docker

Instalación en un Synology (u otro NAS/servidor con Docker) sin necesitar Python instalado.

Un único contenedor sirve el backend (FastAPI) y la interfaz (React) en
el mismo puerto — sin nginx aparte.

La imagen **nunca lleva datos personales horneados dentro**: `config.json`
y `.env` se excluyen del build (`.dockerignore`) y se montan como volumen
en tiempo de ejecución. Por eso la misma imagen sirve tanto para ti como
para compartirla con otra persona — no hace falta elegir entre "mis datos"
o "genéricos" al construirla.

## 📁 Archivos

- `Dockerfile` — receta de la imagen. El contexto de build es la **raíz
  del repo** (no esta carpeta), para que siempre incluya el código real
  y actual, nunca una copia congelada.
- `docker-compose-synology.yml` — cómo ejecutarla (puertos, volúmenes,
  variables).
- `env.template` — plantilla de `docker/.env` (rutas y puerto).

## 🚀 Construir la imagen

Desde la raíz del repo, en Windows:

```
build_docker_image.bat
```

Construye `find-video-duplicates:latest` y pregunta si quieres exportarla
también como `docker/find-video-duplicates.tar` para copiarla a mano al
NAS. A mano sería:

```bash
docker build -f docker/Dockerfile -t find-video-duplicates:latest .
docker save find-video-duplicates:latest -o docker/find-video-duplicates.tar
```

## 🚀 Ejecutarla en el Synology

1. Copia a una carpeta del NAS: `find-video-duplicates.tar`,
   `docker-compose-synology.yml` y `env.template` (o clona el repo entero
   y constrúyela directamente ahí, ver más abajo).
2. `docker load -i find-video-duplicates.tar`
3. Copia `env.template` a `.env` (en esa misma carpeta) y ajusta las
   rutas reales (`MOVIES_PATH`, `PLEX_DB_PATH`...).
4. En la raíz del repo (un nivel arriba) tiene que existir también un
   `.env` con tus claves (Telegram, TMDB, OMDb...) — copia `.env.example`
   si no lo tienes.
5. `docker-compose -f docker-compose-synology.yml up -d`
6. Abre `http://<IP-del-NAS>:8000` (o la IP de Tailscale que hayas
   puesto en `TAILSCALE_IP`).
7. Ve a **⚙️ Configuración** dentro de la app para terminar de ajustar
   Plex, carpeta de debug, etc. — esos cambios quedan guardados en
   `data/config.json` (el volumen persistente), no en la imagen, así que
   sobreviven a actualizar o recrear el contenedor.

### Alternativa: construir directamente en el Synology

Si prefieres clonar el repo en el propio NAS en vez de pasar el `.tar`:
descomenta el bloque `build:` de `docker-compose-synology.yml` y ejecuta
`docker-compose -f docker-compose-synology.yml build` desde ahí.

## 🔧 Comandos útiles

```bash
docker logs find-video-duplicates
docker restart find-video-duplicates
docker stop find-video-duplicates
```

## 🤖 Escaneo programado de Propuestas (opcional)

Configúralo en **⚙️ Configuración → 📅 Programación**: carpetas a
analizar, hora, email de aviso. La propia app trae un programador
interno — no hace falta nada más, dispara el escaneo solo a la hora
configurada mientras el contenedor esté encendido.

Si prefieres controlar el "cuándo" desde fuera del contenedor (para no
depender de que siga vivo justo a esa hora), esa misma sección también
trae las instrucciones exactas para tu caso; con Docker en Synology
sería una tarea en **Panel de control → Planificador de tareas → Tarea
programada → Script definido por el usuario**:

```bash
docker exec find-video-duplicates python scheduled_scan.py
```

Ninguna de las dos vías mueve, renombra ni borra nada — solo detecta
propuestas nuevas y, si las hay, manda el email (necesita
`SMTP_USER`/`SMTP_PASSWORD` en el `.env` de la raíz).

## ⚠️ Notas

- La app nunca borra archivos: los mueve a la carpeta de debug
  configurada (🗑️ Basura dentro de la app).
- `ffmpeg` va incluido en la imagen (necesario para el fotograma de
  comparación de vídeos).
- Recursos: ~2GB RAM.
