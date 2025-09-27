#!/usr/bin/env python3
"""
Script simple para debuggear Telegram
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
    
    return credentials if len(credentials) == 4 else None

async def debug_telegram():
    """Debug de Telegram"""
    creds = get_credentials()
    
    if not creds:
        print("❌ No se pudieron obtener las credenciales")
        return
    
    print(f"🔍 Credenciales encontradas:")
    print(f"   API ID: {creds['TELEGRAM_API_ID']}")
    print(f"   Phone: {creds['TELEGRAM_PHONE']}")
    print(f"   Channel ID: {creds['TELEGRAM_CHANNEL_ID']}")
    
    client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    
    try:
        await client.start(phone=creds['TELEGRAM_PHONE'])
        print("✅ Conectado a Telegram")
        
        # Intentar obtener el canal directamente
        channel_id = creds['TELEGRAM_CHANNEL_ID']
        print(f"\n🔍 Buscando canal con ID: {channel_id}")
        
        try:
            entity = await client.get_entity(channel_id)
            print(f"✅ Canal encontrado: {entity.title}")
            print(f"   ID: {entity.id}")
            print(f"   Tipo: {type(entity).__name__}")
        except Exception as e:
            print(f"❌ Error obteniendo canal: {e}")
            
            # Listar algunos diálogos para ver qué hay disponible
            print(f"\n📋 Listando algunos diálogos disponibles:")
            dialogs = await client.get_dialogs(limit=10)
            
            for dialog in dialogs:
                entity = dialog.entity
                print(f"   📱 {entity.title} (ID: {entity.id})")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_telegram())
