#!/usr/bin/env python3
"""
Script para diagnosticar la configuración de Telegram
"""

import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.settings.settings import settings

def main():
    print("🔍 Diagnóstico de Configuración de Telegram")
    print("=" * 50)
    
    # Verificar archivo .env
    env_path = Path("src/settings/.env")
    print(f"📁 Archivo .env: {env_path}")
    print(f"   Existe: {env_path.exists()}")
    
    if env_path.exists():
        print(f"   Tamaño: {env_path.stat().st_size} bytes")
    
    print("\n🔑 Credenciales leídas:")
    print(f"   TELEGRAM_API_ID: {settings.get('TELEGRAM_API_ID')}")
    print(f"   TELEGRAM_API_HASH: {settings.get('TELEGRAM_API_HASH')}")
    print(f"   TELEGRAM_PHONE: {settings.get('TELEGRAM_PHONE')}")
    print(f"   TELEGRAM_CHANNEL_ID: {settings.get('TELEGRAM_CHANNEL_ID')}")
    print(f"   TELEGRAM_BOT_TOKEN: {settings.get('TELEGRAM_BOT_TOKEN')}")
    
    print("\n🧪 Pruebas de configuración:")
    
    # Probar Telethon
    from src.services.Telegram.telegram_telethon_service import TelegramTelethonService
    telethon_service = TelegramTelethonService()
    print(f"   Telethon configurado: {telethon_service.is_configured()}")
    
    # Probar Bot
    from src.services.Telegram.telegram_bot_service import TelegramBotService
    bot_service = TelegramBotService()
    print(f"   Bot configurado: {bot_service.is_configured()}")
    
    # Probar Manager
    from src.services.Telegram.telegram_manager import TelegramManager
    manager = TelegramManager()
    print(f"   Manager configurado: {manager.telethon_service.is_configured() or manager.bot_service.is_configured()}")
    
    # Probar servicio principal
    from src.services.telegram_service import TelegramService
    telegram_service = TelegramService()
    print(f"   Servicio principal configurado: {telegram_service.is_configured()}")

if __name__ == "__main__":
    main()
