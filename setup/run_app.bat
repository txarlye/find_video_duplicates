@echo off
echo 🎬 Iniciando Detector de Películas Duplicadas...
echo 🌐 Abriendo navegador automáticamente...
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    echo 💡 Instala Python desde https://python.org
    pause
    exit /b 1
)

REM Ejecutar la aplicación
echo ✅ Ejecutando aplicación...
python main.py

pause
