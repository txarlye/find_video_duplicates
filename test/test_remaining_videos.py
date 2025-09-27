#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para subir los videos restantes (2º y 3º)
"""

import sys
import os
from pathlib import Path
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service import TelegramService
from src.settings.settings import settings

def upload_single_video(video_path, video_name, video_title=None, video_year=None):
    """Sube un video individual"""
    print(f"\n{'='*60}")
    print(f"🎬 Subiendo: {video_name}")
    print(f"📁 Ruta: {video_path}")
    print(f"{'='*60}")
    
    # Verificar que el archivo existe
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: El archivo no existe: {video_path}")
        return False
    
    # Obtener información del archivo
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"📊 Tamaño: {size_mb:.2f} MB")
    
    # Crear servicio de Telegram
    telegram_service = TelegramService()
    
    if not telegram_service.is_configured():
        print("❌ Error: Telegram no está configurado")
        return False
    
    print("✅ Telegram configurado correctamente")
    
    # Probar conexión
    if not telegram_service.test_connection():
        print("❌ Error: No se puede conectar con Telegram")
        return False
    
    print("✅ Conexión con Telegram exitosa")
    
    # Crear información del video
    video_info = {
        'title': video_title or video_file.stem,
        'year': video_year,
        'plot': f"Subida: {video_file.name}",
        'poster_url': None
    }
    
    # Crear información del archivo
    file_info = {
        'archivo': str(video_file),
        'nombre': video_file.name,
        'tamaño': f"{size_mb:.2f} MB"
    }
    
    print("📤 Subiendo video...")
    
    try:
        success = telegram_service.upload_movie_to_channel(
            video_info, 
            file_info, 
            None
        )
        
        if success:
            print("✅ Video subido correctamente")
            return True
        else:
            print("❌ Error en la subida")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Subida de Videos Restantes")
    print("=" * 60)
    
    # Videos restantes
    videos = [
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
            'name': 'mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
            'title': 'Mirindas Asesinas',
            'year': None
        },
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\el secreto de la piramide(1985).avi',
            'name': 'el secreto de la piramide(1985).avi',
            'title': 'El Secreto de la Pirámide',
            'year': '1985'
        }
    ]
    
    results = []
    
    for i, video in enumerate(videos, 1):
        print(f"\n🎬 Video {i}/{len(videos)}")
        success = upload_single_video(
            video['path'], 
            video['name'], 
            video['title'], 
            video['year']
        )
        results.append(success)
        
        if i < len(videos):
            print(f"\n⏳ Esperando 3 segundos...")
            time.sleep(3)
    
    # Resumen
    success_count = sum(results)
    print(f"\n{'='*60}")
    print("📊 RESUMEN")
    print(f"{'='*60}")
    print(f"✅ Videos subidos: {success_count}/{len(videos)}")
    
    if success_count == len(videos):
        print("🎉 ¡Todos los videos se subieron correctamente!")
    else:
        print("⚠️ Algunos videos no se pudieron subir")

if __name__ == "__main__":
    main()
