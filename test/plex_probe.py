# tests/plex_probe.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
from pathlib import Path
from datetime import timedelta
from typing import Optional, List, Dict

PLEX_DB_DIR = r"\\DiskStation\docker\plex2\db\Library\Application Support\Plex Media Server\Plug-in Support\Databases"

def find_plex_db(base_dir: Path) -> Path:
    # 1) Preferido: com.plexapp.plugins.library.db
    main = base_dir / "com.plexapp.plugins.library.db"
    if main.exists():
        return main
    # 2) Si no está, coge el más reciente que empiece por ese nombre y termine en .db
    candidates = sorted(
        [p for p in base_dir.glob("com.plexapp.plugins.library.db*") if p.suffix == ".db"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    raise FileNotFoundError("No se encontró la base de datos de Plex en " + str(base_dir))

def ms_to_hms(ms: Optional[int]) -> str:
    if not ms or ms <= 0:
        return "0h 0m 0s"
    td = timedelta(milliseconds=int(ms))
    h = td.seconds // 3600 + td.days * 24
    m = (td.seconds % 3600) // 60
    s = td.seconds % 60
    return f"{h}h {m}m {s}s"

def query_by_filename(db_path: Path, filename: str) -> List[Dict]:
    # Abrimos en solo lectura; si falla, intenta modo normal (algunas builds de sqlite en Windows no soportan uri ro).
    conn = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except Exception:
        conn = sqlite3.connect(str(db_path))

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # metadata_items.metadata_type = 1 -> Movies
    # En media_parts.file está la ruta completa; filtramos por LIKE y luego validamos por basename exacto en Python.
    sql = """
    SELECT
      mi.id              AS metadata_id,
      mi.title           AS title,
      mi.original_title  AS original_title,
      mi.year            AS year,
      mi.duration        AS meta_duration_ms,
      mi.guid            AS guid,
      mi.studio          AS studio,
      mi.content_rating  AS content_rating,
      mi.rating          AS rating,
      mi.summary         AS summary,
      mi.added_at        AS added_at,
      mi.updated_at      AS updated_at,
      m.id               AS media_id,
      m.bitrate          AS bitrate,
      m.width            AS width,
      m.height           AS height,
      m.container        AS container,
      m.video_codec      AS video_codec,
      m.audio_codec      AS audio_codec,
      m.audio_channels   AS audio_channels,
      mp.id              AS part_id,
      mp.file            AS file_path,
      mp.size            AS size_bytes,
      mp.duration        AS part_duration_ms,
      ls.name            AS library_name
    FROM metadata_items mi
    JOIN media_items m        ON m.metadata_item_id = mi.id
    JOIN media_parts mp       ON mp.media_item_id   = m.id
    LEFT JOIN library_sections ls ON ls.id = mi.library_section_id
    WHERE mi.metadata_type = 1
      AND (
            LOWER(ls.name) IN ('películas', 'peliculas')
         OR  ls.name LIKE 'Pelic%'
         OR  ls.name LIKE 'pelic%'
      )
      AND LOWER(mp.file) LIKE '%' || LOWER(?)
    """
    cur.execute(sql, (filename,))
    rows = cur.fetchall()
    conn.close()

    # Filtra por basename exacto (ignorando mayúsculas/minúsculas)
    fname_lower = filename.lower()
    results = []
    for r in rows:
        base = os.path.basename(r["file_path"]).lower()
        if base == fname_lower:
            results.append({
                "title": r["title"],
                "original_title": r["original_title"],
                "year": r["year"],
                "guid": r["guid"],
                "studio": r["studio"],
                "content_rating": r["content_rating"],
                "rating": r["rating"],
                "added_at": r["added_at"],
                "updated_at": r["updated_at"],
                "file_path": r["file_path"],
                "size_bytes": r["size_bytes"],
                "size_gb": round((r["size_bytes"] or 0) / (1024**3), 3),
                "container": r["container"],
                "video_codec": r["video_codec"],
                "audio_codec": r["audio_codec"],
                "audio_channels": r["audio_channels"],
                "width": r["width"],
                "height": r["height"],
                "bitrate_kbps": r["bitrate"],
                "duration_hms_meta": ms_to_hms(r["meta_duration_ms"]),
                "duration_hms_part": ms_to_hms(r["part_duration_ms"]),
                "library": r["library_name"],
            })
    return results

def main():
    # Nombre por defecto hardcodeado si no se pasa argumento
    default_filename = "Disney.-.La.Leyenda.De.Sleepy.Hollow.avi"
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        filename = sys.argv[1]
    else:
        filename = default_filename
        print(f"Usando nombre por defecto: {filename}")
    db_dir = Path(PLEX_DB_DIR)
    if len(sys.argv) >= 3:
        db_path = Path(sys.argv[2])
    else:
        db_path = find_plex_db(db_dir)

    print(f"Usando BD: {db_path}")
    data = query_by_filename(db_path, filename)
    if not data:
        print("No hay coincidencias exactas por nombre de archivo.")
        sys.exit(2)

    for i, d in enumerate(data, 1):
        print(f"\n=== Resultado {i} ===")
        for k, v in d.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()