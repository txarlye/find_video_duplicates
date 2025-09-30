#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de instalación automática de dependencias
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def install_requirements(requirements_file="requirements.txt"):
    """Instala las dependencias desde requirements.txt"""
    if not Path(requirements_file).exists():
        print(f"❌ Archivo {requirements_file} no encontrado")
        return False
    
    print(f"📦 Instalando dependencias desde {requirements_file}...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], check=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def verify_installation():
    """Verifica que las dependencias principales estén instaladas"""
    print("🔍 Verificando instalación...")
    
    required_modules = [
        "streamlit",
        "pandas", 
        "requests",
        "dotenv"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Módulos faltantes: {', '.join(missing_modules)}")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def create_virtual_env():
    """Crea un entorno virtual"""
    print("🐍 Creando entorno virtual...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Entorno virtual creado en 'venv'")
        
        # Determinar el script de activación según el SO
        if os.name == 'nt':  # Windows
            activate_script = "venv\\Scripts\\activate"
        else:  # Linux/Mac
            activate_script = "venv/bin/activate"
        
        print(f"💡 Para activar el entorno virtual:")
        print(f"   {activate_script}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando entorno virtual: {e}")
        return False

def main():
    """Función principal"""
    print("🎬 Instalador de Dependencias - Detector de Películas Duplicadas")
    print("=" * 60)
    
    # Verificar Python
    if not check_python_version():
        input("Presiona Enter para salir...")
        return
    
    # Preguntar si crear entorno virtual
    print("\n¿Deseas crear un entorno virtual? (recomendado)")
    print("1. Sí, crear entorno virtual")
    print("2. No, instalar en el sistema")
    
    choice = input("Selecciona (1/2): ").strip()
    
    if choice == "1":
        if create_virtual_env():
            print("\n⚠️  IMPORTANTE: Activa el entorno virtual antes de continuar")
            print("   Windows: venv\\Scripts\\activate")
            print("   Linux/Mac: source venv/bin/activate")
            input("Presiona Enter después de activar el entorno virtual...")
    
    # Instalar dependencias (solo tenemos un archivo de dependencias)
    print("\n📦 Instalando dependencias...")
    requirements_file = "requirements.txt"
    
    # Instalar dependencias
    if install_requirements(requirements_file):
        # Verificar instalación
        if verify_installation():
            print("\n🎉 ¡Instalación completada exitosamente!")
            print("💡 Ahora puedes ejecutar la aplicación con:")
            print("   python main.py")
            print("\n📋 CONFIGURACIÓN ADICIONAL REQUERIDA:")
            print("   - Configura las variables de entorno en .env")
            print("   - Configura Telegram Bot y Canal")
            print("   - Configura APIs de IMDB/TMDB/OMDb")
            print("   - Configura ruta de base de datos Plex")
            print("\n📖 Ver README.md para instrucciones detalladas")
        else:
            print("\n⚠️  Instalación completada con advertencias")
    else:
        print("\n❌ Error en la instalación")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
