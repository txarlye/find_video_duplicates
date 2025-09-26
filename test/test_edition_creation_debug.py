#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba específico para debuggear la creación de ediciones
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_edition_creation():
    """Prueba la creación de ediciones paso a paso"""
    print("🧪 Probando creación de ediciones...")
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        # Crear creador de ediciones
        creator = PlexEditionCreator()
        
        # Crear archivo de prueba
        test_file = "test_movie.mkv"
        test_path = os.path.join(os.getcwd(), test_file)
        
        # Crear archivo de prueba
        with open(test_path, 'w') as f:
            f.write("test content")
        
        print(f"📁 Archivo de prueba creado: {test_path}")
        
        # Probar creación de edición
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        
        print(f"🎬 Película: {movie_title}")
        print(f"📚 Edición: {edition_name}")
        
        # Crear edición
        new_path = creator.create_edition_file(
            test_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada exitosamente: {new_path}")
            print(f"📁 Archivo original: {test_path}")
            print(f"📁 Archivo nuevo: {new_path}")
            
            # Verificar que el archivo original ya no existe
            if not os.path.exists(test_path):
                print("✅ Archivo original renombrado correctamente")
            else:
                print("❌ Archivo original aún existe")
            
            # Verificar que el archivo nuevo existe
            if os.path.exists(new_path):
                print("✅ Archivo nuevo existe")
            else:
                print("❌ Archivo nuevo no existe")
            
            # Limpiar archivos de prueba
            if os.path.exists(new_path):
                os.remove(new_path)
                print("🧹 Archivo de prueba eliminado")
            
            return True
        else:
            print("❌ Error creando edición")
            # Limpiar archivo de prueba
            if os.path.exists(test_path):
                os.remove(test_path)
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edition_manager():
    """Prueba el gestor de ediciones"""
    print("🧪 Probando gestor de ediciones...")
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        # Crear gestor
        manager = PlexEditionsManager("dummy_path")
        
        # Crear archivo de prueba
        test_file = "test_movie2.mkv"
        test_path = os.path.join(os.getcwd(), test_file)
        
        with open(test_path, 'w') as f:
            f.write("test content")
        
        print(f"📁 Archivo de prueba creado: {test_path}")
        
        # Probar creación de edición
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        
        new_path = manager.create_edition_for_file(
            test_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada exitosamente: {new_path}")
            
            # Limpiar archivos de prueba
            if os.path.exists(new_path):
                os.remove(new_path)
                print("🧹 Archivo de prueba eliminado")
            
            return True
        else:
            print("❌ Error creando edición")
            # Limpiar archivo de prueba
            if os.path.exists(test_path):
                os.remove(test_path)
            return False
            
    except Exception as e:
        print(f"❌ Error en gestor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation():
    """Prueba la validación de nombres de edición"""
    print("🧪 Probando validación de nombres...")
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        creator = PlexEditionCreator()
        
        # Nombres válidos
        valid_names = [
            "Edición del Director",
            "Versión Extendida",
            "Edición Especial",
            "4K",
            "Remasterizada"
        ]
        
        # Nombres inválidos
        invalid_names = [
            "",
            "   ",
            "Edición/Especial",  # Carácter inválido
            "Edición:Especial",  # Carácter inválido
            "Edición|Especial"   # Carácter inválido
        ]
        
        print("📝 Probando nombres válidos:")
        for name in valid_names:
            is_valid = creator.validate_edition_name(name)
            print(f"  {name}: {'✅' if is_valid else '❌'}")
        
        print("📝 Probando nombres inválidos:")
        for name in invalid_names:
            is_valid = creator.validate_edition_name(name)
            print(f"  '{name}': {'✅' if is_valid else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de creación de ediciones...")
    print("=" * 60)
    
    tests = [
        test_validation,
        test_edition_creation,
        test_edition_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Error inesperado en {test.__name__}: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron correctamente!")
        print("✅ La funcionalidad de creación de ediciones está funcionando")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores")

if __name__ == "__main__":
    main()
