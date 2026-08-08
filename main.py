#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para ejecutar la aplicación
"""

import subprocess
import sys
import webbrowser
import time
import os
import threading

def main():
    """Ejecuta la aplicación Streamlit"""
    print("🎬 Iniciando Detector de Películas Duplicadas...")
    
    # Solo mostrar mensaje de navegador si no estamos en Docker
    is_docker = os.environ.get('DOCKER_CONTAINER', False)
    if not is_docker:
        print("🌐 Abriendo navegador automáticamente...")
    else:
        print("🐳 Ejecutando en modo contenedor...")
    
    print("=" * 50)
    
    # Verificar si ya hay una instancia ejecutándose
    try:
        import requests
        response = requests.get("http://localhost:8501", timeout=2)
        if response.status_code == 200:
            print("⚠️ Streamlit ya está ejecutándose en el puerto 8501")
            print("🌐 Abriendo navegador...")
            webbrowser.open("http://localhost:8501")
            return
    except:
        pass  # No hay instancia ejecutándose, continuar normalmente
    
    # Solo abrir navegador si no estamos en Docker
    if not is_docker:
        def open_browser():
            time.sleep(10)  # Más tiempo para que Streamlit esté completamente listo
            try:
                webbrowser.open("http://localhost:8501")
                print("🌐 Navegador abierto en http://localhost:8501")
            except Exception as e:
                print(f"⚠️ Error abriendo navegador: {e}")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    
    try:
        # Ejecutar Streamlit directamente
        # En Docker, usar modo headless
        is_docker = os.environ.get('DOCKER_CONTAINER', False)
        headless_mode = "true" if is_docker else "false"

        # Por defecto solo escucha en localhost. Para acceder desde otro
        # equipo de tu tailnet, exporta STREAMLIT_SERVER_ADDRESS con tu IP
        # de Tailscale (p.ej. 100.x.x.x) antes de ejecutar este script.
        server_address = os.environ.get("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")

        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app_simple.py",
            "--server.port", "8501",
            "--server.headless", headless_mode,
            "--browser.gatherUsageStats", "false",
            "--server.address", server_address
        ])
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando Streamlit: {e}")
        print("💡 Verifica que todas las dependencias estén instaladas correctamente")
        sys.exit(1)

if __name__ == "__main__":
    main()