#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la creación de ediciones con el archivo específico del usuario
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_specific_file_edition():
    """Prueba la creación de edición con el archivo específico del usuario"""
    print("🧪 Probando creación de edición con archivo específico...")
    
    # Archivo específico del usuario
    file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
    
    print(f"📁 Archivo objetivo: {file_path}")
    
    # Normalizar la ruta UNC
    normalized_path = os.path.normpath(file_path)
    print(f"📁 Ruta normalizada: {normalized_path}")
    
    # Verificar que el archivo existe con diferentes métodos
    file_exists = False
    try:
        # Método 1: os.path.exists
        if os.path.exists(normalized_path):
            file_exists = True
            print("✅ Archivo encontrado con os.path.exists")
        else:
            print("❌ os.path.exists falló")
    except Exception as e:
        print(f"⚠️ Error con os.path.exists: {e}")
    
    # Método 2: Verificar con os.access
    if not file_exists:
        try:
            if os.access(normalized_path, os.F_OK):
                file_exists = True
                print("✅ Archivo encontrado con os.access")
            else:
                print("❌ os.access falló")
        except Exception as e:
            print(f"⚠️ Error con os.access: {e}")
    
    # Método 3: Verificar con pathlib
    if not file_exists:
        try:
            from pathlib import Path
            path_obj = Path(normalized_path)
            if path_obj.exists():
                file_exists = True
                print("✅ Archivo encontrado con pathlib")
            else:
                print("❌ pathlib falló")
        except Exception as e:
            print(f"⚠️ Error con pathlib: {e}")
    
    if not file_exists:
        print("❌ El archivo no es accesible con ningún método")
        print("💡 Esto puede ser un problema de rutas UNC o permisos de red")
        return False
    
    print("✅ Archivo encontrado y accesible")
    
    # Obtener información del archivo
    try:
        file_size = os.path.getsize(file_path)
        print(f"📊 Tamaño del archivo: {file_size / (1024*1024*1024):.2f} GB")
        
        # Obtener información de modificación
        import time
        mtime = os.path.getmtime(file_path)
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        print(f"📅 Última modificación: {mtime_str}")
        
    except Exception as e:
        print(f"⚠️ Error obteniendo información del archivo: {e}")
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        # Crear creador de ediciones
        creator = PlexEditionCreator()
        
        # Parámetros para la edición
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        create_subfolder = False
        
        print(f"🎬 Película: {movie_title}")
        print(f"📚 Edición: {edition_name}")
        print(f"📁 Subcarpeta: {create_subfolder}")
        
        # Mostrar el nombre actual del archivo
        current_filename = os.path.basename(file_path)
        print(f"📁 Nombre actual: {current_filename}")
        
        # Calcular el nombre que debería tener después
        directory = os.path.dirname(file_path)
        name, ext = os.path.splitext(current_filename)
        clean_edition_name = creator._clean_edition_name(edition_name)
        expected_new_name = f"{name} {{edition-{clean_edition_name}}}{ext}"
        expected_new_path = os.path.join(directory, expected_new_name)
        
        print(f"📁 Nombre esperado: {expected_new_name}")
        print(f"📁 Ruta esperada: {expected_new_path}")
        
        # Verificar si ya existe un archivo con el nombre esperado
        if os.path.exists(expected_new_path):
            print("⚠️ Ya existe un archivo con el nombre esperado")
            print("💡 Esto podría causar problemas en la creación de la edición")
        
        # Intentar crear la edición
        print("🔄 Creando edición con método UNC-safe...")
        
        # Usar el nuevo método UNC-safe
        new_path = creator.create_edition_file_unc_safe(
            file_path, 
            movie_title, 
            edition_name, 
            create_subfolder
        )
        
        if new_path:
            print("✅ Edición creada exitosamente!")
            print(f"📁 Archivo original: {file_path}")
            print(f"📁 Archivo nuevo: {new_path}")
            
            # Verificar el estado de los archivos
            original_exists = os.path.exists(file_path)
            new_exists = os.path.exists(new_path)
            
            print(f"📁 Archivo original existe: {original_exists}")
            print(f"📁 Archivo nuevo existe: {new_exists}")
            
            if not original_exists and new_exists:
                print("✅ Renombrado exitoso!")
                
                # Mostrar información del archivo nuevo
                try:
                    new_size = os.path.getsize(new_path)
                    print(f"📊 Tamaño del archivo nuevo: {new_size / (1024*1024*1024):.2f} GB")
                except Exception as e:
                    print(f"⚠️ Error obteniendo tamaño del archivo nuevo: {e}")
                
                return True
            else:
                print("❌ Renombrado falló")
                return False
        else:
            print("❌ Error creando edición")
            return False
            
    except Exception as e:
        print(f"❌ Error en la creación de edición: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_manager():
    """Prueba usando el gestor de ediciones"""
    print("🧪 Probando con gestor de ediciones...")
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        # Crear gestor
        manager = PlexEditionsManager("dummy_path")
        
        # Archivo específico
        file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
        
        if not os.path.exists(file_path):
            print("❌ El archivo no existe o no es accesible")
            return False
        
        print("✅ Archivo accesible")
        
        # Crear edición usando el gestor (que ahora usa UNC-safe internamente)
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        
        print("🔄 Creando edición con gestor (UNC-safe)...")
        new_path = manager.create_edition_for_file(
            file_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada: {new_path}")
            return True
        else:
            print("❌ Error creando edición con gestor")
            return False
            
    except Exception as e:
        print(f"❌ Error con gestor: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🚀 Probando creación de edición con archivo específico...")
    print("=" * 70)
    
    # Probar con el archivo específico
    success = test_specific_file_edition()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 ¡Edición creada exitosamente!")
        print("💡 Verifica en el explorador de archivos que el archivo se renombró")
    else:
        print("❌ Error creando edición")
        print("🔧 Revisa los errores anteriores")
        
        # Probar con gestor como alternativa
        print("\n🔄 Probando con gestor alternativo...")
        test_with_manager()

if __name__ == "__main__":
    main()
