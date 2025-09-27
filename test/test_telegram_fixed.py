#!/usr/bin/env python3
"""
Script mejorado para subir videos con Telethon
Maneja caracteres especiales y rutas de red
"""

import os
import sys
import time
import asyncio
import shutil
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Videos a subir
VIDEOS = [
    {
        'path': r'\\DiskStation\data\media\movies\00-borrar\debug\Michael_conoce_a_KITT_test.mp4',
        'name': 'Michael_conoce_a_KITT_test.mp4',
        'title': 'Michael conoce a KITT',
        'year': '2024'
    },
    {
        'path': r'\\DiskStation\data\media\movies\00-borrar\debug\mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
        'name': 'mirindas_asesinas.avi',
        'title': 'Mirindas Asesinas',
        'year': '2024'
    },
    {
        'path': r'\\DiskStation\data\media\movies\00-borrar\debug\el secreto de la piramide(1985).avi',
        'name': 'el_secreto_de_la_piramide_1985.avi',
        'title': 'El Secreto de la Pirámide',
        'year': '1985'
    }
]

def get_credentials():
    """Obtiene las credenciales del archivo .env"""
    env_path = Path("src/settings/.env")
    credentials = {}
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value not in ['tu_api_id', 'tu_api_hash', 'tu_telefono', 'tu_channel_id', 'tu_bot_token']:
                        if key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'TELEGRAM_CHANNEL_ID']:
                            credentials[key] = value
    
    return credentials

def copy_to_temp(video_path, temp_name):
    """Copia el video a una ubicación temporal con nombre limpio"""
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    temp_path = temp_dir / temp_name
    
    print(f"📁 Copiando a temporal: {temp_path}")
    shutil.copy2(video_path, temp_path)
    
    return temp_path

async def upload_video_async(video_path, video_name, video_title, video_year=None):
    """Sube un video usando Telethon con manejo mejorado de errores"""
    print(f"\n{'='*60}")
    print(f"🎬 Subiendo: {video_name}")
    print(f"📁 Ruta: {video_path}")
    print(f"{'='*60}")
    
    # Obtener credenciales
    creds = get_credentials()
    print(f"🔍 Credenciales leídas: {creds}")
    
    if not all(key in creds for key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'TELEGRAM_CHANNEL_ID']):
        print("❌ Credenciales incompletas")
        return False
    
    try:
        # Crear cliente
        client = TelegramClient('session_name', int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
        
        # Conectar
        await client.start(phone=creds['TELEGRAM_PHONE'])
        print("✅ Conectado a Telegram")
        
        # Copiar archivo a temporal con nombre limpio
        temp_path = copy_to_temp(video_path, video_name)
        
        try:
            # Subir archivo
            print("📤 Subiendo archivo...")
            
            # Crear mensaje
            message = f"🎬 **{video_title}**"
            if video_year:
                message += f" ({video_year})"
            
            # Subir como documento (sin límites de tamaño)
            await client.send_file(
                entity=creds['TELEGRAM_CHANNEL_ID'],
                file=temp_path,
                caption=message,
                force_document=True
            )
            
            print("✅ Video subido correctamente")
            return True
            
        finally:
            # Limpiar archivo temporal
            if temp_path.exists():
                temp_path.unlink()
                print("🗑️ Archivo temporal eliminado")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        await client.disconnect()

def upload_video(video_path, video_name, video_title, video_year=None):
    """Wrapper síncrono para upload_video_async"""
    return asyncio.run(upload_video_async(video_path, video_name, video_title, video_year))

def main():
    """Función principal"""
    print("🚀 Script Mejorado de Telethon")
    print("="*50)
    
    results = []
    
    for i, video in enumerate(VIDEOS, 1):
        print(f"\n🎬 Video {i}/{len(VIDEOS)}")
        print("="*60)
        
        # Verificar que el archivo existe
        if not Path(video['path']).exists():
            print(f"❌ Archivo no encontrado: {video['path']}")
            results.append(False)
            continue
        
        # Obtener tamaño del archivo
        file_size = Path(video['path']).stat().st_size
        print(f"📊 Tamaño: {file_size / (1024*1024):.2f} MB")
        
        # Subir video
        success = upload_video(
            video['path'],
            video['name'],
            video['title'],
            video['year']
        )
        
        results.append(success)
        
        if i < len(VIDEOS):
            print("⏳ Esperando 5 segundos...")
            time.sleep(5)
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    for i, (video, success) in enumerate(zip(VIDEOS, results), 1):
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"   {status}: {video['name']}")
    
    success_count = sum(results)
    print(f"📈 Resultados: {success_count}/{len(VIDEOS)} videos subidos correctamente")
    
    # Limpiar directorio temporal
    temp_dir = Path("temp_uploads")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("🗑️ Directorio temporal eliminado")

if __name__ == "__main__":
    main()
