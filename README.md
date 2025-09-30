# 🎬 Detector de Películas Duplicadas

Una aplicación inteligente desarrollada en Python con Streamlit para detectar películas duplicadas en tu colección de videos, con filtros avanzados por duración y similitud de nombres. Incluye integración con **IMDB/TMDB**, **Telegram** y **Plex** para información completa de películas y subida automática.

## ✨ Características Principales

### 🔍 **Detección Inteligente**
- **Escaneo recursivo** de carpetas para encontrar archivos de video
- **Análisis de similitud** de nombres de películas usando algoritmos avanzados
- **Filtro por duración** para descartar falsos positivos (configurable)
- **Soporte múltiples formatos**: MP4, AVI, MKV, MOV, WMV, FLV, M4V, MPG, MPEG, 3GP, WebM

### 🎯 **Filtros Avanzados**
- **Umbral de similitud** configurable (0.1 - 1.0)
- **Filtro por duración** con tolerancia en minutos (1-30 min)
- **Comparación de años** para evitar confundir secuelas
- **Análisis de rutas** para detectar archivos en carpetas diferentes

### 🖥️ **Interfaz Moderna**
- **Interfaz web** con Streamlit
- **Navegación por pares** para mejor rendimiento
- **Reproductores externos** para comparar videos
- **Análisis visual** de similitud con indicadores de color
- **Modo debug** para pruebas seguras

### ⚙️ **Configuración Flexible**
- **Configuración persistente** en JSON
- **Variables de entorno** para datos sensibles
- **Patrón Singleton** para acceso global a configuración
- **Interfaz de configuración** integrada en la aplicación

### 🎬 **Integración IMDB/TMDB**
- **Búsqueda automática** de información de películas
- **Sinopsis en español** usando TMDB API
- **Pósteres de alta calidad** para carátulas
- **Fallback inteligente**: IMDB → TMDB → Plex
- **Información completa**: Rating, director, actores, género

### 📱 **Integración Telegram**
- **Subida automática** de videos a canales de Telegram
- **Envío de carátulas** y sinopsis antes del video
- **Soporte para archivos grandes** (>1.5GB)
- **Progreso en tiempo real** durante la subida
- **Orden correcto**: Carátula → Sinopsis → Video

### 🗄️ **Integración Plex**
- **Conexión de solo lectura** a base de datos de Plex
- **Búsqueda de títulos reales** por nombre de archivo
- **Información de biblioteca** (año, sinopsis, rating)
- **Fallback seguro** cuando IMDB/TMDB fallan

## 🚀 Instalación Automática

### **Windows** 🪟
```bash
# Ejecutar script de instalación automática
setup\instalar_dependencias.bat

# Ejecutar aplicación
setup\run_app.bat
```

### **Linux/Mac** 🐧
```bash
# Hacer ejecutable y ejecutar
chmod +x setup/run_app.sh
./setup/run_app.sh
```

### **Python Cross-Platform** 🐍
```bash
# Instalación con Python
python setup/install_dependencies.py

# Ejecutar aplicación
python main.py
```

> **📋 Nota**: Después de la instalación automática, necesitarás configurar las variables de entorno y APIs. Ver sección [Configuración Completa](#-configuración-completa) más abajo.

## 🚀 Instalación Manual

### 1. **Clonar el Repositorio**
```bash
git clone <tu-repositorio>
cd scrapper-pelis
```

### 2. **Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### 3. **Configurar Variables de Entorno**
```bash
# Copiar plantilla de variables de entorno
cp src/settings/env_template.txt .env

# Editar .env con tus datos
# Ver sección "Configuración Completa" más abajo
```

### 4. **Ejecutar la Aplicación**
```bash
python main.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📁 Estructura del Proyecto

```
scrapper-pelis/
├── main.py                          # Punto de entrada principal
├── app_simple.py                    # Aplicación Streamlit
├── requirements.txt                 # Dependencias Python
├── README.md                        # Este archivo
│
├── src/                            # Código fuente
│   ├── app/                        # Aplicación Streamlit
│   │   └── streamlit_app.py
│   ├── services/                   # Servicios externos
│   │   ├── imdb_service.py         # Integración IMDB
│   │   └── telegram_service.py     # Integración Telegram
│   ├── settings/                   # Configuración
│   │   ├── settings.py            # Patrón Singleton
│   │   ├── config.json            # Configuración JSON
│   │   └── env_template.txt       # Plantilla .env
│   └── utils/                      # Utilidades
│       └── movie_detector.py       # Lógica de detección
│
└── peliculas_duplicadas.py         # Script original (legacy)
```

## ⚙️ Configuración

### **Archivo de Configuración (`src/settings/config.json`)**

```json
{
    "detection": {
        "similarity_threshold": 0.8,           // Umbral de similitud (0.1-1.0)
        "duration_filter_enabled": true,       // Activar filtro por duración
        "duration_tolerance_minutes": 1,       // Tolerancia en minutos
        "supported_extensions": [".mp4", ".avi", ".mkv", ...]
    },
    "ui": {
        "show_video_players": true,            // Mostrar reproductores
        "video_player_size": "medium"          // Tamaño del reproductor
    },
    "debug": {
        "enabled": true,                       // Modo debug activo
        "debug_folder": "ruta/debug"           // Carpeta para archivos debug
    }
}
```

### **Variables de Entorno (`.env`)**

```bash
# ===========================================
# CONFIGURACIÓN BÁSICA
# ===========================================

# Ruta a la base de datos de Plex (SOLO LECTURA)
PLEX_DATABASE_PATH=C:\Users\Usuario\AppData\Local\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db

# ===========================================
# TELEGRAM CONFIGURATION
# ===========================================

# Token del bot de Telegram (obtener de @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ID del canal de Telegram (obtener de @userinfobot)
TELEGRAM_CHANNEL_ID=-1001234567890

# Límite de tamaño de archivo en bytes (50MB = 52428800)
TELEGRAM_MAX_FILE_SIZE=52428800

# Delay entre subidas en segundos
TELEGRAM_UPLOAD_DELAY=2

# ===========================================
# API KEYS (OPCIONAL)
# ===========================================

# OMDb API Key (gratuita en omdbapi.com)
OMDB_API_KEY=tu_omdb_api_key_aqui

# TMDB API Key (gratuita en themoviedb.org)
TMDB_API_KEY=tu_tmdb_api_key_aqui

# IMDB API Key (opcional, para búsquedas adicionales)
IMDB_API_KEY=tu_imdb_api_key_aqui
```

## 🔧 Configuración Completa

### **📱 Configuración de Telegram**

#### **Paso 1: Crear Bot de Telegram**
1. **Abrir Telegram** y buscar `@BotFather`
2. **Enviar comando** `/newbot`
3. **Elegir nombre** para tu bot (ej: "Mi Bot de Películas")
4. **Elegir username** (debe terminar en 'bot', ej: "mi_bot_peliculas_bot")
5. **Copiar el token** que te proporciona BotFather
6. **Agregar token** a tu archivo `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

#### **Paso 2: Crear Canal de Telegram**
1. **Abrir Telegram** y crear un nuevo canal
2. **Elegir nombre** para tu canal (ej: "Mis Películas")
3. **Configurar como canal público** o privado
4. **Agregar tu bot** como administrador del canal
5. **Obtener ID del canal**:
   - Buscar `@userinfobot` en Telegram
   - Enviar el enlace de tu canal
   - Copiar el ID que te proporciona
6. **Agregar ID** a tu archivo `.env`:
   ```bash
   TELEGRAM_CHANNEL_ID=-1001234567890
   ```

#### **Paso 3: Configurar Permisos del Bot**
1. **Ir a configuración** del canal
2. **Administradores** → **Agregar administrador**
3. **Seleccionar tu bot**
4. **Dar permisos**:
   - ✅ Enviar mensajes
   - ✅ Enviar archivos multimedia
   - ✅ Enviar documentos
   - ✅ Enviar fotos

### **🗄️ Configuración de Plex**

#### **Ubicación de la Base de Datos**
La aplicación se conecta a la base de datos de Plex en **modo de solo lectura** para obtener información de películas.

**Ubicaciones típicas:**
- **Windows**: `C:\Users\[Usuario]\AppData\Local\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db`
- **macOS**: `~/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db`
- **Linux**: `~/.local/share/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db`

**Configurar en `.env`:**
```bash
PLEX_DATABASE_PATH=C:\Users\Usuario\AppData\Local\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db
```

⚠️ **IMPORTANTE**: La aplicación **NUNCA modifica** la base de datos de Plex, solo lee información.

### **🎬 Configuración de APIs de Películas**

#### **TMDB API (Recomendado - Español)**
1. **Ir a** [themoviedb.org](https://www.themoviedb.org/settings/api)
2. **Crear cuenta** gratuita
3. **Solicitar API Key** (gratuita)
4. **Agregar a `.env`**:
   ```bash
   TMDB_API_KEY=tu_tmdb_api_key_aqui
   ```

#### **OMDb API (Inglés)**
1. **Ir a** [omdbapi.com](https://www.omdbapi.com/)
2. **Registrarse** para obtener API key gratuita
3. **Agregar a `.env`**:
   ```bash
   OMDB_API_KEY=tu_omdb_api_key_aqui
   ```

#### **Flujo de Búsqueda de Información**
1. **Limpia el nombre** del archivo (elimina [DVDrip], [Spanish], etc.)
2. **Busca en IMDB** con nombre limpio
3. **Si falla IMDB** → Busca en Plex por nombre de archivo
4. **Si Plex encuentra título** → Busca en TMDB (español)
5. **Si TMDB falla** → Busca en OMDb (inglés)
6. **Combina información** de todas las fuentes

## 🎮 Uso de la Aplicación

### **1. Escaneo de Películas**
1. **Selecciona la carpeta** a escanear en el sidebar
2. **Configura los filtros**:
   - Umbral de similitud (recomendado: 0.8)
   - Filtro por duración (recomendado: 1 minuto)
3. **Haz clic en "🔍 Escanear Películas"**
4. **Observa el progreso** en el miniterminal

### **2. Revisar Duplicados**
1. **Navega entre pares** con los botones Anterior/Siguiente
2. **Compara videos** usando "Abrir en Reproductor"
3. **Analiza la similitud** en la sección de análisis
4. **Selecciona películas** para eliminar/mover

### **3. Gestionar Duplicados**
- **Seleccionar películas** con checkboxes (mutuamente excluyentes)
- **Mover archivos seleccionados** a una carpeta específica
- **Eliminar seleccionadas** (modo debug: mueve a carpeta debug)

### **4. Subir a Telegram con Información IMDB**
1. **Ir a la pestaña "IMDB"** en la aplicación
2. **Seleccionar método de subida**:
   - **📁 Desde Carpeta**: Escanear carpeta y seleccionar videos
   - **📎 Archivos Individuales**: Subir archivos específicos
3. **Configurar opciones**:
   - ✅ **Usar Telethon** (para archivos grandes)
   - ✅ **Enviar carátula** (póster de la película)
4. **Hacer clic en "🚀 Subir a IMDB con Información"**
5. **Observar el progreso**:
   - 🔍 **Paso 1**: Buscar información de películas
   - 🖼️ **Paso 2**: Enviar carátulas
   - 📝 **Paso 3**: Enviar sinopsis
   - 🎬 **Paso 4**: Subir videos

### **5. Resultado en Telegram**
Para cada película se enviará en orden:
1. **🖼️ Carátula** (póster de alta calidad)
2. **📝 Información completa**:
   ```
   🎬 **Título de la Película** (Año)
   
   ⭐ **Rating:** 8.5/10
   🎭 **Director:** Nombre del Director
   👥 **Actores:** Actor1, Actor2, Actor3
   🎭 **Género:** Acción, Aventura, Comedia
   
   📖 **Sinopsis:**
   [Sinopsis completa de la película]
   ```
3. **🎬 Video** (archivo de video)

## 🔧 Configuración Avanzada

### **Filtros de Detección**

| Parámetro | Descripción | Rango | Recomendado |
|-----------|-------------|-------|-------------|
| `similarity_threshold` | Umbral de similitud de nombres | 0.1 - 1.0 | 0.8 |
| `duration_tolerance_minutes` | Tolerancia de duración | 1 - 30 | 1 |
| `duration_filter_enabled` | Activar filtro por duración | true/false | true |

### **Formatos Soportados**
- **MP4, AVI, MKV** (recomendados)
- **MOV, WMV, FLV, M4V**
- **MPG, MPEG, 3GP, WebM**

### **Modo Debug**
- **Activado por defecto** para seguridad
- **No elimina archivos** realmente
- **Mueve a carpeta debug** configurada
- **Desactivar** solo cuando estés seguro

## 🛠️ Desarrollo

### **Arquitectura Clean Code**
- **Separación de responsabilidades** en módulos
- **Patrón Singleton** para configuración
- **Inyección de dependencias** para servicios
- **Logging estructurado** para debugging

### **Extensibilidad**
- **Servicios modulares** (IMDB, Telegram)
- **Configuración flexible** via JSON
- **API de detección** reutilizable
- **Interfaz personalizable**

### **Testing**
```bash
# Ejecutar tests (cuando estén implementados)
python -m pytest tests/
```

## 📊 Rendimiento

### **Optimizaciones Implementadas**
- **Paginación** para grandes colecciones
- **Reproductores externos** para mejor rendimiento
- **Filtros inteligentes** para reducir falsos positivos
- **Escaneo eficiente** con metadata de video

### **Recomendaciones**
- **Colecciones grandes**: Usar filtros estrictos
- **Videos largos**: Desactivar reproductores embebidos
- **Red lenta**: Configurar timeouts apropiados

## 🔒 Seguridad

### **Modo Debug (Recomendado)**
- **Activado por defecto** para prevenir pérdida de datos
- **Archivos movidos** a carpeta debug
- **Logging completo** de todas las operaciones
- **Confirmación manual** antes de eliminar

### **Variables Sensibles**
- **API Keys** en archivo `.env` (no en git)
- **Rutas de red** configuradas por usuario
- **Tokens de Telegram** protegidos

## 🐛 Solución de Problemas

### **Problemas Comunes**

#### **"Mutagen no disponible"**
```bash
pip install mutagen>=1.47.0
```

#### **"Streamlit ya está ejecutándose"**
```bash
# Windows
taskkill /f /im python.exe

# Linux/Mac
pkill -f streamlit
```

#### **"Puerto 8501 ocupado"**
```bash
# Cambiar puerto en main.py
subprocess.run([..., "--server.port", "8502", ...])
```

#### **"Error 401: Unauthorized" (OMDb/TMDB)**
```bash
# Verificar que las API keys estén correctas en .env
OMDB_API_KEY=tu_api_key_correcta
TMDB_API_KEY=tu_api_key_correcta
```

#### **"No se encuentra la base de datos de Plex"**
```bash
# Verificar la ruta en .env
PLEX_DATABASE_PATH=C:\ruta\correcta\com.plexapp.plugins.library.db
```

#### **"Bot de Telegram no responde"**
1. **Verificar token** en `.env`
2. **Agregar bot como administrador** del canal
3. **Verificar permisos** del bot
4. **Comprobar ID del canal** (debe empezar con -100)

### **Logs y Debugging**
- **Logs detallados** en `app.log`
- **Modo debug** con información extra
- **Miniterminal** para seguimiento en tiempo real

## 🤝 Contribuir

### **Cómo Contribuir**
1. **Fork** el repositorio
2. **Crear rama** para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crear Pull Request**

### **Estándares de Código**
- **PEP 8** para estilo de Python
- **Docstrings** para documentación
- **Type hints** para mejor legibilidad
- **Tests** para nuevas funcionalidades

## 📝 Changelog

### **v1.0.0** (Actual)
- ✅ Detección básica de duplicados
- ✅ Filtros por duración y similitud
- ✅ Interfaz Streamlit moderna
- ✅ Modo debug para seguridad
- ✅ Configuración flexible
- ✅ Reproductores externos
- ✅ Navegación por pares

### **v2.0.0** (Actual)
- ✅ **Integración IMDB/TMDB completa**
- ✅ **Subida automática a Telegram**
- ✅ **Integración con Plex (solo lectura)**
- ✅ **Búsqueda inteligente de información**
- ✅ **Envío de carátulas y sinopsis**
- ✅ **Soporte para archivos grandes**
- ✅ **Fallback automático entre APIs**
- ✅ **Sinopsis en español (TMDB)**

### **Próximas Versiones**
- 🔄 Análisis de calidad de video
- 🔄 Detección de subtítulos
- 🔄 Interfaz de administración
- 🔄 Soporte para series de TV
- 🔄 Detección automática de ediciones

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Autores

- **Desarrollador Principal**: [Tu Nombre]
- **Contribuidores**: [Lista de contribuidores]

## 🙏 Agradecimientos

- **Streamlit** por la excelente plataforma web
- **Mutagen** por la extracción de metadata de video
- **IMDB API** por la información de películas
- **Telegram Bot API** por la integración de mensajería

---

## 📞 Soporte

Si tienes problemas o preguntas:

1. **Revisa** la sección de solución de problemas
2. **Consulta** los logs en `app.log`
3. **Abre un issue** en GitHub
4. **Contacta** al desarrollador

---

**¡Disfruta organizando tu colección de películas! 🎬✨**