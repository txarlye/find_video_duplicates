# Módulo de Video Organizado

Este módulo contiene utilidades organizadas para el manejo de videos, divididas en clases especializadas.

## 📁 Estructura

```
src/utils/video/
├── __init__.py              # Exportaciones principales
├── video.py                 # Clases básicas de video
├── duration.py              # Gestión inteligente de duración
├── analysis.py              # Análisis avanzado de videos
├── plex_integration.py      # Integración con PLEX
└── README.md                # Este archivo
```

## 🎯 Clases Disponibles

### **VideoPlayer** (`video.py`)
- Manejo de reproductores embebidos y externos
- Verificación de compatibilidad de archivos
- Renderizado de información de videos

### **VideoFormatter** (`video.py`)
- Formateo de duraciones (segundos → "1h 30m 45s")
- Formateo de tamaños (bytes → GB)
- Parsing de cadenas de duración

### **VideoComparison** (`video.py`)
- Comparación de duraciones, tamaños y rutas
- Análisis de similitud entre videos

### **VideoDurationManager** (`duration.py`) ⭐
- **Duración inteligente**: PLEX vs análisis de archivo
- Comparación de duraciones con lógica configurada
- Formateo automático de duraciones

### **VideoAnalyzer** (`analysis.py`)
- Análisis completo de archivos de video
- Detección de calidad (4K, HD, SD, etc.)
- Extracción de metadatos con mutagen

### **PlexVideoIntegration** (`plex_integration.py`)
- Conexión y consulta a base de datos de PLEX
- Comparación entre archivos locales y PLEX
- Obtención de metadatos completos

## 🚀 Uso Rápido

```python
from src.utils.video import VideoDurationManager, VideoAnalyzer

# Duración inteligente
duration_manager = VideoDurationManager()
duracion = duration_manager.obtener_duracion_inteligente(archivo)

# Análisis de video
analyzer = VideoAnalyzer()
info = analyzer.analizar_archivo_video(archivo)
calidad = analyzer.detectar_calidad_video(archivo)
```

## ⚙️ Configuración

La funcionalidad de duración inteligente se controla con:

- `settings.get_plex_prefer_duration()` - Preferir duración de PLEX
- `settings.get_plex_enabled()` - PLEX habilitado
- `settings.get_plex_prefer_duration()` - Preferir duración de PLEX

## 🔧 Dependencias

- **Obligatorias**: `streamlit`, `pathlib`
- **Opcionales**: `mutagen`, `plex_database_direct`

## 📝 Ejemplo Completo

Ver `ejemplo_duracion_inteligente.py` para un ejemplo completo de uso.
