#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para simular la creación de ediciones como en la aplicación real
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_real_edition_creation():
    """Prueba la creación de ediciones simulando el flujo real de la aplicación"""
    print("🧪 Probando creación de ediciones con flujo real...")
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        # Crear gestor como en la aplicación real
        manager = PlexEditionsManager("dummy_path")
        
        # Crear archivo de prueba más realista
        test_file = "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat.mkv"
        test_path = os.path.join(os.getcwd(), test_file)
        
        # Crear archivo de prueba
        with open(test_path, 'w') as f:
            f.write("test content for scooby doo movie")
        
        print(f"📁 Archivo de prueba creado: {test_path}")
        print(f"📁 Tamaño del archivo: {os.path.getsize(test_path)} bytes")
        
        # Simular los parámetros que vienen de la aplicación
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        create_subfolder = False
        
        print(f"🎬 Película: {movie_title}")
        print(f"📚 Edición: {edition_name}")
        print(f"📁 Subcarpeta: {create_subfolder}")
        
        # Verificar que el archivo existe antes
        if not os.path.exists(test_path):
            print("❌ Archivo de prueba no existe")
            return False
        
        print("✅ Archivo existe antes de la creación")
        
        # Crear edición usando el método de la aplicación
        print("🔄 Creando edición...")
        new_path = manager.create_edition_for_file(
            test_path, 
            movie_title, 
            edition_name, 
            create_subfolder
        )
        
        print(f"📊 Resultado: {new_path}")
        
        if new_path:
            print("✅ Edición creada exitosamente")
            print(f"📁 Archivo original: {test_path}")
            print(f"📁 Archivo nuevo: {new_path}")
            
            # Verificar estado de archivos
            original_exists = os.path.exists(test_path)
            new_exists = os.path.exists(new_path)
            
            print(f"📁 Archivo original existe: {original_exists}")
            print(f"📁 Archivo nuevo existe: {new_exists}")
            
            if not original_exists and new_exists:
                print("✅ Renombrado exitoso: archivo original eliminado, archivo nuevo creado")
                
                # Mostrar contenido del archivo nuevo
                with open(new_path, 'r') as f:
                    content = f.read()
                print(f"📄 Contenido del archivo nuevo: {content[:50]}...")
                
                # Limpiar archivo de prueba
                os.remove(new_path)
                print("🧹 Archivo de prueba eliminado")
                
                return True
            else:
                print("❌ Renombrado falló")
                if original_exists:
                    os.remove(test_path)
                if new_exists:
                    os.remove(new_path)
                return False
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

def test_direct_creator():
    """Prueba el creador directamente"""
    print("🧪 Probando creador directamente...")
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        creator = PlexEditionCreator()
        
        # Crear archivo de prueba
        test_file = "test_direct.mkv"
        test_path = os.path.join(os.getcwd(), test_file)
        
        with open(test_path, 'w') as f:
            f.write("test content")
        
        print(f"📁 Archivo creado: {test_path}")
        
        # Crear edición directamente
        movie_title = "Test Movie"
        edition_name = "Test Edition"
        
        print("🔄 Creando edición directamente...")
        new_path = creator.create_edition_file(
            test_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada: {new_path}")
            
            # Verificar archivos
            original_exists = os.path.exists(test_path)
            new_exists = os.path.exists(new_path)
            
            print(f"📁 Original existe: {original_exists}")
            print(f"📁 Nuevo existe: {new_exists}")
            
            # Limpiar
            if new_exists:
                os.remove(new_path)
            if original_exists:
                os.remove(test_path)
            
            return True
        else:
            print("❌ Error creando edición")
            if os.path.exists(test_path):
                os.remove(test_path)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_scenarios():
    """Prueba escenarios de error"""
    print("🧪 Probando escenarios de error...")
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        creator = PlexEditionCreator()
        
        # Escenario 1: Archivo que no existe
        print("📝 Probando archivo inexistente...")
        result = creator.create_edition_file(
            "archivo_inexistente.mkv",
            "Test Movie",
            "Test Edition",
            False
        )
        print(f"   Resultado: {result} (esperado: None)")
        
        # Escenario 2: Nombre de edición vacío
        print("📝 Probando nombre de edición vacío...")
        test_file = "test_error.mkv"
        test_path = os.path.join(os.getcwd(), test_file)
        
        with open(test_path, 'w') as f:
            f.write("test")
        
        result = creator.create_edition_file(
            test_path,
            "Test Movie",
            "",  # Nombre vacío
            False
        )
        print(f"   Resultado: {result}")
        
        # Limpiar
        if os.path.exists(test_path):
            os.remove(test_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de creación de ediciones reales...")
    print("=" * 60)
    
    tests = [
        test_direct_creator,
        test_real_edition_creation,
        test_error_scenarios
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
        print("✅ La funcionalidad está funcionando")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores")

if __name__ == "__main__":
    main()
