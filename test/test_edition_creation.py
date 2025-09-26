#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para la creación de ediciones
"""
import sys
import os
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.Plex.plex_edition_creator import PlexEditionCreator

def test_edition_creation():
    """Prueba la creación de ediciones"""
    print("🧪 Probando creación de ediciones...")
    
    try:
        creator = PlexEditionCreator()
        
        # Probar validación de nombres
        print("\n✅ Probando validación de nombres:")
        test_names = [
            "Edición de Prueba",
            "Director's Cut",
            "Edición Especial",
            "<Invalid>",
            "Test|Name",
            "File/Name"
        ]
        
        for name in test_names:
            is_valid = creator.validate_edition_name(name)
            print(f"  '{name}': {'✅ Válido' if is_valid else '❌ Inválido'}")
        
        # Probar limpieza de nombres
        print("\n🧹 Probando limpieza de nombres:")
        test_editions = [
            "Edición de Prueba",
            "Director's Cut",
            "Edición <Especial>",
            "Test|Name",
            "File/Name"
        ]
        
        for edition in test_editions:
            clean_name = creator._clean_edition_name(edition)
            print(f"  '{edition}' → '{clean_name}'")
        
        # Probar limpieza de nombres de archivo
        print("\n📁 Probando limpieza de nombres de archivo:")
        test_filenames = [
            "Scooby_Doo_3_Comienza_el_misterio_2009.mkv",
            "Test<File>.mkv",
            "File|Name.mkv",
            "Very/Long/Path/Name.mkv"
        ]
        
        for filename in test_filenames:
            clean_name = creator._clean_filename(filename)
            print(f"  '{filename}' → '{clean_name}'")
        
        print("\n🎉 ¡Pruebas de creación de ediciones completadas!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_edition_creation()
