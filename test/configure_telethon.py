#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar Telethon
Basado en Stack Overflow: https://stackoverflow.com/questions/76383605/how-do-i-upload-large-files-to-telegram-in-python
"""

import os
from pathlib import Path

def configure_telethon():
    """Configura las credenciales de Telethon"""
    print("🔧 Configurador de Telethon")
    print("Basado en Stack Overflow para archivos hasta 1.5GB")
    print("=" * 60)
    
    print("\n📋 Para obtener las credenciales de Telegram:")
    print("   1. Ve a: https://my.telegram.org/apps")
    print("   2. Inicia sesión con tu número de teléfono")
    print("   3. Crea una nueva aplicación")
    print("   4. Copia el API ID y API Hash")
    
    print("\n📝 Configuración necesaria:")
    print("   - API ID: Número de tu aplicación")
    print("   - API Hash: Hash de tu aplicación")
    print("   - Phone: Tu número de teléfono (con código de país)")
    print("   - Channel ID: ID del canal donde subir archivos")
    
    # Verificar archivo .env
    env_file = Path('.env')
    if not env_file.exists():
        print("\n❌ Archivo .env no encontrado")
        print("📝 Necesitas crear un archivo .env con tus credenciales")
        return
    else:
        print("\n✅ Archivo .env encontrado")
        
        # Verificar configuración existente
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'TELEGRAM_API_ID' not in content:
            print("📝 Añadiendo configuración de Telethon al .env...")
            
            telethon_config = """
# Configuración de Telethon (Cliente de Usuario)
TELEGRAM_API_ID=tu_api_id
TELEGRAM_API_HASH=tu_api_hash
TELEGRAM_PHONE=tu_telefono
"""
            
            with open('.env', 'a', encoding='utf-8') as f:
                f.write(telethon_config)
            
            print("✅ Configuración de Telethon añadida al .env")
        else:
            print("✅ Configuración de Telethon ya existe en .env")
    
    print("\n📋 Próximos pasos:")
    print("   1. Edita el archivo .env con tus credenciales")
    print("   2. Ejecuta: python test_telegram_telethon.py")
    print("   3. En la primera ejecución, recibirás un código SMS")
    print("   4. Introduce el código para autenticarte")
    
    print("\n💡 Ventajas de Telethon:")
    print("   ✅ Soporta archivos hasta 1.5GB")
    print("   ✅ No requiere servidor local")
    print("   ✅ Usa tu cuenta personal de Telegram")
    print("   ✅ Más estable para archivos grandes")

if __name__ == "__main__":
    configure_telethon()
