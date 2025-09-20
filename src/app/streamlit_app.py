#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación principal de Streamlit
Interfaz de usuario para el detector de películas duplicadas
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
    if 'imdb_service' not in st.session_state:
        st.session_state.imdb_service = IMDBService()
    if 'telegram_service' not in st.session_state:
        st.session_state.telegram_service = TelegramService()
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False


def setup_page_config():
    """Configura la página de Streamlit"""
    st.set_page_config(
        page_title="🎬 Detector de Películas Duplicadas",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_sidebar():
    """Renderiza la barra lateral con configuración"""
    st.sidebar.title("⚙️ Configuración")
    
    # Configuración de detección
    st.sidebar.subheader("🔍 Detección")
    umbral = st.sidebar.slider(
        "Umbral de similitud",
        min_value=0.0,
        max_value=1.0,
        value=settings.get_similarity_threshold(),
        step=0.1,
        help="Umbral para considerar películas como duplicadas"
    )
    
    # Configuración de APIs
    st.sidebar.subheader("🔗 APIs")
    
    # IMDB
    imdb_configured = st.session_state.imdb_service.is_api_configured()
    st.sidebar.write(f"IMDB: {'✅ Configurado' if imdb_configured else '❌ No configurado'}")
    
    if not imdb_configured:
        st.sidebar.warning("Configure la API key de IMDB en las variables de entorno")
    
    # Telegram
    telegram_configured = st.session_state.telegram_service.is_configured()
    st.sidebar.write(f"Telegram: {'✅ Configurado' if telegram_configured else '❌ No configurado'}")
    
    if not telegram_configured:
        st.sidebar.warning("Configure el bot token y channel ID de Telegram")
    
    # Botones de prueba
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🧪 Probar IMDB"):
            if st.session_state.imdb_service.test_connection():
                st.sidebar.success("✅ IMDB conectado")
            else:
                st.sidebar.error("❌ Error en IMDB")
    
    with col2:
        if st.button("🧪 Probar Telegram"):
            if st.session_state.telegram_service.test_connection():
                st.sidebar.success("✅ Telegram conectado")
            else:
                st.sidebar.error("❌ Error en Telegram")
    
    return umbral


def render_scan_section():
    """Renderiza la sección de escaneo"""
    st.header("📁 Escanear Carpeta")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Usar última ruta escaneada como valor por defecto
        default_path = settings.get_last_scan_path()
        carpeta = st.text_input(
            "Ruta de la carpeta a analizar",
            value=default_path,
            help="Seleccione la carpeta que contiene las películas"
        )
    
    with col2:
        st.write("")  # Espaciado
        if st.button("📂 Seleccionar Carpeta", key="select_folder"):
            st.info("Use el explorador de archivos de su sistema")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        scan_button = st.button("🔍 Escanear", type="primary", disabled=st.session_state.scanning)
    
    with col2:
        if st.button("🔄 Limpiar"):
            st.session_state.peliculas = []
            st.session_state.duplicados = []
            st.session_state.detector = None
            st.rerun()
    
    if scan_button and carpeta:
        if not Path(carpeta).exists():
            st.error("❌ La carpeta especificada no existe")
            return
        
        # Crear detector y escanear
        st.session_state.scanning = True
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔍 Iniciando escaneo...")
            progress_bar.progress(10)
            
            # Debug: Mostrar información
            st.info(f"📁 Escaneando carpeta: {carpeta}")
            
            detector = MovieDetector(carpeta)
            st.session_state.detector = detector
            
            status_text.text("📁 Escaneando archivos...")
            progress_bar.progress(30)
            
            # Debug: Mostrar proceso
            st.info("🔍 Buscando archivos de video...")
            
            peliculas = detector.escanear_carpeta()
            st.session_state.peliculas = peliculas
            
            # Debug: Mostrar resultados
            st.success(f"✅ Encontradas {len(peliculas)} películas")
            
            if len(peliculas) > 0:
                # Mostrar algunas películas encontradas
                st.write("**Películas encontradas:**")
                for i, pelicula in enumerate(peliculas[:5]):  # Mostrar solo las primeras 5
                    st.write(f"- {pelicula['nombre']} ({pelicula['año']}) - {pelicula['calidad']}")
                if len(peliculas) > 5:
                    st.write(f"... y {len(peliculas) - 5} más")
            
            status_text.text("🔍 Buscando duplicados...")
            progress_bar.progress(70)
            
            duplicados = detector.encontrar_duplicados()
            st.session_state.duplicados = duplicados
            
            # Debug: Mostrar duplicados
            st.success(f"✅ Encontrados {len(duplicados)} grupos de duplicados")
            
            progress_bar.progress(100)
            status_text.text("✅ Escaneo completado")
            
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error durante el escaneo: {e}")
            st.exception(e)  # Mostrar el traceback completo
        finally:
            st.session_state.scanning = False


def render_results_section():
    """Renderiza la sección de resultados"""
    if not st.session_state.peliculas:
        return
    
    st.header("📊 Resultados del Análisis")
    
    # Estadísticas generales
    detector = st.session_state.detector
    if detector:
        stats = detector.get_estadisticas()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Películas", stats['total_peliculas'])
        
        with col2:
            st.metric("Duplicados", stats['total_duplicados'])
        
        with col3:
            st.metric("Grupos Duplicados", stats['grupos_duplicados'])
        
        with col4:
            st.metric("Espacio Duplicado", stats['espacio_duplicado_formateado'])
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Películas", "🔄 Duplicados", "📈 Análisis"])
    
    with tab1:
        render_movies_list()
    
    with tab2:
        render_duplicates_list()
    
    with tab3:
        render_analysis()


def render_movies_list():
    """Renderiza la lista de películas"""
    if not st.session_state.peliculas:
        st.info("No hay películas para mostrar")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(st.session_state.peliculas)
    
    # Formatear columnas
    df['tamaño_formateado'] = df['tamaño'].apply(lambda x: format_file_size(x))
    df['año_display'] = df['año'].apply(lambda x: str(x) if x > 0 else 'Desconocido')
    
    # Columnas a mostrar
    display_columns = ['titulo', 'año_display', 'calidad', 'tamaño_formateado', 'carpeta']
    column_names = ['Título', 'Año', 'Calidad', 'Tamaño', 'Carpeta']
    
    st.dataframe(
        df[display_columns],
        column_config={
            'titulo': 'Título',
            'año_display': 'Año',
            'calidad': 'Calidad',
            'tamaño_formateado': 'Tamaño',
            'carpeta': 'Carpeta'
        },
        use_container_width=True,
        height=400
    )


def render_duplicates_list():
    """Renderiza la lista de duplicados"""
    if not st.session_state.duplicados:
        st.info("No se encontraron duplicados")
        return
    
    for i, grupo in enumerate(st.session_state.duplicados, 1):
        with st.expander(f"🔄 Grupo {i}: {grupo[0]['titulo']} ({grupo[0]['año'] if grupo[0]['año'] > 0 else 'Desconocido'})"):
            
            # Información del grupo
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Archivos encontrados:** {len(grupo)}")
            
            with col2:
                if st.button(f"📤 Subir a Telegram", key=f"upload_group_{i}"):
                    upload_group_to_telegram(grupo)
            
            # Lista de archivos
            for j, pelicula in enumerate(grupo, 1):
                st.write(f"**{j}.** {pelicula['nombre']}")
                st.write(f"   📁 Carpeta: {pelicula['carpeta']}")
                st.write(f"   🎯 Calidad: {pelicula['calidad']}")
                st.write(f"   💾 Tamaño: {format_file_size(pelicula['tamaño'])}")
                st.write("---")


def render_analysis():
    """Renderiza el análisis detallado"""
    if not st.session_state.peliculas:
        st.info("No hay datos para analizar")
        return
    
    # Análisis por calidad
    st.subheader("📊 Análisis por Calidad")
    
    df = pd.DataFrame(st.session_state.peliculas)
    calidad_counts = df['calidad'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.bar_chart(calidad_counts)
    
    with col2:
        st.write("**Distribución por calidad:**")
        for calidad, count in calidad_counts.items():
            st.write(f"- {calidad}: {count} archivos")
    
    # Análisis por año
    st.subheader("📅 Análisis por Año")
    
    df_años = df[df['año'] > 0]
    if not df_años.empty:
        año_counts = df_años['año'].value_counts().sort_index()
        st.line_chart(año_counts)
    else:
        st.info("No se encontraron años en los archivos")


def upload_group_to_telegram(grupo: List[Dict]):
    """Sube un grupo de duplicados a Telegram"""
    if not st.session_state.telegram_service.is_configured():
        st.error("❌ Telegram no está configurado")
        return
    
    if not st.session_state.imdb_service.is_api_configured():
        st.error("❌ IMDB no está configurado")
        return
    
    # Procesar cada archivo del grupo
    for i, pelicula in enumerate(grupo):
        with st.spinner(f"Procesando {pelicula['nombre']}..."):
            try:
                # Obtener información de IMDB
                movie_info = st.session_state.imdb_service.get_movie_info(
                    pelicula['titulo'], 
                    pelicula['año'] if pelicula['año'] > 0 else None
                )
                
                if not movie_info:
                    st.warning(f"No se encontró información de IMDB para: {pelicula['titulo']}")
                    continue
                
                # Descargar póster si existe
                poster_path = None
                if movie_info.get('poster_url'):
                    poster_filename = f"poster_{pelicula['titulo'].replace(' ', '_')}.jpg"
                    poster_path = Path("temp") / poster_filename
                    poster_path.parent.mkdir(exist_ok=True)
                    
                    if st.session_state.imdb_service.download_poster(
                        movie_info['poster_url'], 
                        poster_path
                    ):
                        st.success(f"Póster descargado: {poster_filename}")
                
                # Subir a Telegram
                success = st.session_state.telegram_service.upload_movie_to_channel(
                    movie_info, 
                    pelicula, 
                    str(poster_path) if poster_path else None
                )
                
                if success:
                    st.success(f"✅ {pelicula['nombre']} subido correctamente")
                else:
                    st.error(f"❌ Error subiendo {pelicula['nombre']}")
                
                # Limpiar póster temporal
                if poster_path and poster_path.exists():
                    poster_path.unlink()
                
            except Exception as e:
                st.error(f"❌ Error procesando {pelicula['nombre']}: {e}")


def format_file_size(bytes_size: int) -> str:
    """Formatea el tamaño en bytes a formato legible"""
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unidad}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def render_export_section():
    """Renderiza la sección de exportación"""
    if not st.session_state.duplicados:
        return
    
    st.header("💾 Exportar Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Exportar a TXT"):
            if st.session_state.detector:
                output_file = st.session_state.detector.guardar_resultados()
                if output_file:
                    st.success(f"✅ Resultados guardados en: {output_file}")
                    
                    # Mostrar botón de descarga
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="📥 Descargar archivo",
                            data=f.read(),
                            file_name=Path(output_file).name,
                            mime="text/plain"
                        )
    
    with col2:
        if st.button("📊 Exportar a CSV"):
            if st.session_state.duplicados:
                export_to_csv()
                st.success("✅ Archivo CSV generado")


def export_to_csv():
    """Exporta los duplicados a CSV"""
    # Crear lista de duplicados para CSV
    csv_data = []
    for i, grupo in enumerate(st.session_state.duplicados, 1):
        for j, pelicula in enumerate(grupo, 1):
            csv_data.append({
                'grupo': i,
                'posicion': j,
                'titulo': pelicula['titulo'],
                'año': pelicula['año'],
                'nombre_archivo': pelicula['nombre'],
                'calidad': pelicula['calidad'],
                'tamaño': pelicula['tamaño'],
                'carpeta': pelicula['carpeta'],
                'archivo_completo': pelicula['archivo']
            })
    
    # Crear DataFrame y guardar
    df = pd.DataFrame(csv_data)
    csv_file = "duplicados.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    # Mostrar botón de descarga
    with open(csv_file, 'rb') as f:
        st.download_button(
            label="📥 Descargar CSV",
            data=f.read(),
            file_name=csv_file,
            mime="text/csv"
        )


def run_streamlit_app():
    """Función principal que ejecuta la aplicación Streamlit"""
    configure_logging()
    setup_page_config()
    init_session_state()
    
    # Título principal
    st.title("🎬 Detector de Películas Duplicadas")
    st.markdown("---")
    
    # Barra lateral
    umbral = render_sidebar()
    
    # Actualizar umbral en configuración
    if umbral != settings.get_similarity_threshold():
        settings.set("detection.similarity_threshold", umbral)
    
    # Sección principal
    render_scan_section()
    
    # Mostrar resultados si existen
    if st.session_state.peliculas:
        render_results_section()
        render_export_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            🎬 Detector de Películas Duplicadas v1.0.0 | 
            Desarrollado con ❤️ usando Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )
