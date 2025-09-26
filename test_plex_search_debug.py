#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para debuggear la búsqueda en Plex
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.plex_service import PlexService

def test_plex_search_debug():
    """Test específico para debuggear la búsqueda en Plex"""
    print("🔍 Test de Búsqueda en Plex - Debug Específico")
    print("=" * 50)
    
    # Crear servicio
    plex_service = PlexService()
    
    # Test de conexión
    print("1️⃣ Verificando conexión...")
    if not plex_service.test_connection():
        print("❌ Error de conexión")
        return
    print("✅ Conexión exitosa")
    
    # Test 1: Buscar "Del revés 2.mkv"
    print("\n2️⃣ Test con 'Del revés 2.mkv':")
    filename1 = "Del revés 2.mkv"
    print(f"   🔍 Buscando: '{filename1}'")
    
    result1 = plex_service.get_library_info_by_filename(filename1)
    if result1:
        print("✅ ENCONTRADO:")
        print(f"   📁 Biblioteca: {result1.get('library_name', 'N/A')}")
        print(f"   🎬 Título: {result1.get('title', 'N/A')}")
        print(f"   📅 Año: {result1.get('year', 'N/A')}")
        print(f"   📁 Ruta en Plex: {result1.get('file_path', 'N/A')}")
    else:
        print("❌ NO ENCONTRADO")
    
    # Test 2: Buscar "Del Revés.mkv"
    print("\n3️⃣ Test con 'Del Revés.mkv':")
    filename2 = "Del Revés.mkv"
    print(f"   🔍 Buscando: '{filename2}'")
    
    result2 = plex_service.get_library_info_by_filename(filename2)
    if result2:
        print("✅ ENCONTRADO:")
        print(f"   📁 Biblioteca: {result2.get('library_name', 'N/A')}")
        print(f"   🎬 Título: {result2.get('title', 'N/A')}")
        print(f"   📅 Año: {result2.get('year', 'N/A')}")
        print(f"   📁 Ruta en Plex: {result2.get('file_path', 'N/A')}")
    else:
        print("❌ NO ENCONTRADO")
    
    # Test 3: Consulta SQL directa para ver qué archivos existen
    print("\n4️⃣ Consulta SQL directa:")
    try:
        conn = plex_service._get_connection()
        cur = conn.cursor()
        
        # Buscar archivos que contengan "Del revés"
        sql = "SELECT file FROM media_parts WHERE file LIKE ?"
        search_term = "%Del revés%"
        cur.execute(sql, (search_term,))
        files = cur.fetchall()
        
        print(f"   📊 Consulta: {sql}")
        print(f"   🔍 Término: {search_term}")
        print(f"   📁 Archivos encontrados: {len(files)}")
        
        for i, file in enumerate(files, 1):
            print(f"   {i}. {file[0]}")
        
        # Buscar específicamente "Del revés 2.mkv"
        print(f"\n   🔍 Buscando específicamente 'Del revés 2.mkv':")
        sql2 = "SELECT file FROM media_parts WHERE file LIKE ?"
        search_term2 = "%Del revés 2.mkv%"
        cur.execute(sql2, (search_term2,))
        files2 = cur.fetchall()
        
        print(f"   📁 Archivos con 'Del revés 2.mkv': {len(files2)}")
        for file in files2:
            print(f"   📁 {file[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en consulta SQL: {e}")
    
    # Test 4: Verificar la estructura de la base de datos
    print("\n5️⃣ Verificando estructura de la base de datos:")
    try:
        conn = plex_service._get_connection()
        cur = conn.cursor()
        
        # Verificar si existe la tabla media_items
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media_items'")
        if cur.fetchone():
            print("   ✅ Tabla media_items existe")
            
            # Verificar columnas de media_items
            cur.execute("PRAGMA table_info(media_items)")
            columns = cur.fetchall()
            print(f"   📊 Columnas de media_items: {len(columns)}")
            for col in columns[:5]:  # Mostrar solo las primeras 5
                print(f"      - {col[1]} ({col[2]})")
        else:
            print("   ❌ Tabla media_items NO existe")
        
        # Verificar media_parts
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media_parts'")
        if cur.fetchone():
            print("   ✅ Tabla media_parts existe")
        else:
            print("   ❌ Tabla media_parts NO existe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
    
    print("\n💡 Análisis:")
    if result1 or result2:
        print("   ✅ Los archivos SÍ están en Plex")
        print("   🔍 El problema está en la lógica de la aplicación")
    else:
        print("   ❌ Los archivos NO están en Plex o hay error en la búsqueda")
        print("   🔍 Verificar nombres, rutas y estructura de BD")

if __name__ == "__main__":
    test_plex_search_debug()
