#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar las credenciales de Telethon
"""

import os
from pathlib import Path

def setup_telethon_credentials():
    """Configura las credenciales de Telethon"""
    print("🔧 Configurador de Credenciales de Telethon")
    print("=" * 50)
    
    # Credenciales que me proporcionaste
    api_id = "REDACTED_TELEGRAM_API_ID"
    api_hash = "REDACTED_TELEGRAM_API_HASH"
    phone = "REDACTED_PHONE"
    
    print(f"📋 Credenciales detectadas:")
    print(f"   API ID: {api_id}")
    print(f"   API Hash: {api_hash}")
    print(f"   Phone: {phone}")
    
    # Verificar si existe .env
    env_file = Path('.env')
    if env_file.exists():
        print(f"\n✅ Archivo .env encontrado")
        
        # Leer contenido actual
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene configuración de Telethon
        if 'TELEGRAM_API_ID' in content:
            print("✅ Configuración de Telethon ya existe en .env")
        else:
            print("📝 Añadiendo configuración de Telethon al .env...")
            
            telethon_config = f"""
# Configuración de Telethon (Cliente de Usuario)
TELEGRAM_API_ID={api_id}
TELEGRAM_API_HASH={api_hash}
TELEGRAM_PHONE={phone}
"""
            
            with open('.env', 'a', encoding='utf-8') as f:
                f.write(telethon_config)
            
            print("✅ Configuración de Telethon añadida al .env")
    else:
        print(f"\n❌ Archivo .env no encontrado")
        print("📝 Necesitas crear un archivo .env con el siguiente contenido:")
        print(f"""
# Configuración de Telegram Bot API
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHANNEL_ID=tu_channel_id

# Configuración de Telethon (Cliente de Usuario)
TELEGRAM_API_ID={api_id}
TELEGRAM_API_HASH={api_hash}
TELEGRAM_PHONE={phone}
""")
    
    print(f"\n📋 Próximos pasos:")
    print(f"   1. Verifica que tu .env tenga las credenciales correctas")
    print(f"   2. Ejecuta: python test_telegram_telethon.py")
    print(f"   3. En la primera ejecución recibirás un código SMS")
    print(f"   4. Introduce el código para autenticarte")
    
    print(f"\n💡 Ventajas de Telethon:")
    print(f"   ✅ Soporta archivos hasta 1.5GB")
    print(f"   ✅ No requiere servidor local")
    print(f"   ✅ Usa tu cuenta personal de Telegram")

if __name__ == "__main__":
    setup_telethon_credentials()
