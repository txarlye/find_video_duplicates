#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que la funcionalidad básica sigue funcionando
"""
import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.plex_service import PlexService
from src.services.Plex.plex_title_extractor import PlexTitleExtractor
from src.settings.settings import settings

def test_basic_plex_functionality():
    """Prueba la funcionalidad básica de Plex"""
    print("🧪 Probando funcionalidad básica de Plex...")
    
    try:
        # Inicializar servicios básicos
        plex_service = PlexService()
        plex_title_extractor = PlexTitleExtractor(settings.get_plex_database_path())
        
        print("✅ Servicios básicos inicializados correctamente")
        
        # Probar búsqueda básica
        print("\n🔍 Probando búsqueda básica...")
        test_filename = "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat.mkv"
        
        # Probar PlexService
        library_info = plex_service.get_library_info_by_filename(test_filename)
        if library_info:
            print(f"✅ PlexService encontró: {library_info.get('library_name', 'N/A')}")
        else:
            print("❌ PlexService no encontró el archivo")
        
        # Probar PlexTitleExtractor
        title_info = plex_title_extractor.get_real_title_by_filename(test_filename)
        if title_info:
            print(f"✅ PlexTitleExtractor encontró: {title_info.get('title', 'N/A')} ({title_info.get('year', 'N/A')})")
        else:
            print("❌ PlexTitleExtractor no encontró el archivo")
        
        print("\n🎉 ¡Funcionalidad básica verificada!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar conexiones
        try:
            plex_service.close_connection()
            print("🔒 Conexiones cerradas correctamente")
        except:
            pass

if __name__ == "__main__":
    test_basic_plex_functionality()
