#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor principal de la aplicación Streamlit
Interfaz de usuario para el detector de películas duplicadas con integración PLEX
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para imports
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional
import time

# Imports relativos para evitar problemas de path
try:
    from src.settings.settings import settings
    from src.utils.movie_detector import MovieDetector
    from src.services.imdb_service import IMDBService
    from src.services.telegram_service import TelegramService
    from src.services.plex.plex_service import PlexService
    from src.services.plex.plex_smart_renamer import PlexSmartRenamer
except ImportError as e:
    st.error(f"❌ Error de importación: {e}")
    st.error("💡 Asegúrate de ejecutar la aplicación desde el directorio raíz del proyecto")
    st.stop()


def configure_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )


def init_session_state():
    """Inicializa el estado de la sesión de Streamlit"""
    if 'detector' not in st.session_state:
        st.session_state.detector = None
    if 'peliculas' not in st.session_state:
        st.session_state.peliculas = []
    if 'duplicados' not in st.session_state:
        st.session_state.duplicados = []
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    if 'plex_service' not in st.session_state:
        st.session_state.plex_service = None


def setup_page_config():
    """Configura la página de Streamlit"""
    st.set_page_config(
        page_title="🎬 Utilidades Plex",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Añadir estilos CSS personalizados - Sidebar oscuro, área principal clara
    st.markdown("""
    <style>
    /* ======================================== */
    /* TEMA HÍBRIDO: SIDEBAR OSCURO + ÁREA PRINCIPAL CLARA */
    /* ======================================== */
    
    /* Fondo principal claro */
    .stApp {
        background-color: #ffffff !important;
        color: #262730 !important;
    }
    
    /* Sidebar más estrecho y oscuro */
    .css-1d391kg {
        width: 250px !important;
    }
    
    /* Fondo muy oscuro para el sidebar */
    .css-1d391kg .css-1v0mbdj {
        background-color: #1a1a1a !important;
    }
    
    /* Texto blanco en el sidebar */
    .css-1d391kg .css-1v0mbdj .stMarkdown {
        color: white !important;
    }
    
    /* Inputs en sidebar oscuro */
    .css-1d391kg .css-1v0mbdj .stTextInput > div > div > input {
        color: white !important;
        background-color: #2d2d2d !important;
        border: 1px solid #555555 !important;
    }
    
    /* Botones en sidebar oscuro */
    .css-1d391kg .css-1v0mbdj .stButton > button {
        background-color: #2d2d2d !important;
        color: white !important;
        border: 1px solid #555555 !important;
    }
    
    /* Checkboxes en sidebar oscuro */
    .css-1d391kg .css-1v0mbdj .stCheckbox > label {
        color: white !important;
    }
    
    /* Selectbox en sidebar oscuro */
    .css-1d391kg .css-1v0mbdj .stSelectbox > div > div {
        background-color: #2d2d2d !important;
        color: white !important;
    }
    
    /* ======================================== */
    /* CONTENIDO PRINCIPAL - MODO CLARO */
    /* ======================================== */
    
    /* Título principal */
    .main .block-container h1 {
        color: #1f2937 !important;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    /* Subtítulos */
    .main .block-container h2 {
        color: #374151 !important;
    }
    
    .main .block-container h3 {
        color: #4b5563 !important;
    }
    
    /* Texto general */
    .main .block-container {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* ======================================== */
    /* BOXES Y CONTAINERS - MODO CLARO */
    /* ======================================== */
    
    /* Boxes principales claros */
    .stContainer {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Expanders claros */
    .streamlit-expander {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expander .streamlit-expanderHeader {
        background-color: #f1f5f9 !important;
        color: #1f2937 !important;
    }
    
    /* Métricas claras */
    .metric-container {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* ======================================== */
    /* TABLAS Y DATAFRAMES - MODO CLARO */
    /* ======================================== */
    
    /* Tablas con fondo claro */
    .stDataFrame {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    /* Headers de tabla */
    .stDataFrame thead th {
        background-color: #f1f5f9 !important;
        color: #1f2937 !important;
    }
    
    /* Filas de tabla alternadas */
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f8fafc !important;
    }
    
    .stDataFrame tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    
    /* ======================================== */
    /* BOTONES Y CONTROLES - MODO CLARO */
    /* ======================================== */
    
    /* Botones principales claros */
    .stButton > button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
        border-radius: 6px !important;
    }
    
    .stButton > button:hover {
        background-color: #2563eb !important;
        border-color: #1d4ed8 !important;
    }
    
    /* Selectbox claro */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Text input claro */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* ======================================== */
    /* PROGRESS BARS Y INDICADORES */
    /* ======================================== */
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #00d4aa !important;
    }
    
    /* Spinner */
    .stSpinner {
        color: #00d4aa !important;
    }
    
    /* ======================================== */
    /* ALERTAS Y MENSAJES - MODO CLARO */
    /* ======================================== */
    
    /* Success messages */
    .stSuccess {
        background-color: #f0fdf4 !important;
        border: 1px solid #22c55e !important;
        color: #15803d !important;
    }
    
    /* Error messages */
    .stError {
        background-color: #fef2f2 !important;
        border: 1px solid #ef4444 !important;
        color: #dc2626 !important;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #fffbeb !important;
        border: 1px solid #f59e0b !important;
        color: #d97706 !important;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #eff6ff !important;
        border: 1px solid #3b82f6 !important;
        color: #1d4ed8 !important;
    }
    
    /* ======================================== */
    /* SCROLLBARS - MODO CLARO */
    /* ======================================== */
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Renderiza la barra lateral con configuración"""
    st.sidebar.title("🎬 Configuración")
    
    # Pestañas en el sidebar
    tab1, tab2, tab3, tab4, tab5, tab6 = st.sidebar.tabs(["📁 Escaneo", "🔍 PLEX Scanner", "⚙️ Configuración", "🎨 UI", "🔍 Detección", "📊 Estado"])
    
    with tab1:
        render_scan_section()
    
    with tab2:
        render_plex_scanner_tab()
    
    with tab3:
        render_configuration_tab()
    
    with tab4:
        render_ui_config_tab()
    
    with tab5:
        render_detection_config_tab()
    
    with tab6:
        render_status_tab()


def render_scan_section():
    """Renderiza la sección de escaneo"""
    st.subheader("📁 Escaneo de Películas")
    
    # Verificar estado de PLEX
    plex_enabled = settings.get_plex_enabled()
    plex_connected = False
    plex_service = None
    
    if plex_enabled:
        try:
            # Verificar conexión directa a la base de datos
            from src.services.plex.plex_database_direct import PlexDatabaseDirect
            db_path = settings.get_plex_database_path()
            
            if db_path and Path(db_path).exists():
                plex_db = PlexDatabaseDirect(db_path)
                if plex_db.connect():
                    plex_connected = True
                    plex_db.close()
                    st.session_state.plex_service = plex_service
                else:
                    st.warning("⚠️ No se pudo conectar a la base de datos de PLEX")
            else:
                st.warning("⚠️ Ruta de base de datos de PLEX no válida")
        except Exception as e:
            st.warning(f"⚠️ Error conectando con PLEX: {e}")
    
    # Mostrar estado de PLEX
    if plex_enabled:
        if plex_connected:
            st.success("✅ PLEX conectado y listo")
            
            # Configuración de PLEX
            use_plex_detection = st.checkbox(
                "🎬 Usar detección PLEX",
                value=settings.get_plex_use_detection(),
                help="Usar PLEX para detectar duplicados directamente",
                key="plex_detection_scan"
            )
            
            if use_plex_detection:
                # Modo PLEX puro
                st.info("🎬 Modo PLEX: Detección directa de duplicados")
                
                # Selector de biblioteca
                try:
                    libraries = plex_service.get_libraries()
                    if libraries:
                        library_names = [lib['title'] for lib in libraries if lib['type'] == 'movie']
                        if library_names:
                            selected_library = st.selectbox(
                                "📚 Seleccionar Biblioteca",
                                library_names,
                                help="Biblioteca de PLEX para analizar"
                            )
                            
                            if st.button("🔍 Buscar Duplicados en PLEX", type="primary"):
                                st.session_state.scanning = True
                                try:
                                    # Obtener duplicados directamente de PLEX
                                    library_id = next(lib['id'] for lib in libraries if lib['title'] == selected_library)
                                    duplicados = plex_service.get_duplicates_from_library(library_id)
                                    st.session_state.duplicados = duplicados
                                    st.session_state.scanning = False
                                    st.success(f"✅ Encontrados {len(duplicados)} grupos de duplicados en PLEX")
                                except Exception as e:
                                    st.error(f"❌ Error obteniendo duplicados: {e}")
                                    st.session_state.scanning = False
                        else:
                            st.warning("⚠️ No se encontraron bibliotecas de películas en PLEX")
                    else:
                        st.warning("⚠️ No se pudieron obtener las bibliotecas de PLEX")
                except Exception as e:
                    st.error(f"❌ Error obteniendo bibliotecas: {e}")
            else:
                # Modo híbrido
                st.info("🎬 Modo Híbrido: Escaneo de archivos + PLEX")
                
                carpeta = st.text_input(
                    "📁 Ruta de la carpeta a analizar",
                    value=settings.get_last_scan_path() or "",
                    help="Ruta de la carpeta que contiene las películas"
                )
                
                if st.button("🔍 Escanear con PLEX", type="primary"):
                    if carpeta and Path(carpeta).exists():
                        # Guardar la carpeta en session_state para procesar en el área principal
                        st.session_state.pending_scan = {
                            'carpeta': carpeta,
                            'tipo': 'hibrido'
                        }
                        st.rerun()
                    else:
                        st.error("❌ Por favor, especifica una carpeta válida")
        else:
            st.warning("⚠️ PLEX no conectado")
            st.info("💡 Configura las credenciales de PLEX en la pestaña 'Configuración'")
            
            # Modo tradicional sin PLEX
            carpeta = st.text_input(
                "📁 Ruta de la carpeta a analizar",
                value=settings.get_last_scan_path() or "",
                help="Ruta de la carpeta que contiene las películas"
            )
            
            if st.button("🔍 Escanear", type="primary"):
                if carpeta and Path(carpeta).exists():
                    # Guardar la carpeta en session_state para procesar en el área principal
                    st.session_state.pending_scan = {
                        'carpeta': carpeta,
                        'tipo': 'tradicional'
                    }
                    st.rerun()
                else:
                    st.error("❌ Por favor, especifica una carpeta válida")
    else:
        # PLEX deshabilitado - modo tradicional
        st.info("🔍 Modo tradicional: Solo análisis de archivos")
        
        carpeta = st.text_input(
            "📁 Ruta de la carpeta a analizar",
            value=settings.get_last_scan_path() or "",
            help="Ruta de la carpeta que contiene las películas"
        )
        
        if st.button("🔍 Escanear", type="primary"):
            if carpeta and Path(carpeta).exists():
                process_traditional_scan(carpeta)
            else:
                st.error("❌ Por favor, especifica una carpeta válida")


def render_plex_scanner_tab():
    """Renderiza la pestaña del escáner de PLEX"""
    st.subheader("🔍 Escáner de PLEX")
    st.markdown("Escanea directorios para detectar películas no reconocidas por PLEX")
    
    # Verificar estado de PLEX
    plex_enabled = settings.get_plex_enabled()
    if not plex_enabled:
        st.warning("⚠️ PLEX no está habilitado. Ve a la pestaña 'Configuración' para habilitarlo.")
        return
    
    # Verificar conexión a PLEX
    try:
        from src.services.plex.plex_database_direct import PlexDatabaseDirect
        db_path = settings.get_plex_database_path()
        if not db_path:
            st.error("❌ Ruta de base de datos de PLEX no configurada")
            return
        
        plex_db = PlexDatabaseDirect(db_path)
        if not plex_db.connect():
            st.error("❌ No se pudo conectar a la base de datos de PLEX")
            return
        
        st.success("✅ Conectado a la base de datos de PLEX")
        plex_db.close()
        
    except Exception as e:
        st.error(f"❌ Error conectando a PLEX: {e}")
        return
    
    # Configuración del escaneo
    st.markdown("### 📁 Configuración del Escaneo")
    
    directorio = st.text_input(
        "📁 Directorio a escanear",
        value=settings.get_last_scan_path() or "",
        help="Ruta del directorio que contiene las películas a verificar"
    )
    
    # Opciones de escaneo
    col1, col2 = st.columns(2)
    
    with col1:
        incluir_subdirectorios = st.checkbox(
            "📂 Incluir subdirectorios",
            value=True,
            help="Escanear también las subcarpetas"
        )
        
        mostrar_encontradas = st.checkbox(
            "✅ Mostrar películas encontradas",
            value=False,
            help="Mostrar también las películas que SÍ están en PLEX"
        )
    
    with col2:
        generar_sugerencias = st.checkbox(
            "💡 Generar sugerencias de renombrado",
            value=True,
            help="Generar sugerencias automáticas de renombrado"
        )
        
        auto_renombrar = st.checkbox(
            "🔄 Renombrado automático",
            value=False,
            help="Aplicar automáticamente el mejor renombrado (¡CUIDADO!)"
        )
    
    # Botón de escaneo
    if st.button("🔍 Escanear Directorio", type="primary"):
        if directorio and Path(directorio).exists():
            # Guardar configuración
            settings.set_last_scan_path(directorio)
            
            # Iniciar escaneo
            st.session_state.plex_scanner_config = {
                'directorio': directorio,
                'incluir_subdirectorios': incluir_subdirectorios,
                'mostrar_encontradas': mostrar_encontradas,
                'generar_sugerencias': generar_sugerencias,
                'auto_renombrar': auto_renombrar
            }
            st.session_state.plex_scanner_pending = True
            st.rerun()
        else:
            st.error("❌ Por favor, especifica un directorio válido")
    
    # Mostrar resultados del escaneo si existen
    if hasattr(st.session_state, 'plex_scanner_results') and st.session_state.plex_scanner_results:
        _mostrar_resultados_plex_scanner()


def _mostrar_resultados_plex_scanner():
    """Muestra los resultados del escáner de PLEX"""
    resultados = st.session_state.plex_scanner_results
    
    st.markdown("### 📊 Resultados del Escaneo")
    
    # Estadísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Total Archivos", resultados['total_archivos'])
    
    with col2:
        st.metric("✅ Encontradas", len(resultados['peliculas_encontradas']))
    
    with col3:
        st.metric("❌ No Encontradas", len(resultados['peliculas_no_encontradas']))
    
    with col4:
        porcentaje = (len(resultados['peliculas_encontradas']) / resultados['total_archivos'] * 100) if resultados['total_archivos'] > 0 else 0
        st.metric("📊 Reconocimiento", f"{porcentaje:.1f}%")
    
    # Pestañas para organizar mejor los resultados
    tab_no_encontradas, tab_encontradas = st.tabs(["❌ No Encontradas", "✅ Encontradas"])
    
    with tab_no_encontradas:
        if resultados['peliculas_no_encontradas']:
            st.markdown(f"### ❌ {len(resultados['peliculas_no_encontradas'])} Películas No Reconocidas por PLEX")
            
            # Filtros y búsqueda
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                filtro_nombre = st.text_input("🔍 Filtrar por nombre:", placeholder="Escriba parte del nombre...")
            with col2:
                mostrar_solo_con_sugerencias = st.checkbox("💡 Solo con sugerencias", value=True)
            with col3:
                renombrado_masivo = st.checkbox("🔄 Modo masivo", value=False, help="Permite seleccionar múltiples archivos para renombrar")
            
            # Aplicar filtros
            peliculas_filtradas = resultados['peliculas_no_encontradas']
            if filtro_nombre:
                peliculas_filtradas = [p for p in peliculas_filtradas if filtro_nombre.lower() in p['nombre'].lower()]
            if mostrar_solo_con_sugerencias:
                peliculas_filtradas = [p for p in peliculas_filtradas if p.get('sugerencias_renombre')]
            
            st.write(f"📊 Mostrando {len(peliculas_filtradas)} de {len(resultados['peliculas_no_encontradas'])} películas")
            
            # Renombrado masivo
            if renombrado_masivo and peliculas_filtradas:
                st.markdown("### 🔄 Renombrado Masivo")
                
                # Seleccionar archivos para renombrado masivo
                archivos_seleccionados = st.multiselect(
                    "📁 Seleccionar archivos para renombrado masivo:",
                    options=[f"{p['nombre']}" for p in peliculas_filtradas],
                    help="Selecciona múltiples archivos para aplicar el mismo patrón de renombrado"
                )
                
                if archivos_seleccionados:
                    # Patrón de renombrado
                    patron_renombrado = st.selectbox(
                        "🎯 Patrón de renombrado:",
                        options=[
                            "Título + Año",
                            "Título limpio",
                            "Título con puntos",
                            "Personalizado"
                        ],
                        help="Selecciona un patrón para aplicar a todos los archivos seleccionados"
                    )
                    
                    if patron_renombrado == "Personalizado":
                        patron_personalizado = st.text_input(
                            "✏️ Patrón personalizado:",
                            placeholder="Ej: {titulo} ({año})",
                            help="Usa {titulo} y {año} como variables"
                        )
                    
                    if st.button("🔄 Aplicar Renombrado Masivo", type="primary"):
                        _aplicar_renombrado_masivo(archivos_seleccionados, peliculas_filtradas, patron_renombrado, patron_personalizado if patron_renombrado == "Personalizado" else None)
            
            # Mostrar películas con renombrado rápido
            for i, pelicula in enumerate(peliculas_filtradas):
                st.markdown("---")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**📁 {pelicula['nombre']}**")
                    st.write(f"`{pelicula['archivo']}`")
                    if 'titulo_extraido' in pelicula:
                        st.write(f"*Título extraído: {pelicula['titulo_extraido']}*")
                
                with col2:
                    if pelicula.get('sugerencias_renombre'):
                        # Selectbox para elegir sugerencia
                        sugerencia_seleccionada = st.selectbox(
                            "💡 Sugerencia:",
                            options=pelicula['sugerencias_renombre'],
                            key=f"sugerencia_{i}",
                            help="Selecciona una sugerencia de renombrado"
                        )
                        
                        # Botón de renombrado rápido
                        if st.button(f"🔄 Renombrar", key=f"rename_{i}", type="primary"):
                            _aplicar_renombrado(pelicula['archivo'], sugerencia_seleccionada)
                    else:
                        st.info("ℹ️ Sin sugerencias")
                        # Input manual para renombrado
                        nuevo_nombre = st.text_input(
                            "✏️ Nuevo nombre:",
                            value=pelicula['nombre'],
                            key=f"manual_{i}",
                            help="Escribe el nuevo nombre del archivo"
                        )
                        if st.button(f"🔄 Renombrar Manual", key=f"manual_rename_{i}"):
                            _aplicar_renombrado(pelicula['archivo'], nuevo_nombre)
        else:
            st.success("🎉 ¡Todas las películas están reconocidas por PLEX!")
    
    with tab_encontradas:
        if resultados['peliculas_encontradas']:
            st.markdown(f"### ✅ {len(resultados['peliculas_encontradas'])} Películas Reconocidas por PLEX")
            
            # Filtros para películas encontradas
            col1, col2 = st.columns([2, 1])
            with col1:
                filtro_titulo = st.text_input("🔍 Filtrar por título:", placeholder="Escriba parte del título...")
            with col2:
                mostrar_detalles = st.checkbox("📋 Mostrar detalles", value=False)
            
            # Aplicar filtros
            peliculas_encontradas_filtradas = resultados['peliculas_encontradas']
            if filtro_titulo:
                peliculas_encontradas_filtradas = [p for p in peliculas_encontradas_filtradas 
                                                 if filtro_titulo.lower() in p.get('titulo_plex', '').lower()]
            
            st.write(f"📊 Mostrando {len(peliculas_encontradas_filtradas)} de {len(resultados['peliculas_encontradas'])} películas")
            
            # Mostrar películas encontradas
            for i, pelicula in enumerate(peliculas_encontradas_filtradas):
                with st.expander(f"✅ {pelicula['nombre']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📁 Archivo:** `{pelicula['archivo']}`")
                        st.write(f"**🎬 Título PLEX:** {pelicula['titulo_plex']}")
                        st.write(f"**📅 Año PLEX:** {pelicula['año_plex']}")
                    
                    with col2:
                        if pelicula['duracion_plex']:
                            duracion_min = pelicula['duracion_plex'] // 60000
                            st.write(f"**⏱️ Duración:** {duracion_min} min")
                        st.write(f"**📂 Ruta PLEX:** `{pelicula['ruta_plex']}`")
                        
                        if mostrar_detalles:
                            st.write("**🔍 Detalles adicionales:**")
                            st.write(f"- ID PLEX: {pelicula.get('id_plex', 'N/A')}")
                            st.write(f"- Resolución: {pelicula.get('resolution_plex', 'N/A')}")
                            st.write(f"- Códec: {pelicula.get('video_codec', 'N/A')}")
        else:
            st.info("ℹ️ No hay películas encontradas para mostrar")


def _aplicar_renombrado(archivo_original: str, nuevo_nombre: str):
    """Aplica el renombrado de un archivo"""
    try:
        from src.utils.video import PlexScanner
        from pathlib import Path
        
        # Validaciones previas
        archivo_path = Path(archivo_original)
        if not archivo_path.exists():
            st.error(f"❌ El archivo no existe: {archivo_original}")
            return
        
        # Verificar que el nuevo nombre sea diferente
        if archivo_path.name == nuevo_nombre:
            st.warning("⚠️ El nuevo nombre es igual al actual")
            return
        
        # Verificar que el nuevo nombre no contenga caracteres inválidos
        caracteres_invalidos = ['<', '>', ':', '"', '|', '?', '*']
        if any(caracter in nuevo_nombre for caracter in caracteres_invalidos):
            st.error(f"❌ El nombre contiene caracteres inválidos: {caracteres_invalidos}")
            return
        
        # Mostrar progreso
        with st.spinner("🔄 Renombrando archivo..."):
            scanner = PlexScanner()
            resultado = scanner.renombrar_archivo(archivo_original, nuevo_nombre)
        
        if resultado['exito']:
            st.success(f"✅ Archivo renombrado exitosamente!")
            st.info(f"📁 Original: `{archivo_path.name}`")
            st.info(f"📁 Nuevo: `{nuevo_nombre}`")
            
            # Actualizar los resultados del escáner
            if hasattr(st.session_state, 'plex_scanner_results'):
                _actualizar_resultados_despues_renombrado(archivo_original, nuevo_nombre)
            
            st.rerun()
        else:
            st.error(f"❌ Error renombrando archivo: {resultado['error']}")
            
    except Exception as e:
        st.error(f"❌ Error aplicando renombrado: {e}")
        import traceback
        traceback.print_exc()


def _actualizar_resultados_despues_renombrado(archivo_original: str, nuevo_nombre: str):
    """Actualiza los resultados del escáner después de un renombrado"""
    try:
        resultados = st.session_state.plex_scanner_results
        
        # Buscar la película en las no encontradas y moverla a encontradas
        for i, pelicula in enumerate(resultados['peliculas_no_encontradas']):
            if pelicula['archivo'] == archivo_original:
                # Crear nueva entrada para película encontrada
                pelicula_encontrada = {
                    'archivo': archivo_original.replace(Path(archivo_original).name, nuevo_nombre),
                    'nombre': nuevo_nombre,
                    'encontrada': True,
                    'titulo_plex': pelicula.get('titulo_extraido', nuevo_nombre),
                    'año_plex': 'N/A',
                    'duracion_plex': 0,
                    'ruta_plex': 'N/A'
                }
                
                # Mover de no encontradas a encontradas
                resultados['peliculas_encontradas'].append(pelicula_encontrada)
                resultados['peliculas_no_encontradas'].pop(i)
                
                # Actualizar contadores
                resultados['total_archivos'] = len(resultados['peliculas_encontradas']) + len(resultados['peliculas_no_encontradas'])
                
                break
                
    except Exception as e:
        st.warning(f"⚠️ No se pudo actualizar los resultados: {e}")


def _aplicar_renombrado_masivo(archivos_seleccionados: list, peliculas_filtradas: list, patron: str, patron_personalizado: str = None):
    """Aplica renombrado masivo a múltiples archivos"""
    try:
        from src.utils.video import PlexScanner
        from pathlib import Path
        
        scanner = PlexScanner()
        exitos = 0
        errores = 0
        
        st.info(f"🔄 Aplicando renombrado masivo a {len(archivos_seleccionados)} archivos...")
        
        # Crear barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, nombre_archivo in enumerate(archivos_seleccionados):
            # Encontrar la película correspondiente
            pelicula = next((p for p in peliculas_filtradas if p['nombre'] == nombre_archivo), None)
            if not pelicula:
                continue
            
            # Actualizar progreso
            progress = (i + 1) / len(archivos_seleccionados)
            progress_bar.progress(progress)
            status_text.text(f"🔄 Renombrando {i+1}/{len(archivos_seleccionados)}: {nombre_archivo}")
            
            # Generar nuevo nombre según el patrón
            nuevo_nombre = _generar_nombre_segun_patron(pelicula, patron, patron_personalizado)
            
            if nuevo_nombre and nuevo_nombre != pelicula['nombre']:
                # Aplicar renombrado
                resultado = scanner.renombrar_archivo(pelicula['archivo'], nuevo_nombre)
                
                if resultado['exito']:
                    exitos += 1
                    # Actualizar resultados
                    _actualizar_resultados_despues_renombrado(pelicula['archivo'], nuevo_nombre)
                else:
                    errores += 1
                    st.warning(f"⚠️ Error renombrando {nombre_archivo}: {resultado['error']}")
            else:
                st.warning(f"⚠️ No se pudo generar nuevo nombre para {nombre_archivo}")
                errores += 1
        
        # Limpiar progreso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if exitos > 0:
            st.success(f"✅ Renombrado masivo completado: {exitos} archivos renombrados exitosamente")
        if errores > 0:
            st.warning(f"⚠️ {errores} archivos no pudieron ser renombrados")
        
        if exitos > 0:
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error en renombrado masivo: {e}")
        import traceback
        traceback.print_exc()


def _generar_nombre_segun_patron(pelicula: dict, patron: str, patron_personalizado: str = None) -> str:
    """Genera un nuevo nombre según el patrón especificado"""
    try:
        from pathlib import Path
        
        # Obtener información de la película
        titulo_extraido = pelicula.get('titulo_extraido', pelicula['nombre'])
        año_extraido = _extraer_año_del_archivo(pelicula['nombre'])
        extension = Path(pelicula['nombre']).suffix
        
        if patron == "Título + Año":
            if año_extraido:
                return f"{titulo_extraido} ({año_extraido}){extension}"
            else:
                return f"{titulo_extraido}{extension}"
        
        elif patron == "Título limpio":
            return f"{titulo_extraido}{extension}"
        
        elif patron == "Título con puntos":
            titulo_puntos = titulo_extraido.replace(' ', '.')
            return f"{titulo_puntos}{extension}"
        
        elif patron == "Personalizado" and patron_personalizado:
            # Reemplazar variables en el patrón personalizado
            nuevo_nombre = patron_personalizado
            nuevo_nombre = nuevo_nombre.replace('{titulo}', titulo_extraido)
            nuevo_nombre = nuevo_nombre.replace('{año}', año_extraido or '')
            return f"{nuevo_nombre}{extension}"
        
        else:
            return pelicula['nombre']
            
    except Exception as e:
        return pelicula['nombre']


def _extraer_año_del_archivo(nombre_archivo: str) -> str:
    """Extrae el año del nombre del archivo"""
    try:
        import re
        # Buscar patrones de año: (1995), 1995, [1995]
        patrones_año = [
            r'\((\d{4})\)',  # (1995)
            r'\[(\d{4})\]',  # [1995]
            r'(\d{4})',  # 1995
        ]
        
        for patron in patrones_año:
            match = re.search(patron, nombre_archivo)
            if match:
                año = match.group(1)
                # Verificar que sea un año válido (1900-2030)
                if 1900 <= int(año) <= 2030:
                    return año
        
        return ""
        
    except Exception:
        return ""


def render_configuration_tab():
    """Renderiza la pestaña de configuración"""
    st.subheader("⚙️ Configuración General")
    
    # Configuración de PLEX
    st.subheader("🎬 Integración con PLEX")
    
    plex_enabled = st.checkbox(
        "🎬 Habilitar PLEX",
        value=settings.get_plex_enabled(),
        help="Activar integración con PLEX Media Server",
        key="plex_enabled_config"
    )
    
    if plex_enabled:
        st.info("💡 Configura las credenciales de PLEX en tu archivo .env")
        
        # Mostrar estado de conexión
        try:
            plex_service = PlexService()
            if plex_service.connect():
                st.success("✅ PLEX conectado")
            else:
                st.warning("⚠️ PLEX no conectado")
        except Exception as e:
            st.error(f"❌ Error: {e}")
        
        # Configuraciones de PLEX
        use_plex_detection = st.checkbox(
            "🎬 Usar detección PLEX",
            value=settings.get_plex_use_detection(),
            help="Usar PLEX para detectar duplicados directamente",
            key="plex_detection_config"
        )
        
        use_plex_metadata = st.checkbox(
            "📊 Usar metadatos PLEX",
            value=settings.get_plex_use_metadata(),
            help="Usar metadatos de PLEX para mejorar la detección",
            key="plex_metadata_config"
        )
        
        # Configuraciones avanzadas de PLEX
        st.subheader("⚙️ Configuraciones Avanzadas PLEX")
        
        prefer_plex_titles = st.checkbox(
            "🎬 Preferir títulos de PLEX",
            value=settings.get_plex_prefer_titles(),
            help="Usar títulos de PLEX en lugar de nombres de archivo",
            key="plex_prefer_titles"
        )
        
        prefer_plex_years = st.checkbox(
            "📅 Preferir años de PLEX",
            value=settings.get_plex_prefer_years(),
            help="Usar años de PLEX en lugar de extraídos del archivo",
            key="plex_prefer_years"
        )
        
        prefer_plex_duration = st.checkbox(
            "⏱️ Preferir duración de PLEX",
            value=settings.get_plex_prefer_duration(),
            help="Usar duración de PLEX para comparación de duplicados",
            key="plex_prefer_duration"
        )
        
        auto_connect = st.checkbox(
            "🔗 Conexión automática PLEX",
            value=settings.get_plex_auto_connect(),
            help="Conectar automáticamente con PLEX al iniciar",
            key="plex_auto_connect"
        )
        
        if st.button("💾 Guardar configuración PLEX"):
            settings.set_plex_enabled(plex_enabled)
            settings.set_plex_use_detection(use_plex_detection)
            settings.set_plex_use_metadata(use_plex_metadata)
            settings.set_plex_prefer_titles(prefer_plex_titles)
            settings.set_plex_prefer_years(prefer_plex_years)
            settings.set_plex_prefer_duration(prefer_plex_duration)
            settings.set_plex_auto_connect(auto_connect)
            st.success("✅ Configuración PLEX guardada")
    else:
        settings.set_plex_enabled(False)
    
    st.markdown("---")
    
    # Configuración de Debug
    st.subheader("🐛 Modo Debug")
    
    debug_enabled = st.checkbox(
        "🐛 Activar Modo Debug",
        value=settings.get_debug_enabled(),
        help="En modo debug, los archivos se mueven a una carpeta en lugar de borrarse",
        key="debug_enabled_config"
    )
    
    debug_folder = st.text_input(
        "📁 Carpeta de Debug",
        value=settings.get_debug_folder(),
        help="Carpeta donde se moverán los archivos en modo debug"
    )
    
    if st.button("💾 Guardar configuración debug"):
        settings.set_debug_enabled(debug_enabled)
        settings.set_debug_folder(debug_folder)
        st.success("✅ Configuración de debug guardada")


def render_ui_config_tab():
    """Renderiza la pestaña de configuración de UI"""
    st.subheader("🎨 Configuración de Interfaz")
    
    # Configuración de reproductores
    st.markdown("**🎬 Reproductores de Video:**")
    
    show_video_players = st.checkbox(
        "▶️ Mostrar reproductores de video",
        value=settings.get("ui.show_video_players", True),
        help="Mostrar botones de reproducción en los resultados",
        key="show_video_players_config"
    )
    
    show_embedded_players = st.checkbox(
        "📺 Reproductor embebido",
        value=settings.get("ui.show_embedded_players", False),
        help="Usar reproductor embebido en lugar del reproductor del sistema",
        key="show_embedded_players_config"
    )
    
    video_start_time = st.number_input(
        "⏰ Tiempo de inicio (minutos)",
        min_value=0,
        max_value=300,
        value=settings.get("ui.video_start_time_seconds", 900) // 60,
        help="Minuto desde el cual empezar a reproducir (por defecto 15 min)",
        key="video_start_time_config"
    )
    
    video_player_size = st.selectbox(
        "📏 Tamaño del reproductor",
        ["small", "medium", "large"],
        index=["small", "medium", "large"].index(settings.get("ui.video_player_size", "medium")),
        help="Tamaño del reproductor embebido",
        key="video_player_size_config"
    )
    
    # Configuración de frame preview
    st.markdown("**📸 Frame Preview:**")
    
    show_frame_preview = st.checkbox(
        "🖼️ Mostrar frame preview",
        value=settings.get("ui.show_frame_preview", True),
        help="Mostrar preview del frame en el sidebar",
        key="show_frame_preview_config"
    )
    
    frame_preview_time = st.number_input(
        "⏰ Tiempo del frame (minutos)",
        min_value=0,
        max_value=300,
        value=settings.get("ui.frame_preview_time_seconds", 900) // 60,
        help="Minuto del cual extraer el frame preview",
        key="frame_preview_time_config"
    )
    
    # Botón para guardar configuración
    if st.button("💾 Guardar Configuración UI", type="primary"):
        try:
            settings.set("ui.show_video_players", show_video_players)
            settings.set("ui.show_embedded_players", show_embedded_players)
            settings.set("ui.video_start_time_seconds", video_start_time * 60)
            settings.set("ui.video_player_size", video_player_size)
            settings.set("ui.show_frame_preview", show_frame_preview)
            settings.set("ui.frame_preview_time_seconds", frame_preview_time * 60)
            
            st.success("✅ Configuración de UI guardada")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error guardando configuración: {e}")


def render_detection_config_tab():
    """Renderiza la pestaña de configuración de detección"""
    st.subheader("🔍 Configuración de Detección")
    
    # Configuración de duración
    st.markdown("**⏱️ Filtros de Duración:**")
    
    duration_filter_enabled = st.checkbox(
        "🎯 Usar filtro de duración",
        value=settings.get("detection.duration_filter_enabled", True),
        help="Filtrar duplicados por diferencia de duración",
        key="duration_filter_enabled_config"
    )
    
    duration_tolerance = st.number_input(
        "⏱️ Tolerancia de duración (minutos)",
        min_value=0,
        max_value=60,
        value=settings.get("detection.duration_tolerance_minutes", 1),
        help="Diferencia máxima en minutos para considerar duplicados",
        key="duration_tolerance_config"
    )
    
    # Configuración de similitud
    st.markdown("**🎯 Umbrales de Similitud:**")
    
    similarity_threshold = st.slider(
        "🎯 Umbral de similitud",
        min_value=0.0,
        max_value=1.0,
        value=settings.get("detection.similarity_threshold", 0.8),
        step=0.1,
        help="Umbral de similitud para considerar duplicados (0.0 = muy estricto, 1.0 = muy permisivo)",
        key="similarity_threshold_config"
    )
    
    # Configuración de extensiones
    st.markdown("**📁 Extensiones Soportadas:**")
    
    supported_extensions = settings.get("detection.supported_extensions", [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp", ".webm"
    ])
    
    st.write("Extensiones actuales:")
    for ext in supported_extensions:
        st.write(f"• {ext}")
    
    # Botón para guardar configuración
    if st.button("💾 Guardar Configuración de Detección", type="primary"):
        try:
            settings.set("detection.duration_filter_enabled", duration_filter_enabled)
            settings.set("detection.duration_tolerance_minutes", duration_tolerance)
            settings.set("detection.similarity_threshold", similarity_threshold)
            
            st.success("✅ Configuración de detección guardada")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error guardando configuración: {e}")


def render_status_tab():
    """Renderiza la pestaña de estado"""
    st.subheader("📊 Estado del Sistema")
    
    # Estado de PLEX
    if settings.get_plex_enabled():
        try:
            plex_service = PlexService()
            if plex_service.connect():
                st.success("✅ PLEX conectado")
                try:
                    libraries = plex_service.get_libraries()
                    st.info(f"📚 Bibliotecas disponibles: {len(libraries)}")
                except:
                    st.warning("⚠️ No se pudieron obtener las bibliotecas")
            else:
                st.warning("⚠️ PLEX no conectado")
        except Exception as e:
            st.error(f"❌ Error PLEX: {e}")
    else:
        st.info("ℹ️ PLEX deshabilitado")
    
    # Estado del detector
    if 'detector' in st.session_state and st.session_state.detector:
        st.success("✅ Detector inicializado")
        if 'peliculas' in st.session_state:
            st.info(f"📁 Películas cargadas: {len(st.session_state.peliculas)}")
        if 'duplicados' in st.session_state:
            st.info(f"🎯 Duplicados encontrados: {len(st.session_state.duplicados)}")
    else:
        st.info("ℹ️ Detector no inicializado")
    
    # Estado de la sesión
    st.markdown("**📊 Estado de la Sesión:**")
    
    if 'duplicados' in st.session_state:
        duplicados = st.session_state.duplicados
        st.write(f"🎯 Duplicados encontrados: {len(duplicados)} grupos")
        
        total_peliculas = sum(len(grupo) for grupo in duplicados)
        st.write(f"📁 Total de películas duplicadas: {total_peliculas}")
    else:
        st.info("ℹ️ No hay resultados de escaneo")
    
    # Estado de configuración
    st.markdown("**⚙️ Configuración Actual:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"🎬 PLEX habilitado: {'✅' if settings.get_plex_enabled() else '❌'}")
        st.write(f"🎯 Filtro duración: {'✅' if settings.get('detection.duration_filter_enabled', True) else '❌'}")
        st.write(f"▶️ Reproductores: {'✅' if settings.get('ui.show_video_players', True) else '❌'}")
    
    with col2:
        st.write(f"📺 Reproductor embebido: {'✅' if settings.get('ui.show_embedded_players', False) else '❌'}")
        st.write(f"🎯 Umbral similitud: {settings.get('detection.similarity_threshold', 0.8)}")
        st.write(f"⏱️ Tolerancia duración: {settings.get('detection.duration_tolerance_minutes', 1)} min")


def process_hybrid_scan(carpeta: str):
    """Procesa el escaneo híbrido con progreso detallado"""
    st.session_state.scanning = True
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Iniciando escaneo híbrido...")
        progress_bar.progress(10)
        
        # Crear detector con PLEX
        detector = MovieDetector(carpeta, use_plex=True)
        st.session_state.detector = detector
        
        # Mostrar estado de PLEX
        plex_status = detector.get_plex_status()
        if plex_status['connected']:
            st.success("✅ PLEX conectado y listo")
        else:
            st.warning(f"⚠️ PLEX no conectado: {plex_status.get('message', 'Error desconocido')}")
        
        status_text.text("📁 Escaneando archivos...")
        progress_bar.progress(30)
        
        # Crear miniterminal para mostrar archivos (se mostrará en el área principal)
        terminal_placeholder = st.empty()
        terminal_content = []
        
        def mostrar_archivo(archivo):
            nombre_archivo = Path(archivo).name
            terminal_content.append(f"🎬 {nombre_archivo}")
            # Mostrar en el área principal usando placeholder
            terminal_placeholder.markdown("### 🔍 Miniterminal - Archivos encontrados:")
            terminal_placeholder.code("\n".join(terminal_content[-15:]), language="text")
        
        detector.mostrar_archivo = mostrar_archivo
        
        # Callback para mostrar progreso
        def mostrar_progreso(contador, mensaje):
            status_text.text(mensaje)
        
        detector.mostrar_progreso = mostrar_progreso
        
        # Escanear archivos
        peliculas = detector.escanear_carpeta()
        st.session_state.peliculas = peliculas
        
        progress_bar.progress(60)
        status_text.text("🔍 Buscando duplicados híbridos...")
        
        # Crear placeholder para mostrar progreso
        progress_placeholder = st.empty()
        
        # Callback para mostrar progreso en Streamlit (con manejo seguro de contexto)
        def mostrar_progreso_streamlit(mensaje):
            try:
                # Verificar si estamos en el contexto correcto de Streamlit
                if hasattr(st, '_is_running_with_streamlit') and st._is_running_with_streamlit:
                    progress_placeholder.text(mensaje)
                else:
                    # Si no estamos en contexto de Streamlit, solo logear
                    import logging
                    logging.getLogger(__name__).info(f"Progreso: {mensaje}")
            except Exception as e:
                # Si hay error, solo logear sin causar warnings
                import logging
                logging.getLogger(__name__).info(f"Progreso: {mensaje} (callback error: {e})")
        
        # Asignar callback al detector
        detector.mostrar_progreso_streamlit = mostrar_progreso_streamlit
        
        # NUEVO ENFOQUE: Búsqueda rápida + acceso directo a BBDD PLEX
        st.info("🔍 **Nuevo enfoque:** Búsqueda rápida + acceso directo a base de datos PLEX...")
        
        # NUEVO ENFOQUE: Usar el método optimizado del detector
        st.info("🔍 **Nuevo enfoque:** Búsqueda rápida + metadatos de PLEX desde base de datos...")
        
        try:
            # Usar el método optimizado del detector
            duplicados_mejorados = detector.encontrar_duplicados_rapido_con_plex(callback_progreso=mostrar_progreso_streamlit)
            
            if duplicados_mejorados:
                st.success(f"✅ Escaneo completado: {len(duplicados_mejorados)} grupos con metadatos de PLEX")
                
                # Guardar en session state
                st.session_state.duplicados = duplicados_mejorados
                st.session_state.descartados = []
                
                # Mostrar resultados inmediatamente
                st.rerun()
            else:
                st.info("ℹ️ No se encontraron duplicados")
                
        except Exception as e:
            st.error(f"❌ Error en escaneo optimizado: {e}")
            # Fallback al método tradicional
            st.info("🔄 Usando método tradicional como fallback...")
            duplicados_tradicionales = detector.encontrar_duplicados()
            st.session_state.duplicados = duplicados_tradicionales
            st.session_state.descartados = []
            st.rerun()
        
        progress_bar.progress(100)
        status_text.text("✅ Escaneo híbrido completado")
        
        # Mostrar resultados inmediatamente
        total_grupos = len(st.session_state.duplicados) if 'duplicados' in st.session_state else 0
        grupos_descartados = len(st.session_state.descartados) if 'descartados' in st.session_state else 0
        
        if total_grupos > 0:
            st.success(f"🎯 Escaneo híbrido completado: {total_grupos} grupos encontrados")
            if grupos_descartados > 0:
                st.info(f"📊 {grupos_descartados} grupos descartados, {total_grupos - grupos_descartados} grupos mantenidos")
            else:
                st.info("📊 Todos los grupos se mantienen para procesamiento")
            
            # Forzar actualización de la página para mostrar resultados
            st.rerun()
        else:
            st.info("ℹ️ No se encontraron duplicados en el escaneo híbrido")
        
    except Exception as e:
        st.error(f"❌ Error durante el escaneo: {e}")
        st.session_state.scanning = False
    finally:
        st.session_state.scanning = False


def process_traditional_scan(carpeta: str):
    """Procesa el escaneo tradicional"""
    st.session_state.scanning = True
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Iniciando escaneo tradicional...")
        progress_bar.progress(10)
        
        # Crear detector sin PLEX
        detector = MovieDetector(carpeta, use_plex=False)
        st.session_state.detector = detector
        
        status_text.text("📁 Escaneando archivos...")
        progress_bar.progress(30)
        
        # Escanear archivos
        peliculas = detector.escanear_carpeta()
        st.session_state.peliculas = peliculas
        
        progress_bar.progress(60)
        status_text.text("🔍 Buscando duplicados...")
        
        # Buscar duplicados
        duplicados = detector.encontrar_duplicados()
        st.session_state.duplicados = duplicados
        
        progress_bar.progress(100)
        status_text.text("✅ Escaneo completado")
        
    except Exception as e:
        st.error(f"❌ Error durante el escaneo: {e}")
        st.session_state.scanning = False
    finally:
        st.session_state.scanning = False


def _procesar_plex_scanner():
    """Procesa el escáner de PLEX"""
    try:
        from src.utils.video import PlexScanner
        
        config = st.session_state.plex_scanner_config
        directorio = config['directorio']
        
        st.info(f"🔍 Escaneando directorio: {directorio}")
        
        # Crear scanner
        scanner = PlexScanner()
        
        # Mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 Iniciando escaneo de PLEX...")
        progress_bar.progress(10)
        
        # Escanear directorio
        resultados = scanner.escanear_directorio(directorio)
        
        progress_bar.progress(50)
        status_text.text("📊 Procesando resultados...")
        
        # Guardar resultados
        st.session_state.plex_scanner_results = resultados
        
        progress_bar.progress(100)
        status_text.text("✅ Escaneo completado")
        
        # Mostrar resumen
        if resultados['error']:
            st.error(f"❌ Error en el escaneo: {resultados['error']}")
        else:
            total = resultados['total_archivos']
            encontradas = len(resultados['peliculas_encontradas'])
            no_encontradas = len(resultados['peliculas_no_encontradas'])
            
            st.success(f"✅ Escaneo completado: {total} archivos procesados")
            st.info(f"📊 Resultados: {encontradas} encontradas, {no_encontradas} no encontradas")
            
            if no_encontradas > 0:
                st.warning(f"⚠️ {no_encontradas} películas no están reconocidas por PLEX")
        
        # Limpiar progreso
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Error procesando escáner de PLEX: {e}")
        import traceback
        traceback.print_exc()


def render_results_section():
    """Renderiza la sección de resultados"""
    if not st.session_state.duplicados:
        return
    
    st.subheader("🎯 Resultados de Duplicados")
    
    # Estadísticas
    total_grupos = len(st.session_state.duplicados)
    total_archivos = sum(len(grupo) for grupo in st.session_state.duplicados)
    total_size = sum(
        sum(p.get('tamaño', 0) for p in grupo) 
        for grupo in st.session_state.duplicados
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Grupos de Duplicados", total_grupos)
    with col2:
        st.metric("📁 Archivos Duplicados", total_archivos)
    with col3:
        st.metric("💾 Tamaño Total", f"{total_size / (1024**3):.2f} GB")
    with col4:
        st.metric("💰 Espacio Recuperable", f"{total_size / (1024**3) / 2:.2f} GB")
    
    # Mostrar progreso si está escaneando
    if st.session_state.get('scanning', False):
        st.info("🔄 Procesando grupos en segundo plano...")
        st.progress(0.5)  # Progreso aproximado
    
    # Lista de duplicados
    if st.session_state.duplicados:
        total_grupos = len(st.session_state.duplicados)
        
        # Navegación entre grupos
        if total_grupos > 0:
            # Inicializar índice de grupo actual si no existe
            if 'current_group_index' not in st.session_state:
                st.session_state.current_group_index = 0
            
            # Mostrar navegación si hay más de 1 grupo
            if total_grupos > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("⬅️ Anterior", disabled=st.session_state.current_group_index == 0):
                        if st.session_state.current_group_index > 0:
                            st.session_state.current_group_index -= 1
                            st.rerun()
                with col2:
                    st.write(f"📊 Grupo {st.session_state.current_group_index + 1} de {total_grupos}")
                with col3:
                    if st.button("➡️ Siguiente", disabled=st.session_state.current_group_index >= total_grupos - 1):
                        if st.session_state.current_group_index < total_grupos - 1:
                            st.session_state.current_group_index += 1
                            st.rerun()
            else:
                st.write(f"📊 Mostrando 1 grupo de duplicados")
        
        # Mostrar grupos
        if total_grupos > 1:
            # Mostrar solo el grupo actual con navegación
            current_index = st.session_state.get('current_group_index', 0)
            grupo_actual = st.session_state.duplicados[current_index]
            
            with st.expander(f"🎬 Grupo {current_index + 1}: {grupo_actual[0].get('titulo', 'Sin título')} ({len(grupo_actual)} copias)"):
                _mostrar_grupo_duplicados(grupo_actual, current_index)
        else:
            # Mostrar todos los grupos si hay pocos
            for i, grupo in enumerate(st.session_state.duplicados):
                with st.expander(f"🎬 Grupo {i+1}: {grupo[0].get('titulo', 'Sin título')} ({len(grupo)} copias)"):
                    _mostrar_grupo_duplicados(grupo, i)
    else:
        st.info("ℹ️ No hay duplicados para mostrar")


def _mostrar_grupo_duplicados(grupo: List[Dict], indice: int):
    """Muestra un grupo de duplicados"""
    if not grupo:
        return
    
    # Mostrar información del grupo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Archivos", len(grupo))
    with col2:
        total_size = sum(p.get('tamaño', 0) for p in grupo)
        st.metric("💾 Tamaño Total", f"{total_size / (1024**3):.2f} GB")
    with col3:
        st.metric("🎯 Similitud", f"{grupo[0].get('similitud', 0):.1%}")
    
    # Mostrar cada archivo del grupo
    for i, pelicula in enumerate(grupo):
        with st.expander(f"📁 {pelicula.get('nombre', 'Sin nombre')} ({i+1})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Ruta:** `{pelicula.get('archivo', 'Sin ruta')}`")
                st.write(f"**Tamaño:** {pelicula.get('tamaño', 0) / (1024**3):.2f} GB")
                st.write(f"**Calidad:** {pelicula.get('calidad', 'Desconocida')}")
            
            with col2:
                if pelicula.get('has_plex_metadata'):
                    st.success("✅ Metadatos de PLEX disponibles")
                    if pelicula.get('duration_plex'):
                        st.write(f"**Duración:** {pelicula.get('duration_plex', 0) // 60000} min")
                    if pelicula.get('rating_plex'):
                        st.write(f"**Rating:** {pelicula.get('rating_plex', 0)}")
                    if pelicula.get('genres_plex'):
                        st.write(f"**Géneros:** {', '.join(pelicula.get('genres_plex', []))}")
                else:
                    st.info("ℹ️ Sin metadatos de PLEX")
            
            # Botones de acción
            debug_mode = settings.get_debug_enabled()
            st.write(f"🔧 Debug mode: {debug_mode}")  # Debug info
            
            if debug_mode:
                # En modo debug: solo botón de mover a debug (que actúa como eliminar)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button(f"🗑️ Mover a Debug", key=f"move_debug_{indice}_{i}"):
                        _move_to_debug(pelicula)
                with col2:
                    if st.button(f"🔄 Renombrar PLEX", key=f"rename_{indice}_{i}"):
                        _show_rename_options(pelicula)
                with col3:
                    if st.button(f"▶️ Reproducir", key=f"play_{indice}_{i}"):
                        _play_video(pelicula)
                with col4:
                    show_details = st.checkbox(f"👁️ Ver Detalles", key=f"details_{indice}_{i}")
                    if show_details:
                        _show_detailed_info(pelicula)
            else:
                # En modo normal: botones de eliminar y mover a debug
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    if st.button(f"🗑️ Eliminar", key=f"delete_{indice}_{i}"):
                        st.warning("⚠️ Función de eliminación no implementada")
                with col2:
                    if st.button(f"📁 Mover a Debug", key=f"move_{indice}_{i}"):
                        _move_to_debug(pelicula)
                with col3:
                    if st.button(f"🔄 Renombrar PLEX", key=f"rename_{indice}_{i}"):
                        _show_rename_options(pelicula)
                with col4:
                    if st.button(f"▶️ Reproducir", key=f"play_{indice}_{i}"):
                        _play_video(pelicula)
                with col5:
                    show_details = st.checkbox(f"👁️ Ver Detalles", key=f"details_{indice}_{i}")
                    if show_details:
                        _show_detailed_info(pelicula)


def _move_to_debug(pelicula: Dict):
    """Mueve una película a la carpeta de debug"""
    try:
        from pathlib import Path
        import shutil
        
        debug_folder = settings.get_debug_folder()
        if not debug_folder:
            st.error("❌ Carpeta de debug no configurada")
            return
        
        archivo_origen = Path(pelicula.get('archivo', ''))
        if not archivo_origen.exists():
            st.error(f"❌ Archivo no encontrado: {archivo_origen}")
            return
        
        # Crear carpeta de debug si no existe
        Path(debug_folder).mkdir(parents=True, exist_ok=True)
        
        # Mover archivo
        archivo_destino = Path(debug_folder) / archivo_origen.name
        shutil.move(str(archivo_origen), str(archivo_destino))
        
        st.success(f"✅ Archivo movido a debug: {archivo_destino.name}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error moviendo archivo: {e}")


def _show_rename_options(pelicula: Dict):
    """Muestra opciones de renombrado para PLEX"""
    try:
        archivo_path = pelicula.get('archivo', '')
        if not archivo_path:
            st.error("❌ No se encontró la ruta del archivo")
            return
        
        renamer = PlexSmartRenamer()
        
        # Analizar archivo
        file_info = renamer.analyze_filename(Path(archivo_path).name)
        
        if not file_info.get('version'):
            st.info("ℹ️ Este archivo no parece tener una versión especial (Director's Cut, Extended, etc.)")
            return
        
        st.subheader("🔄 Opciones de Renombrado para PLEX")
        
        # Mostrar información del archivo
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Archivo actual:** {Path(archivo_path).name}")
            st.write(f"**Título:** {file_info['title']}")
            st.write(f"**Año:** {file_info['year']}")
            st.write(f"**Versión:** {file_info['version']}")
        
        with col2:
            st.write(f"**Ruta:** {archivo_path}")
            st.write(f"**Tamaño:** {pelicula.get('tamaño', 'N/A')}")
            st.write(f"**Calidad:** {pelicula.get('calidad', 'N/A')}")
        
        st.divider()
        
        # Opción 1: Misma carpeta
        st.subheader("📂 Opción 1: Misma Carpeta")
        suggestion1 = renamer.suggest_rename(archivo_path, create_folder=False)
        if suggestion1:
            st.write(f"**Nuevo nombre:** `{suggestion1['suggested_name']}`")
            st.write(f"**Nueva ruta:** `{suggestion1['suggested_path']}`")
            
            if st.button("✅ Renombrar en la misma carpeta", key=f"rename_same_{pelicula.get('archivo', '')}"):
                if _perform_rename(suggestion1):
                    st.success("✅ Archivo renombrado exitosamente")
                    st.rerun()
        
        # Opción 2: Carpeta separada
        st.subheader("📁 Opción 2: Carpeta Separada")
        suggestion2 = renamer.suggest_rename(archivo_path, create_folder=True)
        if suggestion2:
            st.write(f"**Nuevo nombre:** `{suggestion2['suggested_name']}`")
            st.write(f"**Nueva ruta:** `{suggestion2['suggested_path']}`")
            
            if st.button("✅ Renombrar en carpeta separada", key=f"rename_folder_{pelicula.get('archivo', '')}"):
                if _perform_rename(suggestion2):
                    st.success("✅ Archivo renombrado exitosamente")
                    st.rerun()
        
        # Información adicional
        st.info("💡 **Consejo:** PLEX reconocerá automáticamente las ediciones usando el formato `{edition-Nombre}`. Esto permitirá que PLEX muestre ambas versiones como ediciones separadas de la película duplicada.")
        
    except Exception as e:
        st.error(f"❌ Error mostrando opciones de renombrado: {e}")


def _perform_rename(suggestion: Dict) -> bool:
    """Realiza el renombrado del archivo"""
    try:
        from pathlib import Path
        import shutil
        
        original_path = Path(suggestion['original_path'])
        new_path = Path(suggestion['suggested_path'])
        
        # Verificar que el archivo original existe
        if not original_path.exists():
            st.error(f"❌ Archivo no encontrado: {original_path}")
            return False
        
        # Crear carpeta de destino si es necesario
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear backup
        backup_path = original_path.with_suffix(original_path.suffix + '.backup')
        shutil.copy2(original_path, backup_path)
        st.info(f"📁 Backup creado: {backup_path.name}")
        
        # Renombrar archivo
        original_path.rename(new_path)
        
        st.success(f"✅ Archivo renombrado: {original_path.name} → {new_path.name}")
        return True
        
    except Exception as e:
        st.error(f"❌ Error renombrando archivo: {e}")
        return False


def _play_video(pelicula: Dict):
    """Reproduce un video"""
    try:
        from src.settings.settings import Settings
        import subprocess
        import os
        import platform
        
        settings = Settings()
        show_embedded = settings.get("ui.show_embedded_players", False)
        video_path = pelicula.get('archivo', '')
        
        if not video_path:
            st.error("❌ No se encontró la ruta del archivo")
            return
        
        if show_embedded:
            # Mostrar reproductor embebido
            start_time = settings.get("ui.video_start_time_seconds", 900)
            st.markdown("### 🎬 Reproductor Embebido")
            
            # Convertir ruta de Windows a formato web
            if video_path.startswith('\\'):
                # Ruta UNC → file:///server/path
                tmp_web_path = video_path.replace('\\', '/')
                web_path = 'file:///' + tmp_web_path.lstrip('/')
            else:
                # Ruta local → file:///C:/path
                tmp_web_path = video_path.replace('\\', '/')
                web_path = 'file:///' + tmp_web_path
            
            # Mostrar controles de tiempo
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Inicio:** {start_time // 60}:{start_time % 60:02d}")
            with col2:
                new_start = st.number_input("Minuto de inicio", min_value=0, value=start_time // 60, key=f"start_{video_path}")
                start_seconds = new_start * 60
            
            # Mostrar reproductor HTML5 usando st.video
            st.video(web_path, start_time=start_seconds)
            
            # Guardar en session state para persistir
            st.session_state[f"player_{video_path}"] = {
                'web_path': web_path,
                'start_time': start_seconds,
                'video_path': video_path
            }
            
        else:
            # Abrir con reproductor del sistema
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            else:  # Linux
                subprocess.run(["xdg-open", video_path])
            
            st.success(f"🎬 Abriendo: {os.path.basename(video_path)}")
            
    except Exception as e:
        st.error(f"❌ Error reproduciendo video: {e}")


def _show_detailed_info(pelicula: Dict):
    """Muestra información detallada de una película"""
    try:
        st.markdown("### 📁 Información del Archivo")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Título:** {pelicula.get('titulo', 'N/A')}")
            st.write(f"**Año:** {pelicula.get('año', 'N/A')}")
            st.write(f"**Tamaño:** {pelicula.get('tamaño', 0) / (1024**3):.2f} GB")
            st.write(f"**Calidad:** {pelicula.get('calidad', 'N/A')}")
        
        with col2:
            duracion = pelicula.get('duracion', 0)
            if duracion > 0:
                st.write(f"**Duración:** {duracion // 60000} min")
            else:
                st.write("**Duración:** No disponible")
            st.write(f"**Ruta:** `{pelicula.get('archivo', 'N/A')}`")
            
            # Mostrar información de análisis de video si está disponible
            if pelicula.get('video_analysis_available'):
                st.markdown("---")
                st.markdown("**🔍 Análisis de Video:**")
                if pelicula.get('resolution'):
                    st.write(f"**Resolución:** {pelicula.get('resolution')}")
                if pelicula.get('quality_category'):
                    st.write(f"**Calidad:** {pelicula.get('quality_category')}")
                if pelicula.get('bitrate'):
                    st.write(f"**Bitrate:** {pelicula.get('bitrate')} kbps")
                if pelicula.get('fps'):
                    st.write(f"**FPS:** {pelicula.get('fps')}")
                if pelicula.get('video_codec'):
                    st.write(f"**Video:** {pelicula.get('video_codec')}")
                if pelicula.get('audio_codec'):
                    st.write(f"**Audio:** {pelicula.get('audio_codec')}")
        
        # Información de PLEX si está disponible
        if pelicula.get('has_plex_metadata'):
            st.markdown("### 🎬 Metadatos de PLEX")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Título PLEX:** {pelicula.get('title_plex', 'N/A')}")
                st.write(f"**Año PLEX:** {pelicula.get('year_plex', 'N/A')}")
                duration_plex = pelicula.get('duration_plex', 0)
                if duration_plex > 0:
                    st.write(f"**Duración PLEX:** {duration_plex // 60000} min")
                else:
                    st.write("**Duración PLEX:** No disponible")
                st.write(f"**Rating PLEX:** {pelicula.get('rating_plex', 'N/A')}")
            
            with col2:
                if pelicula.get('genres_plex'):
                    st.write(f"**Géneros:** {', '.join(pelicula.get('genres_plex', []))}")
                if pelicula.get('resolution_plex'):
                    st.write(f"**Resolución:** {pelicula.get('resolution_plex', 'N/A')}")
                if pelicula.get('video_codec'):
                    st.write(f"**Códec de Video:** {pelicula.get('video_codec', 'N/A')}")
                if pelicula.get('audio_codec'):
                    st.write(f"**Códec de Audio:** {pelicula.get('audio_codec', 'N/A')}")
        else:
            st.markdown("### ⚠️ Sin Metadatos de PLEX")
            st.info("Esta película no se encontró en PLEX. Esto puede deberse a:")
            st.write("- El archivo no está en ninguna biblioteca de PLEX")
            st.write("- El nombre del archivo no coincide con el título en PLEX")
            st.write("- La película no ha sido escaneada por PLEX")
            st.write("- El archivo está en una ubicación no monitoreada por PLEX")
            
    except Exception as e:
        st.error(f"❌ Error mostrando detalles: {e}")


def _show_persistent_players():
    """Muestra reproductores persistentes guardados en session state"""
    import os
    
    # Buscar reproductores en session state
    player_keys = [key for key in st.session_state.keys() if key.startswith('player_')]
    
    if player_keys:
        st.markdown("### 🎬 Reproductores Activos")
        for key in player_keys:
            value = st.session_state[key]
            video_path = value.get('video_path', '')
            web_path = value.get('web_path', '')
            start_time = value.get('start_time', 0)
            
            st.markdown(f"**Reproduciendo:** {os.path.basename(video_path)}")
            st.video(web_path, start_time=start_time)
            
            if st.button(f"❌ Cerrar reproductor", key=f"close_{key}"):
                del st.session_state[key]
                st.rerun()


def run_streamlit_app():
    """Función principal de la aplicación Streamlit"""
    # Configurar logging
    configure_logging()
    
    # Inicializar estado de sesión
    init_session_state()
    
    # Configurar página
    setup_page_config()
    
    # Título principal
    st.title("🎬 Utilidades Plex")
    st.markdown("---")
    
    # Renderizar sidebar
    render_sidebar()
    
    # Mostrar reproductores persistentes
    _show_persistent_players()
    
    # Área principal de contenido
    st.markdown("## 📊 Área Principal")
    
    # Mostrar estado de escaneo
    if st.session_state.scanning:
        st.info("🔍 Escaneo en progreso...")
        st.progress(0.5)
    elif st.session_state.peliculas:
        st.success(f"✅ Escaneo completado: {len(st.session_state.peliculas)} películas encontradas")
    
    # Procesar escaneo pendiente en el área principal
    if hasattr(st.session_state, 'pending_scan') and st.session_state.pending_scan:
        pending = st.session_state.pending_scan
        st.session_state.pending_scan = None  # Limpiar para evitar repetición
        
        if pending['tipo'] == 'hibrido':
            process_hybrid_scan(pending['carpeta'])
        elif pending['tipo'] == 'tradicional':
            process_traditional_scan(pending['carpeta'])
    
    # Procesar escáner de PLEX pendiente
    if hasattr(st.session_state, 'plex_scanner_pending') and st.session_state.plex_scanner_pending:
        st.session_state.plex_scanner_pending = False  # Limpiar para evitar repetición
        _procesar_plex_scanner()
    
    # Debug: Mostrar estado de session_state
    if st.checkbox("🔍 Debug - Mostrar estado de sesión", value=False):
        st.write("Session State keys:", list(st.session_state.keys()))
        if hasattr(st.session_state, 'plex_scanner_results'):
            st.write("PLEX Scanner Results:", st.session_state.plex_scanner_results)
    
    # Mostrar resultados si existen
    if st.session_state.duplicados:
        st.markdown("---")
        render_results_section()
    elif hasattr(st.session_state, 'plex_scanner_results') and st.session_state.plex_scanner_results:
        # Mostrar resultados del PLEX Scanner
        st.markdown("---")
        _mostrar_resultados_plex_scanner()
    else:
        st.info("ℹ️ No hay duplicados para mostrar. Realiza un escaneo para ver resultados.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            🎬 Utilidades Plex v1.0.0 | 
            Desarrollado con ❤️ usando Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )


class StreamlitAppManager:
    """Gestor principal de la aplicación Streamlit"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Ejecuta la aplicación principal"""
        run_streamlit_app()