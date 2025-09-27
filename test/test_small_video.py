#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar solo el video pequeño
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service import TelegramService

def test_small_video():
    """Prueba solo el video pequeño"""
    print("🚀 Test del Video Pequeño")
    print("=" * 40)
    
    video_path = r'\\DiskStation\data\media\movies\00-borrar\debug\Michael_conoce_a_KITT_test.mp4'
    
    print(f"📁 Ruta: {video_path}")
    
    # Verificar archivo
    video_file = Path(video_path)
    if not video_file.exists():
        print("❌ Archivo no encontrado")
        return False
    
    size_mb = video_file.stat().st_size / (1024 * 1024)
    print(f"📊 Tamaño: {size_mb:.2f} MB")
    
    # Crear servicio
    telegram_service = TelegramService()
    
    if not telegram_service.is_configured():
        print("❌ Telegram no configurado")
        return False
    
    print("✅ Telegram configurado")
    
    if not telegram_service.test_connection():
        print("❌ Sin conexión")
        return False
    
    print("✅ Conexión OK")
    
    # Crear datos
    video_info = {
        'title': 'Michael conoce a KITT',
        'year': None,
        'plot': f'Test: {video_file.name}',
        'poster_url': None
    }
    
    file_info = {
        'archivo': str(video_file),
        'nombre': video_file.name,
        'tamaño': f"{size_mb:.2f} MB"
    }
    
    print("📤 Subiendo...")
    
    try:
        success = telegram_service.upload_movie_to_channel(video_info, file_info, None)
        
        if success:
            print("✅ Video subido correctamente")
            return True
        else:
            print("❌ Error en subida")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_small_video()
