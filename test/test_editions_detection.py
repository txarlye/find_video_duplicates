#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la detección de ediciones
"""
import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.Plex.plex_editions_detector import PlexEditionsDetector
from src.settings.settings import settings

def test_editions_detection():
    """Prueba la detección de ediciones"""
    print("🧪 Probando detección de ediciones...")
    
    try:
        # Inicializar detector
        database_path = settings.get_plex_database_path()
        detector = PlexEditionsDetector(database_path)
        
        # Probar detección de ediciones para Scooby-Doo
        print("\n🔍 Probando detección de ediciones para Scooby-Doo...")
        editions = detector.check_existing_editions("Scooby-Doo: Comienza el misterio", "2009")
        
        print(f"📚 Ediciones encontradas: {len(editions)}")
        
        for i, edition in enumerate(editions, 1):
            print(f"  {i}. **{edition['edition']}** ({edition['year']})")
            if edition.get('summary'):
                print(f"     Resumen: {edition['summary'][:100]}...")
        
        # Probar todas las ediciones
        print("\n📖 Probando todas las ediciones...")
        all_editions = detector.get_all_editions_for_movie("Scooby-Doo: Comienza el misterio", "2009")
        
        print(f"📚 Total de ediciones: {len(all_editions)}")
        
        for i, edition in enumerate(all_editions, 1):
            print(f"  {i}. **{edition['edition']}** ({edition['year']})")
            if edition.get('summary'):
                print(f"     Resumen: {edition['summary'][:100]}...")
        
        print("\n🎉 ¡Detección de ediciones verificada!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar conexiones
        try:
            detector.close_connection()
            print("🔒 Conexiones cerradas correctamente")
        except:
            pass

if __name__ == "__main__":
    test_editions_detection()
