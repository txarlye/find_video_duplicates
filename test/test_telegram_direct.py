#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script directo para subir videos con Telethon
Sin depender del sistema de settings
"""

import sys
from pathlib import Path
import time
import asyncio
from telethon import TelegramClient

# Credenciales directas (sin hardcodear)
def get_credentials():
    """Obtiene las credenciales del archivo .env manualmente"""
    env_path = Path("src/settings/.env")
    credentials = {}
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Filtrar valores de plantilla
                    if value not in ['tu_api_id', 'tu_api_hash', 'tu_telefono', 'tu_channel_id', 'tu_bot_token']:
                        if key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'TELEGRAM_CHANNEL_ID']:
                            credentials[key] = value
    
    print(f"🔍 Credenciales leídas: {credentials}")
    return credentials

async def upload_video_async(video_path: str, video_name: str, video_title: str, video_year: str = None):
    """Sube un video usando Telethon"""
    print(f"\n{'='*60}")
    print(f"🎬 Subiendo: {video_name}")
    print(f"📁 Ruta: {video_path}")
    print(f"{'='*60}")

    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: El archivo no existe: {video_path}")
        return False
    
    file_size = video_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"📊 Tamaño: {size_mb:.2f} MB")

    # Obtener credenciales
    creds = get_credentials()
    
    if not all([creds.get('TELEGRAM_API_ID'), creds.get('TELEGRAM_API_HASH'), creds.get('TELEGRAM_PHONE'), creds.get('TELEGRAM_CHANNEL_ID')]):
        print("❌ Credenciales incompletas")
        return False
    
    # Crear cliente
    client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    
    try:
        # Conectar
        await client.start(phone=creds['TELEGRAM_PHONE'])
        print("✅ Conectado a Telegram")
        
        # Obtener canal
        channel = await client.get_entity(int(creds['TELEGRAM_CHANNEL_ID']))
        
        # Crear mensaje
        message = f"🎬 **{video_title}**"
        if video_year:
            message += f" ({video_year})"
        message += f"\n\n📝 Test de subida: {video_name}"
        message += f"\n💾 **Tamaño:** {size_mb:.2f} MB"
        message += f"\n📁 **Archivo:** {video_file.name}"
        
        # Subir archivo
        print("📤 Subiendo archivo...")
        await client.send_file(
            channel,
            video_path,
            caption=message,
            force_document=True
        )
        
        print("✅ Video subido correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.disconnect()

def upload_video(video_path: str, video_name: str, video_title: str, video_year: str = None):
    """Método síncrono para subir video"""
    return asyncio.run(upload_video_async(video_path, video_name, video_title, video_year))

def main():
    """Función principal"""
    print("🚀 Script Directo de Telethon")
    print("=" * 50)
    
    # Videos a subir
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
        success = upload_video(
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
