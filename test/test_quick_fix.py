#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script rápido para probar la corrección del límite de 20MB
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service_simple import TelegramServiceSimple

def test_video_upload(video_path: str, video_name: str, video_title: str) -> bool:
    """Prueba la subida de un video"""
    print(f"\n🎬 Probando: {video_name}")
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Archivo no encontrado: {video_path}")
        return False
    
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"📊 Tamaño: {size_mb:.2f} MB")
    
    # Verificar límite
    max_video_size = 20 * 1024 * 1024  # 20MB
    if file_size > max_video_size:
        print(f"📋 Archivo grande ({size_mb:.2f} MB > 20 MB), se enviará como documento")
    else:
        print(f"📋 Archivo pequeño ({size_mb:.2f} MB ≤ 20 MB), se enviará como video")
    
    # Crear servicio
    telegram_service = TelegramServiceSimple()
    
    if not telegram_service.is_configured():
        print("❌ Telegram no configurado")
        return False
    
    if not telegram_service.test_connection():
        print("❌ Sin conexión")
        return False
    
    # Crear datos
    video_info = {
        'title': video_title,
        'year': None,
        'plot': f"Test: {video_name}",
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

def main():
    """Función principal"""
    print("🚀 Test Rápido - Corrección de Límite 20MB")
    print("=" * 50)
    
    # Solo probar el video de 60MB que falló
    video = {
        'path': r'\\DiskStation\data\media\movies\00-borrar\debug\mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
        'name': 'mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
        'title': 'Mirindas Asesinas'
    }
    
    success = test_video_upload(video['path'], video['name'], video['title'])
    
    if success:
        print("\n🎉 ¡El video se subió correctamente como documento!")
    else:
        print("\n❌ El video falló")

if __name__ == "__main__":
    main()
