@echo off
REM Lanza la API nueva (FastAPI + frontend React) en local, con
REM autoapertura de navegador — mismo patron que run_main.bat/main.py.
REM Doble clic para arrancar sin tener que abrir PowerShell a mano.

cd /d "%~dp0"
powershell -NoExit -ExecutionPolicy Bypass -Command ".\venv\Scripts\python.exe main_api.py"
