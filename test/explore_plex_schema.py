"""
Script para explorar el esquema de la base de datos de Plex
"""

import sqlite3
from pathlib import Path

def explore_schema():
    """Explora el esquema de la base de datos"""
    
    # Obtener ruta desde settings
    from src.settings.settings import Settings
    settings = Settings()
    db_path = settings.get_plex_database_path()
    
    if not Path(db_path).exists():
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("🔍 Explorando esquema de la base de datos...")
        print("=" * 60)
        
        # Obtener todas las tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        
        print(f"📊 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n" + "=" * 60)
        
        # Explorar tabla media_items
        print("\n🔍 Tabla media_items:")
        cur.execute("PRAGMA table_info(media_items)")
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n🔍 Tabla media_parts:")
        cur.execute("PRAGMA table_info(media_parts)")
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Probar consulta simple
        print("\n🧪 Probando consulta simple:")
        cur.execute("SELECT COUNT(*) FROM media_items")
        count = cur.fetchone()[0]
        print(f"  - Total media_items: {count}")
        
        cur.execute("SELECT COUNT(*) FROM media_parts")
        count = cur.fetchone()[0]
        print(f"  - Total media_parts: {count}")
        
        # Ver algunas filas de ejemplo
        print("\n📋 Ejemplos de media_items:")
        cur.execute("SELECT id, title, year FROM media_items LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(f"  - ID: {row[0]}, Título: {row[1]}, Año: {row[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_schema()
