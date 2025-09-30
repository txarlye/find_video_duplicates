#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar el servidor local en settings
"""

import os
from pathlib import Path

# Actualizar .env con servidor local
env_file = Path('.env')
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Añadir configuración del servidor local
    if 'TELEGRAM_LOCAL_SERVER' not in content:
        content += '\n# Servidor local de Telegram Bot API\n'
        content += 'TELEGRAM_LOCAL_SERVER=http://localhost:8081\n'
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Configuración añadida al .env")
    else:
        print("✅ Configuración ya existe en .env")
else:
    print("❌ Archivo .env no encontrado")
