# 📱 Instalación solo con Synology + móvil/tablet (sin PC, sin terminal)

Esta guía es para instalar la app **enteramente desde el navegador de
DSM** (el panel web de tu Synology), usando **Container Manager** —
la versión gráfica de Docker de Synology. No hace falta terminal, SSH,
ni ningún ordenador aparte: todo se hace tocando pantalla.

> 💡 Consejo: en el navegador del móvil, activa "Ver como escritorio"
> (Chrome/Safari, menú de los tres puntos) al entrar en DSM — la
> interfaz de Container Manager está pensada para pantalla grande y
> así se usa mucho mejor con el dedo. Una tablet va bastante mejor que
> un móvil para esto.

## 0. Antes de nada: ¿tu NAS puede con esto?

Entra en DSM (`https://IP-de-tu-NAS:5001` desde el navegador) →
**Centro de Paquetes** → busca **"Container Manager"**. Si aparece
como instalable, tu modelo vale. Si no aparece (algunos modelos muy
básicos no lo soportan), no se puede seguir por este camino — dímelo
si es tu caso.

Instálalo si no lo tienes ya (botón **Instalar**, esperas a que
termine).

## 1. Crea la carpeta del proyecto y sus dos archivos

Abre la app **File Station** en DSM.

1. Ve a la carpeta `docker` (si no existe, créala: botón **Crear** →
   **Nueva carpeta**, dentro de tu volumen principal, ej.
   `/docker/find-video-duplicates`).
2. Dentro de `find-video-duplicates`, toca **Crear** → **Crear
   archivo de texto**. Nómbralo exactamente `docker-compose.yml`.
3. Ábrelo (aparece un editor de texto simple) y pega ahí el contenido
   completo de este archivo:
   👉 https://raw.githubusercontent.com/txarlye/find_video_duplicates/main/docker-compose.yml
   (ábrelo en otra pestaña del móvil, selecciona todo el texto,
   cópialo, y pégalo en el editor de File Station). Guarda.
4. Repite lo mismo para un segundo archivo, nómbralo `.env` (con el
   punto delante, sin nada más), pegando el contenido de:
   👉 https://raw.githubusercontent.com/txarlye/find_video_duplicates/main/env.template

## 2. Rellena tus rutas reales en el `.env`

Con el `.env` abierto en el editor de File Station, cambia estas dos
líneas por las rutas **reales** de tu NAS (para encontrarlas: en File
Station, navega hasta la carpeta correspondiente y mira la ruta que
aparece arriba, tipo `/volume1/...`):

```
MOVIES_PATH=/volume1/tu-ruta-real/peliculas
PLEX_DB_PATH=/volume1/PlexMediaServer/AppData/Plex Media Server/Plug-in Support/Databases
```

(`PLEX_DB_PATH` es la **carpeta** que contiene el archivo
`com.plexapp.plugins.library.db` — no pongas el archivo, la carpeta
que lo contiene. Si tienes Plex instalado como paquete de Synology,
casi siempre está en esa ruta de arriba, cambiando `volume1` por el
volumen donde lo instalaste.)

El resto del `.env` (`TELEGRAM_*`, `*_API_KEY`, etc.) puedes dejarlo
todo vacío por ahora — la app funciona igual, esas funciones
simplemente no se activan hasta que las rellenes.

Guarda el archivo.

## 3. Crea el proyecto en Container Manager

1. Abre **Container Manager** → pestaña **Proyecto** → **Crear**.
2. Nombre del proyecto: `find-video-duplicates`.
3. Ruta: selecciona la misma carpeta que creaste en el paso 1
   (`/docker/find-video-duplicates`) — como ya tiene el
   `docker-compose.yml` dentro, Container Manager lo detecta solo.
4. Sigue el asistente (siguiente, siguiente) hasta **Compilar**. La
   primera vez tarda un poco porque descarga la imagen (~450MB) desde
   internet — no compila nada, solo se descarga ya hecha.
5. Cuando termine, el contenedor debería quedar **en ejecución**
   (estado verde). Si algo falla, el propio Container Manager te
   enseña el registro/log del contenedor — cópiame el error si te
   atascas ahí.

## 4. Abre la app

En el navegador del móvil: `http://IP-de-tu-NAS:8000` (la misma IP que
usas para entrar en DSM, cambiando el puerto). Si tienes Tailscale en
el NAS, también funciona con la IP `100.x.x.x` desde cualquier sitio,
sin nada más que configurar.

Ve primero a **⚙️ Configuración** dentro de la app para terminar de
ajustar Plex, el umbral de similitud, la carpeta de "papelera" que
quieras usar, etc.

## Si algo no encaja con lo que ves en pantalla

DSM cambia ligeramente de un modelo/versión a otro (los nombres exactos
de botones pueden variar un poco). Si en algún paso ves algo distinto a
lo descrito aquí, dime exactamente qué pantalla tienes delante y lo
adaptamos.

## Problemas típicos

- **El contenedor arranca y se para solo, con un error de permisos**:
  en File Station, botón derecho sobre la carpeta del proyecto →
  **Propiedades** → **Permiso** → dale permiso de lectura/escritura al
  usuario con el que corre Docker (o, más simple, márcalo como
  accesible para "Todos" si es una carpeta dedicada solo a esto).
- **"Bind mount ... does not exist"**: la ruta que pusiste en
  `MOVIES_PATH` o `PLEX_DB_PATH` no es exactamente la real — vuelve a
  File Station y comprueba la ruta tal cual aparece ahí.
- Todo lo demás, en la pantalla **ℹ️ Acerca de** dentro de la propia
  app.
