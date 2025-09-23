#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componentes de interfaz de usuario reutilizables
"""

import streamlit as st
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.settings.settings import settings


class UIComponents:
    """Clase para componentes de interfaz reutilizables"""
    
    @staticmethod
    def render_movie_title(title: str, color: str = "#1f77b4", size: str = "h3") -> None:
        """
        Renderiza un título de película con estilo
        
        Args:
            title: Título de la película
            color: Color del título
            size: Tamaño del título (h3, h4, etc.)
        """
        st.markdown(f"<{size} style='color: {color}; margin-bottom: 10px;'>🎬 {title}</{size}>", unsafe_allow_html=True)
    
    @staticmethod
    def render_separator_line() -> None:
        """Renderiza una línea separadora gruesa"""
        st.markdown("""
        <div style="border-top: 3px solid #ff6b6b; margin: 20px 0; padding: 10px 0;">
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_navigation_controls(current: int, total: int) -> int:
        """
        Renderiza controles de navegación
        
        Args:
            current: Página actual
            total: Total de páginas
            
        Returns:
            int: Nueva página seleccionada
        """
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 2, 1, 1])
        
        with col_nav1:
            if st.button("⬅️ Anterior", disabled=current == 0, key=f"prev_{current}"):
                return max(0, current - 1)
        
        with col_nav2:
            st.markdown(f"**Par {current + 1} de {total}**")
        
        with col_nav3:
            if st.button("Siguiente ➡️", disabled=current >= total - 1, key=f"next_{current}"):
                return min(total - 1, current + 1)
        
        with col_nav4:
            if st.button("🔄 Reiniciar", key=f"reset_{current}"):
                return 0
        
        return current
    
    @staticmethod
    def render_selection_summary(selections: Dict[str, bool]) -> None:
        """
        Renderiza resumen de selecciones
        
        Args:
            selections: Diccionario de selecciones
        """
        selected_count = sum(1 for v in selections.values() if v)
        
        if selected_count > 0:
            st.success(f"✅ {selected_count} película(s) seleccionada(s)")
        else:
            st.info("ℹ️ Selecciona películas para procesar")


class MovieInfoDisplay:
    """Clase para mostrar información de películas"""
    
    def __init__(self):
        self.ui = UIComponents()
    
    def render_movie_comparison(self, row: Dict[str, Any], index: int) -> None:
        """
        Renderiza comparación de dos películas
        
        Args:
            row: Datos de la fila con información de ambas películas
            index: Índice del par
        """
        # Títulos con colores diferentes
        col_video1, col_video2 = st.columns(2)
        
        with col_video1:
            self.ui.render_movie_title(row['Peli 1'], "#1f77b4", "h3")
            st.write(f"📊 Tamaño: {row['Tamaño 1 (GB)']} GB")
            st.write(f"⏱️ Duración: {row['Duración 1']}")
        
        with col_video2:
            self.ui.render_movie_title(row['Peli 2'], "#ff7f0e", "h3")
            st.write(f"📊 Tamaño: {row['Tamaño 2 (GB)']} GB")
            st.write(f"⏱️ Duración: {row['Duración 2']}")
    
    def render_similarity_analysis(self, row: Dict[str, Any]) -> None:
        """
        Renderiza análisis de similitud
        
        Args:
            row: Datos de la fila con información de ambas películas
        """
        st.subheader("🔍 Análisis de Similitud")
        
        col_analysis1, col_analysis2 = st.columns(2)
        
        with col_analysis1:
            st.write("**📊 Comparación de Tamaños:**")
            size1 = float(row['Tamaño 1 (GB)'].replace(' GB', ''))
            size2 = float(row['Tamaño 2 (GB)'].replace(' GB', ''))
            
            if size1 > size2:
                diferencia = ((size1 - size2) / size1) * 100
                st.write(f"🔴 Video 1 es {diferencia:.1f}% más grande")
            elif size2 > size1:
                diferencia = ((size2 - size1) / size2) * 100
                st.write(f"🔴 Video 2 es {diferencia:.1f}% más grande")
            else:
                st.write("🟢 Mismo tamaño")
        
        with col_analysis2:
            st.write("**📁 Comparación de Rutas:**")
            ruta1 = Path(row['Ruta 1']).parent
            ruta2 = Path(row['Ruta 2']).parent
            
            if ruta1 == ruta2:
                st.write("🟢 Carpeta duplicada")
            else:
                st.write("🔴 Carpetas diferentes")
                st.write(f"📁 1: {ruta1}")
                st.write(f"📁 2: {ruta2}")
        
        # Comparación de duración
        self._render_duration_comparison(row)
    
    def _render_duration_comparison(self, row: Dict[str, Any]) -> None:
        """Renderiza comparación de duración"""
        st.write("**⏱️ Comparación de Duración:**")
        duracion1_str = row['Duración 1']
        duracion2_str = row['Duración 2']
        
        if duracion1_str != "N/A" and duracion2_str != "N/A":
            # Extraer duración en segundos para comparación
            def parsear_duracion(duracion_str):
                if duracion_str == "N/A":
                    return 0
                # Formato: "1h 30m 45s" o "30m 45s"
                match = re.match(r'(?:(\d+)h\s+)?(?:(\d+)m\s+)?(?:(\d+)s)?', duracion_str)
                if match:
                    horas = int(match.group(1) or 0)
                    minutos = int(match.group(2) or 0)
                    segundos = int(match.group(3) or 0)
                    return horas * 3600 + minutos * 60 + segundos
                return 0
            
            dur1 = parsear_duracion(duracion1_str)
            dur2 = parsear_duracion(duracion2_str)
            
            if dur1 > 0 and dur2 > 0:
                diferencia_segundos = abs(dur1 - dur2)
                diferencia_minutos = diferencia_segundos / 60
                
                if diferencia_minutos <= 2:
                    st.write("🟢 Duración muy similar")
                elif diferencia_minutos <= 5:
                    st.write("🟡 Duración similar")
                else:
                    st.write("🔴 Duración muy diferente")
                
                st.write(f"📊 Diferencia: {diferencia_minutos:.1f} minutos")
            else:
                st.write("⚠️ No se pudo comparar duración")
        else:
            st.write("⚠️ Duración no disponible")


class SelectionManager:
    """Clase para manejar selecciones de películas"""
    
    def __init__(self):
        self.session_key = 'selecciones'
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}
    
    def get_selection_key(self, movie_index: int, movie_number: int) -> str:
        """Obtiene la clave de selección para una película"""
        return f"peli{movie_number}_{movie_index}"
    
    def is_selected(self, movie_index: int, movie_number: int) -> bool:
        """Verifica si una película está seleccionada"""
        key = self.get_selection_key(movie_index, movie_number)
        return st.session_state[self.session_key].get(key, False)
    
    def set_selection(self, movie_index: int, movie_number: int, selected: bool) -> None:
        """Establece la selección de una película"""
        key = self.get_selection_key(movie_index, movie_number)
        st.session_state[self.session_key][key] = selected
    
    def render_selection_checkbox(self, movie_index: int, movie_number: int, 
                                movie_title: str) -> bool:
        """
        Renderiza un checkbox de selección
        
        Args:
            movie_index: Índice del par
            movie_number: Número de película (1 o 2)
            movie_title: Título de la película
            
        Returns:
            bool: True si está seleccionada
        """
        key = self.get_selection_key(movie_index, movie_number)
        label = f"Seleccionar Película {movie_number}"
        
        checkbox = st.checkbox(
            label,
            key=key,
            value=self.is_selected(movie_index, movie_number)
        )
        
        if checkbox:
            self.set_selection(movie_index, movie_number, True)
            # Desmarcar la otra película del mismo par
            other_movie = 2 if movie_number == 1 else 1
            self.set_selection(movie_index, other_movie, False)
        else:
            self.set_selection(movie_index, movie_number, False)
        
        return checkbox
    
    def get_selected_movies(self, total_pairs: int) -> List[Dict[str, Any]]:
        """
        Obtiene lista de películas seleccionadas
        
        Args:
            total_pairs: Total de pares de duplicados
            
        Returns:
            List[Dict]: Lista de películas seleccionadas con sus rutas
        """
        selected = []
        for i in range(total_pairs):
            for movie_num in [1, 2]:
                if self.is_selected(i, movie_num):
                    selected.append({
                        'pair_index': i,
                        'movie_number': movie_num,
                        'key': self.get_selection_key(i, movie_num)
                    })
        return selected
    
    def clear_selections(self) -> None:
        """Limpia todas las selecciones"""
        st.session_state[self.session_key] = {}
