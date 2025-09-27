#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar videos grandes como documentos
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service import TelegramService

def test_large_video(video_path, video_name):
    """Prueba un video grande como documento"""
    print(f"\n🎬 Probando: {video_name}")
    print(f"📁 Ruta: {video_path}")
    
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
        'title': video_file.stem,
        'year': None,
        'plot': f'Test como documento: {video_file.name}',
        'poster_url': None
    }
    
    file_info = {
        'archivo': str(video_file),
        'nombre': video_file.name,
        'tamaño': f"{size_mb:.2f} MB"
    }
    
    print("📤 Subiendo como documento...")
    
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

def main():
    """Función principal"""
    print("🚀 Test de Videos Grandes como Documentos")
    print("=" * 50)
    
    # Videos grandes
    videos = [
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
            'name': 'Mirindas Asesinas (60MB)'
        },
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\el secreto de la piramide(1985).avi',
            'name': 'El Secreto de la Pirámide (700MB)'
        }
    ]
    
    results = []
    
    for video in videos:
        success = test_large_video(video['path'], video['name'])
        results.append(success)
    
    # Resumen
    success_count = sum(results)
    print(f"\n{'='*50}")
    print("📊 RESUMEN")
    print(f"{'='*50}")
    print(f"✅ Videos subidos: {success_count}/{len(videos)}")
    
    if success_count == len(videos):
        print("🎉 ¡Todos los videos se subieron correctamente!")
    else:
        print("⚠️ Algunos videos no se pudieron subir")

if __name__ == "__main__":
    main()
