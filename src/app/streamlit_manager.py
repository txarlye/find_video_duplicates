#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor principal de la aplicación Streamlit
"""

import streamlit as st
import sys
import time
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configurar logging para mostrar en terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurar el path
current_dir = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(current_dir))

from src.settings.settings import settings
from src.utils.movie_detector import MovieDetector
from src.utils.video import VideoPlayer, VideoFormatter, VideoComparison
from src.utils.ui_components import UIComponents, MovieInfoDisplay, SelectionManager, DuplicatePairsManager
from src.utils.file_operations import FileBatchProcessor
from src.services.plex_service import PlexService
from src.services.video_info_service import VideoInfoService
from src.services.plex_refresh_service import PlexRefreshService
from src.services.Plex.plex_title_extractor import PlexTitleExtractor
from src.services.Plex.plex_editions_manager import PlexEditionsManager
from src.services.scan_data_manager import ScanDataManager
from src.services.telegram_service import TelegramService
from src.services.Telegram.telegram_manager import TelegramManager
from src.services.Telegram.telegram_uploader import TelegramUploader


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
        self.plex_refresh_service = PlexRefreshService()
        self.plex_title_extractor = PlexTitleExtractor(settings.get_plex_database_path())
        self.plex_editions_manager = PlexEditionsManager(settings.get_plex_database_path())
        self.pairs_manager = DuplicatePairsManager()
        self.scan_data_manager = ScanDataManager()
        self.telegram_service = TelegramService()
        self.telegram_manager = TelegramManager()
        self.telegram_uploader = TelegramUploader()
        
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
        st.title("🎬 Utilidades de gestión de video con Plex y Telegram")
        st.markdown("---")
        
        # Botones principales
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Escanear Carpeta", type="primary", use_container_width=True):
                st.session_state.show_scan_interface = True
                st.rerun()
        
        with col2:
            if st.button("📱 Telegram", use_container_width=True):
                st.session_state.show_telegram_interface = True
                st.rerun()
        
        st.markdown("---")
        
        # Aclaración importante
        st.info("⚠️ **IMPORTANTE:** Esta aplicación NUNCA borra archivos. Solo detecta y muestra duplicados para que puedas decidir qué hacer con ellos.")
        st.markdown("---")
    
    def render_sidebar(self):
        """Renderiza el sidebar con configuración"""
        with st.sidebar:
            st.header("⚙️ Configuración")
            
            # Pestañas en el sidebar
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Detección", "⚙️ Configuración", "🎬 Plex", "📱 Telegram"])
            
            with tab1:
                self._render_detection_tab()
            
            with tab2:
                self._render_configuration_tab()
            
            with tab3:
                self._render_plex_tab()
            
            with tab4:
                self._render_telegram_tab()
    
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
        
        # Directorios excluidos
        st.subheader("🚫 Directorios Excluidos")
        st.info("💡 Estos directorios se excluirán automáticamente del escaneo")
        
        excluded_dirs = settings.get_excluded_directories()
        st.write("**Directorios actualmente excluidos:**")
        for dir_name in excluded_dirs:
            st.write(f"• {dir_name}")
        
        # Permitir agregar/quitar directorios
        col1, col2 = st.columns(2)
        
        with col1:
            new_dir = st.text_input("Agregar directorio a excluir:", placeholder="ej: test")
            if st.button("➕ Agregar") and new_dir:
                settings.add_excluded_directory(new_dir)
                st.success(f"✅ Directorio '{new_dir}' agregado a la exclusión")
                st.rerun()
        
        with col2:
            if excluded_dirs:
                dir_to_remove = st.selectbox("Remover directorio:", options=excluded_dirs, key="remove_dir")
                if st.button("➖ Remover") and dir_to_remove:
                    settings.remove_excluded_directory(dir_to_remove)
                    st.success(f"✅ Directorio '{dir_to_remove}' removido de la exclusión")
                    st.rerun()
        
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
        
        # Sección de refresh de Plex
        st.subheader("🔄 Refrescar Bibliotecas")
        
        col_refresh1, col_refresh2 = st.columns(2)
        
        with col_refresh1:
            if st.button("🔄 Refrescar Películas", key="refresh_movies"):
                with st.spinner("Refrescando biblioteca de películas..."):
                    if self.plex_refresh_service.refresh_movies_library():
                        st.success("✅ Biblioteca de películas refrescada")
                    else:
                        st.error("❌ Error refrescando películas")
        
        with col_refresh2:
            if st.button("🔄 Refrescar Series", key="refresh_tv"):
                with st.spinner("Refrescando biblioteca de series..."):
                    if self.plex_refresh_service.refresh_tv_shows_library():
                        st.success("✅ Biblioteca de series refrescada")
                    else:
                        st.error("❌ Error refrescando series")
        
        # Refresh via API
        if st.button("🚀 Refrescar Todas las Bibliotecas (API)", key="refresh_all_api"):
            with st.spinner("Refrescando todas las bibliotecas via API..."):
                if self.plex_refresh_service.refresh_all_libraries_via_api():
                    st.success("✅ Todas las bibliotecas refrescadas via API")
                else:
                    st.error("❌ Error refrescando bibliotecas via API")
        
        # Información del servidor
        if st.button("ℹ️ Info del Servidor Plex", key="plex_server_info"):
            server_info = self.plex_refresh_service.get_plex_server_info()
            if "error" in server_info:
                st.error(f"❌ {server_info['error']}")
            else:
                st.success("✅ Servidor Plex conectado")
                st.json(server_info)
        
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
        
        # Sección de gestión de datos de escaneo
        st.markdown("---")
        st.subheader("💾 Gestión de Datos de Escaneo")
        
        col_save, col_load = st.columns(2)
        
        with col_save:
            if st.button("💾 Guardar Escaneo", disabled=not hasattr(st.session_state, 'detector') or not st.session_state.detector):
                self._save_scan_data()
        
        with col_load:
            if st.button("📂 Cargar Escaneo"):
                # Activar modo de carga
                st.session_state.show_load_interface = True
                st.rerun()
        
        # Mostrar interfaz de carga si está activada
        if getattr(st.session_state, 'show_load_interface', False):
            st.markdown("---")
            self._show_load_scan_interface()
        
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
        
        # Resetear contadores de pares
        settings.reset_pairs_counters()
        
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
        # Debug: verificar estado de la sesión
        duplicados_count = len(st.session_state.duplicados) if st.session_state.duplicados else 0
        peliculas_count = len(st.session_state.peliculas) if st.session_state.peliculas else 0
        
        logging.info(f"🔍 render_results - duplicados: {duplicados_count}")
        logging.info(f"🔍 render_results - peliculas: {peliculas_count}")
        
        # Mostrar información de debug en la interfaz
        with st.expander("🔍 Debug - Estado de la sesión", expanded=False):
            st.write(f"**Duplicados en session_state:** {duplicados_count}")
            st.write(f"**Películas en session_state:** {peliculas_count}")
            st.write(f"**Tipo de duplicados:** {type(st.session_state.duplicados)}")
            st.write(f"**Scan cargado:** {getattr(st.session_state, 'scan_loaded', False)}")
            if st.session_state.duplicados and len(st.session_state.duplicados) > 0:
                st.write(f"**Primer elemento:** {type(st.session_state.duplicados[0])}")
        
        # Verificar si hay duplicados
        if not st.session_state.duplicados or len(st.session_state.duplicados) == 0:
            logging.info("⚠️ render_results - No hay duplicados, saliendo")
            # Mostrar mensaje de debug en la interfaz
            if getattr(st.session_state, 'scan_loaded', False):
                st.warning("⚠️ Se cargó un escaneo pero no se encontraron duplicados. Esto puede indicar un problema con el formato de datos.")
                # Intentar recargar los datos
                st.info("🔄 Intentando recargar los datos...")
                st.rerun()
            else:
                st.info("💡 No hay datos de duplicados para mostrar. Escanea una carpeta o carga un escaneo guardado.")
            return
        
        # Verificar que los datos están en el formato correcto
        if isinstance(st.session_state.duplicados, list) and len(st.session_state.duplicados) > 0:
            # Verificar que el primer elemento es un diccionario (formato correcto)
            first_item = st.session_state.duplicados[0]
            if not isinstance(first_item, dict):
                logging.warning("⚠️ Formato de datos incorrecto, intentando convertir...")
                # Aquí podrías agregar lógica de conversión si es necesario
        
        # Métricas
        total_peliculas = len(st.session_state.peliculas) if st.session_state.peliculas else 0
        total_duplicados = len(st.session_state.duplicados)
        
        # Si no hay películas pero sí duplicados, es un escaneo cargado
        if total_peliculas == 0 and total_duplicados > 0:
            # Estimar películas basándose en los duplicados
            total_peliculas = total_duplicados * 2  # Aproximación
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Total Películas", total_peliculas)
        with col2:
            st.metric("🔍 Duplicados Encontrados", total_duplicados)
        with col3:
            if total_duplicados > 0:
                # Calcular espacio ahorrable manejando ambos formatos
                espacio_ahorrado = 0
                for duplicado in st.session_state.duplicados:
                    size1, size2 = 0, 0
                    
                    # Verificar si es una lista (formato antiguo) o diccionario (formato nuevo)
                    if isinstance(duplicado, list) and len(duplicado) >= 2:
                        # Formato antiguo: [archivo1, archivo2]
                        archivo1, archivo2 = duplicado[0], duplicado[1]
                        size1 = archivo1.get('tamaño', 0) / (1024**3) if isinstance(archivo1, dict) else 0
                        size2 = archivo2.get('tamaño', 0) / (1024**3) if isinstance(archivo2, dict) else 0
                    elif isinstance(duplicado, dict):
                        # Formato nuevo: {'Tamaño 1': '1.5 GB', 'Tamaño 2': '1.4 GB', ...}
                        size1_str = duplicado.get('Tamaño 1', '0 GB')
                        size2_str = duplicado.get('Tamaño 2', '0 GB')
                        
                        # Convertir a GB
                        if isinstance(size1_str, str) and 'GB' in size1_str:
                            size1 = float(size1_str.replace(' GB', ''))
                        elif isinstance(size1_str, str) and 'MB' in size1_str:
                            size1 = float(size1_str.replace(' MB', '')) / 1024
                        else:
                            size1 = 0
                            
                        if isinstance(size2_str, str) and 'GB' in size2_str:
                            size2 = float(size2_str.replace(' GB', ''))
                        elif isinstance(size2_str, str) and 'MB' in size2_str:
                            size2 = float(size2_str.replace(' MB', '')) / 1024
                        else:
                            size2 = 0
                    
                    # Sumar el menor de los dos tamaños
                    espacio_ahorrado += min(size1, size2)
                
                st.metric("💾 Espacio Ahorrable (GB)", f"{espacio_ahorrado:.1f} GB")
        
        st.markdown("---")
        
        # Mostrar duplicados
        if st.session_state.duplicados:
            self._render_duplicates()
    
    def _render_duplicates(self):
        """Renderiza la lista de duplicados usando el nuevo gestor de pares"""
        # Crear datos para el DataFrame
        df_data = self._create_dataframe_data()
        
        if not df_data:
            st.warning("⚠️ No hay datos de duplicados para mostrar")
            return
        
        # Establecer la lista de pares en el gestor
        self.pairs_manager.set_pairs_list(df_data)
        
        # Mostrar interfaz principal del gestor de pares
        self.pairs_manager.render_main_interface()
        
        # Integrar con análisis de Plex existente
        current_pair = self.pairs_manager.navigation.get_current_pair()
        if current_pair:
            current_index = self.pairs_manager.navigation.get_current_index()
            self._render_current_pair_with_plex(current_pair, current_index)
    
    def _render_current_pair_with_plex(self, pair_data: Dict[str, Any], index: int):
        """Renderiza el par actual con análisis de Plex integrado"""
        # Mostrar información básica inmediatamente
        self._render_basic_info_immediate(pair_data, index)
        
        # Análisis de Plex si está habilitado
        if settings.get_plex_fetch_metadata() and self.plex_service.is_configured():
            # Cargar metadatos automáticamente si está habilitado
            self._render_plex_metadata_auto(pair_data, index)
        else:
            # Mostrar expander opcional si no está habilitado
            with st.expander("🎬 Metadatos de Plex (deshabilitado)", expanded=False):
                st.info("💡 Habilita 'Traer metadatos de Plex' en la configuración para ver metadatos automáticamente")
        
        # SIEMPRE mostrar reproductores (más consistente)
        self._render_video_comparison(pair_data, index)
        
        # Información y controles
        self._render_movie_controls(pair_data, index)
    
    def _parse_size_to_bytes(self, size_str: str) -> int:
        """Convierte una cadena de tamaño a bytes"""
        if not size_str or not isinstance(size_str, str):
            return 0
        
        try:
            if 'GB' in size_str:
                return int(float(size_str.replace(' GB', '')) * (1024**3))
            elif 'MB' in size_str:
                return int(float(size_str.replace(' MB', '')) * (1024**2))
            elif 'KB' in size_str:
                return int(float(size_str.replace(' KB', '')) * 1024)
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _create_dataframe_data(self) -> List[Dict[str, Any]]:
        """Crea los datos para el DataFrame"""
        df_data = []
        
        for i, duplicado in enumerate(st.session_state.duplicados):
            # Verificar si es una lista o un diccionario
            if isinstance(duplicado, list) and len(duplicado) >= 2:
                archivo1, archivo2 = duplicado[0], duplicado[1]
            elif isinstance(duplicado, dict):
                # Si ya es un diccionario, usar directamente
                # Los datos vienen en formato: {'Peli 1': ..., 'Ruta 1': ..., 'Tamaño 1': ..., etc.}
                archivo1 = {
                    'archivo': duplicado.get('Ruta 1', ''),
                    'nombre': duplicado.get('Peli 1', 'N/A'),
                    'tamaño': self._parse_size_to_bytes(duplicado.get('Tamaño 1', '0 GB'))
                }
                archivo2 = {
                    'archivo': duplicado.get('Ruta 2', ''),
                    'nombre': duplicado.get('Peli 2', 'N/A'),
                    'tamaño': self._parse_size_to_bytes(duplicado.get('Tamaño 2', '0 GB'))
                }
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
            
            # Mostrar información de carpeta
            self._render_folder_comparison(row, video_num)
            
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
    
    def _render_folder_comparison(self, row: Dict[str, Any], video_num: int):
        """Renderiza la comparación de carpetas entre los dos archivos"""
        try:
            # Obtener rutas de ambos archivos
            ruta1 = row.get('Ruta 1', '')
            ruta2 = row.get('Ruta 2', '')
            
            if not ruta1 or not ruta2:
                return
            
            # Extraer carpetas de las rutas
            from pathlib import Path
            carpeta1 = Path(ruta1).parent.name
            carpeta2 = Path(ruta2).parent.name
            
            # Mostrar información de carpeta
            if video_num == 1:
                st.write(f"📁 Carpeta: `{carpeta1}`")
            else:
                st.write(f"📁 Carpeta: `{carpeta2}`")
            
            # Comparar carpetas (solo mostrar una vez, en el primer video)
            if video_num == 1:
                if carpeta1 != carpeta2:
                    st.warning("⚠️ **Carpetas diferentes**")
                    st.info(f"📂 Izquierda: `{carpeta1}` | Derecha: `{carpeta2}`")
                else:
                    st.info("👁️ **Ojo que están en la misma carpeta**")
                    st.info(f"📂 Ambas en: `{carpeta1}`")
                    
        except Exception as e:
            logging.error(f"Error en comparación de carpetas: {e}")
    
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
            # Obtener tamaño real del archivo
            ruta1 = row.get('Ruta 1', '')
            if ruta1:
                file_info = self._get_file_info(ruta1)
                if file_info and 'size' in file_info:
                    size_gb = file_info['size'] / (1024**3)
                    st.write(f"📊 Tamaño: {size_gb:.2f} GB")
                else:
                    st.write(f"📊 Tamaño: {row.get('Tamaño 1 (GB)', 'N/A')} GB")
            else:
                st.write(f"📊 Tamaño: {row.get('Tamaño 1 (GB)', 'N/A')} GB")
            st.write(f"⏱️ Duración: {row.get('Duración 1', 'N/A')}")
            st.write(f"📁 Ruta: {row.get('Ruta 1', 'N/A')}")
            
            # Fecha de creación
            ruta1 = row.get('Ruta 1', '')
            if ruta1:
                creation_date1 = self._format_creation_date(ruta1)
                st.write(f"📅 Creado: {creation_date1}")
                
                # Obtener comparación para mostrar etiqueta
                ruta2 = row.get('Ruta 2', '')
                if ruta2:
                    comparison = self._compare_creation_dates(ruta1, ruta2)
                    if comparison['newer'] == 1:
                        st.markdown("🆕 **Archivo más nuevo**")
                    elif comparison['newer'] == 2:
                        st.markdown("📜 **Archivo más viejo**")
            
            # Información de video local
            if ruta1 and os.path.exists(ruta1):
                self._render_local_video_info(ruta1, f"local1_{index}")
        
        with col2:
            st.write("**Película 2:**")
            st.markdown(f"<h4 style='color: #ff7f0e'>{row.get('Peli 2', 'N/A')}</h4>", unsafe_allow_html=True)
            # Obtener tamaño real del archivo
            ruta2 = row.get('Ruta 2', '')
            if ruta2:
                file_info = self._get_file_info(ruta2)
                if file_info and 'size' in file_info:
                    size_gb = file_info['size'] / (1024**3)
                    st.write(f"📊 Tamaño: {size_gb:.2f} GB")
                else:
                    st.write(f"📊 Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            else:
                st.write(f"📊 Tamaño: {row.get('Tamaño 2 (GB)', 'N/A')} GB")
            st.write(f"⏱️ Duración: {row.get('Duración 2', 'N/A')}")
            st.write(f"📁 Ruta: {row.get('Ruta 2', 'N/A')}")
            
            # Fecha de creación
            ruta2 = row.get('Ruta 2', '')
            if ruta2:
                creation_date2 = self._format_creation_date(ruta2)
                st.write(f"📅 Creado: {creation_date2}")
                
                # Obtener comparación para mostrar etiqueta
                ruta1 = row.get('Ruta 1', '')
                if ruta1:
                    comparison = self._compare_creation_dates(ruta1, ruta2)
                    if comparison['newer'] == 2:
                        st.markdown("🆕 **Archivo más nuevo**")
                    elif comparison['newer'] == 1:
                        st.markdown("📜 **Archivo más viejo**")
            
            # Información de video local
            ruta2 = row.get('Ruta 2', '')
            if ruta2 and os.path.exists(ruta2):
                self._render_local_video_info(ruta2, f"local2_{index}")
        
        # Comparación de fechas de creación
        ruta1 = row.get('Ruta 1', '')
        ruta2 = row.get('Ruta 2', '')
        if ruta1 and ruta2:
            self._render_creation_date_comparison(ruta1, ruta2)
        
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
        
        # Verificar si son la misma película en Plex
        if library_info1 and library_info2:
            title1 = library_info1.get('title', '')
            title2 = library_info2.get('title', '')
            year1 = library_info1.get('year', '')
            year2 = library_info2.get('year', '')
            
            if title1 == title2 and year1 == year2 and title1 != 'N/A':
                # Usar el nuevo análisis de ediciones
                self._render_plex_editions_analysis(plex_info, row, index)
    
    def _render_plex_editions_analysis(self, plex_info: Dict, row: Dict[str, Any], index: int):
        """Renderiza el análisis de ediciones usando PlexEditionsManager"""
        st.markdown("---")
        st.subheader("🔍 Análisis de Duplicados con Ediciones")
        
        try:
            # Obtener rutas de archivos
            file1_path = row.get('Ruta 1', '')
            file2_path = row.get('Ruta 2', '')
            
            # Mostrar indicador de progreso para análisis que puede tardar
            with st.spinner("🔍 Analizando duplicados (calculando hash si es necesario)..."):
                # Análisis completo con ediciones
                analysis = self.plex_editions_manager.analyze_duplicate_pair_with_editions(
                    file1_path, file2_path, plex_info['file1'], plex_info['file2']
                )
            
            # Mostrar resultados del análisis
            self._display_editions_analysis(analysis, file1_path, file2_path, index)
            
        except Exception as e:
            st.error(f"❌ Error en análisis de ediciones: {e}")
            # Fallback al método anterior
            self._render_legacy_duplicate_analysis(plex_info, row, index)
    
    def _display_editions_analysis(self, analysis: Dict, file1_path: str, file2_path: str, index: int):
        """Muestra los resultados del análisis de ediciones"""
        
        if not analysis['same_movie']:
            st.info("🎬 **Películas diferentes** según Plex")
            return
        
        # Mostrar información de ediciones existentes
        if analysis.get('has_existing_editions', False):
            st.info(f"📚 **Ediciones existentes**: {len(analysis['existing_editions'])} encontradas")
            
            with st.expander("Ver ediciones existentes"):
                for edition in analysis['existing_editions']:
                    st.write(f"• **{edition['edition']}** ({edition['year']})")
                    if edition.get('summary'):
                        st.write(f"  _{edition['summary'][:100]}..._")
        
        # Mostrar si los archivos ya tienen ediciones
        if analysis.get('file1_has_edition', False):
            st.warning("⚠️ **Archivo 1** ya tiene una edición asignada")
            edition_info = analysis.get('file1_edition', {})
            st.write(f"   Edición: **{edition_info.get('edition', 'N/A')}**")
        
        if analysis.get('file2_has_edition', False):
            st.warning("⚠️ **Archivo 2** ya tiene una edición asignada")
            edition_info = analysis.get('file2_edition', {})
            st.write(f"   Edición: **{edition_info.get('edition', 'N/A')}**")
        
        # Mostrar recomendaciones
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            st.info("💡 **Recomendaciones:**")
            for rec in recommendations:
                st.write(f"• {rec}")
        
        # Mostrar análisis específico
        if analysis['recommendation'] == 'create_editions':
            self._render_editions_creation_ui(analysis, file1_path, file2_path, index)
        elif analysis['recommendation'] == 'delete_duplicate':
            self._render_delete_duplicate_ui(analysis, file1_path, file2_path, index)
        else:
            st.warning(f"⚠️ **Análisis no concluyente**: {analysis.get('message', 'Error desconocido')}")
    
    def _render_editions_creation_ui(self, analysis: Dict, file1_path: str, file2_path: str, index: int):
        """Renderiza la UI para crear ediciones"""
        
        if 'size_difference_percent' in analysis:
            st.warning("🎬 **MISMA PELÍCULA, ARCHIVOS DIFERENTES**")
            st.info(f"💡 **Tamaños muy diferentes**: {analysis['file1_size_gb']:.2f}GB vs {analysis['file2_size_gb']:.2f}GB ({analysis['size_difference_percent']:.1f}% diferencia)")
        else:
            st.warning("🎬 **MISMA PELÍCULA, ARCHIVOS DIFERENTES**")
            st.info("💡 **Opciones**: Puedes crear ediciones diferentes en Plex")
        
        # Botones para crear ediciones
        col_edit1, col_edit2 = st.columns(2)
        
        with col_edit1:
            if st.button("🎬 Crear Edición - Archivo 1", key=f"edition1_{index}"):
                self._show_edition_creator_advanced(file1_path, analysis, f"edition1_{index}")
        
        with col_edit2:
            if st.button("🎬 Crear Edición - Archivo 2", key=f"edition2_{index}"):
                self._show_edition_creator_advanced(file2_path, analysis, f"edition2_{index}")
    
    def _render_delete_duplicate_ui(self, analysis: Dict, file1_path: str, file2_path: str, index: int):
        """Renderiza la UI para eliminar duplicados"""
        st.error("⚠️ **MISMO ARCHIVO**: El hash es idéntico")
        st.info("💡 **Recomendación**: Es el mismo archivo con diferente nombre. Puedes eliminar uno de los dos.")
        
        # Botones para eliminar duplicados
        col_del1, col_del2 = st.columns(2)
        
        with col_del1:
            if st.button("🗑️ Eliminar Archivo 1", key=f"delete1_{index}"):
                st.warning("⚠️ Función de eliminación no implementada por seguridad")
        
        with col_del2:
            if st.button("🗑️ Eliminar Archivo 2", key=f"delete2_{index}"):
                st.warning("⚠️ Función de eliminación no implementada por seguridad")
    
    def _show_edition_creator_advanced(self, file_path: str, analysis: Dict, key: str):
        """Muestra el creador de ediciones avanzado"""
        st.markdown("---")
        st.subheader("🎬 Crear Edición en Plex")
        
        # Mostrar información del archivo
        filename = os.path.basename(file_path)
        st.write(f"**Archivo:** {filename}")
        
        # Obtener título de la película
        movie_title = "Película"
        if analysis.get('file1_edition'):
            movie_title = analysis['file1_edition'].get('title', 'Película')
        elif analysis.get('file2_edition'):
            movie_title = analysis['file2_edition'].get('title', 'Película')
        
        st.write(f"**Película:** {movie_title}")
        
        # Obtener sugerencias de edición
        suggestions = self.plex_editions_manager.get_edition_suggestions_for_movie(movie_title)
        
        # Selector de edición
        selected_edition = st.selectbox(
            "Selecciona el tipo de edición:",
            ["Personalizada"] + suggestions,
            key=f"edition_type_{key}"
        )
        
        # Campo para edición personalizada
        if selected_edition == "Personalizada":
            custom_edition = st.text_input(
                "Nombre de la edición:",
                placeholder="Ej: Edición del Director, Versión Extendida...",
                key=f"custom_edition_{key}"
            )
            edition_name = custom_edition
        else:
            edition_name = selected_edition
        
        # Opción de subcarpeta
        create_subfolder = st.checkbox(
            "Crear subcarpeta para la edición",
            value=False,
            key=f"subfolder_{key}"
        )
        
        # Botón para aplicar
        if st.button("✅ Crear Edición", key=f"apply_edition_{key}"):
            if edition_name:
                if self.plex_editions_manager.creator.validate_edition_name(edition_name):
                    new_path = self.plex_editions_manager.create_edition_for_file(
                        file_path, movie_title, edition_name, create_subfolder
                    )
                    
                    if new_path:
                        st.success("✅ Edición creada exitosamente!")
                        st.info(f"📁 **Nuevo archivo:** {os.path.basename(new_path)}")
                        st.info("💡 **Siguiente paso:** Ejecuta un escaneo en Plex para que detecte la nueva edición")
                        
                        # Mostrar instrucciones
                        st.markdown("### 📋 Instrucciones para Plex:")
                        st.markdown("""
                        1. **Abre Plex Media Server**
                        2. **Ve a la biblioteca** donde está la película
                        3. **Haz clic en "Más" → "Escanear archivos de biblioteca"**
                        4. **Espera** a que termine el escaneo
                        5. **Verifica** que aparezca la nueva edición
                        """)
                    else:
                        st.error("❌ Error creando la edición")
                else:
                    st.error("❌ Nombre de edición inválido. Evita caracteres especiales.")
            else:
                st.error("❌ Debes especificar un nombre para la edición")
    
    def _render_legacy_duplicate_analysis(self, plex_info: Dict, row: Dict[str, Any], index: int):
        """Método de respaldo para análisis de duplicados (método anterior)"""
        st.warning("⚠️ Usando análisis de respaldo...")
        
        # Obtener información de archivos (tamaño y fecha)
        file_info1 = self._get_file_info(row.get('Ruta 1', ''))
        file_info2 = self._get_file_info(row.get('Ruta 2', ''))

        if file_info1 and file_info2:
            size1 = file_info1['size']
            size2 = file_info2['size']
            
            # Calcular diferencia porcentual de tamaño
            size_diff_percent = abs(size1 - size2) / max(size1, size2) * 100 if max(size1, size2) > 0 else 0
            
            # DECISIÓN INTELIGENTE: Solo calcular hash si tamaños son similares
            if size_diff_percent > 10:  # Si la diferencia es mayor al 10%
                st.warning("🎬 **MISMA PELÍCULA, ARCHIVOS DIFERENTES**")
                st.info(f"💡 **Tamaños muy diferentes**: {size1/1024/1024/1024:.2f}GB vs {size2/1024/1024/1024:.2f}GB ({size_diff_percent:.1f}% diferencia)")
                st.info("💡 **Opciones**: Puedes crear ediciones diferentes en Plex")
                
                # Botones para crear ediciones (sin calcular hash)
                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    if st.button("🎬 Crear Edición - Película 1", key=f"edition1_{index}"):
                        self._show_edition_creator_advanced(row.get('Ruta 1', ''), {'file1_edition': {'title': 'Película'}}, f"edition1_{index}")
                with col_edit2:
                    if st.button("🎬 Crear Edición - Película 2", key=f"edition2_{index}"):
                        self._show_edition_creator_advanced(row.get('Ruta 2', ''), {'file2_edition': {'title': 'Película'}}, f"edition2_{index}")
            else:
                # Tamaños similares - proceder a calcular hash
                st.info(f"📊 **Tamaños similares**: {size1/1024/1024/1024:.2f}GB vs {size2/1024/1024/1024:.2f}GB ({size_diff_percent:.1f}% diferencia)")
                st.info("🔍 Calculando hash para verificar si son idénticos...")
                
                with st.spinner("🔍 Calculando hash de archivos..."):
                    hash1 = self._calculate_file_hash(row.get('Ruta 1', ''))
                    hash2 = self._calculate_file_hash(row.get('Ruta 2', ''))
                
                if hash1 and hash2:
                    if hash1 == hash2:
                        st.error("⚠️ **MISMO ARCHIVO**: El hash es idéntico")
                        st.info("💡 **Recomendación**: Es el mismo archivo con diferente nombre. Puedes eliminar uno de los dos.")
                    else:
                        st.warning("🎬 **MISMA PELÍCULA, ARCHIVOS DIFERENTES**")
                        st.info("💡 **Opciones**: Puedes crear ediciones diferentes en Plex")
                        
                        # Botones para crear ediciones
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            if st.button("🎬 Crear Edición - Película 1", key=f"edition1_{index}"):
                                self._show_edition_creator_advanced(row.get('Ruta 1', ''), {'file1_edition': {'title': 'Película'}}, f"edition1_{index}")
                        with col_edit2:
                            if st.button("🎬 Crear Edición - Película 2", key=f"edition2_{index}"):
                                self._show_edition_creator_advanced(row.get('Ruta 2', ''), {'file2_edition': {'title': 'Película'}}, f"edition2_{index}")
                else:
                    # Fallback si el cálculo de hash falla (a pesar de tamaños similares)
                    st.warning("⚠️ No se pudo calcular hash, usando comparación por fecha...")
                    if (file_info1['mtime'] == file_info2['mtime']):
                        st.error("⚠️ **MISMO ARCHIVO**: Tamaño y fecha idénticos")
                        st.info("💡 **Recomendación**: Es el mismo archivo con diferente nombre. Puedes eliminar uno de los dos.")
                    else:
                        st.warning("🎬 **MISMA PELÍCULA, ARCHIVOS DIFERENTES**")
                        st.info("💡 **Opciones**: Puedes crear ediciones diferentes en Plex")
                        
                        # Botones para crear ediciones
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            if st.button("🎬 Crear Edición - Película 1", key=f"edition1_{index}"):
                                self._show_edition_creator_advanced(row.get('Ruta 1', ''), {'file1_edition': {'title': 'Película'}}, f"edition1_{index}")
                        with col_edit2:
                            if st.button("🎬 Crear Edición - Película 2", key=f"edition2_{index}"):
                                self._show_edition_creator_advanced(row.get('Ruta 2', ''), {'file2_edition': {'title': 'Película'}}, f"edition2_{index}")
        else:
            st.warning("⚠️ No se pudo obtener información de tamaño/fecha de los archivos.")
    
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
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("💾 Renombrar", key=f"rename_btn_{key}"):
                    self._rename_file(file_path, new_name)
            
            with col2:
                # Botón para refrescar búsqueda de Plex después de renombrar
                if st.button("🔄 Refrescar Plex", key=f"refresh_plex_{key}", 
                           help="Refresca la búsqueda de Plex para ver si ahora encuentra el archivo"):
                    self._refresh_plex_search_for_file(file_path)
        
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
            
            # Refrescar biblioteca de Plex automáticamente
            self._refresh_plex_after_rename()
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error renombrando archivo: {e}")
    
    def _create_edition(self, file_path: str, selected_movie: str, edition_name: str):
        """Crea una edición diferente de una película con soporte para rutas UNC"""
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
            
            # Verificar si es una ruta UNC
            is_unc = file_path.startswith('\\')
            
            if is_unc:
                # Para rutas UNC, usar manejo especial
                try:
                    # Intentar renombrar directamente
                    os.rename(file_path, new_path)
                    st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
                    
                    # Refrescar biblioteca de Plex automáticamente
                    self._refresh_plex_after_rename()
                    
                    st.rerun()
                except Exception as unc_error:
                    st.warning(f"⚠️ Error con ruta UNC: {unc_error}")
                    st.info("💡 Intentando con método alternativo...")
                    
                    # Método alternativo para UNC
                    try:
                        import shutil
                        shutil.move(file_path, new_path)
                        st.success(f"✅ Edición creada (método alternativo): {os.path.basename(new_path)}")
                        
                        # Refrescar biblioteca de Plex automáticamente
                        self._refresh_plex_after_rename()
                        
                        st.rerun()
                    except Exception as alt_error:
                        st.error(f"❌ Error con método alternativo: {alt_error}")
                        st.error("💡 Verifica que tienes permisos de escritura en la ruta UNC")
            else:
                # Para rutas locales, usar método normal
                os.rename(file_path, new_path)
                st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
                
                # Refrescar biblioteca de Plex automáticamente
                self._refresh_plex_after_rename()
                
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error creando edición: {e}")
    
    def _refresh_plex_after_rename(self):
        """Refresca automáticamente la biblioteca de Plex después de un renombrado"""
        try:
            # Verificar si Plex está configurado
            if not self.plex_refresh_service.is_configured():
                st.info("💡 Plex no configurado - no se puede refrescar automáticamente")
                return
            
            # Determinar qué biblioteca refrescar basándose en la configuración
            movies_library = settings.get_plex_movies_library()
            tv_library = settings.get_plex_tv_shows_library()
            
            # Intentar refrescar biblioteca de películas primero
            if movies_library:
                with st.spinner("🔄 Refrescando biblioteca de películas..."):
                    if self.plex_refresh_service.refresh_library_by_name(movies_library):
                        st.success("✅ Biblioteca de películas refrescada automáticamente")
                    else:
                        st.warning("⚠️ No se pudo refrescar la biblioteca de películas")
            
            # Si hay biblioteca de series configurada, también refrescarla
            if tv_library and tv_library != movies_library:
                with st.spinner("🔄 Refrescando biblioteca de series..."):
                    if self.plex_refresh_service.refresh_library_by_name(tv_library):
                        st.success("✅ Biblioteca de series refrescada automáticamente")
                    else:
                        st.warning("⚠️ No se pudo refrescar la biblioteca de series")
                        
        except Exception as e:
            st.warning(f"⚠️ Error refrescando Plex automáticamente: {e}")
            st.info("💡 Puedes refrescar manualmente desde la configuración de Plex")
    
    def _refresh_plex_search_for_file(self, file_path: str):
        """Refresca la búsqueda de Plex para un archivo específico"""
        try:
            with st.spinner("🔄 Refrescando búsqueda de Plex..."):
                # Refrescar biblioteca primero
                self._refresh_plex_after_rename()
                
                # Esperar un momento para que Plex procese
                import time
                time.sleep(2)
                
                # Buscar el archivo nuevamente en Plex
                plex_info = self.plex_service.get_library_info_by_filename(file_path)
                
                if plex_info:
                    st.success("✅ ¡Archivo encontrado en Plex!")
                    st.info(f"📚 Biblioteca: {plex_info.get('library_name', 'N/A')}")
                    st.info(f"🎬 Título: {plex_info.get('title', 'N/A')}")
                    st.info(f"📅 Año: {plex_info.get('year', 'N/A')}")
                    st.rerun()  # Refrescar la interfaz para mostrar el nuevo estado
                else:
                    st.warning("⚠️ Archivo aún no encontrado en Plex")
                    st.info("💡 Puede que necesites esperar más tiempo o refrescar manualmente")
                    
        except Exception as e:
            st.error(f"❌ Error refrescando búsqueda: {e}")
    
    def _save_scan_data(self):
        """Guarda los datos del escaneo actual"""
        try:
            if not hasattr(st.session_state, 'duplicados') or not st.session_state.duplicados:
                st.warning("⚠️ No hay datos de escaneo para guardar")
                return
            
            # Obtener ruta escaneada
            scan_path = getattr(st.session_state, 'last_scan_path', 'Carpeta desconocida')
            
            # Guardar datos
            file_path = self.scan_data_manager.save_scan_data(
                pairs_data=st.session_state.duplicados,
                scan_path=scan_path
            )
            
            st.success(f"✅ Escaneo guardado: {Path(file_path).name}")
            
        except Exception as e:
            st.error(f"❌ Error guardando escaneo: {e}")
    
    def _show_load_scan_interface(self):
        """Muestra la interfaz para cargar un escaneo"""
        try:
            scans = self.scan_data_manager.get_available_scans()
            
            if not scans:
                st.info("📋 No hay escaneos guardados")
                return
            
            st.subheader("📂 Cargar Escaneo Guardado")
            
            # Crear opciones para el selectbox
            scan_options = []
            for scan in scans:
                scan_date = scan.get('scan_date', 'N/A')
                scan_path = scan.get('scan_path', 'N/A')
                total_pairs = scan.get('total_pairs', 0)
                scan_options.append(f"{scan_date[:19]} - {scan_path} ({total_pairs} pares)")
            
            selected_scan = st.selectbox(
                "Seleccionar escaneo:",
                options=range(len(scans)),
                format_func=lambda x: scan_options[x],
                key="load_scan_select"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Cargar Escaneo Seleccionado"):
                    # Cargar directamente el escaneo
                    self._load_scan_data(scans[selected_scan]['file_path'])
                    # Desactivar la interfaz de carga
                    st.session_state.show_load_interface = False
            with col2:
                if st.button("❌ Cancelar"):
                    # Desactivar la interfaz de carga
                    st.session_state.show_load_interface = False
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error mostrando escaneos: {e}")
    
    def _load_scan_data(self, file_path: str):
        """Carga los datos de un escaneo"""
        try:
            logging.info(f"📂 Cargando escaneo desde: {file_path}")
            logging.info(f"🔍 _load_scan_data llamado con archivo: {file_path}")
            scan_data = self.scan_data_manager.load_scan_data(file_path)
            
            # Actualizar estado de sesión
            pairs_data = scan_data.get('pairs_data', [])
            logging.info(f"📊 Datos cargados: {len(pairs_data)} pares")
            
            # Establecer datos en session_state
            st.session_state.duplicados = pairs_data
            st.session_state.last_scan_path = scan_data.get('metadata', {}).get('scan_path', '')
            
            # Establecer la lista en el pairs_manager
            self.pairs_manager.set_pairs_list(pairs_data)
            logging.info(f"🔄 Lista establecida en pairs_manager: {len(pairs_data)} pares")
            
            # Actualizar contadores
            settings.set_total_pairs(len(pairs_data))
            settings.set_pairs_deleted(0)
            logging.info(f"📈 Contadores actualizados: total={len(pairs_data)}")
            
            # Debug: verificar que los datos se establecieron correctamente
            logging.info(f"🔍 Después de cargar - st.session_state.duplicados: {len(st.session_state.duplicados) if st.session_state.duplicados else 0}")
            logging.info(f"🔍 Después de cargar - pairs_manager tiene: {len(self.pairs_manager.get_pairs_list()) if hasattr(self.pairs_manager, 'get_pairs_list') else 'N/A'}")
            
            # Verificar que los datos se cargaron correctamente
            if len(pairs_data) > 0:
                st.success(f"✅ Escaneo cargado exitosamente: {len(pairs_data)} pares")
                st.info("🔄 Los datos se han cargado correctamente.")
                
                # Marcar que se ha cargado un escaneo
                st.session_state.scan_loaded = True
                
                # Mostrar los datos inmediatamente
                self._render_loaded_data(pairs_data)
            else:
                st.warning("⚠️ El archivo de escaneo está vacío")
            
        except Exception as e:
            st.error(f"❌ Error cargando escaneo: {e}")
            logging.error(f"❌ Error cargando escaneo: {e}")
    
    def _render_loaded_data(self, pairs_data):
        """Renderiza los datos cargados inmediatamente"""
        st.subheader("📊 Datos Cargados")
        
        # Métricas
        total_duplicados = len(pairs_data)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔍 Duplicados Encontrados", total_duplicados)
        with col2:
            st.metric("📁 Total Películas", total_duplicados * 2)
        with col3:
            st.metric("💾 Espacio Ahorrable", "Calculando...")
        
        # Mostrar algunos ejemplos
        st.subheader("🔍 Ejemplos de Duplicados")
        for i, duplicado in enumerate(pairs_data[:5]):  # Mostrar solo los primeros 5
            with st.expander(f"Par {i+1}: {duplicado.get('Peli 1', 'N/A')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Archivo 1:** {duplicado.get('Peli 1', 'N/A')}")
                    st.write(f"**Ruta 1:** {duplicado.get('Ruta 1', 'N/A')}")
                    st.write(f"**Tamaño 1:** {duplicado.get('Tamaño 1 (GB)', 'N/A')} GB")
                    # Mostrar información de carpeta
                    self._render_folder_info_for_loaded_data(duplicado, 1)
                with col2:
                    st.write(f"**Archivo 2:** {duplicado.get('Peli 2', 'N/A')}")
                    st.write(f"**Ruta 2:** {duplicado.get('Ruta 2', 'N/A')}")
                    st.write(f"**Tamaño 2:** {duplicado.get('Tamaño 2 (GB)', 'N/A')} GB")
                    # Mostrar información de carpeta
                    self._render_folder_info_for_loaded_data(duplicado, 2)
        
        if len(pairs_data) > 5:
            st.info(f"📋 Mostrando 5 de {len(pairs_data)} duplicados. Usa la navegación para ver más.")
    
    def _render_folder_info_for_loaded_data(self, duplicado: Dict[str, Any], video_num: int):
        """Renderiza la información de carpeta para datos cargados"""
        try:
            # Obtener rutas de ambos archivos
            ruta1 = duplicado.get('Ruta 1', '')
            ruta2 = duplicado.get('Ruta 2', '')
            
            if not ruta1 or not ruta2:
                return
            
            # Extraer carpetas de las rutas
            from pathlib import Path
            carpeta1 = Path(ruta1).parent.name
            carpeta2 = Path(ruta2).parent.name
            
            # Mostrar información de carpeta
            if video_num == 1:
                st.write(f"📁 **Carpeta:** `{carpeta1}`")
            else:
                st.write(f"📁 **Carpeta:** `{carpeta2}`")
            
            # Comparar carpetas (solo mostrar una vez, en el primer video)
            if video_num == 1:
                if carpeta1 != carpeta2:
                    st.warning("⚠️ **Carpetas diferentes**")
                    st.info(f"📂 Izquierda: `{carpeta1}` | Derecha: `{carpeta2}`")
                else:
                    st.info("👁️ **Ojo que están en la misma carpeta**")
                    st.info(f"📂 Ambas en: `{carpeta1}`")
                    
        except Exception as e:
            logging.error(f"Error en comparación de carpetas para datos cargados: {e}")
    
    def _show_saved_scans(self):
        """Muestra la lista de escaneos guardados"""
        try:
            scans = self.scan_data_manager.get_available_scans()
            
            if not scans:
                st.info("📋 No hay escaneos guardados")
                return
            
            st.subheader("📋 Escaneos Guardados")
            
            for i, scan in enumerate(scans):
                with st.expander(f"📁 {scan['filename']}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Ruta:** {scan['scan_path']}")
                        st.write(f"**Fecha:** {scan['scan_date']}")
                    
                    with col2:
                        st.write(f"**Pares:** {scan['total_pairs']}")
                        st.write(f"**Archivo:** {scan['filename']}")
                    
                    with col3:
                        if st.button(f"📂 Cargar", key=f"load_{i}"):
                            logging.info(f"🔍 Botón Cargar presionado para escaneo {i}: {scan['filename']}")
                            # Usar session_state para pasar el archivo a cargar
                            st.session_state.load_from_list_file = scan['file_path']
                            st.session_state.load_from_list_filename = scan['filename']
                            logging.info(f"📝 Archivo guardado en session_state: {scan['file_path']}")
                            st.rerun()
                        
                        if st.button(f"🗑️ Eliminar", key=f"delete_{i}"):
                            if self.scan_data_manager.delete_scan_data(scan['file_path']):
                                st.success("✅ Escaneo eliminado")
                                st.rerun()
                            else:
                                st.error("❌ Error eliminando escaneo")
                
        except Exception as e:
            st.error(f"❌ Error mostrando escaneos: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calcula el hash MD5 de un archivo con indicador de progreso"""
        try:
            # Normalizar la ruta para rutas UNC
            normalized_path = os.path.normpath(file_path)
            
            # Para rutas UNC, intentar acceso directo sin verificar existencia previa
            if file_path.startswith('\\\\'):
                logging.info(f"🔗 Calculando hash de ruta UNC: {file_path}")
                try:
                    hash_md5 = hashlib.md5()
                    bytes_read = 0
                    chunk_size = 8192
                    
                    # Obtener tamaño del archivo para mostrar progreso
                    try:
                        file_size = os.path.getsize(normalized_path)
                        logging.info(f"📊 Tamaño del archivo: {file_size / (1024*1024):.1f} MB")
                    except:
                        file_size = 0
                    
                    with open(normalized_path, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            hash_md5.update(chunk)
                            bytes_read += len(chunk)
                            
                            # Mostrar progreso cada 10MB
                            if file_size > 0 and bytes_read % (10 * 1024 * 1024) == 0:
                                progress = (bytes_read / file_size) * 100
                                logging.info(f"🔄 Progreso hash: {progress:.1f}% ({bytes_read / (1024*1024):.1f}MB/{file_size / (1024*1024):.1f}MB)")
                    
                    logging.info(f"✅ Hash calculado: {hash_md5.hexdigest()[:16]}...")
                    return hash_md5.hexdigest()
                except (OSError, IOError) as e:
                    logging.warning(f"⚠️ No se puede acceder a ruta UNC {file_path}: {e}")
                    return None
            else:
                # Para rutas locales, verificar existencia
                if not os.path.exists(normalized_path):
                    st.warning(f"⚠️ Archivo no encontrado: {normalized_path}")
                    return None
                
                # Verificar que es un archivo (no directorio)
                if not os.path.isfile(normalized_path):
                    st.warning(f"⚠️ No es un archivo: {normalized_path}")
                    return None
                
                hash_md5 = hashlib.md5()
                bytes_read = 0
                chunk_size = 8192
                
                # Obtener tamaño del archivo para mostrar progreso
                try:
                    file_size = os.path.getsize(normalized_path)
                    if file_size > 50 * 1024 * 1024:  # Solo mostrar progreso para archivos > 50MB
                        logging.info(f"📊 Calculando hash de archivo local: {file_size / (1024*1024):.1f} MB")
                except:
                    file_size = 0
                
                # Usar try/except para manejar errores de acceso
                try:
                    with open(normalized_path, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            hash_md5.update(chunk)
                            bytes_read += len(chunk)
                            
                            # Mostrar progreso cada 10MB para archivos grandes
                            if file_size > 50 * 1024 * 1024 and bytes_read % (10 * 1024 * 1024) == 0:
                                progress = (bytes_read / file_size) * 100
                                logging.info(f"🔄 Progreso hash: {progress:.1f}% ({bytes_read / (1024*1024):.1f}MB/{file_size / (1024*1024):.1f}MB)")
                    
                    return hash_md5.hexdigest()
                except (OSError, IOError) as e:
                    st.warning(f"⚠️ Error accediendo al archivo: {e}")
                    return None
                
        except Exception as e:
            st.warning(f"⚠️ Error calculando hash: {e}")
            return None
    
    def _get_file_info(self, file_path: str) -> Optional[Dict]:
        """Obtiene información básica del archivo (tamaño y fecha)"""
        try:
            normalized_path = os.path.normpath(file_path)
            
            if not os.path.exists(normalized_path):
                return None
            
            stat = os.stat(normalized_path)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'ctime': stat.st_ctime  # Fecha de creación
            }
        except Exception as e:
            st.warning(f"⚠️ Error obteniendo info del archivo: {e}")
            return None
    
    def _format_creation_date(self, file_path: str) -> str:
        """Formatea la fecha de creación del archivo"""
        try:
            file_info = self._get_file_info(file_path)
            if file_info and 'ctime' in file_info:
                import datetime
                creation_time = datetime.datetime.fromtimestamp(file_info['ctime'])
                return creation_time.strftime("%Y-%m-%d %H:%M:%S")
            return "N/A"
        except Exception:
            return "N/A"
    
    def _compare_creation_dates(self, file_path1: str, file_path2: str) -> Dict[str, Any]:
        """Compara las fechas de creación de dos archivos"""
        try:
            info1 = self._get_file_info(file_path1)
            info2 = self._get_file_info(file_path2)
            
            if not info1 or not info2 or 'ctime' not in info1 or 'ctime' not in info2:
                return {'newer': None, 'difference': None}
            
            ctime1 = info1['ctime']
            ctime2 = info2['ctime']
            
            if ctime1 > ctime2:
                newer = 1
                difference = ctime1 - ctime2
            elif ctime2 > ctime1:
                newer = 2
                difference = ctime2 - ctime1
            else:
                newer = None
                difference = 0
            
            return {
                'newer': newer,
                'difference': difference
            }
        except Exception:
            return {'newer': None, 'difference': None}
    
    def _render_creation_date_comparison(self, file_path1: str, file_path2: str):
        """Renderiza la comparación de fechas de creación"""
        try:
            comparison = self._compare_creation_dates(file_path1, file_path2)
            
            if comparison['newer'] is None:
                return
            
            import datetime
            
            # Calcular diferencia en formato legible
            if comparison['difference']:
                diff_seconds = comparison['difference']
                if diff_seconds < 60:
                    diff_text = f"{int(diff_seconds)} segundos"
                elif diff_seconds < 3600:
                    diff_text = f"{int(diff_seconds/60)} minutos"
                elif diff_seconds < 86400:
                    diff_text = f"{int(diff_seconds/3600)} horas"
                else:
                    diff_text = f"{int(diff_seconds/86400)} días"
            else:
                diff_text = "mismo momento"
            
            # Mostrar resultado de la comparación
            st.markdown("---")
            st.subheader("📅 Comparación de Fechas de Creación")
            
            if comparison['newer'] == 1:
                st.success(f"🆕 **Película 1 es más reciente** (por {diff_text})")
                st.info("💡 La Película 1 fue creada más tarde, probablemente es la versión más actualizada")
            elif comparison['newer'] == 2:
                st.success(f"🆕 **Película 2 es más reciente** (por {diff_text})")
                st.info("💡 La Película 2 fue creada más tarde, probablemente es la versión más actualizada")
            else:
                st.info("📅 **Ambas películas fueron creadas al mismo tiempo**")
                
        except Exception as e:
            st.warning(f"⚠️ Error comparando fechas: {e}")
    
    def _show_edition_creator(self, file_path: str, movie_title: str, key: str):
        """Muestra el creador de ediciones para Plex"""
        st.markdown("---")
        st.subheader("🎬 Crear Edición en Plex")
        
        # Mostrar información del archivo
        st.write(f"**Archivo:** {os.path.basename(file_path)}")
        st.write(f"**Película:** {movie_title}")
        
        # Opciones de edición predefinidas
        edition_options = [
            "Edición del Director",
            "Edición Especial",
            "Edición Extendida", 
            "Edición Teatral",
            "Edición 20 Aniversario",
            "Edición 4K",
            "Edición Remasterizada",
            "Edición Sin Cortes",
            "Edición Unrated",
            "Edición Especial 25 Aniversario"
        ]
        
        # Selector de edición
        selected_edition = st.selectbox(
            "Selecciona el tipo de edición:",
            ["Personalizada"] + edition_options,
            key=f"edition_type_{key}"
        )
        
        # Campo para edición personalizada
        if selected_edition == "Personalizada":
            custom_edition = st.text_input(
                "Nombre de la edición:",
                placeholder="Ej: Edición del Director, Versión Extendida...",
                key=f"custom_edition_{key}"
            )
            edition_name = custom_edition
        else:
            edition_name = selected_edition
        
        # Botón para aplicar
        if st.button("✅ Aplicar Edición", key=f"apply_edition_{key}"):
            if edition_name:
                self._apply_plex_edition(file_path, edition_name)
            else:
                st.error("❌ Debes especificar un nombre para la edición")
    
    def _apply_plex_edition(self, file_path: str, edition_name: str):
        """Aplica la edición renombrando el archivo según las convenciones de Plex"""
        try:
            # Obtener directorio y nombre base
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            # Crear nuevo nombre con formato Plex: {edition-Nombre de la Edición}
            new_filename = f"{name} {{edition-{edition_name}}}{ext}"
            new_path = os.path.join(directory, new_filename)
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            
            st.success(f"✅ Archivo renombrado exitosamente!")
            st.info(f"📁 **Nuevo nombre:** {new_filename}")
            st.info("💡 **Siguiente paso:** Ejecuta un escaneo en Plex para que detecte la nueva edición")
            
            # Mostrar instrucciones
            st.markdown("### 📋 Instrucciones para Plex:")
            st.markdown("""
            1. **Abre Plex Media Server**
            2. **Ve a la biblioteca** donde está la película
            3. **Haz clic en "Más" → "Escanear archivos de biblioteca"**
            4. **Espera** a que termine el escaneo
            5. **Verifica** que aparezca la nueva edición
            """)
            
        except Exception as e:
            st.error(f"❌ Error aplicando edición: {e}")
    
    def _render_telegram_tab(self):
        """Renderiza la pestaña de configuración de Telegram"""
        st.subheader("📱 Configuración de Telegram")
        
        # Verificar si Telegram está configurado
        telegram_service = self.telegram_service
        is_configured = telegram_service.is_configured()
        
        if is_configured:
            st.success("✅ Telegram configurado correctamente")
            
            # Probar conexión
            if st.button("🔍 Probar Conexión"):
                with st.spinner("Probando conexión..."):
                    if telegram_service.test_connection():
                        st.success("✅ Conexión exitosa con Telegram")
                    else:
                        st.error("❌ Error de conexión con Telegram")
        else:
            st.warning("⚠️ Telegram no está configurado")
            st.info("💡 Configura el bot token y channel ID en la configuración")
        
        # Configuración básica
        st.subheader("⚙️ Configuración")
        
        # Bot Token
        bot_token = st.text_input(
            "Bot Token",
            value=settings.get_telegram_bot_token() or "",
            type="password",
            help="Token del bot de Telegram"
        )
        
        # Channel ID
        channel_id = st.text_input(
            "Channel ID",
            value=settings.get_telegram_channel_id() or "",
            help="ID del canal de Telegram"
        )
        
        # Guardar configuración
        if st.button("💾 Guardar Configuración"):
            try:
                settings.set_telegram_bot_token(bot_token)
                settings.set_telegram_channel_id(channel_id)
                st.success("✅ Configuración guardada")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error guardando configuración: {e}")
        
        # Funcionalidades de Telegram
        if is_configured:
            st.subheader("🚀 Funcionalidades")
            
            # Enviar mensaje de prueba
            if st.button("📤 Enviar Mensaje de Prueba"):
                with st.spinner("Enviando mensaje..."):
                    try:
                        result = telegram_service.send_message("🧪 Mensaje de prueba desde la aplicación")
                        if result:
                            st.success("✅ Mensaje enviado correctamente")
                        else:
                            st.error("❌ Error enviando mensaje")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            # Enviar duplicados actuales
            if hasattr(st.session_state, 'duplicados') and st.session_state.duplicados:
                if st.button("📊 Enviar Reporte de Duplicados"):
                    with st.spinner("Enviando reporte..."):
                        try:
                            # Crear reporte
                            total_duplicados = len(st.session_state.duplicados)
                            mensaje = f"🔍 **Reporte de Duplicados**\n\n"
                            mensaje += f"📊 Total de duplicados encontrados: {total_duplicados}\n"
                            mensaje += f"📁 Total de películas: {total_duplicados * 2}\n\n"
                            mensaje += "📋 **Ejemplos de duplicados:**\n"
                            
                            # Agregar algunos ejemplos
                            for i, duplicado in enumerate(st.session_state.duplicados[:3]):
                                mensaje += f"{i+1}. {duplicado.get('Peli 1', 'N/A')}\n"
                            
                            if total_duplicados > 3:
                                mensaje += f"... y {total_duplicados - 3} más\n"
                            
                            result = telegram_service.send_message(mensaje)
                            if result:
                                st.success("✅ Reporte enviado correctamente")
                            else:
                                st.error("❌ Error enviando reporte")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            else:
                st.info("💡 No hay duplicados para enviar. Escanea una carpeta primero.")
    
    def _render_telegram_interface(self):
        """Renderiza la interfaz principal de Telegram"""
        st.header("📱 Interfaz de Telegram")
        
        # Botón para volver
        if st.button("← Volver al Inicio"):
            st.session_state.show_telegram_interface = False
            st.rerun()
        
        st.markdown("---")
        
        # Mostrar solo la funcionalidad de subida de videos
        self._render_telegram_upload_interface()
    
    def _render_telegram_upload_interface(self):
        """Renderiza la interfaz de subida de videos de Telegram"""
        # Verificar si Telegram está configurado
        if not self.telegram_service.is_configured():
            st.warning("⚠️ Telegram no está configurado")
            st.info("💡 Configura el bot token y channel ID en la barra lateral")
            return
        
        st.success("✅ Telegram configurado correctamente")
        
        # Funcionalidad: Subir videos desde carpeta
        st.subheader("📁 Subir Videos desde Carpeta")
        
        # Seleccionar carpeta de videos
        folder_path = st.text_input(
            "Ruta de la carpeta:",
            value=st.session_state.get('telegram_folder_path', ''),
            help="Introduce la ruta de la carpeta que contiene los videos que quieres subir"
        )
        
        if folder_path:
            st.session_state.telegram_folder_path = folder_path
            
            if st.button("🔍 Escanear Carpeta", type="primary"):
                with st.spinner("Escaneando carpeta..."):
                    videos = self._scan_telegram_folder(folder_path)
                    if videos:
                        st.session_state.telegram_videos = videos
                        st.session_state.telegram_selected_videos = []
                        st.success(f"✅ Encontrados {len(videos)} videos")
                    else:
                        st.warning("⚠️ No se encontraron videos en la carpeta")
        
        # Mostrar videos si están cargados
        if 'telegram_videos' in st.session_state and st.session_state.telegram_videos:
            st.markdown("---")
            st.subheader("🎬 Videos Encontrados")
            
            # Opciones de selección
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Seleccionar Todos"):
                    st.session_state.telegram_selected_videos = list(range(len(st.session_state.telegram_videos)))
                    st.rerun()
            with col2:
                if st.button("❌ Deseleccionar Todos"):
                    st.session_state.telegram_selected_videos = []
                    st.rerun()
            with col3:
                if st.button("🔄 Actualizar Lista"):
                    videos = self._scan_telegram_folder(st.session_state.telegram_folder_path)
                    if videos:
                        st.session_state.telegram_videos = videos
                        st.rerun()
            
            # Lista de videos con checkboxes
            if 'telegram_selected_videos' not in st.session_state:
                st.session_state.telegram_selected_videos = []
            
            for i, video in enumerate(st.session_state.telegram_videos):
                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                
                with col1:
                    selected = st.checkbox(
                        f"Seleccionar {video['name']}",
                        value=i in st.session_state.telegram_selected_videos,
                        key=f"telegram_video_{i}",
                        label_visibility="collapsed"
                    )
                    if selected and i not in st.session_state.telegram_selected_videos:
                        st.session_state.telegram_selected_videos.append(i)
                    elif not selected and i in st.session_state.telegram_selected_videos:
                        st.session_state.telegram_selected_videos.remove(i)
                
                with col2:
                    st.write(f"**{video['name']}**")
                    st.caption(f"📁 {video['path']}")
                
                with col3:
                    st.write(f"{video['size']:.2f} MB")
                
                with col4:
                    if video['size'] > 1500:  # 1.5GB
                        st.warning("⚠️ Grande")
                    else:
                        st.success("✅ OK")
                
                st.markdown("---")
            
            # Botón de subida
            if st.session_state.telegram_selected_videos:
                st.subheader("📤 Subir Videos Seleccionados")
                st.info(f"📊 {len(st.session_state.telegram_selected_videos)} videos seleccionados")
                
                if st.button("🚀 Subir a Telegram", type="primary", use_container_width=True):
                    self._upload_selected_videos_to_telegram()
            else:
                st.info("💡 Selecciona videos para subir")
    
    def run(self):
        """Ejecuta la aplicación completa"""
        # Verificar si hay un archivo pendiente de cargar desde la lista
        if hasattr(st.session_state, 'load_from_list_file') and st.session_state.load_from_list_file:
            logging.info(f"📂 Cargando escaneo desde lista: {st.session_state.load_from_list_file}")
            self._load_scan_data(st.session_state.load_from_list_file)
            # Limpiar el archivo pendiente
            del st.session_state.load_from_list_file
            if hasattr(st.session_state, 'load_from_list_filename'):
                del st.session_state.load_from_list_filename
        
        self.render_header()
        self.render_sidebar()
        
        # Manejar interfaces especiales
        if getattr(st.session_state, 'show_scan_interface', False):
            self.render_scan_section()
            self.render_results()
        elif getattr(st.session_state, 'show_telegram_interface', False):
            self._render_telegram_interface()
        else:
            # Mostrar interfaz principal por defecto
            self.render_scan_section()
            self.render_results()
    
    def _scan_telegram_folder(self, folder_path: str) -> list:
        """Escanea una carpeta en busca de videos para Telegram usando TelegramManager"""
        try:
            # Usar el método del TelegramManager para escanear
            videos = []
            folder = Path(folder_path)
            
            if not folder.exists():
                return []
            
            # Extensiones de video soportadas
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
            
            # Buscar archivos de video
            for file_path in folder.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                    try:
                        # Obtener información del archivo
                        file_size = file_path.stat().st_size
                        size_mb = file_size / (1024 * 1024)
                        
                        # Crear entrada de video
                        video_info = {
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': size_mb,
                            'extension': file_path.suffix.lower()
                        }
                        
                        videos.append(video_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Error procesando archivo {file_path}: {e}")
                        continue
            
            # Ordenar por nombre
            videos.sort(key=lambda x: x['name'])
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Error escaneando carpeta {folder_path}: {e}")
            return []
    
    def _upload_selected_videos_to_telegram(self):
        """Sube los videos seleccionados a Telegram usando el mismo sistema que el test"""
        if not st.session_state.telegram_selected_videos:
            st.warning("⚠️ No hay videos seleccionados")
            return
        
        selected_videos = [st.session_state.telegram_videos[i] for i in st.session_state.telegram_selected_videos]
        
        # Filtrar videos que son demasiado grandes
        valid_videos = []
        oversized_videos = []
        
        for video in selected_videos:
            if video['size'] > 1500:  # 1.5GB límite de Telethon
                oversized_videos.append(video)
            else:
                valid_videos.append(video)
        
        if oversized_videos:
            st.warning(f"⚠️ {len(oversized_videos)} videos son demasiado grandes (>1.5GB) y se omitirán:")
            for video in oversized_videos:
                st.write(f"  • {video['name']} ({video['size']:.2f} MB)")
        
        if not valid_videos:
            st.error("❌ No hay videos válidos para subir (todos son demasiado grandes)")
            return
        
        # Configurar callback de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(message: str, progress: float):
            progress_bar.progress(progress / 100)
            status_text.text(f"📤 {message}")
        
        st.info(f"📤 Subiendo {len(valid_videos)} videos...")
        
        # Usar TelegramUploader (mismo sistema que el test que funcionó)
        results = self.telegram_uploader.upload_multiple_videos(
            videos=valid_videos,
            progress_callback=progress_callback
        )
        
        # Mostrar resultados individuales
        for i, (video, success) in enumerate(zip(valid_videos, results)):
            if success:
                st.success(f"✅ {video['name']} subido correctamente")
            else:
                st.error(f"❌ {video['name']} falló")
        
        # Mostrar resultados finales
        success_count = sum(results)
        error_count = len(results) - success_count
        
        if success_count > 0:
            st.success(f"✅ {success_count} videos subidos correctamente")
        if error_count > 0:
            st.error(f"❌ {error_count} videos fallaron")
        
        # Limpiar UI de progreso
        progress_bar.empty()
        status_text.empty()
