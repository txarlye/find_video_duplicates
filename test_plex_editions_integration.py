#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para la integración de ediciones de Plex
"""
import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.Plex import PlexEditionsManager
from src.settings.settings import settings

def test_plex_editions_integration():
    """Prueba la integración de ediciones de Plex"""
    print("🧪 Probando integración de ediciones de Plex...")
    
    try:
        # Inicializar el gestor de ediciones
        database_path = settings.get_plex_database_path()
        print(f"📁 Base de datos: {database_path}")
        
        editions_manager = PlexEditionsManager(database_path)
        print("✅ PlexEditionsManager inicializado correctamente")
        
        # Probar detección de ediciones existentes
        print("\n🔍 Probando detección de ediciones...")
        existing_editions = editions_manager.detector.check_existing_editions("Scooby-Doo: Comienza el misterio", "2009")
        print(f"📚 Ediciones encontradas: {len(existing_editions)}")
        
        for edition in existing_editions:
            print(f"  • {edition['edition']} ({edition['year']})")
        
        # Probar sugerencias de edición
        print("\n💡 Probando sugerencias de edición...")
        suggestions = editions_manager.get_edition_suggestions_for_movie("Scooby-Doo: Comienza el misterio")
        print(f"🎬 Sugerencias: {suggestions[:3]}...")
        
        # Probar validación de nombres
        print("\n✅ Probando validación de nombres...")
        valid_names = ["Director's Cut", "Edición Especial", "4K Edition"]
        invalid_names = ["<Invalid>", "Test|Name", "File/Name"]
        
        for name in valid_names:
            is_valid = editions_manager.creator.validate_edition_name(name)
            print(f"  '{name}': {'✅ Válido' if is_valid else '❌ Inválido'}")
        
        for name in invalid_names:
            is_valid = editions_manager.creator.validate_edition_name(name)
            print(f"  '{name}': {'✅ Válido' if is_valid else '❌ Inválido'}")
        
        print("\n🎉 ¡Integración de ediciones funcionando correctamente!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar conexiones
        try:
            editions_manager.close_connections()
            print("🔒 Conexiones cerradas correctamente")
        except:
            pass

if __name__ == "__main__":
    test_plex_editions_integration()
