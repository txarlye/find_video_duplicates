#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comprimir archivos grandes antes de subirlos a Telegram
"""

import sys
from pathlib import Path
import time
import zipfile
import os

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service_simple import TelegramServiceSimple

def compress_file(file_path: str, max_size_mb: int = 45) -> str:
    """Comprime un archivo si es necesario"""
    file_obj = Path(file_path)
    if not file_obj.exists():
        return None
    
    file_size = file_obj.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    if size_mb <= max_size_mb:
        print(f"📤 Archivo pequeño ({size_mb:.2f} MB), no necesita compresión")
        return file_path
    
    print(f"📦 Comprimiendo archivo {file_obj.name} ({size_mb:.2f} MB)...")
    
    # Crear archivo comprimido
    compressed_path = file_obj.parent / f"{file_obj.stem}_compressed.zip"
    
    with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(file_path, file_obj.name)
    
    compressed_size = compressed_path.stat().st_size
    compressed_mb = compressed_size / (1024 * 1024)
    
    print(f"✅ Comprimido: {compressed_mb:.2f} MB (reducción: {((size_mb - compressed_mb) / size_mb * 100):.1f}%)")
    
    if compressed_mb <= max_size_mb:
        return str(compressed_path)
    else:
        print(f"❌ Aún demasiado grande ({compressed_mb:.2f} MB > {max_size_mb} MB)")
        # Limpiar archivo comprimido
        compressed_path.unlink()
        return None

def test_video_upload_compress(video_path: str, video_name: str, video_title: str, video_year: str = None) -> bool:
    """Prueba la subida de un video comprimiéndolo si es necesario"""
    print(f"\n{'='*60}")
    print(f"🎬 Probando: {video_name}")
    print(f"📁 Ruta: {video_path}")
    print(f"{'='*60}")

    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: El archivo no existe: {video_path}")
        return False
    
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"📊 Tamaño original: {size_mb:.2f} MB")
    
    # Comprimir si es necesario
    final_path = compress_file(video_path, 45)
    if not final_path:
        print("❌ No se pudo comprimir lo suficiente")
        return False
    
    final_file = Path(final_path)
    final_size = final_file.stat().st_size
    final_mb = final_size / (1024 * 1024)
    
    if final_path != video_path:
        print(f"📦 Usando archivo comprimido: {final_file.name} ({final_mb:.2f} MB)")
    else:
        print(f"📤 Usando archivo original: {final_file.name} ({final_mb:.2f} MB)")
    
    # Crear servicio
    telegram_service = TelegramServiceSimple()
    
    if not telegram_service.is_configured():
        print("❌ Telegram no configurado")
        return False
    
    if not telegram_service.test_connection():
        print("❌ Sin conexión")
        return False
    
    # Crear datos del video
    video_info = {
        'title': video_title,
        'year': video_year,
        'plot': f"Test de subida: {video_name}" + (f" (comprimido de {size_mb:.2f} MB)" if final_path != video_path else ""),
        'poster_url': None
    }
    
    file_info = {
        'archivo': str(final_file),
        'nombre': final_file.name,
        'tamaño': f"{final_mb:.2f} MB"
    }
    
    print("📤 Subiendo archivo...")
    
    try:
        success = telegram_service.upload_movie_to_channel(video_info, file_info, None)
        
        if success:
            print("✅ Archivo subido correctamente")
            return True
        else:
            print("❌ Error en subida")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Limpiar archivo comprimido si se creó
        if final_path != video_path and Path(final_path).exists():
            try:
                Path(final_path).unlink()
                print(f"🗑️ Eliminado archivo temporal: {final_file.name}")
            except:
                pass

def main():
    """Función principal"""
    print("🚀 Script de Subida con Compresión")
    print("=" * 50)
    
    # Videos a probar
    videos_to_test = [
        {
            'path': r'\\DiskStation\data\media\movies\00-borrar\debug\Michael_conoce_a_KITT_test.mp4',
            'name': 'Michael_conoce_a_KITT_test.mp4',
            'title': 'Michael conoce a KITT',
            'year': None
        },
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
    for i, video in enumerate(videos_to_test, 1):
        print(f"\n🎬 Video {i}/{len(videos_to_test)}")
        success = test_video_upload_compress(
            video['path'], 
            video['name'], 
            video['title'], 
            video['year']
        )
        results.append({
            'name': video['name'],
            'success': success
        })
        
        if i < len(videos_to_test):
            print("\n⏳ Esperando 5 segundos...")
            time.sleep(5)
    
    # Resumen
    print(f"\n{'='*60}")
    print("📊 RESUMEN")
    print(f"{'='*60}")
    
    success_count = 0
    for result in results:
        status = "✅ ÉXITO" if result['success'] else "❌ FALLO"
        print(f"   {status}: {result['name']}")
        if result['success']:
            success_count += 1
    
    print(f"\n📈 Resultados: {success_count}/{len(results)} videos subidos correctamente")

if __name__ == "__main__":
    main()
