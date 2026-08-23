# ⚙️ Guía de Configuración (Synology / NAS propio)

Esta guía explica cómo apuntar la aplicación a **tu** NAS y tus rutas reales.
El repositorio nunca contiene tus datos: solo plantillas de ejemplo que copias
y rellenas tú.

## 1. Los dos ficheros de configuración

| Plantilla en el repo | Copia local que creas tú | Para qué |
|---|---|---|
| `src/settings/config.example.json` | `src/settings/config.json` | Rutas, umbrales de detección, Plex, IA... |
| `src/settings/env_template.txt` | `.env` (en la raíz del proyecto) | API keys y tokens (datos sensibles) |

Ambas copias locales están en `.gitignore`: puedes rellenarlas con tus datos
reales sin miedo a subirlas por error.

```bash
# Configuración general (rutas, umbrales...)
cp src/settings/config.example.json src/settings/config.json

# Variables de entorno (claves de API, tokens)
cp src/settings/env_template.txt .env
```

Si `config.json` no existe, la app arranca igualmente con valores por
defecto vacíos; no verás tus películas hasta que rellenes las rutas.

## 2. Rutas de `config.json`

```json
{
    "paths": {
        "last_scan_path": "",
        "debug_folder": "",
        "selected_movies_folder": ""
    },
    "plex": {
        "database_path": ""
    }
}
```

- **`last_scan_path`**: carpeta raíz donde tienes tus vídeos (películas o
  series). Puedes cambiarla desde la propia app; se guarda sola. Desde la
  actualización de "rutas recientes" (ver más abajo), cada sección
  (duplicados / huérfanos / series) recuerda su propio historial de hasta 5
  carpetas, así que no hace falta que esta ruta sea la misma para las tres.
- **`debug_folder`**: la "papelera" de la app. Nada se borra de verdad —
  todo lo que eliminas o mueves va aquí primero. Puedes revisarlo y vaciarlo
  tú a mano desde el propio NAS cuando quieras recuperar espacio (pestaña
  🗑️ Basura de la app).
- **`selected_movies_folder`**: destino por defecto cuando mueves archivos
  seleccionados en vez de borrarlos.
- **`plex.database_path`**: ruta a la base de datos de Plex, **en modo solo
  lectura** (la app nunca escribe en ella). Ver siguiente sección para
  localizarla en un Synology.

### Cómo escribir rutas de tu NAS

- **Windows**, con la carpeta mapeada como unidad de red o por ruta UNC:
  `\\NOMBRE-DE-TU-NAS\carpeta\subcarpeta` (en JSON hay que escapar las
  barras: `"\\\\NOMBRE-DE-TU-NAS\\carpeta\\subcarpeta"`).
- **macOS/Linux**, con el volumen montado por SMB/NFS:
  `/Volumes/carpeta/...` o el punto de montaje que uses.

## 3. Encontrar la base de datos de Plex en un Synology

Depende de cómo tengas instalado Plex:

- **Plex como paquete nativo del Synology** (Package Center):
  ```
  \\TU-NAS\PlexMediaServer\AppData\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db
  ```
- **Plex como contenedor Docker en el Synology** (Container Manager):
  ```
  \\TU-NAS\docker\<nombre-del-contenedor>\db\Library\Application Support\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db
  ```
  (sustituye `<nombre-del-contenedor>` por el volumen que le mapeaste al
  contenedor, p.ej. `plex`, `plex2`...)

Si no la encuentras a simple vista, entra por File Station o SSH al NAS y
busca `com.plexapp.plugins.library.db` dentro de la carpeta de Plex.

**Requisito de acceso**: el usuario/carpeta compartida desde la que lees
esa ruta necesita permiso de lectura sobre esa carpeta de Plex (suele estar
restringida). Compártela como solo lectura en lugar de abrir permisos de
más.

## 4. Variables de entorno (`.env`)

Copia `src/settings/env_template.txt` a `.env` y rellena lo que vayas a
usar — todo es opcional salvo lo que necesites:

| Variable | Para qué | Dónde conseguirla |
|---|---|---|
| `TMDB_API_KEY` | Sinopsis/pósteres en español, contraste de sugerencias de IA | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) (gratis) |
| `OMDB_API_KEY` | Contraste alternativo de sugerencias de IA (inglés) | [omdbapi.com/apikey.aspx](https://www.omdbapi.com/apikey.aspx) (gratis) |
| `IMDB_API_KEY` | Búsquedas adicionales de IMDB | [imdb-api.com](https://imdb-api.com/api) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHANNEL_ID` | Subida de vídeos a un canal, **hasta 50MB por archivo** | @BotFather / @userinfobot en Telegram |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` / `TELEGRAM_PHONE` | Subida de archivos **más grandes de 50MB** (usa tu cuenta personal vía Telethon, no el bot) | [my.telegram.org](https://my.telegram.org) → API development tools |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | Solo si eliges OpenAI o Gemini como proveedor de IA para nombrar huérfanos | platform.openai.com / aistudio.google.com |

**Sobre los límites de tamaño en Telegram**: el Bot API de Telegram
(`TELEGRAM_BOT_TOKEN`) tiene un límite real de 50MB por archivo tanto
para vídeo como para documento — no hay forma de saltárselo sin montar
tu propio servidor de Bot API. Para películas más pesadas, la app usa
Telethon (un cliente de tu cuenta personal de Telegram, con
`TELEGRAM_API_ID`/`TELEGRAM_API_HASH`/`TELEGRAM_PHONE`), que sube
directamente hasta ~1.5-2GB. Sin esas tres variables, cualquier archivo
de más de 50MB fallará al subir sin más explicación en la interfaz.

Si usas **Ollama en local** para la IA de nombrado de huérfanos, no
necesitas ninguna de las dos claves de arriba (`OPENAI_API_KEY`/
`GEMINI_API_KEY`) — solo tener Ollama corriendo (por defecto en
`http://localhost:11434`, configurable en la pestaña de IA de la app).

## 5. Acceso remoto por Tailscale (sin abrir puertos)

Por defecto la app solo escucha en `127.0.0.1` (tu propio PC/NAS). Si
quieres usarla desde el móvil o desde otro equipo sin exponer el puerto
8000 a internet, la forma recomendada es [Tailscale](https://tailscale.com/):

1. Instala Tailscale en el equipo donde corre la app (el que ejecuta
   `python main.py`) y en los dispositivos desde los que quieras acceder,
   y únelos a la misma tailnet.
2. Averigua la IP de Tailscale del equipo que corre la app (algo tipo
   `100.x.x.x`, con `tailscale ip -4` o desde la consola de Tailscale).
3. Antes de arrancar la app, exporta esa IP como variable de entorno:

   ```bash
   # Windows (PowerShell)
   $env:API_SERVER_ADDRESS = "100.x.x.x"
   python main.py

   # Linux/Mac
   API_SERVER_ADDRESS=100.x.x.x python main.py
   ```

4. Desde cualquier dispositivo de tu tailnet, entra a
   `http://100.x.x.x:8000`.

Esto **no** abre nada a internet: solo es alcanzable dentro de tu tailnet
privada. Si no defines `API_SERVER_ADDRESS`, la app sigue escuchando
únicamente en `127.0.0.1` como hasta ahora.

## 6. Arrancar la aplicación

```bash
# Windows
setup\run_app.bat

# Linux/Mac
./setup/run_app.sh

# Cualquier plataforma con Python
python main.py
```

La primera vez que entres, ve a la pestaña ⚙️ **Configuración** del menú
lateral para revisar/ajustar rutas, umbrales y el resto de opciones desde
la propia interfaz (no hace falta editar `config.json` a mano salvo la
primera vez).

## 7. Problemas comunes

- **"No se encuentra la base de datos de Plex"**: revisa el permiso de
  lectura de la carpeta compartida y que la ruta en `config.json` use el
  formato correcto para tu sistema operativo (ver punto 2).
- **La app no ve mis películas**: comprueba que `last_scan_path` (o la
  ruta que escribas en el propio formulario de la app) apunta a una
  carpeta accesible desde el equipo donde corre la app, no desde tu PC de
  siempre si son máquinas distintas.
- **No puedo entrar desde el móvil**: confirma que ambos dispositivos
  están en la misma tailnet (`tailscale status`) y que exportaste
  `API_SERVER_ADDRESS` **antes** de lanzar `main.py` en esa sesión.
