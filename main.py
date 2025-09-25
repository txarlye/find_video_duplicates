#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Streamlit principal - Detector de Películas Duplicadas
Ejecuta la aplicación Streamlit directamente
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Función principal que ejecuta Streamlit"""
    print("🎬 Iniciando Detector de Películas Duplicadas...")
    print("🌐 Abriendo navegador automáticamente...")
    print()
    
    # Obtener el directorio actual
    current_dir = Path(__file__).parent.absolute()
    
    # Cambiar al directorio del proyecto
    os.chdir(current_dir)
    
    try:
        # Ejecutar streamlit con app.py
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app.py",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Streamlit: {e}")
        print("💡 Asegúrate de que Streamlit esté instalado: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()