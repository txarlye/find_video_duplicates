#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para Scooby-Doo - Verificar si ambas rutas apuntan a la misma película en Plex
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.plex_service import PlexService

def test_scooby_plex():
    """Test específico para Scooby-Doo en Plex"""
    print("🔍 Test Scooby-Doo en Plex")
    print("=" * 40)
    
    # Crear servicio
    plex_service = PlexService()
    
    # Test de conexión
    if not plex_service.test_connection():
        print("❌ Error de conexión")
        return
    print("✅ Conexión exitosa")
    
    # Rutas específicas de Scooby-Doo
    file1 = "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat.mkv"
    file2 = "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
    
    print(f"\n1️⃣ Test con archivo 1: {file1}")
    result1 = plex_service.get_library_info_by_filename(file1)
    if result1:
        print("✅ ENCONTRADO:")
        print(f"   📁 Biblioteca: {result1.get('library_name', 'N/A')}")
        print(f"   🎬 Título: {result1.get('title', 'N/A')}")
        print(f"   📅 Año: {result1.get('year', 'N/A')}")
        print(f"   📁 Ruta en Plex: {result1.get('file_path', 'N/A')}")
    else:
        print("❌ NO ENCONTRADO")
    
    print(f"\n2️⃣ Test con archivo 2: {file2}")
    result2 = plex_service.get_library_info_by_filename(file2)
    if result2:
        print("✅ ENCONTRADO:")
        print(f"   📁 Biblioteca: {result2.get('library_name', 'N/A')}")
        print(f"   🎬 Título: {result2.get('title', 'N/A')}")
        print(f"   📅 Año: {result2.get('year', 'N/A')}")
        print(f"   📁 Ruta en Plex: {result2.get('file_path', 'N/A')}")
    else:
        print("❌ NO ENCONTRADO")
    
    # Test 3: Consulta SQL directa para obtener metadatos reales
    print(f"\n3️⃣ Consulta SQL directa para metadatos reales:")
    try:
        conn = plex_service._get_connection()
        cur = conn.cursor()
        
        # Buscar archivos de Scooby-Doo y obtener metadatos reales
        sql = """
        SELECT 
            mp.file,
            mi.title,
            mi.year,
            mi.summary,
            mi.studio,
            mi.duration,
            ls.name as library_name
        FROM media_parts mp
        JOIN media_items mi ON mp.media_item_id = mi.id
        JOIN library_sections ls ON mi.library_section_id = ls.id
        WHERE mp.file LIKE ?
        """
        
        # Buscar archivos que contengan "Scooby_Doo_3_Comienza_el_misterio"
        search_term = "%Scooby_Doo_3_Comienza_el_misterio%"
        cur.execute(sql, (search_term,))
        rows = cur.fetchall()
        
        print(f"   📊 Archivos encontrados: {len(rows)}")
        for i, row in enumerate(rows, 1):
            print(f"   {i}. Archivo: {row[0]}")
            print(f"      🎬 Título Plex: {row[1]}")
            print(f"      📅 Año: {row[2]}")
            print(f"      📝 Resumen: {row[3][:100] if row[3] else 'N/A'}...")
            print(f"      🏢 Estudio: {row[4]}")
            print(f"      ⏱️ Duración: {row[5]}")
            print(f"      📁 Biblioteca: {row[6]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en consulta SQL: {e}")
    
    print("\n💡 Análisis:")
    if result1 and result2:
        print("   ✅ Ambos archivos están en Plex")
        # Verificar si son la misma película
        if result1.get('file_path') and result2.get('file_path'):
            print("   🔍 Verificando si son la misma película...")
            # Aquí podríamos comparar más metadatos si los tuviéramos
            print("   📝 Necesitamos obtener metadatos reales de Plex para comparar")
    else:
        print("   ❌ Algunos archivos no están en Plex")

if __name__ == "__main__":
    test_scooby_plex()
