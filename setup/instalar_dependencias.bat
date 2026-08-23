@echo off
echo 🎬 Instalador de Dependencias - Detector de Películas Duplicadas
echo ================================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    echo 💡 Instala Python desde https://python.org
    echo    Asegúrate de marcar "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Preguntar si crear entorno virtual
echo ¿Deseas crear un entorno virtual? (recomendado)
echo 1. Sí, crear entorno virtual
echo 2. No, instalar en el sistema
set /p choice="Selecciona (1/2): "

if "%choice%"=="1" (
    echo.
    echo 🐍 Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Error creando entorno virtual
        pause
        exit /b 1
    )
    echo ✅ Entorno virtual creado
    echo.
    echo ⚠️  IMPORTANTE: Activa el entorno virtual antes de continuar
    echo    venv\Scripts\activate
    echo.
    pause
)

REM Instalar dependencias
echo 📦 Instalando dependencias...
set requirements_file=requirements.txt

echo.
echo 📦 Instalando dependencias desde %requirements_file%...
pip install -r %requirements_file%
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo ✅ Dependencias instaladas correctamente
echo.

REM Verificar instalación
echo 🔍 Verificando instalación...
python -c "import fastapi, pandas, requests; print('✅ Dependencias verificadas')"
if errorlevel 1 (
    echo ❌ Error verificando dependencias
    pause
    exit /b 1
)

echo.
echo 🎉 ¡Instalación completada exitosamente!
echo 💡 Ahora puedes ejecutar la aplicación con:
echo    python main.py
echo.
echo 📋 CONFIGURACIÓN ADICIONAL REQUERIDA:
echo    - Configura las variables de entorno en .env
echo    - Configura Telegram Bot y Canal
echo    - Configura APIs de IMDB/TMDB/OMDb
echo    - Configura ruta de base de datos Plex
echo.
echo 📖 Ver README.md para instrucciones detalladas
echo.
pause
