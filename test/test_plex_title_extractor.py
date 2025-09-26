"""
Script de prueba para el extractor de títulos de Plex
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.Plex.plex_title_extractor import PlexTitleExtractor

def test_title_extractor():
    """Prueba el extractor de títulos"""
    
    # Ruta de la base de datos
    db_path = r"\\DiskStation\docker\plex2\db\Library\Application Support\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db"
    
    # Crear extractor
    extractor = PlexTitleExtractor(db_path)
    
    # Probar conexión
    print("🔍 Probando conexión...")
    if not extractor.test_connection():
        print("❌ Error de conexión")
        return
    print("✅ Conexión exitosa")
    
    # Archivos de prueba
    test_files = [
        "Del revés 2.mkv",
        "Del Revés.mkv", 
        "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat.mkv",
        "Scooby_Doo_3_Comienza_el_misterio_2009_m1080p_h264_AC3_Spa_Eng_Lat_2.mkv"
    ]
    
    print("\n🎬 Probando extracción de títulos:")
    print("=" * 60)
    
    for filename in test_files:
        print(f"\n📁 Archivo: {filename}")
        result = extractor.get_real_title_by_filename(filename)
        
        if result:
            print(f"✅ Título real: {result['title']}")
            print(f"📅 Año: {result['year']}")
        else:
            print("❌ No se encontró título real")

if __name__ == "__main__":
    test_title_extractor()
