#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar dotenv directamente
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def test_dotenv():
    """Prueba la carga de dotenv"""
    print("🔍 Test de dotenv")
    print("=" * 30)
    
    # Ruta del archivo .env
    env_path = Path("src/settings/.env")
    print(f"📁 Ruta: {env_path}")
    print(f"📁 Existe: {'✅ Sí' if env_path.exists() else '❌ No'}")
    
    if env_path.exists():
        print(f"\n📋 Cargando dotenv...")
        result = load_dotenv(env_path)
        print(f"📋 Resultado: {'✅ Éxito' if result else '❌ Fallo'}")
        
        print(f"\n🌍 Variables después de load_dotenv:")
        print(f"   TELEGRAM_API_ID: {os.getenv('TELEGRAM_API_ID', 'No encontrada')}")
        print(f"   TELEGRAM_API_HASH: {os.getenv('TELEGRAM_API_HASH', 'No encontrada')}")
        print(f"   TELEGRAM_PHONE: {os.getenv('TELEGRAM_PHONE', 'No encontrada')}")
        print(f"   TELEGRAM_CHANNEL_ID: {os.getenv('TELEGRAM_CHANNEL_ID', 'No encontrada')}")

if __name__ == "__main__":
    test_dotenv()
