#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para renombrar Amateur con {version borrar}
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_amateur_version_rename():
    """Test para renombrar Amateur con {version borrar}"""
    print("🧪 Test de renombrado Amateur con {version borrar}")
    print("=" * 60)
    
    # Archivo específico del usuario
    file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
    
    print(f"📁 Archivo objetivo: {file_path}")
    
    # Test 1: Verificar acceso al archivo
    print("\n🔍 Test 1: Verificar acceso al archivo")
    file_accessible = False
    
    try:
        exists = os.path.exists(file_path)
        print(f"✅ os.path.exists: {exists}")
        if exists:
            file_accessible = True
    except Exception as e:
        print(f"❌ os.path.exists falló: {e}")
    
    if not file_accessible:
        print("⚠️ Archivo no accesible con métodos estándar")
        print("💡 Continuando con test de renombrado de todas formas...")
    
    # Test 2: Renombrado directo con {version borrar}
    print("\n🔄 Test 2: Renombrado directo con {version borrar}")
    
    try:
        # Crear nombre de edición
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        # Crear nombre con {version borrar}
        new_name = f"{name} {{version borrar}}{ext}"
        new_path = os.path.join(directory, new_name)
        
        print(f"📁 Nombre original: {filename}")
        print(f"📁 Nombre nuevo: {new_name}")
        print(f"📁 Ruta nueva: {new_path}")
        
        # Verificar si el archivo de destino ya existe
        if os.path.exists(new_path):
            print("⚠️ El archivo de destino ya existe")
            print("🔄 Eliminando archivo existente...")
            try:
                os.remove(new_path)
                print("✅ Archivo existente eliminado")
            except Exception as e:
                print(f"❌ Error eliminando archivo existente: {e}")
                return False
        
        # Intentar renombrar
        print("🔄 Intentando renombrar...")
        os.rename(file_path, new_path)
        print("✅ Renombrado exitoso!")
        
        # Verificar que el archivo nuevo existe
        if os.path.exists(new_path):
            print("✅ Archivo renombrado verificado")
            print(f"📁 Archivo renombrado: {os.path.basename(new_path)}")
            
            # Verificar que el archivo original ya no existe
            if not os.path.exists(file_path):
                print("✅ Archivo original eliminado correctamente")
            else:
                print("⚠️ Archivo original aún existe")
            
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
        import traceback
        traceback.print_exc()
        return False

def test_with_plex_creator():
    """Test usando PlexEditionCreator con {version borrar}"""
    print("\n🧪 Test 3: Usando PlexEditionCreator con {version borrar}")
    print("=" * 60)
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
        
        creator = PlexEditionCreator()
        
        print("🔄 Probando método UNC-safe con {version borrar}...")
        new_path = creator.create_edition_file_unc_safe(
            file_path=file_path,
            movie_title="Amateur",
            edition_name="version borrar",
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada: {new_path}")
            
            # Verificar que el archivo existe
            if os.path.exists(new_path):
                print("✅ Archivo de edición verificado")
                print(f"📁 Archivo renombrado: {os.path.basename(new_path)}")
                
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
    """Test usando PlexEditionsManager con {version borrar}"""
    print("\n🧪 Test 4: Usando PlexEditionsManager con {version borrar}")
    print("=" * 60)
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
        
        manager = PlexEditionsManager("dummy_path")
        
        print("🔄 Probando con gestor y {version borrar}...")
        new_path = manager.create_edition_for_file(
            file_path=file_path,
            movie_title="Amateur",
            edition_name="version borrar",
            create_subfolder=False
        )
        
        if new_path:
            print(f"✅ Edición creada por gestor: {new_path}")
            
            # Verificar que el archivo existe
            if os.path.exists(new_path):
                print("✅ Archivo de edición verificado")
                print(f"📁 Archivo renombrado: {os.path.basename(new_path)}")
                
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

def test_directory_listing():
    """Test para listar archivos en el directorio"""
    print("\n🔍 Test 5: Listar archivos en el directorio")
    print("=" * 60)
    
    directory = r"\\DiskStation\data\media\movies\00- Recién descargadas"
    
    try:
        # Listar archivos en el directorio
        files = os.listdir(directory)
        print(f"📁 Archivos en el directorio ({len(files)} encontrados):")
        
        # Buscar archivos Amateur
        amateur_files = [f for f in files if "Amateur" in f]
        
        print(f"\n📁 Archivos Amateur encontrados ({len(amateur_files)}):")
        for file in amateur_files:
            print(f"  - {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo al directorio: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Test completo de renombrado Amateur con {version borrar}")
    print("=" * 70)
    
    # Test 0: Listar archivos en el directorio
    dir_success = test_directory_listing()
    
    # Test 1: Renombrado directo
    success1 = test_amateur_version_rename()
    
    # Test 2: Con PlexEditionCreator
    success2 = test_with_plex_creator()
    
    # Test 3: Con PlexEditionsManager
    success3 = test_with_manager()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"✅ Listado de directorio: {'ÉXITO' if dir_success else 'FALLO'}")
    print(f"✅ Renombrado directo: {'ÉXITO' if success1 else 'FALLO'}")
    print(f"✅ PlexEditionCreator: {'ÉXITO' if success2 else 'FALLO'}")
    print(f"✅ PlexEditionsManager: {'ÉXITO' if success3 else 'FALLO'}")
    
    if any([success1, success2, success3]):
        print("\n🎉 ¡Al menos un método funcionó!")
        print("💡 El renombrado con {version borrar} es posible")
    else:
        print("\n❌ Todos los métodos fallaron")
        print("💡 Puede ser un problema de permisos o acceso a la red")

if __name__ == "__main__":
    main()
