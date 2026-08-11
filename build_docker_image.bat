@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo  Construir imagen Docker
echo  Detector de Peliculas Duplicadas
echo ========================================
echo.
echo Esta imagen SIEMPRE es generica: config.json y .env nunca se
echo hornean dentro (se montan como volumen al ejecutarla), asi que la
echo misma imagen sirve tanto para ti como para compartirla con otros.
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encuentra "docker" en el PATH. Instala/abre Docker Desktop primero.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker no esta arrancado. Abre Docker Desktop y vuelve a intentarlo.
    pause
    exit /b 1
)

echo Construyendo imagen "find-video-duplicates:latest" desde la raiz del repo...
echo (contexto = esta carpeta, receta = docker\Dockerfile)
echo.

docker build -f docker\Dockerfile -t find-video-duplicates:latest .
if errorlevel 1 (
    echo.
    echo [ERROR] El build ha fallado. Revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo [OK] Imagen construida correctamente.
echo.

set /p EXPORTAR="¿Exportar tambien un .tar para compartir/copiar a tu Synology? (S/N): "
if /i "%EXPORTAR%"=="S" (
    echo.
    echo Exportando docker\find-video-duplicates.tar ...
    docker save find-video-duplicates:latest -o docker\find-video-duplicates.tar
    if errorlevel 1 (
        echo [ERROR] Fallo al exportar el .tar.
        pause
        exit /b 1
    )
    echo [OK] Generado docker\find-video-duplicates.tar
    echo.
    echo Siguiente paso en el Synology:
    echo   1. Copia docker\find-video-duplicates.tar y docker\docker-compose-synology.yml
    echo      ^(y docker\env.template^) a una carpeta del NAS.
    echo   2. docker load -i find-video-duplicates.tar
    echo   3. Copia env.template a .env y ajusta las rutas ^(MOVIES_PATH, PLEX_DB_PATH...^).
    echo   4. Asegurate de tener tambien un .env en la raiz del repo con tus claves
    echo      ^(copia .env.example si no lo tienes^).
    echo   5. docker-compose -f docker-compose-synology.yml up -d
) else (
    echo.
    echo Listo. La imagen "find-video-duplicates:latest" ya esta disponible en tu Docker local.
    echo Para probarla aqui mismo: docker-compose -f docker\docker-compose-synology.yml up -d
)

echo.
pause
