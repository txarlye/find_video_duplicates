#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para PLEX
"""

import sys
import os
sys.path.append('.')

from src.services.plex.plex_service import PlexService
from src.settings.settings import Settings

def main():
    print("🔍 Diagnóstico de PLEX")
    print("=" * 50)
    
    # Cargar configuración
    settings = Settings()
    plex_user = settings.get_plex_user()
    plex_pass = settings.get_plex_pass()
    plex_token = settings.get_plex_token()
    
    print(f"PLEX_USER: {plex_user}")
    print(f"PLEX_PASS: {plex_pass}")
    print(f"PLEX_TOKEN: {plex_token[:10]}..." if plex_token else "PLEX_TOKEN: None")
    
    # Probar conexión
    print("\n🔗 Probando conexión con PLEX...")
    plex_service = PlexService()
    
    if plex_service.connect():
        print("✅ PLEX conectado")
        
        # Obtener bibliotecas
        libraries = plex_service.get_libraries()
        print(f"📚 Bibliotecas encontradas: {len(libraries)}")
        
        for lib in libraries:
            print(f"  - {lib.get('title')} (ID: {lib.get('id')}, Tipo: {lib.get('type')})")
        
        # Buscar bibliotecas de películas
        movie_libs = [lib for lib in libraries if lib.get('type') == 'movie']
        print(f"\n🎬 Bibliotecas de películas: {len(movie_libs)}")
        
        for lib in movie_libs:
            print(f"  - {lib.get('title')} (ID: {lib.get('id')})")
            
            # Probar obtener duplicados
            try:
                print(f"    🔍 Buscando duplicados en {lib.get('title')}...")
                duplicates = plex_service.get_duplicates_from_library(lib.get('id'))
                print(f"    ✅ Duplicados encontrados: {len(duplicates)}")
                
                if duplicates:
                    print(f"    📊 Primeros 3 grupos de duplicados:")
                    for i, dup_group in enumerate(duplicates[:3]):
                        print(f"      Grupo {i+1}: {len(dup_group.get('movies', []))} películas")
                        for j, movie in enumerate(dup_group.get('movies', [])[:2]):
                            print(f"        - {movie.get('title')} ({movie.get('year')})")
                
            except Exception as e:
                print(f"    ❌ Error obteniendo duplicados: {e}")
    else:
        print("❌ PLEX no conectado")
        print("💡 Verifica que PLEX esté ejecutándose y las credenciales sean correctas")

if __name__ == "__main__":
    main()
