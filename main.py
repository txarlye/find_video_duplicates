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
    print("🌐 Abriendo navegador automáticamente...")
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
    
    # Abrir navegador después de un delay (solo una vez)
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
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app_simple.py",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()