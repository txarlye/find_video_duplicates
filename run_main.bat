@echo off
REM Lanza la app (mismo comando que usamos en las pruebas: venv + main.py)
REM Doble clic para arrancar sin tener que abrir PowerShell a mano.

cd /d "%~dp0"
powershell -NoExit -ExecutionPolicy Bypass -Command ".\venv\Scripts\python.exe main.py"
