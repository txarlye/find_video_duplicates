# 🎬 Integración con PLEX Media Server

## 📋 Descripción

La aplicación ahora incluye integración opcional con **PLEX Media Server** para mejorar la detección de duplicados y obtener estadísticas detalladas de tu biblioteca de películas.

## ✨ Características

### 🔍 **Detección Mejorada**
- **Metadatos precisos**: Títulos, años, duraciones y calificaciones de PLEX
- **Detección híbrida**: Combina análisis de archivos con metadatos de PLEX
- **Detección nativa**: Usa la detección de duplicados de PLEX directamente
- **Información rica**: Géneros, directores, actores, estudios, etc.

### 📊 **Estadísticas Avanzadas**
- **Métricas de biblioteca**: Total de películas, tamaño, duración
- **Distribuciones**: Por año, género, resolución, códec
- **Calificaciones**: Promedio de calificaciones IMDB/TMDB
- **Análisis de calidad**: Distribución de resoluciones y códecs

## 🚀 Configuración

### **1. Variables de Entorno**

Agrega tus credenciales de PLEX al archivo `.env`:

```bash
# Credenciales de PLEX Media Server
PLEX_USER=tu_usuario_plex
PLEX_PASS=tu_contraseña_plex
```

### **2. Instalación de Dependencias**

```bash
pip install python-plexapi>=4.15.0
```

### **3. Configuración en la Aplicación**

1. **Ve a la pestaña "Configuración"** en el sidebar
2. **Habilita la integración con PLEX**
3. **Configura las opciones**:
   - ✅ **Usar detección de PLEX**: Usar PLEX para detectar duplicados
   - ✅ **Usar metadatos de PLEX**: Mejorar detección con metadatos
   - ✅ **Conectar automáticamente**: Conectar al iniciar
   - ✅ **Preferir títulos de PLEX**: Usar títulos de PLEX
   - ✅ **Preferir años de PLEX**: Usar años de PLEX
   - ✅ **Preferir duración de PLEX**: Usar duración de PLEX

## 🎯 Modos de Detección

### **1. Detección Estándar (Sin PLEX)**
- Análisis de nombres de archivos
- Extracción de metadatos básicos
- Comparación por similitud de títulos

### **2. Detección Híbrida (Recomendada)**
- Combina análisis de archivos con metadatos de PLEX
- Usa información de PLEX para mejorar precisión
- Mantiene compatibilidad con archivos no en PLEX

### **3. Detección Nativa de PLEX**
- Usa directamente la detección de PLEX
- Máxima precisión para películas en PLEX
- Requiere que las películas estén en bibliotecas de PLEX

## 📊 Estadísticas Disponibles

### **Métricas Básicas**
- Total de películas en PLEX
- Tamaño total de la biblioteca (GB)
- Duración total (horas)
- Calificación promedio

### **Distribuciones**
- **Por año**: Películas por año de lanzamiento
- **Por género**: Géneros más comunes
- **Por resolución**: 1080p, 720p, 4K, etc.
- **Por códec**: H.264, H.265, etc.

### **Información Detallada**
- Calificaciones IMDB/TMDB
- Información de estudio
- Conteo de visualizaciones
- Fecha de última visualización

## 🔧 Uso de la Aplicación

### **1. Escaneo con PLEX**

1. **Selecciona la carpeta** a analizar
2. **Activa "Usar integración con PLEX"**
3. **Haz clic en "Escanear"**
4. **La aplicación**:
   - Se conecta a PLEX automáticamente
   - Escanea archivos de la carpeta
   - Obtiene metadatos de PLEX para archivos coincidentes
   - Detecta duplicados usando información mejorada

### **2. Visualización de Resultados**

- **Métricas mejoradas** con información de PLEX
- **Estadísticas de biblioteca** de PLEX
- **Información detallada** de cada película
- **Distribuciones** por género, resolución, etc.

### **3. Gestión de Duplicados**

- **Selección inteligente** basada en metadatos
- **Información de calidad** para decidir qué mantener
- **Estadísticas de visualización** para priorizar

## ⚙️ Configuración Avanzada

### **Preferencias de Metadatos**

```json
{
    "plex": {
        "enabled": true,
        "use_plex_detection": false,
        "use_plex_metadata": true,
        "auto_connect": true,
        "prefer_plex_titles": true,
        "prefer_plex_years": true,
        "prefer_plex_duration": true
    }
}
```

### **Opciones de Detección**

- **`use_plex_detection`**: Usar detección nativa de PLEX
- **`use_plex_metadata`**: Usar metadatos de PLEX para mejorar detección
- **`prefer_plex_*`**: Preferir metadatos de PLEX sobre análisis de archivos

## 🛠️ Solución de Problemas

### **Error de Conexión**

```
❌ PLEX no conectado: Error de autenticación
```

**Solución:**
1. Verifica credenciales en `.env`
2. Asegúrate de que PLEX esté ejecutándose
3. Verifica conectividad de red

### **Credenciales No Encontradas**

```
⚠️ Credenciales de PLEX no configuradas en .env
```

**Solución:**
1. Crea archivo `.env` en la raíz del proyecto
2. Agrega `PLEX_USER=tu_usuario` y `PLEX_PASS=tu_contraseña`
3. Reinicia la aplicación

### **Bibliotecas No Encontradas**

```
❌ No se encontraron bibliotecas de películas en PLEX
```

**Solución:**
1. Asegúrate de tener bibliotecas de películas en PLEX
2. Verifica que las bibliotecas estén configuradas correctamente
3. Revisa permisos de acceso

## 📈 Beneficios de la Integración

### **Para Usuarios**
- **Detección más precisa** de duplicados
- **Información rica** sobre cada película
- **Estadísticas detalladas** de la biblioteca
- **Gestión inteligente** de duplicados

### **Para la Aplicación**
- **Mejor rendimiento** con metadatos pre-calculados
- **Detección más inteligente** usando información de PLEX
- **Experiencia mejorada** con información visual
- **Automatización** de tareas repetitivas

## 🔒 Seguridad

- **Credenciales seguras** almacenadas en `.env`
- **Conexión encriptada** con PLEX
- **No almacenamiento** de credenciales en código
- **Acceso de solo lectura** a metadatos de PLEX

## 📝 Notas Importantes

1. **PLEX debe estar ejecutándose** para usar la integración
2. **Las películas deben estar en bibliotecas de PLEX** para obtener metadatos
3. **La integración es opcional** - la aplicación funciona sin PLEX
4. **Los metadatos de PLEX** mejoran la precisión pero no son obligatorios

---

**¡Disfruta de la detección mejorada de duplicados con PLEX! 🎬✨**
