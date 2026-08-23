# 🎬 Detector de Películas y Series Duplicadas

Aplicación en Python con Streamlit para organizar una biblioteca de vídeo
local: detecta **películas y series duplicadas**, encuentra **archivos sin
indexar en Plex** (con ayuda de IA para renombrarlos), y contrasta todo
contra **Plex, TMDB/OMDb/IMDB y Telegram**.

> 📖 **¿Primera vez?** Antes de nada, sigue [SETUP.md](SETUP.md) para
> apuntar la app a tu propio NAS (rutas, base de datos de Plex, API keys y
> acceso remoto por Tailscale).

> 🚧 **En migración de Streamlit a FastAPI + React**, pantalla a
> pantalla — mientras dura, la app corre en dos puertos a la vez
> (`:8501` Streamlit, con lo aún no migrado; `:8000` la interfaz nueva,
> adaptativa a móvil). Ver [docker/README.md](docker/README.md).

## ✨ Funcionalidades

### 🔍 Duplicados de películas
- Escaneo recursivo de carpetas con detección por similitud de nombre + año
- Filtro por duración configurable para descartar falsos positivos
- Comparación por fotograma (mucho más rápido que reproducir el vídeo
  completo, sobre todo en carpetas de red), con botones ◀ -10s / +10s ▶ y
  un campo para saltar directo a un minuto exacto — útil para reconocer
  la película cuando el nombre de archivo no dice nada
- Reproductor de vídeo completo embebido, opcional, para cuando el
  fotograma no basta
- Tamaño, duración y resolución reales (no solo lo calculado en el
  escaneo) justo antes de decidir qué eliminar
- Navegación por pares, con guardado/carga del progreso de un escaneo
- Integración con **Ediciones de Plex**: cuando dos "duplicados" son en
  realidad versiones distintas de la misma película (Director's Cut,
  Extendida...), la app puede convertir uno de los dos en una Edición de
  Plex en lugar de borrarlo

![Comparando un par de duplicados: fotograma navegable, reproductor embebido opcional, y tamaño/duración/resolución reales antes de eliminar](.img/manejo%20de%20duplicados.png)

### 🧩 Huérfanos (películas sin indexar en Plex)
- Detecta archivos en disco que Plex no tiene indexados
- Sugerencia de nombre con IA: **Ollama** (local, gratis), **OpenAI** o
  **Gemini**, a elegir — individual o en lote (con límite configurable y
  botón de detener, para colecciones grandes)
- La sugerencia de la IA se contrasta contra **TMDB/OMDb** antes de
  aceptarla (mejor título en español vía TMDB, año real de la base de
  datos en vez de un año inventado por el modelo)
- Si el nombre de archivo no dice nada (títulos crípticos, nombres de
  escena...), el mismo visualizador con fotograma navegable de
  duplicados permite "hojear" el vídeo hasta encontrar los créditos o
  cualquier escena que revele de qué película se trata
- Modo "sugerir" (confirmas tú cada renombrado) o "automático"
- Listados paginados para colecciones grandes

![Renombrando una huérfana con nombre críptico: navegando hasta el minuto 0:29 aparece el título en los créditos](.img/renombrado%20peli%20huerfana.png)

![Después de renombrar: archivo en verde, y biblioteca de Plex refrescada automáticamente](.img/renombrado%20peli%20huerfana2.png)

### 📺 Series
- Detecta capítulos duplicados, capítulos sueltos sin indexar y **series
  enteras sin indexar en Plex** (agrupadas por serie, con desplegable)
- Compara por episodios indexados, no por título de serie — así una serie
  con título traducido en Plex (p.ej. "Earth Abides" en disco vs. "La
  Tierra Permanece" en Plex) no sale como falso "sin indexar"
- Permite marcar series como "ignoradas" de forma permanente
- Guardado/carga de progreso, igual que en duplicados y huérfanos

### 🗑️ Basura / Purgatorio
- La app **nunca borra nada directamente** — modo debug siempre activo,
  no se puede desactivar desde la interfaz: todo lo eliminado o
  renombrado se mueve primero a una carpeta de debug configurable
- Vista dedicada con el contenido de esa carpeta (separado en películas /
  capítulos de serie), tamaño total ocupado y, si indicas el tamaño
  aproximado de tu biblioteca, qué porcentaje llevas ya "purgado"
- **Restaurar** archivos a su carpeta original con un checkbox, sin tener
  que ir a buscarlos a mano por el NAS
- Vaciarla de verdad (borrado real) es una acción manual tuya en el NAS,
  la app nunca lo hace por ti ni automática ni manualmente

![Papelera/Purgatorio: nada se borra de verdad, solo se mueve aquí — y desde la app solo se puede restaurar, no vaciar](.img/basura.png)

### 🤖 Propuestas (revisión asistida, con aviso por email)
- Escaneo programado (hora configurable, o bajo demanda con un botón) que
  revisa las carpetas configuradas y genera dos tipos de propuesta:
  - **Huérfanos**: nombre sugerido por IA, igual que en la pestaña
    Huérfanos pero centralizado aquí
  - **Duplicados**: qué copia borrar, **solo cuando Plex tiene la
    resolución de ambos archivos indexada** — compara calidad vs. tamaño
    con un umbral configurable ("¿compensa X% / Y GB más por mejor
    resolución?") y nunca arriesga una recomendación sin datos fiables
- Revisión en lote: casillas + un único botón "Aplicar/Descartar
  seleccionadas" (un solo refresco para varias propuestas, no uno por
  clic — pensado para revisar desde el móvil)
- Descartar una propuesta es **permanente** ("no, ese no, no me lo
  vuelvas a proponer"), con lista reversible desde la propia pantalla
- Aviso por email (SMTP, Gmail con contraseña de aplicación por defecto)
  con enlace directo a esta pantalla — el programador interno vive dentro
  de la propia app, sin depender de crear una tarea en el NAS (aunque
  también se puede, ver más abajo)

### 🎬 IMDB / TMDB / OMDb
- Sinopsis, pósteres y datos (rating, director, actores, género)
- TMDB como fuente primaria (mejor cobertura en español), con OMDb como
  contraste/fallback

### 📱 Telegram
- Subida de vídeos a un canal, con carátula + sinopsis antes del vídeo
- Dos vías de subida: **Bot API** (archivos pequeños) y **Telethon**
  (sesión de usuario, para archivos grandes que superan el límite del Bot
  API)

### 🗄️ Plex
- Conexión de **solo lectura** a la base de datos de Plex
- Cruce de duplicados, huérfanos y series contra tu biblioteca real
- Refresco de biblioteca desde la propia app tras renombrar/mover archivos

### ⚙️ Configuración (pantalla dentro de la app)
- Página completa en Utilidades con Detección, Reproductores/Debug, Plex
  y **Programación** (carpetas/hora/email de Propuestas) — antes repartido
  en pestañas del sidebar, ahora también accesible como pantalla propia
- Las API keys/tokens **no están aquí a propósito**: viven solo en `.env`,
  nunca en un campo de la UI que pueda acabar guardado en `config.json`

## 🚀 Instalación

```bash
git clone <tu-fork-o-este-repositorio>
cd find_video_duplicates
pip install -r requirements.txt
```

O con los instaladores incluidos:

```bash
# Windows
setup\instalar_dependencias.bat
setup\run_app.bat

# Linux/Mac
chmod +x setup/run_app.sh
./setup/run_app.sh

# Cualquier plataforma
python setup/install_dependencies.py
python main.py
```

La app se abre en `http://localhost:8501`.

**Después de instalar**, sigue [SETUP.md](SETUP.md) para configurar tus
rutas reales, la base de datos de Plex y las API keys — sin eso la app
arranca pero no tiene nada que escanear.

### 🐳 Alternativa: Docker (Synology u otro NAS, sin instalar Python)

```
build_docker_image.bat
```

Construye la imagen y te deja instrucciones para copiarla a tu NAS
(`docker load` + `docker-compose up`). La imagen **nunca lleva datos
personales horneados dentro** — `config.json` y `.env` se montan como
volumen en tiempo de ejecución, así que la misma imagen sirve tanto para
ti como para compartirla. Guía completa en [docker/README.md](docker/README.md).

## 📁 Estructura del Proyecto

```
find_video_duplicates/
├── main.py                          # Punto de entrada (abre navegador, Tailscale-friendly)
├── app_simple.py                    # Entry point de Streamlit
├── scheduled_scan.py                # Entrypoint sin interfaz para Propuestas (tarea externa opcional)
├── build_docker_image.bat           # Construye la imagen Docker desde la raíz del repo
├── requirements.txt
├── README.md
├── SETUP.md                         # Configuración paso a paso (rutas, Plex, Tailscale)
├── .env.example                     # Plantilla de secretos — cópiala a .env
├── .dockerignore
│
├── docker/                          # Receta Docker (versionada, sin secretos ni datos personales)
│   ├── Dockerfile                   # Contexto = raíz del repo, código siempre actual
│   ├── docker-compose-synology.yml
│   ├── env.template                 # Plantilla de docker/.env (rutas, puerto, TZ)
│   └── README.md
│
├── src/
│   ├── app/
│   │   └── streamlit_manager.py     # Toda la UI: escaneo, huérfanos, series, basura, propuestas...
│   ├── services/
│   │   ├── ai_naming_service.py     # IA (Ollama/OpenAI/Gemini) + contraste TMDB/OMDb
│   │   ├── proposals_service.py     # Genera propuestas (nombres IA + qué duplicado borrar)
│   │   ├── email_service.py         # Aviso por email (SMTP) de propuestas nuevas
│   │   ├── scan_scheduler.py        # Programador interno (hilo en segundo plano, hora configurable)
│   │   ├── plex_service.py
│   │   ├── plex_refresh_service.py
│   │   ├── scan_data_manager.py     # Guardado/carga de progreso de escaneos
│   │   ├── video_info_service.py
│   │   ├── Plex/                    # Detección/creación de Ediciones de Plex
│   │   ├── Imdb/                    # Búsqueda de películas en IMDB/TMDB/OMDb
│   │   └── Telegram/                # Bot API + Telethon
│   ├── settings/
│   │   ├── settings.py              # Singleton de configuración
│   │   ├── config.example.json      # Plantilla — cópiala a config.json
│   │   └── env_template.txt         # Plantilla — cópiala a .env
│   └── utils/
│       ├── movie_detector.py        # Similitud de nombres para películas
│       ├── series_detector.py       # Parseo SxxExx / NxNN, agrupado por serie
│       ├── file_operations.py
│       └── ui_components.py
│
└── setup/                           # Instaladores por plataforma
```

## ⚙️ Configuración

Ver **[SETUP.md](SETUP.md)** para la guía completa (rutas de tu NAS, dónde
está la base de datos de Plex en un Synology, variables de entorno y
acceso remoto por Tailscale).

Resumen rápido:

```bash
cp src/settings/config.example.json src/settings/config.json
cp src/settings/env_template.txt .env
```

Después edita `config.json` y `.env` con tus valores, o ajústalos desde la
pestaña ⚙️ Configuración de la propia app. Ambos ficheros están en
`.gitignore`: puedes meter tus rutas y claves reales sin miedo a subirlas.

## 🎮 Uso rápido

1. **Escanear**: elige carpeta en el sidebar, ajusta umbral de similitud y
   filtro de duración, pulsa "🔍 Escanear".
2. **Revisar pares**: navega con Anterior/Siguiente, compara por fotograma
   o vídeo completo, decide si eliminar (va a la papelera) o mover.
3. **Huérfanos**: pestaña 🧩, deja que la IA sugiera nombre y contrástalo
   antes de renombrar.
4. **Series**: pestaña 📺, mismo flujo pero por episodios y series enteras.
5. **Basura**: pestaña 🗑️, revisa qué se ha ido acumulando en la papelera
   antes de vaciarla tú a mano en el NAS.
6. **Propuestas**: pestaña 🤖, revisa lo que la app te sugiere (nombres de
   huérfanos, duplicados a borrar), marca casillas y aplica/descarta en
   lote. Configura carpetas/hora/email en ⚙️ Configuración → 📅 Programación.
7. **Telegram/IMDB**: subida opcional a un canal con carátula y sinopsis.

## 🔒 Seguridad

- La app **nunca borra archivos directamente**: todo pasa primero por la
  carpeta de debug/papelera configurada. El modo debug está siempre
  activo y, de momento, no se puede desactivar desde la interfaz.
- La conexión a Plex es **de solo lectura**: `PlexService` solo abre la
  base de datos con `mode=ro` y, si esa conexión falla, **nunca** cae a
  una conexión editable como red de seguridad — antes sí lo hacía, y se
  corrigió porque es una vía real de corrupción (ver más abajo).
- ⚠️ **SQLite y rutas de red no son buena combinación.** La base de datos
  de Plex normalmente vive en una carpeta de red (SMB/CIFS), y SQLite no
  garantiza el bloqueo de archivos correcto ahí — si algo más (otra
  herramienta, un script propio) abre esa misma base de datos en modo
  escritura mientras Plex la tiene abierta, puede corromperla (error
  típico: `database disk image is malformed`, Plex sin arrancar y en
  bucle de reinicio). Esta app siempre se conecta en solo lectura, pero
  si escribes tus propios scripts contra esa ruta, ábrela también en
  modo `ro` (`sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)`). Ver la
  solución si ya te ha pasado en **[🐛 Solución de problemas](#-solución-de-problemas)**.
- Las claves de API y tokens viven solo en `.env` / `config.json`, ambos
  excluidos de git — nunca se hardcodean en el código, ni tampoco en
  campos editables de la UI (por diseño, para que no acaben en
  `config.json` por accidente).
- **La app no tiene login propio.** Si la expones por Tailscale (recomendado,
  ver [SETUP.md](SETUP.md#5-acceso-remoto-por-tailscale-sin-abrir-puertos)),
  la única barrera es pertenecer a tu tailnet — cualquiera fuera de ella
  no puede alcanzarla ni probando IPs, porque las direcciones `100.x.x.x`
  no son enrutables desde fuera de tu propia red Tailscale. El riesgo real
  es que se comprometa tu cuenta de Tailscale, no que adivinen la IP.
- Con Docker (`docker-compose-synology.yml`), el puerto solo se publica en
  tu IP de Tailscale, nunca en `0.0.0.0` — ni tu propia LAN sin Tailscale
  puede alcanzarlo.
- Email de Propuestas: `SMTP_PASSWORD` debe ser una **contraseña de
  aplicación** de Gmail (16 caracteres, myaccount.google.com/apppasswords),
  no tu contraseña normal — esta última da error de credenciales.

## 🐛 Solución de problemas

Ver la sección de problemas comunes en **[SETUP.md](SETUP.md#7-problemas-comunes)**
para lo relacionado con rutas, Plex y acceso remoto.

Otros problemas frecuentes:

- **"Streamlit ya está ejecutándose"**: hay un proceso previo ocupando el
  puerto 8501 (`taskkill /f /im python.exe` en Windows, `pkill -f
  streamlit` en Linux/Mac).
- **"Mutagen no disponible"**: `pip install mutagen>=1.47.0`.
- **Error 401 en OMDb/TMDB**: revisa que la API key en `.env` sea correcta.
- **Plex no arranca, log con "database disk image is malformed"**: la
  base de datos de Plex se ha corrompido (ver el aviso en
  [🔒 Seguridad](#-seguridad) sobre SQLite en rutas de red). Se recupera
  con las copias de seguridad automáticas que el propio Plex genera
  periódicamente, en la misma carpeta que la base de datos activa
  (`Plug-in Support/Databases/`), con la fecha en el nombre:
  `com.plexapp.plugins.library.db-YYYY-MM-DD` y su pareja
  `com.plexapp.plugins.library.blobs.db-YYYY-MM-DD`.

  1. **Para Plex** (Container Manager / Docker → detener el contenedor).
  2. **No borres nada** — renombra los archivos actuales (añádeles algo
     como `.corrupto`): `com.plexapp.plugins.library.db`, `-wal`, `-shm`,
     `com.plexapp.plugins.library.blobs.db` y sus `-wal`/`-shm` si existen.
  3. **Copia** (no muevas) la pareja fechada más reciente y quítales la
     fecha del nombre al copiarlas:
     `com.plexapp.plugins.library.db-YYYY-MM-DD` → `com.plexapp.plugins.library.db`
     `com.plexapp.plugins.library.blobs.db-YYYY-MM-DD` → `com.plexapp.plugins.library.blobs.db`
  4. Arranca Plex de nuevo.

  Perderás la actividad (visto/no visto, añadidos) desde la fecha de esa
  copia hasta ahora, pero el resto de la biblioteca se recupera intacta.

## 🤝 Contribuir

1. Fork del repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de tus cambios
4. Push y abre un Pull Request

---

**¡Disfruta organizando tu colección! 🎬✨**
