#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar renombrado con el archivo Amateur
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_amateur_rename():
    """Test para verificar si podemos renombrar el archivo Amateur"""
    print("🧪 Test de renombrado con archivo Amateur")
    print("=" * 60)
    
    # Archivo específico del usuario
    file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
    
    print(f"📁 Archivo objetivo: {file_path}")
    print(f"📁 Directorio: {os.path.dirname(file_path)}")
    
    # Test 1: Verificar acceso al archivo
    print("\n🔍 Test 1: Verificar acceso al archivo")
    file_accessible = False
    
    try:
        # Método 1: os.path.exists
        exists_1 = os.path.exists(file_path)
        print(f"✅ os.path.exists: {exists_1}")
        if exists_1:
            file_accessible = True
    except Exception as e:
        print(f"❌ os.path.exists falló: {e}")
    
    try:
        # Método 2: os.access
        exists_2 = os.access(file_path, os.R_OK)
        print(f"✅ os.access: {exists_2}")
        if exists_2:
            file_accessible = True
    except Exception as e:
        print(f"❌ os.access falló: {e}")
    
    try:
        # Método 3: pathlib
        path_obj = Path(file_path)
        exists_3 = path_obj.exists()
        print(f"✅ pathlib.Path.exists: {exists_3}")
        if exists_3:
            file_accessible = True
    except Exception as e:
        print(f"❌ pathlib falló: {e}")
    
    if not file_accessible:
        print("⚠️ Archivo no accesible con métodos estándar")
        print("💡 Continuando con test de renombrado de todas formas...")
    
    # Test 2: Intentar renombrado directo
    print("\n🔄 Test 2: Intentar renombrado directo")
    
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
    print("=" * 60)
    
    try:
        from src.services.Plex.plex_edition_creator import PlexEditionCreator
        
        file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
        
        creator = PlexEditionCreator()
        
        print("🔄 Probando método UNC-safe...")
        new_path = creator.create_edition_file_unc_safe(
            file_path=file_path,
            movie_title="Amateur",
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
    print("=" * 60)
    
    try:
        from src.services.Plex.plex_editions_manager import PlexEditionsManager
        
        file_path = r"\\DiskStation\data\media\movies\00- Recién descargadas\Amateur.(2025).(Spanish.English.Subs).WEB-DL.1080p.x264-EAC3.by.xusman.(nocturniap2p).mkv"
        
        manager = PlexEditionsManager("dummy_path")
        
        print("🔄 Probando con gestor...")
        new_path = manager.create_edition_for_file(
            file_path=file_path,
            movie_title="Amateur",
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

def test_directory_access():
    """Test para verificar acceso al directorio"""
    print("\n🔍 Test 5: Verificar acceso al directorio")
    print("=" * 60)
    
    directory = r"\\DiskStation\data\media\movies\00- Recién descargadas"
    
    try:
        # Listar archivos en el directorio
        files = os.listdir(directory)
        print(f"📁 Archivos en el directorio ({len(files)} encontrados):")
        
        for file in files[:10]:  # Mostrar solo los primeros 10
            print(f"  - {file}")
        
        if len(files) > 10:
            print(f"  ... y {len(files) - 10} archivos más")
        
        # Buscar archivos específicos
        amateur_mkv = None
        amateur_mp4 = None
        
        for file in files:
            if "Amateur" in file and file.endswith('.mkv'):
                amateur_mkv = file
            elif "Amateur" in file and file.endswith('.mp4'):
                amateur_mp4 = file
        
        print(f"\n📁 Archivo Amateur.mkv encontrado: {amateur_mkv}")
        print(f"📁 Archivo Amateur.mp4 encontrado: {amateur_mp4}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo al directorio: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Test completo de renombrado con archivo Amateur")
    print("=" * 70)
    
    # Test 0: Verificar acceso al directorio
    dir_success = test_directory_access()
    
    # Test 1: Renombrado directo
    success1 = test_amateur_rename()
    
    # Test 2: Con PlexEditionCreator
    success2 = test_with_plex_creator()
    
    # Test 3: Con PlexEditionsManager
    success3 = test_with_manager()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"✅ Acceso al directorio: {'ÉXITO' if dir_success else 'FALLO'}")
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
