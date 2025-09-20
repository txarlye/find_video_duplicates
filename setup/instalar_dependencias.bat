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

REM Preguntar tipo de instalación
echo ¿Qué tipo de instalación prefieres?
echo 1. Completa (todas las dependencias)
echo 2. Mínima (solo lo esencial)
set /p install_choice="Selecciona (1/2): "

if "%install_choice%"=="1" (
    set requirements_file=requirements.txt
) else (
    set requirements_file=requirements-minimal.txt
)

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
python -c "import streamlit, pandas, requests; print('✅ Dependencias verificadas')"
if errorlevel 1 (
    echo ❌ Error verificando dependencias
    pause
    exit /b 1
)

echo.
echo 🎉 ¡Instalación completada exitosamente!
echo 💡 Ahora puedes ejecutar la aplicación con:
echo    python iniciar_app.py
echo.
pause
