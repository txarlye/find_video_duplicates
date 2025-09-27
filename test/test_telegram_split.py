#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para subir archivos grandes dividiéndolos en partes
"""

import sys
from pathlib import Path
import time
import os

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service_simple import TelegramServiceSimple

def split_file(file_path: str, max_size_mb: int = 45) -> list:
    """Divide un archivo en partes más pequeñas"""
    file_obj = Path(file_path)
    if not file_obj.exists():
        return []
    
    file_size = file_obj.stat().st_size
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size <= max_size_bytes:
        return [file_path]  # No necesita división
    
    print(f"📦 Dividiendo archivo {file_obj.name} ({file_size / (1024*1024):.2f} MB) en partes de {max_size_mb} MB...")
    
    parts = []
    part_num = 1
    
    with open(file_path, 'rb') as original_file:
        while True:
            chunk = original_file.read(max_size_bytes)
            if not chunk:
                break
            
            part_filename = f"{file_obj.stem}_part{part_num:02d}{file_obj.suffix}"
            part_path = file_obj.parent / part_filename
            
            with open(part_path, 'wb') as part_file:
                part_file.write(chunk)
            
            parts.append(str(part_path))
            print(f"   ✅ Parte {part_num}: {part_filename} ({len(chunk) / (1024*1024):.2f} MB)")
            part_num += 1
    
    return parts

def upload_file_parts(parts: list, video_info: dict, file_info: dict) -> bool:
    """Sube las partes de un archivo"""
    telegram_service = TelegramServiceSimple()
    
    if not telegram_service.is_configured():
        print("❌ Telegram no configurado")
        return False
    
    if not telegram_service.test_connection():
        print("❌ Sin conexión")
        return False
    
    success_count = 0
    
    for i, part_path in enumerate(parts, 1):
        print(f"\\n📤 Subiendo parte {i}/{len(parts)}: {Path(part_path).name}")
        
        # Crear info para esta parte
        part_file_info = file_info.copy()
        part_file_info['archivo'] = part_path
        part_file_info['nombre'] = Path(part_path).name
        
        # Añadir información de parte al mensaje
        part_video_info = video_info.copy()
        part_video_info['plot'] = f"{video_info.get('plot', '')}\\n\\n📦 Parte {i}/{len(parts)} de {file_info.get('nombre', '')}"
        
        try:
            success = telegram_service.upload_movie_to_channel(part_video_info, part_file_info, None)
            if success:
                print(f"✅ Parte {i} subida correctamente")
                success_count += 1
            else:
                print(f"❌ Error subiendo parte {i}")
        except Exception as e:
            print(f"❌ Error en parte {i}: {e}")
        
        # Pausa entre partes
        if i < len(parts):
            print("⏳ Esperando 3 segundos...")
            time.sleep(3)
    
    # Limpiar archivos temporales
    for part_path in parts:
        try:
            os.remove(part_path)
            print(f"🗑️ Eliminado: {Path(part_path).name}")
        except:
            pass
    
    return success_count == len(parts)

def test_video_upload_split(video_path: str, video_name: str, video_title: str, video_year: str = None) -> bool:
    """Prueba la subida de un video dividiéndolo si es necesario"""
    print(f"\\n{'='*60}")
    print(f"🎬 Probando: {video_name}")
    print(f"📁 Ruta: {video_path}")
    print(f"{'='*60}")

    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: El archivo no existe: {video_path}")
        return False
    
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"📊 Tamaño: {size_mb:.2f} MB")
    
    # Crear datos del video
    video_info = {
        'title': video_title,
        'year': video_year,
        'plot': f"Test de subida: {video_name}",
        'poster_url': None
    }
    
    file_info = {
        'archivo': str(video_file),
        'nombre': video_file.name,
        'tamaño': f"{size_mb:.2f} MB"
    }
    
    # Verificar si necesita división
    if size_mb <= 45:
        print("📤 Archivo pequeño, subiendo directamente...")
        telegram_service = TelegramServiceSimple()
        return telegram_service.upload_movie_to_channel(video_info, file_info, None)
    else:
        print("📦 Archivo grande, dividiendo en partes...")
        parts = split_file(video_path, 45)
        return upload_file_parts(parts, video_info, file_info)

def main():
    """Función principal"""
    print("🚀 Script de Subida con División de Archivos")
    print("=" * 60)
    
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
        print(f"\\n🎬 Video {i}/{len(videos_to_test)}")
        success = test_video_upload_split(
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
            print("\\n⏳ Esperando 5 segundos...")
            time.sleep(5)
    
    # Resumen
    print(f"\\n{'='*60}")
    print("📊 RESUMEN")
    print(f"{'='*60}")
    
    success_count = 0
    for result in results:
        status = "✅ ÉXITO" if result['success'] else "❌ FALLO"
        print(f"   {status}: {result['name']}")
        if result['success']:
            success_count += 1
    
    print(f"\\n📈 Resultados: {success_count}/{len(results)} videos subidos correctamente")

if __name__ == "__main__":
    main()
