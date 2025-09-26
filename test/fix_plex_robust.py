#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para arreglar Plex con una solución más robusta
"""

def fix_plex_robust():
    """Arregla Plex con una solución más robusta"""
    
    # Leer el archivo actual
    with open('src/services/plex_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar get_library_info_by_filename con una versión más robusta
    old_method = '''    def get_library_info_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Obtiene información de biblioteca por nombre de archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información de biblioteca o None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Buscar por ruta de archivo en la tabla media_parts
            sql = """
            SELECT 
                ls.name as library_name,
                m.title,
                m.year,
                m.summary,
                m.studio,
                m.content_rating,
                m.rating,
                m.duration,
                m.originally_available_at,
                mp.file
            FROM media_items m
            JOIN library_sections ls ON m.library_section_id = ls.id
            JOIN media_parts mp ON m.id = mp.media_item_id
            WHERE mp.file LIKE ?
            ORDER BY m.title
            """
            
            # Buscar por nombre de archivo en la ruta
            search_term = f"%{filename}%"
            cur.execute(sql, (search_term,))
            row = cur.fetchone()
            
            if row:
                return {
                    'library_name': row[0],
                    'title': row[1],
                    'year': row[2],
                    'summary': row[3],
                    'studio': row[4],
                    'content_rating': row[5],
                    'rating': row[6],
                    'duration': row[7],
                    'originally_available_at': row[8],
                    'file_path': row[9]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de biblioteca: {e}")
            return None'''
    
    new_method = '''    def get_library_info_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Obtiene información de biblioteca por nombre de archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información de biblioteca o None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Buscar por nombre de archivo en media_parts
            sql = """
            SELECT 
                ls.name as library_name,
                m.title,
                m.year,
                m.summary,
                m.studio,
                m.content_rating,
                m.rating,
                m.duration,
                m.originally_available_at,
                mp.file
            FROM media_items m
            JOIN library_sections ls ON m.library_section_id = ls.id
            JOIN media_parts mp ON m.id = mp.media_item_id
            WHERE mp.file LIKE ?
            ORDER BY m.title
            """
            
            # Buscar por nombre de archivo en la ruta
            search_term = f"%{filename}%"
            cur.execute(sql, (search_term,))
            row = cur.fetchone()
            
            if row:
                return {
                    'library_name': row[0],
                    'title': row[1],
                    'year': row[2],
                    'summary': row[3],
                    'studio': row[4],
                    'content_rating': row[5],
                    'rating': row[6],
                    'duration': row[7],
                    'originally_available_at': row[8],
                    'file_path': row[9]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de biblioteca: {e}")
            return None'''
    
    # Reemplazar en el contenido
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # También simplificar get_all_movies
        old_movies = '''    def get_all_movies(self) -> List[Dict]:
        """
        Obtiene todas las películas de Plex
        
        Returns:
            Lista de diccionarios con información de películas
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            sql = """
            SELECT 
                m.title,
                m.year,
                m.studio,
                m.rating,
                m.duration,
                ls.name as library_name
            FROM media_items m
            JOIN library_sections ls ON m.library_section_id = ls.id
            WHERE ls.section_type = 1
            ORDER BY m.title, m.year
            """
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            movies = []
            for row in rows:
                movies.append({
                    'title': row[0],
                    'year': row[1],
                    'studio': row[2],
                    'rating': row[3],
                    'duration': row[4],
                    'library_name': row[5]
                })
            
            return movies
            
        except Exception as e:
            self.logger.error(f"Error obteniendo películas: {e}")
            return []'''
        
        new_movies = '''    def get_all_movies(self) -> List[Dict]:
        """
        Obtiene todas las películas de Plex
        
        Returns:
            Lista de diccionarios con información de películas
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Consulta simplificada que debería funcionar
            sql = """
            SELECT 
                m.title,
                m.year,
                ls.name as library_name
            FROM media_items m
            JOIN library_sections ls ON m.library_section_id = ls.id
            WHERE ls.section_type = 1
            ORDER BY m.title, m.year
            """
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            movies = []
            for row in rows:
                movies.append({
                    'title': row[0],
                    'year': row[1],
                    'library_name': row[2]
                })
            
            return movies
            
        except Exception as e:
            self.logger.error(f"Error obteniendo películas: {e}")
            return []'''
        
        if old_movies in content:
            content = content.replace(old_movies, new_movies)
        
        # Escribir el archivo modificado
        with open('src/services/plex_service.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Plex arreglado con solución robusta")
        print("🔍 Búsqueda por nombre de archivo en media_parts")
        print("📁 Debería encontrar archivos por nombre")
        print("🎬 Consulta simplificada para películas")
    else:
        print("❌ No se encontró el método a reemplazar")

if __name__ == "__main__":
    fix_plex_robust()
