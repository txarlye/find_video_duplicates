#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar renombrado con rutas UNC
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_unc_rename():
    """Test para verificar si podemos renombrar archivos UNC"""
    print("🧪 Test de renombrado con rutas UNC")
    print("=" * 50)
    
    # Archivo específico del usuario
    file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
    
    print(f"📁 Archivo objetivo: {file_path}")
    
    # Test 1: Verificar acceso al archivo
    print("\n🔍 Test 1: Verificar acceso al archivo")
    try:
        # Método 1: os.path.exists
        exists_1 = os.path.exists(file_path)
        print(f"✅ os.path.exists: {exists_1}")
    except Exception as e:
        print(f"❌ os.path.exists falló: {e}")
    
    try:
        # Método 2: os.access
        exists_2 = os.access(file_path, os.R_OK)
        print(f"✅ os.access: {exists_2}")
    except Exception as e:
        print(f"❌ os.access falló: {e}")
    
    try:
        # Método 3: pathlib
        path_obj = Path(file_path)
        exists_3 = path_obj.exists()
        print(f"✅ pathlib.Path.exists: {exists_3}")
    except Exception as e:
        print(f"❌ pathlib falló: {e}")
    
    # Test 2: Intentar renombrado directo
    print("\n🔄 Test 2: Intentar renombrado directo")
    
    if not os.path.exists(file_path):
        print("❌ Archivo no accesible - saltando test de renombrado")
        return False
    
    try:
        # Crear nombre de edición
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        new_name = f"{name} {{edition-Test Edition}}{ext}"
        new_path = os.path.join(directory, new_name)
        
        print(f"📁 Nombre original: {filename}")
        print(f"📁 Nombre nuevo: {new_name}")
        print(f"📁 Ruta nueva: {new_path}")
        
        # Verificar si el archivo de destino ya existe
        if os.path.exists(new_path):
            print("⚠️ El archivo de destino ya existe")
            return False
        
        # Intentar renombrar
        print("🔄 Intentando renombrar...")
        os.rename(file_path, new_path)
        print("✅ Renombrado exitoso!")
        
        # Verificar que el archivo nuevo existe
        if os.path.exists(new_path):
            print("✅ Archivo renombrado verificado")
            
            # Renombrar de vuelta
            print("🔄 Renombrando de vuelta...")
            os.rename(new_path, file_path)
            print("✅ Archivo restaurado")
            return True
        else:
            print("❌ El archivo no se renombró correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error en renombrado: {e}")
        return False

def test_with_plex_creator():
    """Test usando el creador de ediciones de Plex"""
    print("\n🧪 Test 3: Usando PlexEditionCreator")
    print("=" * 50)
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
        
        creator = PlexEditionCreator()
        
        print("🔄 Probando método UNC-safe...")
        new_path = creator.create_edition_file_unc_safe(
            file_path=file_path,
            movie_title="Scooby-Doo: Comienza el misterio",
            edition_name="Test Edition UNC",
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada: {new_path}")
            
            # Verificar que el archivo existe
            if os.path.exists(new_path):
                print("✅ Archivo de edición verificado")
                
                # Restaurar archivo original
                print("🔄 Restaurando archivo original...")
                try:
                    os.rename(new_path, file_path)
                    print("✅ Archivo restaurado")
                    return True
                except Exception as e:
                    print(f"❌ Error restaurando: {e}")
                    return False
            else:
                print("❌ Archivo de edición no encontrado")
                return False
        else:
            print("❌ No se pudo crear la edición")
            return False
            
    except Exception as e:
        print(f"❌ Error con PlexEditionCreator: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_manager():
    """Test usando el gestor de ediciones"""
    print("\n🧪 Test 4: Usando PlexEditionsManager")
    print("=" * 50)
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        file_path = r"\\DiskStation\data\media\movies\00-ANIMACION\Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
        
        manager = PlexEditionsManager("dummy_path")
        
        print("🔄 Probando con gestor...")
        new_path = manager.create_edition_for_file(
            file_path=file_path,
            movie_title="Scooby-Doo: Comienza el misterio",
            edition_name="Test Edition Manager",
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada por gestor: {new_path}")
            
            # Verificar que el archivo existe
            if os.path.exists(new_path):
                print("✅ Archivo de edición verificado")
                
                # Restaurar archivo original
                print("🔄 Restaurando archivo original...")
                try:
                    os.rename(new_path, file_path)
                    print("✅ Archivo restaurado")
                    return True
                except Exception as e:
                    print(f"❌ Error restaurando: {e}")
                    return False
            else:
                print("❌ Archivo de edición no encontrado")
                return False
        else:
            print("❌ No se pudo crear la edición con gestor")
            return False
            
    except Exception as e:
        print(f"❌ Error con PlexEditionsManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🚀 Test completo de renombrado con rutas UNC")
    print("=" * 70)
    
    # Test 1: Renombrado directo
    success1 = test_unc_rename()
    
    # Test 2: Con PlexEditionCreator
    success2 = test_with_plex_creator()
    
    # Test 3: Con PlexEditionsManager
    success3 = test_with_manager()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"✅ Renombrado directo: {'ÉXITO' if success1 else 'FALLO'}")
    print(f"✅ PlexEditionCreator: {'ÉXITO' if success2 else 'FALLO'}")
    print(f"✅ PlexEditionsManager: {'ÉXITO' if success3 else 'FALLO'}")
    
    if any([success1, success2, success3]):
        print("\n🎉 ¡Al menos un método funcionó!")
        print("💡 El renombrado con rutas UNC es posible")
    else:
        print("\n❌ Todos los métodos fallaron")
        print("💡 Puede ser un problema de permisos o acceso a la red")

if __name__ == "__main__":
    main()
