"""
Script para explorar las tablas de metadatos de Plex
"""

import sqlite3
from pathlib import Path

def explore_metadata():
    """Explora las tablas de metadatos"""
    
    db_path = r"\\DiskStation\docker\plex2\db\Library\Application Support\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("🔍 Explorando tablas de metadatos...")
        print("=" * 60)
        
        # Buscar tablas que contengan 'metadata'
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%metadata%'")
        metadata_tables = cur.fetchall()
        
        print("📊 Tablas de metadatos:")
        for table in metadata_tables:
            print(f"  - {table[0]}")
        
        # Explorar metadata_items
        print("\n🔍 Tabla metadata_items:")
        cur.execute("PRAGMA table_info(metadata_items)")
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Probar consulta con metadata_items
        print("\n🧪 Probando consulta con metadata_items:")
        cur.execute("SELECT COUNT(*) FROM metadata_items")
        count = cur.fetchone()[0]
        print(f"  - Total metadata_items: {count}")
        
        # Ver algunas filas de ejemplo
        print("\n📋 Ejemplos de metadata_items:")
        cur.execute("SELECT id, title, year FROM metadata_items LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(f"  - ID: {row[0]}, Título: {row[1]}, Año: {row[2]}")
        
        # Probar JOIN entre media_parts y metadata_items
        print("\n🔗 Probando JOIN:")
        cur.execute("""
        SELECT 
            mp.file,
            mi.title,
            mi.year
        FROM media_parts mp
        JOIN media_items m ON mp.media_item_id = m.id
        JOIN metadata_items mi ON m.metadata_item_id = mi.id
        WHERE mp.file LIKE '%Del revés%'
        LIMIT 3
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"  - Archivo: {row[0]}")
            print(f"    Título: {row[1]}")
            print(f"    Año: {row[2]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_metadata()
