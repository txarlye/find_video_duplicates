# 🎬 Gestión de Pares de Duplicados - Funcionalidades de Navegación

## 📋 Descripción

Se han implementado nuevas funcionalidades para la gestión y navegación de pares de duplicados, permitiendo:

- **Navegación entre pares**: Ir al siguiente/anterior par o saltar a un par específico
- **Vista detallada**: Mostrar información completa de cada par
- **Selección de pares**: Elegir pares específicos para trabajar con ellos
- **Análisis configurable**: Mostrar/ocultar diferentes tipos de análisis

## 🏗️ Arquitectura

### Clases Principales

#### 1. `PairNavigationManager`
- **Propósito**: Gestiona la navegación entre pares de duplicados
- **Funcionalidades**:
  - Navegación secuencial (anterior/siguiente)
  - Salto a par específico mediante dropdown
  - Reinicio a la primera posición
  - Control del estado actual

#### 2. `PairListManager`
- **Propósito**: Gestiona la lista completa de pares
- **Funcionalidades**:
  - Mostrar resumen estadístico
  - Tabla expandible con todos los pares
  - Filtros y opciones de visualización

#### 3. `PairDetailViewer`
- **Propósito**: Muestra información detallada de un par específico
- **Funcionalidades**:
  - Encabezado con información básica
  - Opciones de análisis configurables
  - Acciones rápidas
  - Resumen del par

#### 4. `DuplicatePairsManager`
- **Propósito**: Gestor principal que integra todas las funcionalidades
- **Funcionalidades**:
  - Coordinación entre todos los gestores
  - Interfaz principal unificada
  - Gestión de selecciones

## 🚀 Uso Básico

### Inicialización

```python
from src.utils.ui_components import DuplicatePairsManager

# Crear el gestor principal
pairs_manager = DuplicatePairsManager()

# Establecer la lista de pares (datos del escaneo)
pairs_manager.set_pairs_list(duplicate_pairs_list)

# Renderizar la interfaz principal
pairs_manager.render_main_interface()
```

### Navegación

```python
# Obtener par actual
current_pair = pairs_manager.navigation.get_current_pair()

# Ir al siguiente par
pairs_manager.navigation.go_to_next()

# Ir a un par específico
pairs_manager.navigation.go_to_pair(5)  # Par 6

# Obtener información de navegación
current_index = pairs_manager.navigation.get_current_index()
total_pairs = pairs_manager.navigation.get_total_pairs()
```

### Gestión de Selecciones

```python
# Obtener películas seleccionadas
selected_movies = pairs_manager.get_selected_movies()

# Limpiar todas las selecciones
pairs_manager.clear_all_selections()
```

## 🎯 Funcionalidades Implementadas

### 1. Navegación Intuitiva
- **Botones de navegación**: Anterior, Siguiente, Reiniciar
- **Selector de par**: Dropdown para ir a cualquier par específico
- **Indicador de posición**: "Par X de Y"

### 2. Vista Detallada
- **Información básica**: Nombres de archivos, tamaños, similitud
- **Métricas visuales**: Diferencias de tamaño, porcentajes
- **Resumen estadístico**: Comparación entre archivos

### 3. Opciones Configurables
- **Análisis de Plex**: Mostrar/ocultar análisis de Plex
- **Reproductores**: Mostrar/ocultar reproductores de video
- **Opciones de Edición**: Mostrar/ocultar gestión de ediciones

### 4. Acciones Rápidas
- **Eliminación**: Botones para eliminar cada película del par
- **Renombrado**: Opciones para renombrar archivos
- **Gestión**: Acciones específicas por película

## 🔧 Integración con la Aplicación Principal

### En `streamlit_manager.py`

```python
from src.utils.ui_components import DuplicatePairsManager

class StreamlitManager:
    def __init__(self):
        # ... código existente ...
        self.pairs_manager = DuplicatePairsManager()
    
    def render_duplicate_pairs(self, duplicate_pairs):
        """Renderiza los pares de duplicados con navegación"""
        # Establecer la lista de pares
        self.pairs_manager.set_pairs_list(duplicate_pairs)
        
        # Mostrar la interfaz principal
        self.pairs_manager.render_main_interface()
        
        # Integrar con análisis de Plex existente
        current_pair = self.pairs_manager.navigation.get_current_pair()
        if current_pair:
            self._render_plex_analysis_for_pair(current_pair)
```

### Personalización de Análisis

```python
def _render_specific_analysis(self, pair_data, pair_index):
    """Renderiza análisis específico según configuración"""
    show_plex = st.session_state.get('show_plex_analysis', True)
    
    if show_plex:
        # Integrar con PlexEditionsManager existente
        analysis = self.plex_editions_manager.analyze_duplicate_pair_with_editions(
            pair_data['Ruta 1'], 
            pair_data['Ruta 2'],
            plex_info1, 
            plex_info2
        )
        self._display_editions_analysis(analysis, pair_data['Ruta 1'], pair_data['Ruta 2'], pair_index)
```

## 📊 Ejemplo de Datos

```python
example_pairs = [
    {
        'Ruta 1': '/movies/pelicula1.mkv',
        'Ruta 2': '/movies/pelicula1_copy.mkv',
        'Tamaño 1': 2147483648,  # 2GB
        'Tamaño 2': 2147483648,  # 2GB
        'Similitud': 95.5
    },
    # ... más pares
]
```

## 🎨 Interfaz de Usuario

### Controles de Navegación
```
[⏮️ Anterior] [Par 1 de 3] [Selector de Par ▼] [⏭️ Siguiente] [🔄 Reiniciar]
```

### Información del Par
```
🎬 Par 1 de 3
┌─────────────────┬─────────────────┐
│ Película 1:     │ Película 2:     │
│ 📁 archivo1.mkv │ 📁 archivo2.mkv │
│ 📊 2.0 GB       │ 📊 2.0 GB       │
│ 📏 95.5%        │ 📏 95.5%        │
└─────────────────┴─────────────────┘
```

### Opciones de Análisis
```
🔧 Opciones de Análisis
[✓] 🔍 Análisis de Plex    [✓] 🎥 Reproductores    [✓] 📚 Opciones de Edición
```

## 🚀 Próximos Pasos

1. **Integración completa**: Conectar con `StreamlitManager` existente
2. **Análisis de Plex**: Integrar con `PlexEditionsManager`
3. **Reproductores**: Implementar reproductores de video
4. **Acciones**: Conectar botones con funcionalidades reales
5. **Filtros**: Implementar filtros avanzados para la lista de pares

## 📝 Notas de Implementación

- **Estado de sesión**: Todas las clases manejan su propio estado en `st.session_state`
- **Navegación circular**: Al llegar al último par, vuelve al primero
- **Responsive**: La interfaz se adapta al número de pares disponibles
- **Extensible**: Fácil agregar nuevas funcionalidades a cada gestor

## 🔍 Debugging

Para debuggear la navegación:

```python
# Verificar estado actual
print(f"Par actual: {pairs_manager.navigation.get_current_index()}")
print(f"Total pares: {pairs_manager.navigation.get_total_pairs()}")
print(f"Par actual: {pairs_manager.navigation.get_current_pair()}")
```
