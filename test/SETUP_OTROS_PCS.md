# Instrucciones para Sincronizar el Código en Otros PCs

## 📋 Requisitos Previos

1. **Git instalado** en el PC de destino
2. **Python 3.8+** instalado
3. **Acceso al repositorio** (URL del repositorio)

## 🚀 Pasos para Sincronizar

### Opción 1: Clonar el Repositorio (Primera vez)

```bash
# 1. Clonar el repositorio
git clone https://github.com/txarlye/find_video_duplicates.git

# 2. Entrar al directorio
cd find_video_duplicates

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python main.py
```

### Opción 2: Sincronizar con Repositorio Existente

Si ya tienes el repositorio clonado:

```bash
# 1. Ir al directorio del proyecto
cd "ruta/del/proyecto"

# 2. Verificar que estás en la rama main
git branch

# 3. Hacer pull de los últimos cambios
git pull origin main

# 4. Instalar/actualizar dependencias si es necesario
pip install -r requirements.txt

# 5. Ejecutar la aplicación
python main.py
```

## 🔄 Flujo de Trabajo Diario

### Para Obtener los Últimos Cambios

```bash
# 1. Verificar estado actual
git status

# 2. Hacer pull de cambios remotos
git pull origin main

# 3. Si hay conflictos, resolverlos y hacer commit
git add .
git commit -m "Resolución de conflictos"
```

### Para Enviar Cambios al Repositorio

```bash
# 1. Agregar archivos modificados
git add .

# 2. Hacer commit con mensaje descriptivo
git commit -m "Descripción de los cambios realizados"

# 3. Enviar cambios al repositorio remoto
git push origin main
```

## 🛠️ Solución de Problemas Comunes

### Error: "Your branch is ahead of origin/main"
```bash
# Hacer push de los cambios locales
git push origin main
```

### Error: "Your branch is behind origin/main"
```bash
# Hacer pull de los cambios remotos
git pull origin main
```

### Error: "Merge conflict"
```bash
# 1. Abrir los archivos con conflictos y resolverlos manualmente
# 2. Agregar los archivos resueltos
git add .

# 3. Completar el merge
git commit -m "Resolución de conflictos de merge"
```

### Error: "Repository not found"
- Verificar que la URL del repositorio sea correcta
- Verificar que tengas permisos de acceso al repositorio
- Verificar tu conexión a internet

## 📁 Estructura del Proyecto

```
scrapper pelis/
├── main.py                 # Script principal
├── app_simple.py          # Aplicación Streamlit
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación principal
├── ARCHITECTURE.md       # Arquitectura del proyecto
├── .gitignore           # Archivos a ignorar por Git
├── setup/               # Scripts de instalación
│   ├── install_dependencies.py
│   ├── instalar_dependencias.bat
│   ├── run_app.bat
│   └── run_app.sh
└── src/                 # Código fuente
    ├── app/             # Aplicación Streamlit
    ├── services/        # Servicios (IMDB, Telegram)
    ├── settings/        # Configuración
    └── utils/           # Utilidades
```

## 🔧 Comandos Útiles

```bash
# Ver estado del repositorio
git status

# Ver historial de commits
git log --oneline

# Ver diferencias con el repositorio remoto
git diff origin/main

# Cambiar a la rama main
git checkout main

# Crear una nueva rama
git checkout -b nombre-nueva-rama

# Ver ramas disponibles
git branch -a
```

## 📞 Soporte

Si tienes problemas:

1. **Verificar conexión a internet**
2. **Verificar que Git esté instalado correctamente**
3. **Verificar permisos del repositorio**
4. **Revisar los logs de error**

## 🎯 Notas Importantes

- **Siempre hacer `git pull` antes de empezar a trabajar**
- **Hacer commit frecuentemente con mensajes descriptivos**
- **No hacer push de archivos sensibles (contraseñas, claves API)**
- **Usar el archivo `.gitignore` para excluir archivos innecesarios**
