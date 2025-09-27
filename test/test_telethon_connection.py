#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para Telethon
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.settings.settings import settings

def test_telethon_config():
    """Verifica la configuración de Telethon"""
    print("🔍 Diagnóstico de Telethon")
    print("=" * 40)
    
    # Verificar configuración
    api_id = settings.get("telegram.api_id")
    api_hash = settings.get("telegram.api_hash")
    phone = settings.get("telegram.phone")
    channel_id = settings.get_telegram_channel_id()
    
    print(f"📋 Configuración actual:")
    print(f"   API ID: {'✅ ' + str(api_id) if api_id else '❌ No configurado'}")
    print(f"   API Hash: {'✅ Configurado' if api_hash else '❌ No configurado'}")
    print(f"   Phone: {'✅ ' + str(phone) if phone else '❌ No configurado'}")
    print(f"   Channel ID: {'✅ ' + str(channel_id) if channel_id else '❌ No configurado'}")
    
    if not all([api_id, api_hash, phone, channel_id]):
        print("\n❌ Configuración incompleta")
        return False
    
    print("\n✅ Configuración completa")
    
    # Probar importación de Telethon
    try:
        from telethon import TelegramClient
        print("✅ Telethon importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Telethon: {e}")
        return False
    
    # Probar conexión básica
    try:
        client = TelegramClient('test_session', api_id, api_hash)
        print("✅ Cliente Telethon creado")
        
        # Intentar conectar
        print("🔍 Probando conexión...")
        # No ejecutamos start() aquí para evitar el SMS
        
        print("✅ Cliente configurado correctamente")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: python test_telegram_telethon.py")
        print("   2. Espera el código SMS (puede tardar 1-2 minutos)")
        print("   3. Introduce el código cuando te lo pida")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        return False

if __name__ == "__main__":
    test_telethon_config()
