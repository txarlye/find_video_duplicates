#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test para probar la subida de videos específicos a Telegram
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service import TelegramService
from src.settings.settings import settings

def test_video_upload(video_path, video_name):
    """Prueba la subida de un video específico"""
    print(f"\n{'='*60}")
    print(f"🎬 Probando subida: {video_name}")
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
        print(f"   Bot Token: {'✅ Configurado' if settings.get_telegram_bot_token() else '❌ No configurado'}")
        print(f"   Channel ID: {'✅ Configurado' if settings.get_telegram_channel_id() else '❌ No configurado'}")
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
        'title': video_file.stem,
        'year': None,
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
    print(f"   Max file size: {telegram_service.max_file_size} (tipo: {type(telegram_service.max_file_size)})")
    
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

def main():
    """Función principal del script de test"""
    print("🚀 Script de Test para Subida de Videos a Telegram")
    print("=" * 60)
    
    # Videos a probar (rutas absolutas)
    videos_to_test = [
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\Michael_conoce_a_KITT_test.mp4',
            'name': 'Michael_conoce_a_KITT_test.mp4'
        },
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
            'name': 'mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi'
        }
    ]
    
    # Mostrar configuración actual
    print("\n📋 Configuración actual:")
    print(f"   Bot Token: {'✅ Configurado' if settings.get_telegram_bot_token() else '❌ No configurado'}")
    print(f"   Channel ID: {'✅ Configurado' if settings.get_telegram_channel_id() else '❌ No configurado'}")
    
    # Probar cada video
    results = []
    for i, video in enumerate(videos_to_test, 1):
        print(f"\n🎬 Video {i}/{len(videos_to_test)}")
        success = test_video_upload(video['path'], video['name'])
        results.append({
            'name': video['name'],
            'success': success
        })
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE RESULTADOS")
    print(f"{'='*60}")
    
    success_count = 0
    for result in results:
        status = "✅ ÉXITO" if result['success'] else "❌ FALLO"
        print(f"   {status}: {result['name']}")
        if result['success']:
            success_count += 1
    
    print(f"\n📈 Resultados: {success_count}/{len(results)} videos subidos correctamente")
    
    if success_count == len(results):
        print("🎉 ¡Todos los videos se subieron correctamente!")
    elif success_count > 0:
        print("⚠️ Algunos videos se subieron correctamente")
    else:
        print("❌ Ningún video se pudo subir")

if __name__ == "__main__":
    main()
