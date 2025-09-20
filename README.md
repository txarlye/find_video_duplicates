# 🎬 Detector de Películas Duplicadas

Una aplicación inteligente desarrollada en Python con Streamlit para detectar películas duplicadas en tu colección de videos, con filtros avanzados por duración y similitud de nombres.

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

## 🚀 Instalación Rápida

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
# OPEN_AI_API=tu_api_key_aqui
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
# API Keys (opcional)
OPEN_AI_API=tu_api_key_aqui
IMDB_API_KEY=tu_imdb_key_aqui
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui
TELEGRAM_CHANNEL_ID=tu_channel_id_aqui
```

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

### **Próximas Versiones**
- 🔄 Integración IMDB completa
- 🔄 Subida automática a Telegram
- 🔄 Análisis de calidad de video
- 🔄 Detección de subtítulos
- 🔄 Interfaz de administración

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