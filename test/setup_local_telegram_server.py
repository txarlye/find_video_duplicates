#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar servidor local de Telegram Bot API
Basado en Tanpachiro-bot para soportar archivos hasta 2GB
"""

import os
import subprocess
import sys
from pathlib import Path

def check_docker():
    """Verifica si Docker está instalado"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker encontrado:", result.stdout.strip())
            return True
        else:
            print("❌ Docker no encontrado")
            return False
    except FileNotFoundError:
        print("❌ Docker no está instalado")
        return False

def setup_telegram_server():
    """Configura el servidor local de Telegram Bot API"""
    print("🚀 Configurando Servidor Local de Telegram Bot API")
    print("=" * 60)
    
    # Verificar Docker
    if not check_docker():
        print("\n📋 Para instalar Docker:")
        print("   1. Ve a: https://www.docker.com/products/docker-desktop")
        print("   2. Descarga e instala Docker Desktop")
        print("   3. Reinicia el sistema")
        return False
    
    # Obtener token del bot
    from src.settings.settings import settings
    bot_token = settings.get_telegram_bot_token()
    
    if not bot_token:
        print("❌ Bot token no configurado")
        return False
    
    print(f"✅ Bot token encontrado: {bot_token[:10]}...")
    
    # Crear docker-compose.yml
    docker_compose_content = f"""version: '3.8'
services:
  telegram-bot-api:
    image: aiogram/telegram-bot-api:latest
    container_name: telegram-bot-api
    ports:
      - "8081:8081"
    environment:
      - TELEGRAM_API_ID=your_api_id
      - TELEGRAM_API_HASH=your_api_hash
    command: 
      - "--local"
      - "--http-port=8081"
      - "--http-ip=0.0.0.0"
      - "--log-level=info"
    volumes:
      - ./telegram_data:/var/lib/telegram-bot-api
    restart: unless-stopped
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)
    
    print("✅ Archivo docker-compose.yml creado")
    
    # Crear script de inicio
    start_script = f"""#!/bin/bash
echo "🚀 Iniciando Servidor Local de Telegram Bot API"
echo "📡 Puerto: 8081"
echo "🔗 URL: http://localhost:8081"
echo ""

# Iniciar contenedor
docker-compose up -d

echo "✅ Servidor iniciado"
echo "📋 Para ver logs: docker-compose logs -f"
echo "🛑 Para detener: docker-compose down"
"""
    
    with open('start_telegram_server.sh', 'w') as f:
        f.write(start_script)
    
    # Hacer ejecutable en sistemas Unix
    if os.name != 'nt':
        os.chmod('start_telegram_server.sh', 0o755)
    
    print("✅ Script de inicio creado: start_telegram_server.sh")
    
    # Crear script de configuración
    config_script = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Script para configurar el servidor local en settings
\"\"\"

import os
from pathlib import Path

# Actualizar .env con servidor local
env_file = Path('.env')
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Añadir configuración del servidor local
    if 'TELEGRAM_LOCAL_SERVER' not in content:
        content += '\\n# Servidor local de Telegram Bot API\\n'
        content += 'TELEGRAM_LOCAL_SERVER=http://localhost:8081\\n'
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Configuración añadida al .env")
    else:
        print("✅ Configuración ya existe en .env")
else:
    print("❌ Archivo .env no encontrado")
"""
    
    with open('configure_local_server.py', 'w') as f:
        f.write(config_script)
    
    print("✅ Script de configuración creado: configure_local_server.py")
    
    print("\\n📋 Próximos pasos:")
    print("   1. Ejecutar: python configure_local_server.py")
    print("   2. Ejecutar: ./start_telegram_server.sh (o start_telegram_server.bat en Windows)")
    print("   3. Esperar a que el servidor esté listo")
    print("   4. Ejecutar: python test_telegram_local.py")
    
    return True

def main():
    """Función principal"""
    print("🔧 Configurador de Servidor Local de Telegram Bot API")
    print("Basado en Tanpachiro-bot para archivos hasta 2GB")
    print("=" * 60)
    
    if setup_telegram_server():
        print("\\n🎉 ¡Configuración completada!")
        print("📖 Documentación: https://github.com/tdlib/telegram-bot-api")
    else:
        print("\\n❌ Configuración falló")

if __name__ == "__main__":
    main()
