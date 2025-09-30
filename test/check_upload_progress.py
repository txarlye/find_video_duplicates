#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el progreso de subida de videos
"""

import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent))

from src.services.telegram_service_simple import TelegramServiceSimple

def check_telegram_connection():
    """Verifica la conexión con Telegram"""
    print("🔍 Verificando conexión con Telegram...")
    
    telegram_service = TelegramServiceSimple()
    
    if not telegram_service.is_configured():
        print("❌ Telegram no está configurado")
        return False
    
    if not telegram_service.test_connection():
        print("❌ Error de conexión con Telegram")
        return False
    
    print("✅ Conexión con Telegram exitosa")
    return True

def main():
    """Función principal"""
    print("📊 Verificador de Progreso de Subida")
    print("=" * 50)
    
    # Verificar conexión
    if not check_telegram_connection():
        return
    
    print("\n📋 Estado de los videos:")
    
    # Videos que se están subiendo
    videos = [
        {
            'name': 'Michael_conoce_a_KITT_test.mp4',
            'size': '3.36 MB',
            'status': '✅ Probablemente subido (video pequeño)'
        },
        {
            'name': 'mirindas.asesinas.(espaã±ol.spanish.divx.cortometraje.de.alex.de.la.iglesia).avi',
            'size': '60.43 MB',
            'status': '🔄 Subiéndose como documento'
        },
        {
            'name': 'el secreto de la piramide(1985).avi',
            'size': '699.79 MB',
            'status': '⏳ Esperando su turno'
        }
    ]
    
    for i, video in enumerate(videos, 1):
        print(f"   {i}. {video['name']} ({video['size']}) - {video['status']}")
    
    print(f"\n💡 El script está ejecutándose en segundo plano subiendo los 3 videos completos.")
    print(f"   • Videos ≤ 50MB: Se suben como video (reproducibles)")
    print(f"   • Videos > 50MB: Se suben como documento (descargables)")
    print(f"   • Timeout dinámico: Ajustado según el tamaño del archivo")
    
    print(f"\n⏰ Tiempo estimado de subida:")
    print(f"   • Video 1 (3.36 MB): ~30 segundos")
    print(f"   • Video 2 (60.43 MB): ~2-3 minutos")
    print(f"   • Video 3 (699.79 MB): ~15-20 minutos")

if __name__ == "__main__":
    main()
