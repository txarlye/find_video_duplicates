#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componentes de interfaz de usuario reutilizables
"""

import streamlit as st
import re
import logging
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
                st.write("🟢 Misma carpeta")
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


class PairNavigationManager:
    """Gestor de navegación entre pares de duplicados"""
    
    def __init__(self, session_key: str = "pair_navigation"):
        """
        Inicializa el gestor de navegación
        
        Args:
            session_key: Clave para el estado de sesión
        """
        self.session_key = session_key
        self.logger = logging.getLogger(__name__)
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Inicializa el estado de sesión para la navegación"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'current_pair': 0,
                'total_pairs': 0,
                'pairs_list': []
            }
    
    def set_pairs_list(self, pairs_list: List[Dict[str, Any]]) -> None:
        """
        Establece la lista de pares disponibles
        
        Args:
            pairs_list: Lista de pares de duplicados
        """
        st.session_state[self.session_key]['pairs_list'] = pairs_list
        st.session_state[self.session_key]['total_pairs'] = len(pairs_list)
        if st.session_state[self.session_key]['current_pair'] >= len(pairs_list):
            st.session_state[self.session_key]['current_pair'] = 0
        
        # Guardar el total original para las métricas
        st.session_state['original_total_pairs'] = len(pairs_list)
        
        # Actualizar contadores en settings
        settings.set_total_pairs(len(pairs_list))
        settings.set_pairs_deleted(0)  # Resetear contador de eliminados
    
    def get_current_pair(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el par actual
        
        Returns:
            Diccionario con el par actual o None si no hay pares
        """
        pairs_list = st.session_state[self.session_key]['pairs_list']
        current_index = st.session_state[self.session_key]['current_pair']
        
        if not pairs_list or current_index >= len(pairs_list):
            return None
        
        return pairs_list[current_index]
    
    def get_current_index(self) -> int:
        """
        Obtiene el índice del par actual
        
        Returns:
            Índice del par actual
        """
        return st.session_state[self.session_key]['current_pair']
    
    def get_total_pairs(self) -> int:
        """
        Obtiene el total de pares
        
        Returns:
            Total de pares disponibles
        """
        return st.session_state[self.session_key]['total_pairs']
    
    def go_to_pair(self, index: int) -> None:
        """
        Va a un par específico
        
        Args:
            index: Índice del par al que ir
        """
        total_pairs = st.session_state[self.session_key]['total_pairs']
        if 0 <= index < total_pairs:
            old_index = st.session_state[self.session_key]['current_pair']
            st.session_state[self.session_key]['current_pair'] = index
            self.logger.info(f"🔄 Navegación: Cambiando de Par {old_index + 1} a Par {index + 1}")
            st.rerun()
        else:
            self.logger.warning(f"⚠️ Navegación: Índice {index} fuera de rango (0-{total_pairs-1})")
    
    def go_to_next(self) -> None:
        """Va al siguiente par"""
        current = st.session_state[self.session_key]['current_pair']
        total = st.session_state[self.session_key]['total_pairs']
        
        if total > 0:
            next_index = (current + 1) % total
            st.session_state[self.session_key]['current_pair'] = next_index
            self.logger.info(f"⏭️ Navegación: Siguiente - Par {current + 1} → Par {next_index + 1}")
            st.rerun()
        else:
            self.logger.warning("⚠️ Navegación: No hay pares disponibles para navegar")
    
    def go_to_previous(self) -> None:
        """Va al par anterior"""
        current = st.session_state[self.session_key]['current_pair']
        total = st.session_state[self.session_key]['total_pairs']
        
        if total > 0:
            prev_index = (current - 1) % total
            st.session_state[self.session_key]['current_pair'] = prev_index
            self.logger.info(f"⏮️ Navegación: Anterior - Par {current + 1} → Par {prev_index + 1}")
            st.rerun()
        else:
            self.logger.warning("⚠️ Navegación: No hay pares disponibles para navegar")
    
    def render_navigation_controls(self) -> None:
        """Renderiza los controles de navegación"""
        current_index = self.get_current_index()
        total_pairs = self.get_total_pairs()
        
        if total_pairs == 0:
            st.info("📋 No hay pares de duplicados para mostrar")
            return
        
        # Crear controles de navegación
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ Anterior", key="nav_prev", disabled=total_pairs <= 1):
                self.go_to_previous()
        
        with col2:
            st.markdown(f"**Par {current_index + 1} de {total_pairs}**")
        
        with col3:
            # Selector de par específico con nombres de archivos
            pairs_list = st.session_state[self.session_key]['pairs_list']
            pair_options = []
            for i, pair in enumerate(pairs_list):
                file1_name = Path(pair.get('Ruta 1', '')).name if pair.get('Ruta 1') else 'N/A'
                file2_name = Path(pair.get('Ruta 2', '')).name if pair.get('Ruta 2') else 'N/A'
                pair_options.append(f"Par {i+1} - [{file1_name}] [{file2_name}]")
            
            selected_pair = st.selectbox(
                "Ir a par específico:",
                options=range(total_pairs),
                index=current_index,
                format_func=lambda x: pair_options[x] if x < len(pair_options) else f"Par {x+1}",
                key="pair_selector"
            )
            
            if selected_pair != current_index:
                self.go_to_pair(selected_pair)
        
        with col4:
            if st.button("⏭️ Siguiente", key="nav_next", disabled=total_pairs <= 1):
                self.go_to_next()
        
        with col5:
            if st.button("🔄 Reiniciar", key="nav_reset"):
                self.logger.info("🔄 Navegación: Reiniciando a Par 1")
                self.go_to_pair(0)

        self._render_bulk_remove_table(pairs_list)

        # Botón para eliminar par de la lista
        if st.button("🗑️ Eliminar Par de la Lista", key="delete_pair"):
            self._delete_current_pair()

    def _render_bulk_remove_table(self, pairs_list: List[Dict[str, Any]]) -> None:
        """
        Tabla con checkbox para quitar varios pares de la lista de golpe.
        Solo saca el par de esta cola de revisión — no mueve ni borra
        ningún archivo (eso es "Eliminar Película 1/2" en cada par, más
        abajo). Útil cuando ya sabes de un vistazo, por el nombre, qué
        pares no son duplicados reales de verdad.
        """
        with st.expander(f"☑️ Quitar varios pares de la lista de golpe ({len(pairs_list)} en total)", expanded=False):
            st.caption(
                "Esto solo saca el par de esta lista de revisión, no toca "
                "ningún archivo en disco. Para borrar/mover archivos usa "
                "'Eliminar Película 1/2' en cada par."
            )

            tabla = []
            for i, pair in enumerate(pairs_list):
                file1_name = Path(pair.get('Ruta 1', '')).name if pair.get('Ruta 1') else 'N/A'
                file2_name = Path(pair.get('Ruta 2', '')).name if pair.get('Ruta 2') else 'N/A'
                tabla.append({
                    'Quitar': False,
                    'Par': i + 1,
                    'Película 1': file1_name,
                    'Película 2': file2_name,
                })

            edited = st.data_editor(
                tabla,
                column_order=['Quitar', 'Par', 'Película 1', 'Película 2'],
                disabled=['Par', 'Película 1', 'Película 2'],
                hide_index=True,
                use_container_width=True,
                key="pairs_bulk_remove_editor",
            )

            seleccionados = [i for i, fila in enumerate(edited) if fila['Quitar']]
            if seleccionados:
                if st.button(f"🗑️ Quitar {len(seleccionados)} par(es) de la lista", key="pairs_bulk_remove_btn"):
                    self._remove_pairs_from_list(seleccionados)

    def _remove_pairs_from_list(self, indices: List[int]) -> None:
        """Quita de golpe varios pares (por índice) de la lista de revisión — sin tocar archivos"""
        pairs_list = st.session_state[self.session_key]['pairs_list']
        a_quitar = set(indices)

        nueva_lista = [p for i, p in enumerate(pairs_list) if i not in a_quitar]
        quitados = len(pairs_list) - len(nueva_lista)

        st.session_state[self.session_key]['pairs_list'] = nueva_lista
        st.session_state[self.session_key]['total_pairs'] = len(nueva_lista)
        st.session_state.duplicados = nueva_lista

        settings.set_total_pairs(len(nueva_lista))

        current_index = st.session_state[self.session_key]['current_pair']
        if current_index >= len(nueva_lista) and len(nueva_lista) > 0:
            st.session_state[self.session_key]['current_pair'] = len(nueva_lista) - 1
        elif len(nueva_lista) == 0:
            st.session_state[self.session_key]['current_pair'] = 0

        self.logger.info(f"🗑️ Navegación: Quitados {quitados} pares de golpe - Quedan {len(nueva_lista)} pares")
        st.success(f"✅ {quitados} par(es) quitado(s) de la lista — quedan {len(nueva_lista)}")
        st.rerun()

    def _delete_current_pair(self) -> None:
        """Elimina el par actual de la lista"""
        current_index = self.get_current_index()
        pairs_list = st.session_state[self.session_key]['pairs_list']
        
        if 0 <= current_index < len(pairs_list):
            # Obtener información del par antes de eliminarlo
            pair_data = pairs_list[current_index]
            file1_name = Path(pair_data.get('Ruta 1', '')).name if pair_data.get('Ruta 1') else 'N/A'
            file2_name = Path(pair_data.get('Ruta 2', '')).name if pair_data.get('Ruta 2') else 'N/A'
            
            # Eliminar el par de la lista
            del pairs_list[current_index]
            st.session_state[self.session_key]['pairs_list'] = pairs_list
            st.session_state[self.session_key]['total_pairs'] = len(pairs_list)
            
            # ACTUALIZAR st.session_state.duplicados para que se refleje en la interfaz
            st.session_state.duplicados = pairs_list
            self.logger.info(f"🔄 Actualizado st.session_state.duplicados: {len(pairs_list)} pares")
            
            # Actualizar contadores en settings
            # No incrementar eliminados, solo actualizar el total
            settings.set_total_pairs(len(pairs_list))
            remaining_pairs = len(pairs_list)
            self.logger.info(f"📊 Contadores actualizados: total={settings.get_total_pairs()}, restantes={remaining_pairs}")
            
            # Ajustar índice actual si es necesario
            if current_index >= len(pairs_list) and len(pairs_list) > 0:
                st.session_state[self.session_key]['current_pair'] = len(pairs_list) - 1
            elif len(pairs_list) == 0:
                st.session_state[self.session_key]['current_pair'] = 0
            
            self.logger.info(f"🗑️ Navegación: Eliminado Par {current_index + 1} - [{file1_name}] [{file2_name}] - Quedan {remaining_pairs} pares")
            
            # Mostrar confirmación visual
            st.success(f"✅ Par {current_index + 1} eliminado - Quedan {remaining_pairs} pares")
            
            st.rerun()
        else:
            self.logger.warning(f"⚠️ Navegación: No se puede eliminar - índice {current_index} fuera de rango")
    
    def render_pair_info(self, pair_data: Dict[str, Any]) -> None:
        """
        Renderiza la información del par actual
        
        Args:
            pair_data: Datos del par de duplicados
        """
        if not pair_data:
            st.warning("⚠️ No hay datos del par disponible")
            return
        
        st.markdown("---")
        st.subheader(f"🎬 Par {self.get_current_index() + 1}: Información Básica")
        
        # Mostrar información básica del par
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            if 'Ruta 1' in pair_data:
                filename1 = Path(pair_data['Ruta 1']).name
                st.write(f"📁 {filename1}")
                st.write(f"📊 Tamaño: {pair_data.get('Tamaño 1 (GB)', 'N/A')} GB")
                st.write(f"⏱️ Duración: {pair_data.get('Duración 1', 'N/A')}")

        with col2:
            st.write("**Película 2:**")
            if 'Ruta 2' in pair_data:
                filename2 = Path(pair_data['Ruta 2']).name
                st.write(f"📁 {filename2}")
                st.write(f"📊 Tamaño: {pair_data.get('Tamaño 2 (GB)', 'N/A')} GB")
                st.write(f"⏱️ Duración: {pair_data.get('Duración 2', 'N/A')}")


class PairListManager:
    """Gestor para mostrar y seleccionar pares de duplicados"""
    
    def __init__(self, session_key: str = "pair_list"):
        """
        Inicializa el gestor de lista de pares
        
        Args:
            session_key: Clave para el estado de sesión
        """
        self.session_key = session_key
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Inicializa el estado de sesión para la lista de pares"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'pairs_list': [],
                'selected_pairs': [],
                'filter_options': {
                    'show_only_plex_found': False,
                    'show_only_different_sizes': False,
                    'min_size_difference': 0
                }
            }
    
    def set_pairs_list(self, pairs_list: List[Dict[str, Any]]) -> None:
        """
        Establece la lista de pares
        
        Args:
            pairs_list: Lista de pares de duplicados
        """
        st.session_state[self.session_key]['pairs_list'] = pairs_list
    
    def get_pairs_list(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de pares
        
        Returns:
            Lista de pares de duplicados
        """
        return st.session_state[self.session_key]['pairs_list']
    
    def render_pairs_summary(self) -> None:
        """Renderiza un resumen de los pares encontrados"""
        pairs_list = self.get_pairs_list()
        
        if not pairs_list:
            st.info("📋 No se encontraron pares de duplicados")
            return
        
        # Usar valores actuales
        remaining_pairs = len(pairs_list)  # Usar la lista actual
        
        # Obtener el total original desde session_state si está disponible
        original_total = st.session_state.get('original_total_pairs', remaining_pairs)
        
        st.success(f"🎯 **{remaining_pairs} pares de duplicados encontrados**")
        
        # Mostrar estadísticas básicas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de pares", original_total)
        
        with col2:
            st.metric("Pares restantes", remaining_pairs)
        
        with col3:
            st.metric("Pares eliminados", original_total - remaining_pairs)
        
        # Calcular pares con diferentes tamaños
        def _tamaño_gb(pair: Dict[str, Any], num: int) -> float:
            try:
                return float(pair.get(f'Tamaño {num} (GB)', 0))
            except (TypeError, ValueError):
                return 0.0

        different_sizes = 0
        for pair in pairs_list:
            size1 = _tamaño_gb(pair, 1)
            size2 = _tamaño_gb(pair, 2)
            if size1 and size2 and size1 != size2:
                different_sizes += 1
        
        # Mostrar métricas adicionales
        st.write(f"📊 **Tamaños diferentes:** {different_sizes}")
        st.write(f"📊 **Tamaños similares:** {len(pairs_list) - different_sizes}")
    
    def render_pairs_table(self) -> None:
        """Renderiza una tabla con los pares encontrados"""
        pairs_list = self.get_pairs_list()
        
        if not pairs_list:
            return
        
        st.subheader("📋 Lista de Pares de Duplicados")
        
        # Crear tabla de pares
        for i, pair in enumerate(pairs_list):
            with st.expander(f"Par {i+1}: {Path(pair.get('Ruta 1', '')).name} vs {Path(pair.get('Ruta 2', '')).name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Película 1:**")
                    st.write(f"📁 {Path(pair.get('Ruta 1', '')).name}")
                    st.write(f"📊 Tamaño: {pair.get('Tamaño 1 (GB)', 'N/A')} GB")
                    st.write(f"⏱️ Duración: {pair.get('Duración 1', 'N/A')}")

                with col2:
                    st.write("**Película 2:**")
                    st.write(f"📁 {Path(pair.get('Ruta 2', '')).name}")
                    st.write(f"📊 Tamaño: {pair.get('Tamaño 2 (GB)', 'N/A')} GB")
                    st.write(f"⏱️ Duración: {pair.get('Duración 2', 'N/A')}")
                
                # Botón para ir a este par
                if st.button(f"🎯 Ir a Par {i+1}", key=f"go_to_pair_{i}"):
                    # Aquí se implementaría la navegación al par específico
                    st.session_state['selected_pair_index'] = i
                    st.rerun()


class PairDetailViewer:
    """Visor detallado para un par específico de duplicados"""
    
    def __init__(self, session_key: str = "pair_detail"):
        """
        Inicializa el visor de detalles
        
        Args:
            session_key: Clave para el estado de sesión
        """
        self.session_key = session_key
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Inicializa el estado de sesión para el visor de detalles"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'current_pair_data': None,
                'show_plex_analysis': True,
                'show_video_players': True,
                'show_edition_options': True
            }
    
    def set_current_pair(self, pair_data: Dict[str, Any]) -> None:
        """
        Establece el par actual para mostrar
        
        Args:
            pair_data: Datos del par de duplicados
        """
        st.session_state[self.session_key]['current_pair_data'] = pair_data
    
    def get_current_pair(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el par actual
        
        Returns:
            Datos del par actual o None
        """
        return st.session_state[self.session_key]['current_pair_data']
    
    def render_pair_header(self, pair_index: int, total_pairs: int) -> None:
        """
        Renderiza el encabezado del par
        
        Args:
            pair_index: Índice del par actual
            total_pairs: Total de pares
        """
        st.markdown("---")
        st.subheader(f"🎬 Par {pair_index + 1} de {total_pairs}")
        
        # Mostrar información básica
        pair_data = self.get_current_pair()
        if not pair_data:
            st.warning("⚠️ No hay datos del par disponible")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            if 'Ruta 1' in pair_data:
                filename1 = Path(pair_data['Ruta 1']).name
                st.write(f"📁 {filename1}")
                st.write(f"📊 Tamaño: {pair_data.get('Tamaño 1 (GB)', 'N/A')} GB")
                st.write(f"⏱️ Duración: {pair_data.get('Duración 1', 'N/A')}")

        with col2:
            st.write("**Película 2:**")
            if 'Ruta 2' in pair_data:
                filename2 = Path(pair_data['Ruta 2']).name
                st.write(f"📁 {filename2}")
                st.write(f"📊 Tamaño: {pair_data.get('Tamaño 2 (GB)', 'N/A')} GB")
                st.write(f"⏱️ Duración: {pair_data.get('Duración 2', 'N/A')}")
    
    def render_analysis_options(self) -> None:
        """Renderiza las opciones de análisis (simplificado)"""
        # Opciones de análisis se manejan en la aplicación principal
        pass
    
    def render_quick_actions(self, pair_index: int) -> None:
        """
        Renderiza acciones rápidas para el par
        
        Args:
            pair_index: Índice del par actual
        """
        st.subheader("⚡ Acciones Rápidas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ Eliminar Película 1", key=f"delete_1_{pair_index}"):
                st.warning("⚠️ Función de eliminación no implementada")
        
        with col2:
            if st.button("🗑️ Eliminar Película 2", key=f"delete_2_{pair_index}"):
                st.warning("⚠️ Función de eliminación no implementada")
        
        with col3:
            if st.button("📝 Renombrar Película 1", key=f"rename_1_{pair_index}"):
                st.info("💡 Función de renombrado no implementada")
        
        with col4:
            if st.button("📝 Renombrar Película 2", key=f"rename_2_{pair_index}"):
                st.info("💡 Función de renombrado no implementada")
    
    def render_pair_summary(self) -> None:
        """Renderiza un resumen del par actual (simplificado)"""
        # Resumen se maneja en la aplicación principal
        pass


class DuplicatePairsManager:
    """Gestor principal para la gestión de pares de duplicados"""
    
    def __init__(self):
        """Inicializa el gestor principal"""
        self.navigation = PairNavigationManager()
        self.list_manager = PairListManager()
        self.detail_viewer = PairDetailViewer()
        self.selection_manager = SelectionManager()
    
    def set_pairs_list(self, pairs_list: List[Dict[str, Any]]) -> None:
        """
        Establece la lista de pares en todos los gestores
        
        Args:
            pairs_list: Lista de pares de duplicados
        """
        self.navigation.set_pairs_list(pairs_list)
        self.list_manager.set_pairs_list(pairs_list)
    
    def render_main_interface(self) -> None:
        """Renderiza la interfaz principal de gestión de pares"""
        st.title("🎬 Gestor de Pares de Duplicados")
        
        # Mostrar resumen de pares
        self.list_manager.render_pairs_summary()
        
        # Mostrar controles de navegación
        self.navigation.render_navigation_controls()
        
        # Obtener par actual
        current_pair = self.navigation.get_current_pair()
        if current_pair:
            # Establecer par actual en el visor de detalles
            self.detail_viewer.set_current_pair(current_pair)
            
            # Mostrar información del par actual
            current_index = self.navigation.get_current_index()
            total_pairs = self.navigation.get_total_pairs()
            
            self.detail_viewer.render_pair_header(current_index, total_pairs)
        else:
            st.info("📋 No hay pares de duplicados para mostrar")
    
    def _render_specific_analysis(self, pair_data: Dict[str, Any], pair_index: int) -> None:
        """
        Renderiza el análisis específico según las opciones seleccionadas
        
        Args:
            pair_data: Datos del par de duplicados
            pair_index: Índice del par actual
        """
        # Solo mostrar análisis si es necesario (se implementará en la aplicación principal)
        pass
    
    def render_pairs_list_view(self) -> None:
        """Renderiza la vista de lista de pares"""
        st.title("📋 Lista de Pares de Duplicados")
        
        # Mostrar tabla de pares
        self.list_manager.render_pairs_table()
    
    def get_selected_movies(self) -> List[Dict[str, Any]]:
        """
        Obtiene las películas seleccionadas
        
        Returns:
            Lista de películas seleccionadas
        """
        return self.selection_manager.get_selected_movies(
            self.navigation.get_total_pairs()
        )
    
    def clear_all_selections(self) -> None:
        """Limpia todas las selecciones"""
        self.selection_manager.clear_selections()
        st.rerun()