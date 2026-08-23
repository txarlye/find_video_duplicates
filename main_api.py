#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador de la API nueva (FastAPI + frontend React) — vive en paralelo
a main.py (Streamlit) mientras dura la migración pantalla a pantalla.
Mismo patrón que main.py: sondea el health endpoint antes de abrir
navegador, no abre nada en Docker, dirección/puerto configurables.

Al cerrar la migración (ver plan), este script sustituye a main.py.
"""

import subprocess
import sys
import webbrowser
import time
import os
import threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    print("🎬 Iniciando API (FastAPI + frontend)...")

    is_docker = os.environ.get("DOCKER_CONTAINER", False)
    if not is_docker:
        print("🌐 Abriendo navegador automáticamente...")
    else:
        print("🐳 Ejecutando en modo contenedor...")

    print("=" * 50)

    server_address = os.environ.get("API_SERVER_ADDRESS", "127.0.0.1")
    port = os.environ.get("API_PORT", "8000")
    base_url = f"http://{server_address}:{port}"

    try:
        import requests
        response = requests.get(f"{base_url}/api/health", timeout=2)
        if response.status_code == 200:
            print(f"⚠️ La API ya está ejecutándose en el puerto {port}")
            print("🌐 Abriendo navegador...")
            webbrowser.open(base_url)
            return
    except Exception:
        pass

    if not is_docker:
        def open_browser():
            import requests as _requests
            limite = time.time() + 30
            while time.time() < limite:
                try:
                    if _requests.get(f"{base_url}/api/health", timeout=1).status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            try:
                webbrowser.open(base_url)
                print(f"🌐 Navegador abierto en {base_url}")
            except Exception as e:
                print(f"⚠️ Error abriendo navegador: {e}")

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", server_address,
            "--port", port,
        ])
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando la API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
