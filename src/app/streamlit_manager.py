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
from typing import List, Dict, Any, Optional

# Configurar el path
current_dir = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(current_dir))

from src.settings.settings import settings
from src.utils.movie_detector import MovieDetector
from src.utils.video import VideoPlayer, VideoFormatter, VideoComparison
from src.utils.ui_components import UIComponents, MovieInfoDisplay, SelectionManager
from src.utils.file_operations import FileBatchProcessor
from src.services.plex_service import PlexService
from src.services.video_info_service import VideoInfoService
from src.services.Plex.plex_title_extractor import PlexTitleExtractor


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
        self.plex_service = PlexService()
        self.video_info_service = VideoInfoService()
        self.plex_title_extractor = PlexTitleExtractor(settings.get_plex_database_path())
        
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
        if 'plex_cache' not in st.session_state:
            st.session_state.plex_cache = {}
    
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
            tab1, tab2, tab3 = st.tabs(["🔍 Detección", "⚙️ Configuración", "🎬 Plex"])
            
            with tab1:
                self._render_detection_tab()
            
            with tab2:
                self._render_configuration_tab()
            
            with tab3:
                self._render_plex_tab()
    
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
    
    def _render_plex_tab(self):
        """Renderiza la pestaña de configuración de Plex"""
        st.subheader("🎬 Configuración de Plex")
        
        # Estado de conexión
        plex_configured = self.plex_service.is_configured()
        if plex_configured:
            st.success("✅ Plex configurado")
        else:
            st.error("❌ Plex no configurado")
        
        # Ruta de base de datos
        db_path = st.text_input(
            "📁 Ruta de Base de Datos",
            value=settings.get_plex_database_path(),
            help="Ruta completa al archivo com.plexapp.plugins.library.db"
        )
        
        # Bibliotecas
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("🎬 Biblioteca de Películas")
            if st.button("🔄 Cargar Bibliotecas", key="load_libraries"):
                st.rerun()
            
            # Obtener bibliotecas disponibles
            libraries = self.plex_service.get_available_libraries()
            if libraries:
                library_names = [lib['name'] for lib in libraries]
                current_movies_lib = settings.get_plex_movies_library()
                
                try:
                    default_index = library_names.index(current_movies_lib)
                except ValueError:
                    default_index = 0
                
                movies_lib = st.selectbox(
                    "Seleccionar biblioteca de películas:",
                    options=library_names,
                    index=default_index,
                    key="movies_library_select",
                    help="Biblioteca de películas en Plex"
                )
            else:
                movies_lib = st.text_input(
                    "Biblioteca de Películas",
                    value=settings.get_plex_movies_library(),
                    help="Nombre de la biblioteca de películas en Plex"
                )
        
        with col2:
            st.write("📺 Biblioteca de Series")
            if libraries:
                current_tv_lib = settings.get_plex_tv_shows_library()
                
                try:
                    default_index = library_names.index(current_tv_lib)
                except ValueError:
                    default_index = 0
                
                tv_lib = st.selectbox(
                    "Seleccionar biblioteca de series:",
                    options=library_names,
                    index=default_index,
                    key="tv_library_select",
                    help="Biblioteca de series en Plex"
                )
            else:
                tv_lib = st.text_input(
                    "Biblioteca de Series",
                    value=settings.get_plex_tv_shows_library(),
                    help="Nombre de la biblioteca de series en Plex"
                )
        
        # Opciones de metadatos
        st.subheader("📊 Metadatos")
        
        fetch_metadata = st.checkbox(
            "🔍 Traer metadatos de Plex",
            value=settings.get_plex_fetch_metadata(),
            help="Obtener metadatos de Plex para mostrar información adicional"
        )
        
        duration_filter = st.checkbox(
            "⏱️ Filtro por duración",
            value=settings.get_plex_duration_filter_enabled(),
            help="Usar duración de Plex para filtrar duplicados"
        )
        
        if duration_filter:
            tolerance = st.slider(
                "Tolerancia de duración (minutos)",
                min_value=1,
                max_value=30,
                value=settings.get_plex_duration_tolerance_minutes(),
                step=1,
                help="Diferencia máxima en minutos permitida entre duplicados"
            )
        else:
            tolerance = settings.get_plex_duration_tolerance_minutes()
        
        # Botones de prueba y guardado
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Probar Conexión", key="test_plex"):
                if self.plex_service.test_connection():
                    st.success("✅ Conexión exitosa")
                else:
                    st.error("❌ Error de conexión")
        
        with col2:
            if st.button("💾 Guardar Configuración", key="save_plex_config"):
                settings.set_plex_database_path(db_path)
                settings.set_plex_movies_library(movies_lib)
                settings.set_plex_tv_shows_library(tv_lib)
                settings.set_plex_fetch_metadata(fetch_metadata)
                settings.set_plex_duration_filter_enabled(duration_filter)
                settings.set_plex_duration_tolerance_minutes(tolerance)
                st.success("✅ Configuración de Plex guardada")
                st.rerun()
    
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
        
        # Mostrar última ruta usada si existe
        if last_path:
            st.caption(f"📁 Última ruta escaneada: {last_path}")
        
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
        
        # 1. MOSTRAR INFORMACIÓN BÁSICA INMEDIATAMENTE
        self._render_basic_info_immediate(row, index)
        
        # 2. Plex metadata - cargar automáticamente si está habilitado
        if settings.get_plex_fetch_metadata() and self.plex_service.is_configured():
            # Cargar metadatos automáticamente si está habilitado
            self._render_plex_metadata_auto(row, index)
        else:
            # Mostrar expander opcional si no está habilitado
            with st.expander("🎬 Metadatos de Plex (deshabilitado)", expanded=False):
                st.info("💡 Habilita 'Traer metadatos de Plex' en la configuración para ver metadatos automáticamente")
        
        # 3. SIEMPRE mostrar reproductores (más consistente)
        self._render_video_comparison(row, index)
        
        # 4. Información y controles
        self._render_movie_controls(row, index)
    
    def _render_video_comparison(self, row: Dict[str, Any], index: int):
        """Renderiza la comparación de videos mejorada"""
        st.subheader("🎬 Comparar Videos")
        
        # Verificar si se deben mostrar reproductores embebidos
        try:
            show_embedded = settings.get_show_embedded_players()
        except AttributeError:
            show_embedded = False
        
        # Crear columnas
        col1, col2 = st.columns(2)
        
        # Película 1
        with col1:
            self._render_single_video(row, 1, index, col1, show_embedded)
        
        # Película 2
        with col2:
            self._render_single_video(row, 2, index, col2, show_embedded)
    
    def _render_single_video(self, row: Dict[str, Any], video_num: int, index: int, col, show_embedded: bool = False):
        """Renderiza un solo video con mejor manejo de errores"""
        with col:
            st.write(f"**Película {video_num}:**")
            st.write(f"📁 {row.get(f'Peli {video_num}', 'N/A')}")
            st.write(f"Tamaño: {row.get(f'Tamaño {video_num} (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get(f'Duración {video_num}', 'N/A')}")
            
            # Obtener ruta del archivo
            ruta = row.get(f'Ruta {video_num}', '')
            
            if not ruta or not os.path.exists(ruta):
                st.error("❌ Archivo no encontrado")
                return
            
            # Información del archivo
            try:
                file_size_gb = os.path.getsize(ruta) / (1024**3)
                file_ext = os.path.splitext(ruta)[1].lower()
                
                # Mostrar información del archivo
                st.write(f"📊 Tamaño: {file_size_gb:.2f} GB")
                st.write(f"📄 Extensión: {file_ext}")
                
                # SIEMPRE mostrar botón de reproductor externo
                self._render_external_player_button(ruta, f"open{video_num}_{index}")
                
                # Mostrar reproductores embebidos si están habilitados
                if show_embedded:
                    self._render_embedded_video(ruta, file_size_gb, file_ext, f"video{video_num}_{index}")
                else:
                    st.info("💡 Reproductores embebidos deshabilitados en configuración")
                
            except Exception as e:
                st.error(f"❌ Error procesando archivo: {e}")
                # Aún así mostrar botón de reproductor externo
                self._render_external_player_button(ruta, f"open{video_num}_{index}")
    
    def _render_embedded_video(self, file_path: str, file_size_gb: float, file_ext: str, key: str):
        """Renderiza un video embebido con mejor manejo de errores"""
        try:
            # Obtener tiempo de inicio desde configuración
            start_time = settings.get_video_start_time_seconds()
            
            # Verificar tamaño del archivo (límite más permisivo)
            max_size_gb = 2.0  # Volver a 2GB como límite original
            if file_size_gb > max_size_gb:
                st.warning(f"📁 Archivo muy grande ({file_size_gb:.1f}GB) para reproductor embebido")
                st.info("💡 Usa el botón 'Abrir en Reproductor' para archivos grandes")
                return
            
            # Verificar formato compatible
            supported_formats = ['.mp4', '.webm', '.ogg', '.avi', '.mov']
            if file_ext not in supported_formats:
                st.warning(f"❌ Formato no compatible: {file_ext}")
                st.info(f"📁 Formatos soportados: {', '.join(supported_formats)}")
                return
            
            # Intentar cargar el video
            try:
                # Método mejorado: usar ruta directa en lugar de bytes para archivos grandes
                if file_size_gb <= 0.5:  # Archivos pequeños: usar bytes
                    with open(file_path, "rb") as video_file:
                        video_bytes = video_file.read()
                    st.video(video_bytes, start_time=start_time, width=300)
                else:  # Archivos medianos: usar ruta directa
                    st.video(file_path, start_time=start_time, width=300)
                
                # Mostrar información del tiempo de inicio
                minutes = start_time // 60
                seconds = start_time % 60
                st.caption(f"⏱️ Inicia en {minutes}:{seconds:02d}")
                
            except Exception as video_error:
                st.error(f"❌ Error cargando video: {str(video_error)}")
                st.info("💡 Posibles causas:")
                st.info("• Codec no compatible con el navegador")
                st.info("• Archivo corrupto o incompleto")
                st.info("• Problema de permisos de archivo")
                
                # Sugerir alternativas
                st.info("🔧 Soluciones:")
                st.info("• Usa el botón 'Abrir en Reproductor' para reproducir externamente")
                st.info("• Verifica que el archivo no esté corrupto")
                st.info("• Intenta con un archivo más pequeño para prueba")
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")
    
    def _render_external_player_button(self, file_path: str, key: str):
        """Renderiza botón para abrir en reproductor externo"""
        if st.button(f"🎬 Abrir en Reproductor", key=key, help="Abre el video en tu reproductor predeterminado"):
            try:
                # Intentar abrir con el sistema operativo
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS y Linux
                    os.system(f'open "{file_path}"' if sys.platform == 'darwin' else f'xdg-open "{file_path}"')
                else:
                    st.warning("⚠️ Sistema operativo no soportado para apertura automática")
                    st.info(f"📁 Ruta del archivo: {file_path}")
                
                st.success("✅ Abriendo en reproductor externo...")
                
            except Exception as e:
                st.error(f"❌ No se pudo abrir automáticamente: {e}")
                st.info(f"📁 Ruta del archivo: {file_path}")
                st.info("💡 Copia la ruta y ábrela manualmente en tu reproductor")
        
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
            select1_key = f"select1_{index}"
            if st.checkbox(f"Seleccionar Película 1", key=select1_key):
                st.session_state[f"selected_{index}_1"] = True
                st.session_state[f"selected_{index}_2"] = False  # Deseleccionar la otra
                st.rerun()
            else:
                st.session_state[f"selected_{index}_1"] = False
        
        with col2:
            st.write("**Película 2:**")
            st.markdown(f"<h4 style='color: #ff7f0e'>{row.get('Peli 2', 'N/A')}</h4>", unsafe_allow_html=True)
            st.write(f"Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            st.write(f"Duración: {row.get('Duración 2', 'N/A')}")
            st.write(f"Ruta: {row.get('Ruta 2', 'N/A')}")
            
            # Checkbox para película 2
            select2_key = f"select2_{index}"
            if st.checkbox(f"Seleccionar Película 2", key=select2_key):
                st.session_state[f"selected_{index}_2"] = True
                st.session_state[f"selected_{index}_1"] = False  # Deseleccionar la otra
                st.rerun()
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
    
    def _get_plex_metadata_for_pair(self, row: Dict[str, Any]) -> Optional[Dict]:
        """Obtiene metadatos de Plex para un par de películas"""
        try:
            # Extraer nombres de archivo de las rutas
            filename1 = os.path.basename(row.get('Ruta 1', ''))
            filename2 = os.path.basename(row.get('Ruta 2', ''))
            
            if not filename1 or not filename2:
                return None
            
            # Obtener metadatos para ambos archivos
            metadata1 = self.plex_service.get_movie_metadata_by_filename(filename1)
            metadata2 = self.plex_service.get_movie_metadata_by_filename(filename2)
            
            if metadata1 or metadata2:
                return {
                    'file1': metadata1,
                    'file2': metadata2,
                    'compatibility': self._check_plex_compatibility(metadata1, metadata2)
                }
            
            return None
            
        except Exception as e:
            st.error(f"Error obteniendo metadatos de Plex: {e}")
            return None
    
    def _check_plex_compatibility(self, metadata1: Optional[Dict], metadata2: Optional[Dict]) -> Dict:
        """Verifica compatibilidad entre dos películas usando metadatos de Plex"""
        if not metadata1 or not metadata2:
            return {
                'compatible': True,
                'message': 'No se pudieron obtener metadatos de Plex',
                'duration_check': None
            }
        
        # Verificar duración si está habilitado
        duration_compatible, duration_message = self.plex_service.check_duration_compatibility(
            metadata1, metadata2
        )
        
        return {
            'compatible': duration_compatible,
            'message': duration_message,
            'duration_check': {
                'compatible': duration_compatible,
                'message': duration_message
            }
        }
    
    def _render_plex_metadata(self, plex_metadata: Dict):
        """Renderiza los metadatos de Plex para un par"""
        st.subheader("🎬 Metadatos de Plex")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            metadata1 = plex_metadata['file1']
            if metadata1:
                # Analizar si es None o no encontrado
                title = metadata1.get('title', 'N/A')
                year = metadata1.get('year', 'N/A')
                
                if title == 'N/A' or year == 'N/A' or year is None:
                    st.write("🔍 **Archivo no identificado en Plex**")
                    st.write("💡 *Solo disponible por nombre de archivo*")
                else:
                    # Verificar si es duplicado (mismo título y año)
                    is_duplicate = self._is_plex_duplicate(metadata1, plex_metadata.get('file2', {}))
                    title_color = "🔴" if is_duplicate else "🎬"
                    
                    st.write(f"{title_color} **{title}** ({year})")
                    st.write(f"📊 Estudio: {metadata1.get('studio', 'N/A')}")
                    st.write(f"⏱️ Duración: {metadata1.get('duration', 'N/A')}")
                    st.write(f"📁 Biblioteca: {metadata1.get('library_name', 'N/A')}")
                    st.write(f"📝 Resumen: {metadata1.get('summary', 'N/A')[:100]}...")
            else:
                st.write("❌ No encontrada en Plex")
                st.write("💡 *Solo disponible por nombre de archivo*")
        
        with col2:
            st.write("**Película 2:**")
            metadata2 = plex_metadata['file2']
            if metadata2:
                # Analizar si es None o no encontrado
                title = metadata2.get('title', 'N/A')
                year = metadata2.get('year', 'N/A')
                
                if title == 'N/A' or year == 'N/A' or year is None:
                    st.write("🔍 **Archivo no identificado en Plex**")
                    st.write("💡 *Solo disponible por nombre de archivo*")
                else:
                    # Verificar si es duplicado (mismo título y año)
                    is_duplicate = self._is_plex_duplicate(metadata2, plex_metadata.get('file1', {}))
                    title_color = "🔴" if is_duplicate else "🎬"
                    
                    st.write(f"{title_color} **{title}** ({year})")
                    st.write(f"📊 Estudio: {metadata2.get('studio', 'N/A')}")
                    st.write(f"⏱️ Duración: {metadata2.get('duration', 'N/A')}")
                    st.write(f"📁 Biblioteca: {metadata2.get('library_name', 'N/A')}")
                    st.write(f"📝 Resumen: {metadata2.get('summary', 'N/A')[:100]}...")
            else:
                st.write("❌ No encontrada en Plex")
                st.write("💡 *Solo disponible por nombre de archivo*")
        
        # Mostrar análisis de compatibilidad
        compatibility = plex_metadata['compatibility']
        if compatibility['duration_check']:
            duration_check = compatibility['duration_check']
            if duration_check['compatible']:
                st.success(f"✅ {duration_check['message']}")
            else:
                st.warning(f"⚠️ {duration_check['message']}")
        
        st.markdown("---")
    
    def _is_plex_duplicate(self, metadata1: Dict, metadata2: Dict) -> bool:
        """Verifica si dos metadatos de Plex representan la misma película"""
        if not metadata1 or not metadata2:
            return False
        
        # Comparar título y año
        title1 = metadata1.get('title', '')
        title2 = metadata2.get('title', '')
        year1 = metadata1.get('year', '')
        year2 = metadata2.get('year', '')
        
        # Si tienen el mismo título y año, son la misma película
        return title1 == title2 and year1 == year2 and title1 != 'N/A' and year1 != 'N/A'
    

    def _render_basic_info_immediate(self, row: Dict[str, Any], index: int):
        """Renderiza información básica inmediatamente (nombres, tamaños, rutas)"""
        st.subheader("📁 Información Básica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            st.markdown(f"<h4 style='color: #1f77b4'>{row.get('Peli 1', 'N/A')}</h4>", unsafe_allow_html=True)
            st.write(f"📊 Tamaño: {row.get('Tamaño 1 (GB)', 'N/A')} GB")
            st.write(f"⏱️ Duración: {row.get('Duración 1', 'N/A')}")
            st.write(f"📁 Ruta: {row.get('Ruta 1', 'N/A')}")
            
            # Información de video local
            ruta1 = row.get('Ruta 1', '')
            if ruta1 and os.path.exists(ruta1):
                self._render_local_video_info(ruta1, f"local1_{index}")
        
        with col2:
            st.write("**Película 2:**")
            st.markdown(f"<h4 style='color: #ff7f0e'>{row.get('Peli 2', 'N/A')}</h4>", unsafe_allow_html=True)
            st.write(f"📊 Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            st.write(f"⏱️ Duración: {row.get('Duración 2', 'N/A')}")
            st.write(f"📁 Ruta: {row.get('Ruta 2', 'N/A')}")
            
            # Información de video local
            ruta2 = row.get('Ruta 2', '')
            if ruta2 and os.path.exists(ruta2):
                self._render_local_video_info(ruta2, f"local2_{index}")
        
        st.markdown("---")
    
    def _render_plex_metadata_optional(self, row: Dict[str, Any], index: int):
        """Renderiza metadatos de Plex en expander opcional"""
        # Verificar si ya tenemos cache para estos archivos
        filename1 = os.path.basename(row.get('Ruta 1', ''))
        filename2 = os.path.basename(row.get('Ruta 2', ''))
        
        cache_key = f"{filename1}_{filename2}"
        
        if cache_key in st.session_state.plex_cache:
            # Usar cache
            plex_metadata = st.session_state.plex_cache[cache_key]
            self._render_plex_metadata_content(plex_metadata)
        else:
            # Consultar Plex
            if st.button("🔍 Cargar Metadatos de Plex", key=f"load_plex_{index}"):
                with st.spinner("Consultando base de datos de Plex..."):
                    plex_metadata = self._get_plex_metadata_for_pair(row)
                    
                    if plex_metadata:
                        # Guardar en cache
                        st.session_state.plex_cache[cache_key] = plex_metadata
                        self._render_plex_metadata_content(plex_metadata)
                        st.success("✅ Metadatos cargados")
                    else:
                        st.info("💡 No se encontraron metadatos en Plex para estos archivos")
            else:
                st.info("💡 Haz clic en 'Cargar Metadatos de Plex' para obtener información adicional")
    
    def _render_plex_metadata_content(self, plex_metadata: Dict):
        """Renderiza el contenido de metadatos de Plex"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            metadata1 = plex_metadata['file1']
            if metadata1:
                # Analizar si es None o no encontrado
                title = metadata1.get('title', 'N/A')
                year = metadata1.get('year', 'N/A')
                
                if title == 'N/A' or year == 'N/A' or year is None:
                    st.write("🔍 **Archivo no identificado en Plex**")
                    st.write("💡 *Solo disponible por nombre de archivo*")
                else:
                    st.write(f"🎬 **{title}** ({year})")
                    st.write(f"📊 Estudio: {metadata1.get('studio', 'N/A')}")
                    st.write(f"⏱️ Duración: {metadata1.get('duration_hms_meta', 'N/A')}")
                    st.write(f"🎥 Resolución: {metadata1.get('width', 'N/A')}x{metadata1.get('height', 'N/A')}")
                    st.write(f"📦 Contenedor: {metadata1.get('container', 'N/A')}")
                    st.write(f"🎵 Audio: {metadata1.get('audio_codec', 'N/A')} ({metadata1.get('audio_channels', 'N/A')} canales)")
            else:
                st.write("❌ No encontrada en Plex")
                st.write("💡 *Solo disponible por nombre de archivo*")
        
        with col2:
            st.write("**Película 2:**")
            metadata2 = plex_metadata['file2']
            if metadata2:
                # Analizar si es None o no encontrado
                title = metadata2.get('title', 'N/A')
                year = metadata2.get('year', 'N/A')
                
                if title == 'N/A' or year == 'N/A' or year is None:
                    st.write("🔍 **Archivo no identificado en Plex**")
                    st.write("💡 *Solo disponible por nombre de archivo*")
                else:
                    st.write(f"🎬 **{title}** ({year})")
                    st.write(f"📊 Estudio: {metadata2.get('studio', 'N/A')}")
                    st.write(f"⏱️ Duración: {metadata2.get('duration_hms_meta', 'N/A')}")
                    st.write(f"🎥 Resolución: {metadata2.get('width', 'N/A')}x{metadata2.get('height', 'N/A')}")
                    st.write(f"📦 Contenedor: {metadata2.get('container', 'N/A')}")
                    st.write(f"🎵 Audio: {metadata2.get('audio_codec', 'N/A')} ({metadata2.get('audio_channels', 'N/A')} canales)")
            else:
                st.write("❌ No encontrada en Plex")
                st.write("💡 *Solo disponible por nombre de archivo*")
        
        # Mostrar análisis de compatibilidad
        compatibility = plex_metadata['compatibility']
        if compatibility['duration_check']:
            duration_check = compatibility['duration_check']
            if duration_check['compatible']:
                st.success(f"✅ {duration_check['message']}")
            else:
                st.warning(f"⚠️ {duration_check['message']}")

    def _render_plex_metadata_auto(self, row: Dict[str, Any], index: int):
        """Renderiza información de Plex: biblioteca + opciones de mejora"""
        # Verificar si ya tenemos cache para estos archivos
        filename1 = os.path.basename(row.get('Ruta 1', ''))
        filename2 = os.path.basename(row.get('Ruta 2', ''))
        
        cache_key = f"{filename1}_{filename2}"
        
        if cache_key in st.session_state.plex_cache:
            # Usar cache
            plex_info = st.session_state.plex_cache[cache_key]
            self._render_plex_library_info(plex_info, row, index)
        else:
            # Consultar Plex automáticamente
            with st.spinner("🔍 Consultando base de datos de Plex..."):
                plex_info = self._get_plex_library_info_for_pair(row)
                
                if plex_info:
                    # Guardar en cache
                    st.session_state.plex_cache[cache_key] = plex_info
                    self._render_plex_library_info(plex_info, row, index)
                else:
                    st.info("💡 No se encontraron archivos en Plex")
                    self._render_plex_enhancement_options(row, index)
        
        st.markdown("---")

    def _render_local_video_info(self, file_path: str, key: str):
        """Renderiza información de video local"""
        try:
            # Obtener información del video
            video_info = self.video_info_service.get_summary_info(file_path)
            
            if video_info:
                st.write("🎬 **Información Local:**")
                st.write(f"⏱️ Duración: {video_info['duration']}")
                st.write(f"🎥 Resolución: {video_info['resolution']}")
                st.write(f"📺 Calidad: {video_info['quality']}")
                st.write(f"🎵 Audio: {video_info['audio']}")
                st.write(f"📦 Contenedor: {video_info['container']}")
                
                if video_info['fps'] != 'N/A':
                    st.write(f"🎞️ FPS: {video_info['fps']}")
                if video_info['bitrate'] != 'N/A':
                    st.write(f"📊 Bitrate: {video_info['bitrate']}")
            else:
                st.write("❌ No se pudo obtener información del video")
                
        except Exception as e:
            st.write(f"❌ Error obteniendo información: {e}")

    def _get_plex_library_info_for_pair(self, row: Dict[str, Any]) -> Optional[Dict]:
        """Obtiene información de biblioteca de Plex para un par de películas"""
        try:
            # Extraer nombres de archivo de las rutas
            filename1 = os.path.basename(row.get('Ruta 1', ''))
            filename2 = os.path.basename(row.get('Ruta 2', ''))
            
            if not filename1 or not filename2:
                return None
            
            # Obtener información de biblioteca para ambos archivos
            library_info1 = self.plex_service.get_library_info_by_filename(filename1)
            library_info2 = self.plex_service.get_library_info_by_filename(filename2)
            
            # Si encontramos los archivos en Plex, intentar obtener títulos reales (sin bloquear)
            if library_info1:
                try:
                    real_title1 = self.plex_title_extractor.get_real_title_by_filename(filename1)
                    if real_title1:
                        library_info1['title'] = real_title1['title']
                        library_info1['year'] = real_title1['year']
                except Exception:
                    # Si falla, mantener el título del archivo
                    pass
            
            if library_info2:
                try:
                    real_title2 = self.plex_title_extractor.get_real_title_by_filename(filename2)
                    if real_title2:
                        library_info2['title'] = real_title2['title']
                        library_info2['year'] = real_title2['year']
                except Exception:
                    # Si falla, mantener el título del archivo
                    pass
            
            if library_info1 or library_info2:
                return {
                    'file1': library_info1,
                    'file2': library_info2
                }
            
            return None
            
        except Exception as e:
            st.error(f"Error obteniendo información de biblioteca: {e}")
            return None
    
    def _render_plex_library_info(self, plex_info: Dict, row: Dict[str, Any], index: int):
        """Renderiza información de biblioteca de Plex"""
        st.subheader("🎬 Estado en Plex")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            library_info1 = plex_info['file1']
            if library_info1:
                st.success(f"✅ Encontrada en biblioteca: {library_info1.get('library_name', 'N/A')}")
                st.write(f"📁 Título: {library_info1.get('title', 'N/A')}")
                st.write(f"📅 Año: {library_info1.get('year', 'N/A')}")
            else:
                st.warning("❌ No encontrada en Plex")
                self._render_enhancement_options_for_file(row.get('Ruta 1', ''), f"enhance1_{index}")
        
        with col2:
            st.write("**Película 2:**")
            library_info2 = plex_info['file2']
            if library_info2:
                st.success(f"✅ Encontrada en biblioteca: {library_info2.get('library_name', 'N/A')}")
                st.write(f"📁 Título: {library_info2.get('title', 'N/A')}")
                st.write(f"📅 Año: {library_info2.get('year', 'N/A')}")
            else:
                st.warning("❌ No encontrada en Plex")
                self._render_enhancement_options_for_file(row.get('Ruta 2', ''), f"enhance2_{index}")
    
    def _render_plex_enhancement_options(self, row: Dict[str, Any], index: int):
        """Renderiza opciones de mejora cuando no se encuentran archivos en Plex"""
        st.subheader("🔧 Opciones de Mejora")
        st.info("💡 Los archivos no están en Plex. Puedes mejorarlos:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Película 1:**")
            self._render_enhancement_options_for_file(row.get('Ruta 1', ''), f"enhance1_{index}")
        
        with col2:
            st.write("**Película 2:**")
            self._render_enhancement_options_for_file(row.get('Ruta 2', ''), f"enhance2_{index}")
    
    def _render_enhancement_options_for_file(self, file_path: str, key: str):
        """Renderiza opciones de mejora para un archivo específico"""
        if not file_path:
            st.write("❌ Ruta no disponible")
            return
        
        filename = os.path.basename(file_path)
        st.write(f"📁 {filename}")
        
        # Opción 1: Renombrar archivo
        with st.expander("📝 Renombrar archivo", expanded=False):
            st.write("💡 Renombra el archivo para que Plex lo reconozca mejor")
            
            new_name = st.text_input(
                "Nuevo nombre (sin extensión):",
                value=filename.rsplit('.', 1)[0],
                key=f"rename_{key}",
                help="Ejemplo: 'Avatar (2009)' o 'Avatar (2009) {edition-Director\'s Cut}'"
            )
            
            if st.button("💾 Renombrar", key=f"rename_btn_{key}"):
                self._rename_file(file_path, new_name)
        
        # Opción 2: Crear edición diferente
        with st.expander("🎬 Crear edición diferente", expanded=False):
            st.write("💡 Crea una edición diferente de una película existente")
            
            # Obtener lista de películas de Plex
            movies_list = self._get_plex_movies_list()
            
            if movies_list:
                selected_movie = st.selectbox(
                    "Seleccionar película base:",
                    options=movies_list,
                    key=f"movie_select_{key}",
                    help="Selecciona la película de la que quieres crear una edición"
                )
                
                edition_name = st.text_input(
                    "Nombre de la edición:",
                    key=f"edition_{key}",
                    help="Ejemplo: 'Director\'s Cut', 'Extended Edition', 'Unrated'"
                )
                
                if st.button("🎬 Crear Edición", key=f"edition_btn_{key}"):
                    self._create_edition(file_path, selected_movie, edition_name)
            else:
                st.warning("❌ No se pudo cargar la lista de películas de Plex")
    
    def _get_plex_movies_list(self) -> List[str]:
        """Obtiene lista de películas de Plex para selección"""
        try:
            # Obtener películas de Plex
            movies = self.plex_service.get_all_movies()
            return [f"{movie.get('title', 'N/A')} ({movie.get('year', 'N/A')})" for movie in movies]
        except Exception as e:
            st.error(f"Error obteniendo películas: {e}")
            return []
    
    def _rename_file(self, file_path: str, new_name: str):
        """Renombra un archivo"""
        try:
            if not new_name:
                st.error("❌ Nombre no puede estar vacío")
                return
            
            # Obtener directorio y extensión
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_path = os.path.join(directory, f"{new_name}{extension}")
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            st.success(f"✅ Archivo renombrado: {os.path.basename(new_path)}")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error renombrando archivo: {e}")
    
    def _create_edition(self, file_path: str, selected_movie: str, edition_name: str):
        """Crea una edición diferente de una película"""
        try:
            if not edition_name:
                st.error("❌ Nombre de edición no puede estar vacío")
                return
            
            # Extraer título y año de la película seleccionada
            # Formato: "Título (Año)"
            import re
            match = re.match(r"(.+?)\s*\((\d{4})\)", selected_movie)
            if not match:
                st.error("❌ Formato de película no válido")
                return
            
            title, year = match.groups()
            
            # Crear nuevo nombre con edición
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_name = f"{title} ({year}) {{edition-{edition_name}}}{extension}"
            new_path = os.path.join(directory, new_name)
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
            st.info("💡 Reinicia Plex para que detecte la nueva edición")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error creando edición: {e}")
    def run(self):
        """Ejecuta la aplicación completa"""
        self.render_header()
        self.render_sidebar()
        self.render_scan_section()
        self.render_results()
