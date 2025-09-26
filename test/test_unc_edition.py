#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para manejar rutas UNC en la creación de ediciones
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_unc_edition():
    """Prueba la creación de edición con manejo de rutas UNC"""
    print("🧪 Probando creación de edición con rutas UNC...")
    
    # Archivo específico del usuario
    file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
    
    print(f"📁 Archivo objetivo: {file_path}")
    
    # Intentar diferentes enfoques para rutas UNC
    approaches = [
        ("Ruta original", file_path),
        ("Ruta normalizada", os.path.normpath(file_path)),
        ("Ruta con pathlib", str(Path(file_path))),
    ]
    
    accessible_path = None
    for approach_name, test_path in approaches:
        print(f"🔄 Probando {approach_name}: {test_path}")
        try:
            if os.path.exists(test_path):
                print(f"✅ {approach_name} funciona!")
                accessible_path = test_path
                break
            else:
                print(f"❌ {approach_name} falló")
        except Exception as e:
            print(f"⚠️ Error con {approach_name}: {e}")
    
    if not accessible_path:
        print("❌ Ninguna ruta es accesible")
        print("💡 Soluciones:")
        print("   1. Mapear la unidad: net use Z: \\\\DiskStation\\data\\media\\movies")
        print("   2. Usar ruta local alternativa")
        print("   3. Verificar permisos de red")
        return False
    
    print(f"✅ Usando ruta accesible: {accessible_path}")
    
    # Obtener información del archivo
    try:
        file_size = os.path.getsize(accessible_path)
        print(f"📊 Tamaño: {file_size / (1024*1024*1024):.2f} GB")
    except Exception as e:
        print(f"⚠️ Error obteniendo tamaño: {e}")
    
    # Probar creación de edición
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        creator = PlexEditionCreator()
        
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        
        print(f"🎬 Película: {movie_title}")
        print(f"📚 Edición: {edition_name}")
        
        # Mostrar nombre esperado
        directory = os.path.dirname(accessible_path)
        filename = os.path.basename(accessible_path)
        name, ext = os.path.splitext(filename)
        clean_edition_name = creator._clean_edition_name(edition_name)
        expected_new_name = f"{name} {{edition-{clean_edition_name}}}{ext}"
        expected_new_path = os.path.join(directory, expected_new_name)
        
        print(f"📁 Nombre esperado: {expected_new_name}")
        print(f"📁 Ruta esperada: {expected_new_path}")
        
        # Verificar si ya existe
        if os.path.exists(expected_new_path):
            print("⚠️ Ya existe un archivo con el nombre esperado")
            return False
        
        # Crear edición
        print("🔄 Creando edición...")
        new_path = creator.create_edition_file(
            accessible_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print("✅ Edición creada exitosamente!")
            print(f"📁 Archivo original: {accessible_path}")
            print(f"📁 Archivo nuevo: {new_path}")
            
            # Verificar resultado
            original_exists = os.path.exists(accessible_path)
            new_exists = os.path.exists(new_path)
            
            print(f"📁 Archivo original existe: {original_exists}")
            print(f"📁 Archivo nuevo existe: {new_exists}")
            
            if not original_exists and new_exists:
                print("✅ Renombrado exitoso!")
                return True
            else:
                print("❌ Renombrado falló")
                return False
        else:
            print("❌ Error creando edición")
            return False
            
    except Exception as e:
        print(f"❌ Error en creación: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mapped_drive():
    """Prueba con unidad mapeada"""
    print("🧪 Probando con unidad mapeada...")
    
    # Intentar con unidad mapeada (si existe)
    mapped_paths = [
        r"Z:\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv",
        r"Y:\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv",
        r"X:\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv",
    ]
    
    for mapped_path in mapped_paths:
        print(f"🔄 Probando: {mapped_path}")
        if os.path.exists(mapped_path):
            print(f"✅ Encontrado en: {mapped_path}")
            return test_edition_with_path(mapped_path)
        else:
            print(f"❌ No encontrado en: {mapped_path}")
    
    print("❌ No se encontró en ninguna unidad mapeada")
    return False

def test_edition_with_path(file_path):
    """Prueba la creación de edición con una ruta específica"""
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        creator = PlexEditionCreator()
        
        movie_title = "Scooby-Doo: Comienza el misterio"
        edition_name = "Edición Especial"
        
        print(f"🎬 Creando edición para: {file_path}")
        
        new_path = creator.create_edition_file(
            file_path, 
            movie_title, 
            edition_name, 
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada: {new_path}")
            return True
        else:
            print("❌ Error creando edición")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Probando creación de edición con rutas UNC...")
    print("=" * 70)
    
    # Probar con ruta UNC directa
    success = test_unc_edition()
    
    if not success:
        print("\n🔄 Probando con unidades mapeadas...")
        success = test_mapped_drive()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 ¡Edición creada exitosamente!")
    else:
        print("❌ No se pudo crear la edición")
        print("💡 Soluciones:")
        print("   1. Mapear la unidad: net use Z: \\\\DiskStation\\data\\media\\movies")
        print("   2. Copiar el archivo a una carpeta local")
        print("   3. Verificar permisos de red")

if __name__ == "__main__":
    main()
