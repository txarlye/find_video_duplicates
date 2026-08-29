# 📦 Instalación (sin compilar nada)

Utilidades Synology & Plex: detecta duplicados en tu biblioteca de
vídeo, encuentra archivos sin indexar en Plex, sube vídeos a Telegram y
más. La interfaz está en español. Todo corre en un único contenedor
Docker — no hace falta clonar el repo ni instalar Python/Node.

> 📱 **¿Solo tienes tu Synology y un móvil/tablet, sin PC ni
> terminal?** Sigue [INSTALL_SYNOLOGY_MOVIL.md](INSTALL_SYNOLOGY_MOVIL.md)
> en su lugar — mismo resultado, todo desde Container Manager (DSM).

## 1. Requisitos

- **Docker** instalado y arrancado. En Windows/Mac,
  [Docker Desktop](https://www.docker.com/products/docker-desktop/). En
  Linux o un NAS (Synology, QNAP...), el propio Docker Engine (en
  Synology: Package Center → Container Manager).
- Tu biblioteca de películas/series en una carpeta a la que Docker
  pueda acceder (un disco local, o una carpeta de red/NAS ya montada en
  el sistema).
- (Opcional pero recomendado) Un servidor Plex ya indexando esa misma
  biblioteca, y acceso a su base de datos
  (`com.plexapp.plugins.library.db`). Sin esto, Duplicados funciona
  igual, pero Huérfanos/Series (que cruzan contra lo que Plex ya tiene
  indexado) no.

## 2. Descarga dos archivos

Solo necesitas estos dos, sueltos, en una carpeta nueva (p.ej.
`find-video-duplicates/`):

- [`docker-compose.yml`](https://raw.githubusercontent.com/txarlye/find_video_duplicates/main/docker-compose.yml)
- [`env.template`](https://raw.githubusercontent.com/txarlye/find_video_duplicates/main/env.template)

(Botón derecho → Guardar como..., o `curl -O <url>` si prefieres
terminal.)

## 3. Configura tu `.env`

Copia `env.template` a `.env` (mismo nombre de carpeta, mismo sitio) y
edítalo:

- **`MOVIES_PATH`** (obligatoria): ruta real a tu carpeta de
  películas/series. En Linux/NAS, algo como `/volume1/data/media`; en
  Windows con Docker Desktop, `/c/Users/tu_usuario/Videos` (con `/`, no
  `\`, y sin la unidad tipo `C:`).
- **`PLEX_DB_PATH`** (opcional, recomendada): la **carpeta** que
  contiene `com.plexapp.plugins.library.db` (no el archivo suelto).
- El resto (`DATA_PATH`/`LOGS_PATH`/`SCAN_DATA_PATH`) puedes dejarlo
  como está — Docker crea esas carpetas solo, ahí vive lo que la app
  necesita recordar entre reinicios (config, informes...).
- Todo lo demás (`TELEGRAM_*`, `*_API_KEY`, `SMTP_*`) es opcional: lo
  que dejes vacío simplemente no se activa. Cada variable tiene un
  comentario explicando de dónde sacarla si quieres esa función.

## 4. Arranca

Desde esa misma carpeta:

```bash
docker compose pull   # descarga la imagen ya construida, no compila nada
docker compose up -d
```

¿Prefieres Portainer en vez de terminal? Sube el `docker-compose.yml`
como stack (Web editor: pega su contenido) y, en la sección
"Environment variables" de Portainer, pega el contenido de tu `.env`
en vez de subirlo como archivo — Portainer no lee ficheros `.env` del
disco por sí solo.

## 5. Abre la app

`http://localhost:8000` (o la IP de la máquina/NAS donde la hayas
arrancado, si accedes desde otro dispositivo — con Tailscale
funciona igual, sin configurar nada más).

Ve primero a **⚙️ Configuración** para terminar de ajustar Plex, el
umbral de similitud, la carpeta de "debug" (papelera) que quieras usar,
etc. Dentro de la propia app hay una pantalla **ℹ️ Acerca de** con más
detalle de qué hace cada pantalla y cómo restaurar Plex si algo fallara.

## 6. Actualizar a una versión nueva

```bash
docker compose pull
docker compose up -d
```

Tu configuración (`config.json`) y tus informes guardados sobreviven
siempre — viven en `DATA_PATH`/`SCAN_DATA_PATH`, no en la imagen.

## Problemas típicos

- **"Bind mount ... does not exist"**: `MOVIES_PATH` o `PLEX_DB_PATH`
  apuntan a una ruta que no existe de verdad en esa máquina — revisa
  que la escribiste tal cual la ve el propio Docker, no como la ves tú
  en el explorador de archivos.
- **Permission denied al arrancar**: la carpeta de `DATA_PATH` (o
  `MOVIES_PATH`) no tiene permiso de escritura para el usuario con el
  que corre Docker. Prueba a darle permisos amplios a esa carpeta
  concreta.
- Todo lo demás, en la pantalla **ℹ️ Acerca de** dentro de la propia
  app, o en el [README](README.md) del repo.
