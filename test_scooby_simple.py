#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para Scooby-Doo
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.services.plex_service import PlexService

def test_scooby():
    print('🔍 Test Scooby-Doo en Plex')
    print('=' * 40)
    
    plex_service = PlexService()
    if not plex_service.test_connection():
        print('❌ Error de conexión')
        return
    
    print('✅ Conexión exitosa')
    
    # Test archivos Scooby-Doo
    file1 = 'Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat.mkv'
    file2 = 'Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv'
    
    print(f'\n1️⃣ Test con archivo 1: {file1}')
    result1 = plex_service.get_library_info_by_filename(file1)
    if result1:
        print('✅ ENCONTRADO:')
        print(f'   📁 Biblioteca: {result1.get("library_name", "N/A")}')
        print(f'   🎬 Título: {result1.get("title", "N/A")}')
        print(f'   📅 Año: {result1.get("year", "N/A")}')
        print(f'   📁 Ruta en Plex: {result1.get("file_path", "N/A")}')
    else:
        print('❌ NO ENCONTRADO')
    
    print(f'\n2️⃣ Test con archivo 2: {file2}')
    result2 = plex_service.get_library_info_by_filename(file2)
    if result2:
        print('✅ ENCONTRADO:')
        print(f'   📁 Biblioteca: {result2.get("library_name", "N/A")}')
        print(f'   🎬 Título: {result2.get("title", "N/A")}')
        print(f'   📅 Año: {result2.get("year", "N/A")}')
        print(f'   📁 Ruta en Plex: {result2.get("file_path", "N/A")}')
    else:
        print('❌ NO ENCONTRADO')

if __name__ == "__main__":
    test_scooby()
