#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor principal de la aplicación Streamlit
"""

import streamlit as st
import sys
import time
import os
from pathlib import Path
from typing import List, Dict, Any

# Configurar el path
current_dir = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(current_dir))

from src.settings.settings import settings
from src.utils.movie_detector import MovieDetector
from src.utils.video import VideoPlayer, VideoFormatter, VideoComparison
from src.utils.ui_components import UIComponents, MovieInfoDisplay, SelectionManager
from src.utils.file_operations import FileBatchProcessor


class StreamlitAppManager:
    """Gestor principal de la aplicación Streamlit"""
    
    def __init__(self):
        self.video_player = VideoPlayer()
        self.video_formatter = VideoFormatter()
        self.video_comparison = VideoComparison()
        self.ui_components = UIComponents()
        self.movie_display = MovieInfoDisplay()
        self.selection_manager = SelectionManager()
        self.file_processor = FileBatchProcessor()
        
        # Inicializar estado de sesión
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Inicializa el estado de la sesión"""
        if 'peliculas' not in st.session_state:
            st.session_state.peliculas = []
        if 'duplicados' not in st.session_state:
            st.session_state.duplicados = []
        if 'detector' not in st.session_state:
            st.session_state.detector = None
        if 'scanning' not in st.session_state:
            st.session_state.scanning = False
        if 'par_actual' not in st.session_state:
            st.session_state.par_actual = 0
    
    def render_header(self):
        """Renderiza el encabezado de la aplicación"""
        st.title("🎬 Detector de Películas Duplicadas")
        st.markdown("---")
        
        # Aclaración importante
        st.info("⚠️ **IMPORTANTE:** Esta aplicación NUNCA borra archivos. Solo detecta y muestra duplicados para que puedas decidir qué hacer con ellos.")
        st.markdown("---")
    
    def render_sidebar(self):
        """Renderiza el sidebar con configuración"""
        with st.sidebar:
            st.header("⚙️ Configuración")
            
            # Pestañas en el sidebar
            tab1, tab2 = st.tabs(["🔍 Detección", "⚙️ Configuración"])
            
            with tab1:
                self._render_detection_tab()
            
            with tab2:
                self._render_configuration_tab()
    
    def _render_detection_tab(self):
        """Renderiza la pestaña de detección"""
        # Umbral de similitud
        umbral = st.slider(
            "Umbral de similitud",
            min_value=0.1,
            max_value=1.0,
            value=settings.get_similarity_threshold(),
            step=0.1,
            help="Umbral para considerar películas como duplicadas"
        )
        
        st.write(f"Umbral configurado: {umbral}")
        st.markdown("---")
        
        # Filtro por duración
        st.subheader("🎬 Filtro por Duración")
        
        # Activar filtro por duración
        filtro_duracion = st.checkbox(
            "🔍 Filtrar por duración",
            value=settings.get_duration_filter_enabled(),
            help="Descartar duplicados si la diferencia de duración es muy grande"
        )
        
        # Tolerancia de duración
        if filtro_duracion:
            tolerancia = st.slider(
                "Tolerancia de duración (minutos)",
                min_value=1,
                max_value=30,
                value=settings.get_duration_tolerance_minutes(),
                step=1,
                help="Diferencia máxima en minutos permitida entre duplicados"
            )
            
            st.write(f"Tolerancia: {tolerancia} minutos")
            
            if st.button("💾 Guardar filtro duración", key="save_duration_filter"):
                settings.set_duration_filter_enabled(filtro_duracion)
                settings.set_duration_tolerance_minutes(tolerancia)
                st.success("✅ Filtro de duración guardado")
    
    def _render_configuration_tab(self):
        """Renderiza la pestaña de configuración"""
        st.subheader("🎬 Reproductores de Video")
        
        # Mostrar reproductores de video
        show_players = st.checkbox(
            "🎬 Mostrar Reproductores de Video",
            value=settings.get_show_video_players(),
            help="Mostrar reproductores embebidos para comparar duplicados"
        )
        
        # Reproductores embebidos
        show_embedded = st.checkbox(
            "📺 Mostrar Reproductores Embebidos",
            value=settings.get_show_embedded_players(),
            help="Mostrar reproductores embebidos de Streamlit (más lento pero integrado)"
        )
        
        # Tamaño de reproductores
        player_size = st.selectbox(
            "📏 Tamaño de Reproductores",
            options=["small", "medium", "large"],
            index=["small", "medium", "large"].index(settings.get_video_player_size()),
            help="Tamaño de los reproductores de video"
        )
        
        # Tiempo de inicio para reproductores embebidos
        start_time_minutes = st.slider(
            "⏱️ Minuto de inicio para comparación",
            min_value=1,
            max_value=60,
            value=settings.get_video_start_time_seconds() // 60,
            step=1,
            help="Minuto desde el cual empezar a reproducir para comparar duplicados"
        )
        
        if st.button("💾 Guardar configuración reproductores", key="save_players_config"):
            settings.set_show_video_players(show_players)
            settings.set_show_embedded_players(show_embedded)
            settings.set_video_player_size(player_size)
            settings.set_video_start_time_seconds(start_time_minutes * 60)
            st.success("✅ Configuración de reproductores guardada")
        
        st.markdown("---")
        
        # Configuración de Debug
        st.subheader("🐛 Modo Debug")
        
        # Modo debug
        debug_enabled = st.checkbox(
            "🐛 Activar Modo Debug",
            value=settings.get_debug_enabled(),
            help="En modo debug, los archivos se mueven a una carpeta en lugar de borrarse"
        )
        
        # Carpeta de debug
        debug_folder = st.text_input(
            "📁 Carpeta de Debug",
            value=settings.get_debug_folder(),
            help="Carpeta donde se moverán los archivos en modo debug"
        )
        
        if st.button("💾 Guardar configuración debug", key="save_debug_config"):
            settings.set_debug_enabled(debug_enabled)
            settings.set_debug_folder(debug_folder)
            st.success("✅ Configuración de debug guardada")
    
    def render_scan_section(self):
        """Renderiza la sección de escaneo"""
        st.header("📁 Escanear Carpeta")
        
        # Input de carpeta
        try:
            last_path = settings.get_last_scan_path()
        except AttributeError:
            last_path = settings.get("paths.last_scan_path", "")
        
        carpeta = st.text_input(
            "Ruta de la carpeta a analizar",
            value=last_path,
            help="Seleccione la carpeta que contiene las películas"
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            scan_button = st.button("🔍 Escanear", type="primary", disabled=st.session_state.scanning)
        
        with col2:
            if st.button("🔄 Limpiar"):
                st.session_state.peliculas = []
                st.session_state.duplicados = []
                st.session_state.detector = None
                st.rerun()
        
        # Procesar escaneo
        if scan_button and carpeta:
            st.write("🔍 Botón presionado, iniciando escaneo...")
            self._process_scan(carpeta)
        elif scan_button and not carpeta:
            st.error("❌ Por favor, especifica una carpeta para escanear")
    
    def _process_scan(self, carpeta: str):
        """Procesa el escaneo de la carpeta"""
        if not Path(carpeta).exists():
            st.error("❌ La carpeta especificada no existe")
            return
        
        st.session_state.scanning = True
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔍 Iniciando escaneo...")
            progress_bar.progress(10)
            
            st.info(f"📁 Escaneando carpeta: {carpeta}")
            
            detector = MovieDetector(carpeta)
            st.session_state.detector = detector
            
            status_text.text("📁 Escaneando archivos...")
            progress_bar.progress(30)
            
            # Crear miniterminal para mostrar archivos
            st.write("**🔍 Miniterminal - Archivos encontrados:**")
            terminal_placeholder = st.empty()
            terminal_content = []
            
            def mostrar_archivo(archivo):
                nombre_archivo = Path(archivo).name
                terminal_content.append(f"🎬 {nombre_archivo}")
                terminal_placeholder.code("\n".join(terminal_content[-15:]), language="text")
            
            detector.mostrar_archivo = mostrar_archivo
            
            st.write("🔍 Iniciando escaneo de archivos...")
            peliculas = detector.escanear_carpeta()
            st.write(f"✅ Escaneo completado. Encontradas {len(peliculas)} películas")
            st.session_state.peliculas = peliculas
            
            progress_bar.progress(60)
            status_text.text("🔍 Buscando duplicados...")
            
            duplicados = detector.encontrar_duplicados()
            st.session_state.duplicados = duplicados
            
            progress_bar.progress(100)
            status_text.text("✅ Escaneo completado")
            
            st.success(f"✅ Encontradas {len(peliculas)} películas")
            st.success(f"🔍 Encontrados {len(duplicados)} grupos de duplicados")
            
            # Guardar ruta de escaneo
            try:
                settings.set_last_scan_path(carpeta)
            except AttributeError:
                # Si el método no existe, usar el método genérico
                settings.set("paths.last_scan_path", carpeta)
            
        except Exception as e:
            st.error(f"❌ Error durante el escaneo: {e}")
        finally:
            st.session_state.scanning = False
    
    def render_results(self):
        """Renderiza los resultados del escaneo"""
        if not st.session_state.peliculas:
            return
        
        # Métricas
        total_peliculas = len(st.session_state.peliculas)
        total_duplicados = len(st.session_state.duplicados)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Total Películas", total_peliculas)
        with col2:
            st.metric("🔍 Duplicados Encontrados", total_duplicados)
        with col3:
            if total_duplicados > 0:
                espacio_ahorrado = sum(
                    min(duplicado[0].get('tamaño', 0), duplicado[1].get('tamaño', 0)) 
                    for duplicado in st.session_state.duplicados
                ) / (1024**3)
                st.metric("💾 Espacio Ahorrable (GB)", f"{espacio_ahorrado:.1f} GB)")
        
        st.markdown("---")
        
        # Mostrar duplicados
        if st.session_state.duplicados:
            self._render_duplicates()
    
    def _render_duplicates(self):
        """Renderiza la lista de duplicados"""
        # Crear datos para el DataFrame
        df_data = self._create_dataframe_data()
        
        if not df_data:
            st.warning("⚠️ No hay datos de duplicados para mostrar")
            return
        
        # Mostrar resumen de selecciones
        self.ui_components.render_selection_summary(st.session_state.selecciones)
        
        # Botón de mover archivos seleccionados
        self._render_bulk_operations(df_data)
        
        # Sistema de paginación
        total_pares = len(df_data)
        
        # Controles de navegación
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 2, 1, 1])
        
        with col_nav1:
            if st.button("⬅️ Anterior", disabled=st.session_state.par_actual == 0, key=f"prev_{st.session_state.par_actual}"):
                if st.session_state.par_actual > 0:
                    st.session_state.par_actual -= 1
                    st.rerun()
        
        with col_nav2:
            st.markdown(f"**Par {st.session_state.par_actual + 1} de {total_pares}**")
        
        with col_nav3:
            if st.button("Siguiente ➡️", disabled=st.session_state.par_actual >= total_pares - 1, key=f"next_{st.session_state.par_actual}"):
                if st.session_state.par_actual < total_pares - 1:
                    st.session_state.par_actual += 1
                    st.rerun()
        
        with col_nav4:
            if st.button("🔄 Reiniciar", key=f"reset_{st.session_state.par_actual}"):
                st.session_state.par_actual = 0
                st.rerun()
        
        st.markdown("---")
        
        # Mostrar par actual
        if st.session_state.par_actual < total_pares:
            self._render_current_pair(df_data, st.session_state.par_actual)
    
    def _create_dataframe_data(self) -> List[Dict[str, Any]]:
        """Crea los datos para el DataFrame"""
        df_data = []
        
        for i, duplicado in enumerate(st.session_state.duplicados):
            # Verificar si es una lista o un diccionario
            if isinstance(duplicado, list) and len(duplicado) >= 2:
                archivo1, archivo2 = duplicado[0], duplicado[1]
            elif isinstance(duplicado, dict):
                # Si ya es un diccionario, usar directamente
                archivo1 = duplicado.get('archivo1', {})
                archivo2 = duplicado.get('archivo2', {})
            else:
                continue
            
            # Extraer información del archivo 1
            if archivo1 and isinstance(archivo1, dict):
                ruta1 = archivo1.get('archivo', '')
                nombre1 = archivo1.get('nombre', 'N/A')
                tamaño1 = archivo1.get('tamaño', 0) / (1024**3)
                duracion1 = archivo1.get('duracion', 0)
            else:
                nombre1 = str(archivo1) if archivo1 else "N/A"
                tamaño1 = 0
                ruta1 = "N/A"
                duracion1 = 0
            
            # Extraer información del archivo 2
            if archivo2 and isinstance(archivo2, dict):
                ruta2 = archivo2.get('archivo', '')
                nombre2 = archivo2.get('nombre', 'N/A')
                tamaño2 = archivo2.get('tamaño', 0) / (1024**3)
                duracion2 = archivo2.get('duracion', 0)
            else:
                nombre2 = str(archivo2) if archivo2 else "N/A"
                tamaño2 = 0
                ruta2 = "N/A"
                duracion2 = 0
            
            # Formatear duración
            def format_duration(seconds):
                if seconds == 0:
                    return "N/A"
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                seconds = int(seconds % 60)
                return f"{hours}h {minutes}m {seconds}s"
            
            # Agregar fila al DataFrame
            df_data.append({
                'Peli 1': nombre1,
                'Tamaño 1 (GB)': f"{tamaño1:.2f}",
                'Duración 1': format_duration(duracion1),
                'Ruta 1': ruta1,
                'Peli 2': nombre2,
                'Tamaño 2 (GB)': f"{tamaño2:.2f}",
                'Duración 2': format_duration(duracion2),
                'Ruta 2': ruta2
            })
        
        return df_data
    
    def _render_bulk_operations(self, df_data: List[Dict[str, Any]]):
        """Renderiza operaciones en lote"""
        # Contar selecciones
        seleccionadas = sum(1 for v in st.session_state.selecciones.values() if v)
        
        if seleccionadas > 0:
            st.subheader("📁 Mover Archivos Seleccionados")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                carpeta_destino = st.text_input(
                    "Carpeta de destino",
                    value="C:\\Movies\\Seleccionadas\\",
                    help="Ruta donde se moverán los archivos seleccionados"
                )
            
            with col2:
                st.write("")  # Espaciado
                if st.button("📁 Mover Archivos Seleccionados", type="primary"):
                    self._process_bulk_move(df_data, carpeta_destino)
            
            st.markdown("---")
    
    def _process_bulk_move(self, df_data: List[Dict[str, Any]], destination: str):
        """Procesa el movimiento en lote"""
        selections = self.selection_manager.get_selected_movies(len(df_data))
        result = self.file_processor.process_selected_movies(
            selections, df_data, 'move', destination
        )
        
        if result["success"]:
            if result["moved"] > 0:
                st.success(f"✅ {result['moved']} archivos movidos exitosamente a: {destination}")
            if result["errors"] > 0:
                st.error(f"❌ {result['errors']} archivos no pudieron ser movidos")
            if result["not_found"] > 0:
                st.warning(f"⚠️ {result['not_found']} archivos no encontrados")
        else:
            st.error(f"❌ {result['message']}")
        
        # Limpiar selecciones después de mover
        self.selection_manager.clear_selections()
        st.rerun()
    
    def _render_current_pair(self, df_data: List[Dict[str, Any]], index: int):
        """Renderiza el par actual de duplicados"""
        if index >= len(df_data):
            st.warning("No hay más pares para mostrar")
            return
            
        row = df_data[index]
        
        
        # Línea separadora si no es el primer par
        if index > 0:
            self.ui_components.render_separator_line()
        
        st.markdown(f"**Par {index+1}:**")
        
        # Mostrar reproductores si están habilitados
        try:
            show_players = settings.get_show_video_players()
        except AttributeError:
            show_players = True  # Por defecto mostrar reproductores
        
        if show_players:
            self._render_video_comparison(row, index)
        
        # Información y controles
        self._render_movie_controls(row, index)
    
    def _render_video_comparison(self, row: Dict[str, Any], index: int):
        """Renderiza la comparación de videos"""
        st.subheader("🎬 Comparar Videos")
        
        # Crear columnas
        col1, col2 = st.columns(2)
        
        # Película 1
        with col1:
            st.write("**Película 1:**")
            st.write(f"📁 {row.get('Peli 1', 'N/A')}")
            st.write(f"Tamaño: {row.get('Tamaño 1 (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get('Duración 1', 'N/A')}")
            
            # Reproductor embebido y botón
            ruta1 = row.get('Ruta 1', '')
            if ruta1 and os.path.exists(ruta1):
                # Verificar si se deben mostrar reproductores embebidos
                try:
                    show_embedded = settings.get_show_embedded_players()
                except AttributeError:
                    show_embedded = False
                
                if show_embedded:
                    try:
                        # Obtener tiempo de inicio desde configuración
                        start_time = settings.get_video_start_time_seconds()
                        
                        # Verificar tamaño del archivo (máximo 2GB para reproductor embebido)
                        file_size = os.path.getsize(ruta1) / (1024**3)  # GB
                        if file_size <= 2.0:
                            try:
                                # Leer archivo como bytes según documentación de Streamlit
                                with open(ruta1, "rb") as video_file:
                                    video_bytes = video_file.read()
                                
                                # Verificar si es un formato compatible
                                file_ext = os.path.splitext(ruta1)[1].lower()
                                if file_ext in ['.mp4', '.webm', '.ogg']:
                                    st.video(video_bytes, start_time=start_time, width=300)
                                    st.caption(f"⏱️ Inicia en el minuto {start_time//60}")
                                else:
                                    st.write(f"❌ Formato no compatible: {file_ext}")
                                    st.write("📁 Formatos soportados: MP4, WebM, OGG")
                            except Exception as video_error:
                                st.write(f"❌ Error cargando video: {str(video_error)}")
                                st.write("💡 El codec del video puede no ser compatible con el navegador")
                        else:
                            st.write("📁 Archivo muy grande para reproductor embebido")
                    except Exception as e:
                        st.write(f"❌ Error cargando video: {str(e)}")
                
                # Botón para abrir en reproductor (siempre visible)
                if st.button(f"🎬 Abrir en Reproductor", key=f"open1_{index}"):
                    os.startfile(ruta1)
            else:
                st.error("Archivo no encontrado")
        
        # Película 2
        with col2:
            st.write("**Película 2:**")
            st.write(f"📁 {row.get('Peli 2', 'N/A')}")
            st.write(f"Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get('Duración 2', 'N/A')}")
            
            # Reproductor embebido y botón
            ruta2 = row.get('Ruta 2', '')
            if ruta2 and os.path.exists(ruta2):
                # Verificar si se deben mostrar reproductores embebidos
                try:
                    show_embedded = settings.get_show_embedded_players()
                except AttributeError:
                    show_embedded = False
                
                if show_embedded:
                    try:
                        # Obtener tiempo de inicio desde configuración
                        start_time = settings.get_video_start_time_seconds()
                        
                        # Verificar tamaño del archivo (máximo 2GB para reproductor embebido)
                        file_size = os.path.getsize(ruta2) / (1024**3)  # GB
                        if file_size <= 2.0:
                            try:
                                # Leer archivo como bytes según documentación de Streamlit
                                with open(ruta2, "rb") as video_file:
                                    video_bytes = video_file.read()
                                
                                # Verificar si es un formato compatible
                                file_ext = os.path.splitext(ruta2)[1].lower()
                                if file_ext in ['.mp4', '.webm', '.ogg']:
                                    st.video(video_bytes, start_time=start_time, width=300)
                                    st.caption(f"⏱️ Inicia en el minuto {start_time//60}")
                                else:
                                    st.write(f"❌ Formato no compatible: {file_ext}")
                                    st.write("📁 Formatos soportados: MP4, WebM, OGG")
                            except Exception as video_error:
                                st.write(f"❌ Error cargando video: {str(video_error)}")
                                st.write("💡 El codec del video puede no ser compatible con el navegador")
                        else:
                            st.write("📁 Archivo muy grande para reproductor embebido")
                    except Exception as e:
                        st.write(f"❌ Error cargando video: {str(e)}")
                
                # Botón para abrir en reproductor (siempre visible)
                if st.button(f"🎬 Abrir en Reproductor", key=f"open2_{index}"):
                    os.startfile(ruta2)
            else:
                st.error("Archivo no encontrado")
        
        st.markdown("---")
    
    def _render_movie_controls(self, row: Dict[str, Any], index: int):
        """Renderiza los controles de películas"""
        st.subheader("📋 Información y Controles")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.write("**Película 1:**")
            st.markdown(f"<h4 style='color: #1f77b4'>{row.get('Peli 1', 'N/A')}</h4>", unsafe_allow_html=True)
            st.write(f"Tamaño: {row.get('Tamaño 1 (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get('Duración 1', 'N/A')}")
            st.write(f"Ruta: {row.get('Ruta 1', 'N/A')}")
            
            # Checkbox para película 1
            if st.checkbox(f"Seleccionar Película 1", key=f"select1_{index}"):
                st.session_state[f"selected_{index}_1"] = True
                st.session_state[f"selected_{index}_2"] = False  # Deseleccionar la otra
            else:
                st.session_state[f"selected_{index}_1"] = False
        
        with col2:
            st.write("**Película 2:**")
            st.markdown(f"<h4 style='color: #ff7f0e'>{row.get('Peli 2', 'N/A')}</h4>", unsafe_allow_html=True)
            st.write(f"Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get('Duración 2', 'N/A')}")
            st.write(f"Ruta: {row.get('Ruta 2', 'N/A')}")
            
            # Checkbox para película 2
            if st.checkbox(f"Seleccionar Película 2", key=f"select2_{index}"):
                st.session_state[f"selected_{index}_2"] = True
                st.session_state[f"selected_{index}_1"] = False  # Deseleccionar la otra
            else:
                st.session_state[f"selected_{index}_2"] = False
        
        with col3:
            st.write("**Acciones:**")
            
            # Verificar si alguna película del par está seleccionada
            par_seleccionado = (
                st.session_state.get(f"selected_{index}_1", False) or 
                st.session_state.get(f"selected_{index}_2", False)
            )
            
            if st.button("🗑️ Eliminar Seleccionadas", disabled=not par_seleccionado, key=f"delete_{index}"):
                self._process_pair_deletion(index, row)
        
        st.markdown("---")
    
    def _process_pair_deletion(self, index: int, row: Dict[str, Any]):
        """Procesa la eliminación de un par"""
        try:
            # Agregar el index al row para que esté disponible
            row['index'] = index
            
            # Verificar si está en modo debug
            debug_enabled = settings.get_debug_enabled()
            debug_folder = settings.get_debug_folder()
            
            if debug_enabled:
                # Modo debug: mover a carpeta de debug
                self._move_to_debug_folder(row, debug_folder)
            else:
                # Modo normal: eliminar archivos
                self._delete_selected_files(row)
                
        except Exception as e:
            st.error(f"❌ Error procesando eliminación: {str(e)}")
    
    def _move_to_debug_folder(self, row: Dict[str, Any], debug_folder: str):
        """Mueve archivos seleccionados a la carpeta de debug"""
        import shutil
        from pathlib import Path
        
        # Crear carpeta de debug si no existe
        debug_path = Path(debug_folder)
        debug_path.mkdir(parents=True, exist_ok=True)
        
        moved_files = []
        
        # Verificar qué archivos están seleccionados
        index = row.get('index', 0)
        pelicula1_selected = st.session_state.get(f"selected_{index}_1", False)
        pelicula2_selected = st.session_state.get(f"selected_{index}_2", False)
        
        # Debug: mostrar estado de selección
        st.write(f"🔍 Debug - Index: {index}")
        st.write(f"🔍 Debug - Película 1 seleccionada: {pelicula1_selected}")
        st.write(f"🔍 Debug - Película 2 seleccionada: {pelicula2_selected}")
        
        if pelicula1_selected:
            ruta1 = row.get('Ruta 1', '')
            if ruta1 and os.path.exists(ruta1):
                archivo_origen = Path(ruta1)
                archivo_destino = debug_path / archivo_origen.name
                
                # Si ya existe, agregar número
                contador = 1
                while archivo_destino.exists():
                    nombre_base = archivo_origen.stem
                    extension = archivo_origen.suffix
                    archivo_destino = debug_path / f"{nombre_base}_{contador}{extension}"
                    contador += 1
                
                shutil.move(str(archivo_origen), str(archivo_destino))
                moved_files.append(archivo_destino.name)
        
        if pelicula2_selected:
            ruta2 = row.get('Ruta 2', '')
            if ruta2 and os.path.exists(ruta2):
                archivo_origen = Path(ruta2)
                archivo_destino = debug_path / archivo_origen.name
                
                # Si ya existe, agregar número
                contador = 1
                while archivo_destino.exists():
                    nombre_base = archivo_origen.stem
                    extension = archivo_origen.suffix
                    archivo_destino = debug_path / f"{nombre_base}_{contador}{extension}"
                    contador += 1
                
                shutil.move(str(archivo_origen), str(archivo_destino))
                moved_files.append(archivo_destino.name)
        
        if moved_files:
            st.success(f"✅ Archivos movidos a debug: {', '.join(moved_files)}")
            st.info(f"📁 Ubicación: {debug_folder}")
        else:
            st.warning("⚠️ No se encontraron archivos para mover")
    
    def _delete_selected_files(self, row: Dict[str, Any]):
        """Elimina archivos seleccionados (modo normal)"""
        deleted_files = []
        
        # Verificar qué archivos están seleccionados
        index = row.get('index', 0)
        pelicula1_selected = st.session_state.get(f"selected_{index}_1", False)
        pelicula2_selected = st.session_state.get(f"selected_{index}_2", False)
        
        if pelicula1_selected:
            ruta1 = row.get('Ruta 1', '')
            if ruta1 and os.path.exists(ruta1):
                os.remove(ruta1)
                deleted_files.append(Path(ruta1).name)
        
        if pelicula2_selected:
            ruta2 = row.get('Ruta 2', '')
            if ruta2 and os.path.exists(ruta2):
                os.remove(ruta2)
                deleted_files.append(Path(ruta2).name)
        
        if deleted_files:
            st.success(f"✅ Archivos eliminados: {', '.join(deleted_files)}")
        else:
            st.warning("⚠️ No se encontraron archivos para eliminar")
    
    def run(self):
        """Ejecuta la aplicación completa"""
        self.render_header()
        self.render_sidebar()
        self.render_scan_section()
        self.render_results()
