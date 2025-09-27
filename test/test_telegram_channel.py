#!/usr/bin/env python3
"""
Script para probar diferentes formas de acceder al canal
"""

import asyncio
from telethon import TelegramClient
from pathlib import Path

def get_credentials():
    """Obtiene las credenciales del archivo .env"""
    env_path = Path("src/settings/.env")
    credentials = {}
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value not in ['tu_api_id', 'tu_api_hash', 'tu_telefono', 'tu_channel_id', 'tu_bot_token']:
                        if key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'TELEGRAM_CHANNEL_ID']:
                            credentials[key] = value
    
    return credentials

async def test_channel_access():
    """Prueba diferentes formas de acceder al canal"""
    creds = get_credentials()
    
    if not all(key in creds for key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE']):
        print("❌ Credenciales incompletas")
        return
    
    client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    
    try:
        await client.start(phone=creds['TELEGRAM_PHONE'])
        print("✅ Conectado a Telegram")
        
        # Probar diferentes formas de acceder al canal
        channel_id = creds.get('TELEGRAM_CHANNEL_ID', '')
        
        print(f"\n🔍 Probando acceso al canal: {channel_id}")
        
        # Método 1: Por ID
        try:
            entity = await client.get_entity(channel_id)
            print(f"✅ Canal encontrado por ID: {entity.title}")
            print(f"   ID: {entity.id}")
            print(f"   Username: @{entity.username}" if entity.username else "   Sin username")
            return entity
        except Exception as e:
            print(f"❌ Error accediendo por ID: {e}")
        
        # Método 2: Por username (si tienes el nombre del canal)
        # Reemplaza 'tu_canal' con el nombre real de tu canal
        channel_username = input("\n📝 ¿Cuál es el nombre de tu canal? (ej: @mi_canal o mi_canal): ").strip()
        if channel_username:
            try:
                entity = await client.get_entity(channel_username)
                print(f"✅ Canal encontrado por username: {entity.title}")
                print(f"   ID: {entity.id}")
                print(f"   Username: @{entity.username}" if entity.username else "   Sin username")
                return entity
            except Exception as e:
                print(f"❌ Error accediendo por username: {e}")
        
        # Método 3: Listar todos los canales/grupos
        print("\n📋 Listando tus canales y grupos:")
        async for dialog in client.iter_dialogs():
            if dialog.is_channel or dialog.is_group:
                print(f"   📺 {dialog.name} (ID: {dialog.id})")
                if dialog.username:
                    print(f"      Username: @{dialog.username}")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_channel_access())
