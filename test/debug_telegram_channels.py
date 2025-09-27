#!/usr/bin/env python3
"""
Script para debuggear y listar canales de Telegram
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

async def list_channels():
    """Lista todos los canales y chats disponibles"""
    creds = get_credentials()
    
    if not creds:
        print("❌ No se pudieron obtener las credenciales")
        return
    
    client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    
    try:
        await client.start(phone=creds['TELEGRAM_PHONE'])
        print("✅ Conectado a Telegram")
        
        # Obtener todos los diálogos
        dialogs = await client.get_dialogs()
        
        print(f"\n📋 Encontrados {len(dialogs)} diálogos:")
        print("="*60)
        
        for dialog in dialogs:
            entity = dialog.entity
            print(f"📱 {entity.title}")
            print(f"   ID: {entity.id}")
            print(f"   Tipo: {type(entity).__name__}")
            if hasattr(entity, 'username') and entity.username:
                print(f"   Username: @{entity.username}")
            print("-" * 40)
        
        # Buscar específicamente el canal que estamos buscando
        print(f"\n🔍 Buscando canal con ID: {creds['TELEGRAM_CHANNEL_ID']}")
        target_id = int(creds['TELEGRAM_CHANNEL_ID'])
        
        for dialog in dialogs:
            if dialog.entity.id == target_id:
                print(f"✅ ¡Encontrado! {dialog.entity.title}")
                print(f"   ID: {dialog.entity.id}")
                print(f"   Tipo: {type(dialog.entity).__name__}")
                break
        else:
            print("❌ Canal no encontrado en los diálogos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(list_channels())
