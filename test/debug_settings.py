#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar la configuración
"""

import os
from pathlib import Path

def debug_settings():
    """Diagnostica la configuración"""
    print("🔍 Diagnóstico de Configuración")
    print("=" * 40)
    
    # Verificar archivo .env
    env_path = Path("src/settings/.env")
    print(f"📁 Ruta del .env: {env_path}")
    print(f"📁 Existe: {'✅ Sí' if env_path.exists() else '❌ No'}")
    
    if env_path.exists():
        print(f"\n📋 Contenido del .env:")
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'TELEGRAM' in line:
                    print(f"   Línea {i}: {line.strip()}")
    
    # Verificar variables de entorno
    print(f"\n🌍 Variables de entorno:")
    print(f"   TELEGRAM_API_ID: {os.getenv('TELEGRAM_API_ID', 'No encontrada')}")
    print(f"   TELEGRAM_API_HASH: {os.getenv('TELEGRAM_API_HASH', 'No encontrada')}")
    print(f"   TELEGRAM_PHONE: {os.getenv('TELEGRAM_PHONE', 'No encontrada')}")
    print(f"   TELEGRAM_CHANNEL_ID: {os.getenv('TELEGRAM_CHANNEL_ID', 'No encontrada')}")
    
    # Probar settings
    try:
        from src.settings.settings import settings
        print(f"\n⚙️ Settings:")
        print(f"   API ID: {settings.get('TELEGRAM_API_ID')}")
        print(f"   API Hash: {settings.get('TELEGRAM_API_HASH')}")
        print(f"   Phone: {settings.get('TELEGRAM_PHONE')}")
        print(f"   Channel ID: {settings.get_telegram_channel_id()}")
    except Exception as e:
        print(f"❌ Error cargando settings: {e}")

if __name__ == "__main__":
    debug_settings()
