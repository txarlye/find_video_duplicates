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
- `env.template` — plantilla de `.env`: rutas, puerto, Tailscale **y**
  los secretos de la app (Telegram, TMDB, OMDb, IA, SMTP...) — un único
  fichero, pensado para que todo un despliegue viva en una sola carpeta
  (Container Manager de Synology, Portainer...).

## 🚀 Construir la imagen

Desde la raíz del repo:

```bash
build_docker_image.bat   # Windows
./build_docker_image.sh  # Linux/Mac/Git Bash
```

Los dos construyen `find-video-duplicates:latest` y la exportan a
[`.imagen_docker/`](../.imagen_docker/) (carpeta no versionada salvo el
`docker-compose.yml`/`env.template` que copian ahí) junto con
`find-video-duplicates.tar`, listos para copiar al NAS. A mano sería:

```bash
docker build -f docker/Dockerfile -t find-video-duplicates:latest .
docker save find-video-duplicates:latest -o find-video-duplicates.tar
```

## 🚀 Ejecutarla en el Synology

1. Copia el contenido de [`.imagen_docker/`](../.imagen_docker/) a una
   carpeta del NAS: `find-video-duplicates.tar`, `docker-compose.yml` y
   `env.template` (o clona el repo entero y constrúyela directamente
   ahí, ver más abajo). Con Container Manager, esa carpeta es la del
   propio "Proyecto" que crees.
2. `docker load -i find-video-duplicates.tar`
3. Copia `env.template` a `.env`, **en esa misma carpeta** (junto al
   compose, no un nivel por encima), y rellena tanto las rutas
   (`MOVIES_PATH`, `PLEX_DB_PATH`...) como tus claves (Telegram, TMDB,
   OMDb, IA, SMTP...) — todo en un único fichero.
4. En Container Manager: **Proyecto → Crear**, apuntando a esa carpeta.
   A mano: `docker-compose -f docker-compose.yml up -d`.

   Con **Portainer** (Web editor): pega `docker-compose.yml`, y en su
   sección "Environment variables" usa **"Load variables from .env
   file"** para subir el mismo `.env` (o pégalo a mano) — con Web
   editor, Portainer no lee un `.env` del disco por sí solo, genera el
   suyo propio a partir de esa sección.
5. Abre `http://<IP-del-NAS>:8000` (o la IP de Tailscale que hayas
   puesto en `TAILSCALE_IP`).
6. Ve a **⚙️ Configuración** dentro de la app para terminar de ajustar
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
`SMTP_USER`/`SMTP_PASSWORD` en el `.env`). También hay una tercera vía:
un botón en esa misma pantalla crea la tarea externa directamente en el
Planificador de DSM por ti (necesita `SYNOLOGY_*` en el `.env` — ver
[SETUP.md](../SETUP.md)).

## ⚠️ Notas

- La app nunca borra archivos: los mueve a la carpeta de debug
  configurada (🗑️ Basura dentro de la app).
- `ffmpeg` va incluido en la imagen (necesario para el fotograma de
  comparación de vídeos).
- Recursos: ~2GB RAM.
