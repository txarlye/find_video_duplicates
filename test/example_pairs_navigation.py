#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de uso de las funcionalidades de navegación de pares de duplicados
"""

import streamlit as st
from src.utils.ui_components import DuplicatePairsManager

def main():
    """Función principal del ejemplo"""
    st.set_page_config(
        page_title="Gestor de Pares de Duplicados",
        page_icon="🎬",
        layout="wide"
    )
    
    # Inicializar el gestor de pares
    pairs_manager = DuplicatePairsManager()
    
    # Datos de ejemplo (en una aplicación real, estos vendrían del escaneo)
    example_pairs = [
        {
            'Ruta 1': '/movies/pelicula1.mkv',
            'Ruta 2': '/movies/pelicula1_copy.mkv',
            'Tamaño 1': 2147483648,  # 2GB
            'Tamaño 2': 2147483648,  # 2GB
            'Similitud': 95.5
        },
        {
            'Ruta 1': '/movies/pelicula2.mp4',
            'Ruta 2': '/movies/pelicula2_edition.mp4',
            'Tamaño 1': 1073741824,  # 1GB
            'Tamaño 2': 2147483648,  # 2GB
            'Similitud': 88.2
        },
        {
            'Ruta 1': '/movies/pelicula3.avi',
            'Ruta 2': '/movies/pelicula3_duplicate.avi',
            'Tamaño 1': 536870912,   # 512MB
            'Tamaño 2': 536870912,   # 512MB
            'Similitud': 92.1
        }
    ]
    
    # Establecer la lista de pares
    pairs_manager.set_pairs_list(example_pairs)
    
    # Mostrar la interfaz principal
    pairs_manager.render_main_interface()
    
    # Mostrar información adicional
    st.sidebar.title("📊 Información")
    st.sidebar.write(f"Total de pares: {pairs_manager.navigation.get_total_pairs()}")
    st.sidebar.write(f"Par actual: {pairs_manager.navigation.get_current_index() + 1}")
    
    # Botón para limpiar selecciones
    if st.sidebar.button("🗑️ Limpiar Selecciones"):
        pairs_manager.clear_all_selections()
    
    # Mostrar películas seleccionadas
    selected_movies = pairs_manager.get_selected_movies()
    if selected_movies:
        st.sidebar.subheader("🎯 Películas Seleccionadas")
        for movie in selected_movies:
            st.sidebar.write(f"Par {movie['pair_index'] + 1}, Película {movie['movie_number']}")

if __name__ == "__main__":
    main()
