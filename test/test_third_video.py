#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test para probar la subida del tercer video específico
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service import TelegramService
from src.settings.settings import settings

def test_third_video():
    """Prueba la subida del tercer video específico"""
    print("🚀 Test del Tercer Video - El Secreto de la Pirámide")
    print("=" * 60)
    
    # Video a probar
    video_path = r'\\DiskStation\data\media\movies\00-borrar\debug\el secreto de la piramide(1985).avi'
    video_name = 'el secreto de la piramide(1985).avi'
    
    print(f"🎬 Probando subida: {video_name}")
    print(f"📁 Ruta: {video_path}")
    
    # Verificar que el archivo existe
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: El archivo no existe: {video_path}")
        return False
    
    # Obtener información del archivo
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"📊 Tamaño: {size_mb:.2f} MB")
    print(f"📊 Tamaño en bytes: {file_size:,} bytes")
    
    # Verificar límites de Telegram
    max_size_mb = 2000  # 2GB
    if size_mb > max_size_mb:
        print(f"❌ Error: Archivo demasiado grande ({size_mb:.2f} MB). Límite: {max_size_mb} MB")
        return False
    
    # Crear servicio de Telegram
    telegram_service = TelegramService()
    
    # Verificar configuración
    if not telegram_service.is_configured():
        print("❌ Error: Telegram no está configurado")
        return False
    
    print("✅ Telegram configurado correctamente")
    
    # Probar conexión
    print("🔍 Probando conexión con Telegram...")
    if not telegram_service.test_connection():
        print("❌ Error: No se puede conectar con Telegram")
        return False
    
    print("✅ Conexión con Telegram exitosa")
    
    # Crear información del video
    video_info = {
        'title': 'El Secreto de la Pirámide',
        'year': '1985',
        'plot': f"Test de subida: {video_file.name}",
        'poster_url': None
    }
    
    # Crear información del archivo en el formato esperado
    file_info = {
        'archivo': str(video_file),
        'nombre': video_file.name,
        'tamaño': f"{size_mb:.2f} MB"
    }
    
    print("📤 Intentando subir video...")
    print(f"   Video info: {video_info}")
    print(f"   File info: {file_info}")
    
    try:
        success = telegram_service.upload_movie_to_channel(
            video_info, 
            file_info, 
            None  # Sin póster
        )
        
        if success:
            print("✅ Video subido correctamente")
            return True
        else:
            print("❌ Error en la subida")
            return False
            
    except Exception as e:
        print(f"❌ Excepción durante la subida: {e}")
        return False

if __name__ == "__main__":
    test_third_video()
