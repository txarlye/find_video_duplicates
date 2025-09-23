# -*- coding: utf-8 -*-
"""
Componentes de UI reutilizables para Streamlit
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from pathlib import Path


def render_plex_status(plex_connected: bool, plex_service=None) -> Dict[str, Any]:
    """
    Renderiza el estado de PLEX y retorna información útil
    
    Returns:
        dict: Información del estado de PLEX
    """
    if plex_connected:
        st.success("✅ PLEX conectado y listo")
        
        # Obtener estadísticas de PLEX
        try:
            libraries = plex_service.get_libraries() if plex_service else []
            movie_libraries = [lib for lib in libraries if lib.get('type') == 'movie']
            
            return {
                'connected': True,
                'libraries_count': len(movie_libraries),
                'libraries': movie_libraries
            }
        except Exception as e:
            st.warning(f"⚠️ Error obteniendo información de PLEX: {e}")
            return {'connected': True, 'libraries_count': 0, 'libraries': []}
    else:
        st.warning("⚠️ PLEX no conectado")
        return {'connected': False, 'libraries_count': 0, 'libraries': []}


def render_scan_progress(scanning: bool, peliculas_count: int = 0) -> None:
    """
    Renderiza el progreso del escaneo
    
    Args:
        scanning: Si está escaneando
        peliculas_count: Número de películas encontradas
    """
    if scanning:
        st.info("🔍 Escaneo en progreso...")
        st.progress(0.5)
    elif peliculas_count > 0:
        st.success(f"✅ Escaneo completado: {peliculas_count} películas encontradas")


def render_miniterminal(terminal_content: List[str], max_lines: int = 15) -> None:
    """
    Renderiza el miniterminal con archivos encontrados
    
    Args:
        terminal_content: Lista de líneas del terminal
        max_lines: Número máximo de líneas a mostrar
    """
    if terminal_content:
        st.markdown("### 🔍 Miniterminal - Archivos encontrados:")
        # Mostrar solo las últimas líneas
        recent_lines = terminal_content[-max_lines:] if len(terminal_content) > max_lines else terminal_content
        st.code("\n".join(recent_lines), language="text")


def render_duplicate_group(group: List[Dict], group_index: int, show_plex_info: bool = True) -> None:
    """
    Renderiza un grupo de duplicados de forma estructurada
    
    Args:
        group: Lista de películas duplicadas
        group_index: Índice del grupo
        show_plex_info: Si mostrar información de PLEX
    """
    if not group:
        return
    
    st.subheader(f"🎬 Grupo {group_index + 1}: {group[0].get('titulo', 'Sin título')}")
    
    # Mostrar información del grupo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Archivos", len(group))
    with col2:
        total_size = sum(p.get('tamaño', 0) for p in group)
        st.metric("💾 Tamaño Total", f"{total_size / (1024**3):.2f} GB")
    with col3:
        st.metric("🎯 Similitud", f"{group[0].get('similitud', 0):.1%}")
    
    # Mostrar cada archivo del grupo
    for i, pelicula in enumerate(group):
        with st.expander(f"📁 {pelicula.get('nombre', 'Sin nombre')} ({i+1})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Ruta:** `{pelicula.get('archivo', 'Sin ruta')}`")
                st.write(f"**Tamaño:** {pelicula.get('tamaño', 0) / (1024**3):.2f} GB")
                st.write(f"**Calidad:** {pelicula.get('calidad', 'Desconocida')}")
                
                # Mostrar duración si está disponible
                if pelicula.get('duracion', 0) > 0:
                    st.write(f"**Duración:** {pelicula.get('duracion', 0) // 60000} min")
            
            with col2:
                if show_plex_info and pelicula.get('has_plex_metadata'):
                    st.success("✅ Metadatos de PLEX disponibles")
                    
                    # Mostrar información específica de PLEX
                    if pelicula.get('duration_plex', 0) > 0:
                        st.write(f"**Duración PLEX:** {pelicula.get('duration_plex', 0) // 60000} min")
                    if pelicula.get('rating_plex', 0) > 0:
                        st.write(f"**Rating PLEX:** {pelicula.get('rating_plex', 0)}")
                    if pelicula.get('genres_plex'):
                        st.write(f"**Géneros:** {', '.join(pelicula.get('genres_plex', []))}")
                    if pelicula.get('resolution_plex'):
                        st.write(f"**Resolución:** {pelicula.get('resolution_plex', 'N/A')}")
                else:
                    st.info("ℹ️ Sin metadatos de PLEX")
            
            # Botones de acción
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"🗑️ Eliminar", key=f"delete_{group_index}_{i}"):
                    st.warning("⚠️ Función de eliminación no implementada")
            with col2:
                if st.button(f"📁 Mover a Debug", key=f"move_{group_index}_{i}"):
                    st.warning("⚠️ Función de movimiento no implementada")
            with col3:
                if st.button(f"▶️ Reproducir", key=f"play_{group_index}_{i}"):
                    _play_video(pelicula)
            with col4:
                show_details = st.checkbox(f"👁️ Ver Detalles", key=f"details_{group_index}_{i}")
                if show_details:
                    _show_detailed_info(pelicula)


def _show_detailed_info(pelicula: Dict) -> None:
    """
    Muestra información detallada de una película
    
    Args:
        pelicula: Diccionario con información de la película
    """
    # Información básica del archivo
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
        
        # Información adicional de PLEX
        if pelicula.get('directors_plex'):
            st.write(f"**Directores:** {', '.join(pelicula.get('directors_plex', []))}")
        if pelicula.get('actors_plex'):
            st.write(f"**Actores:** {', '.join(pelicula.get('actors_plex', [])[:5])}")  # Solo primeros 5
        if pelicula.get('studio_plex'):
            st.write(f"**Estudio:** {pelicula.get('studio_plex', 'N/A')}")
        if pelicula.get('summary_plex'):
            st.write(f"**Resumen:** {pelicula.get('summary_plex', 'N/A')[:200]}...")  # Solo primeros 200 caracteres
    else:
        st.markdown("### ⚠️ Sin Metadatos de PLEX")
        st.info("Esta película no se encontró en PLEX. Esto puede deberse a:")
        st.write("- El archivo no está en ninguna biblioteca de PLEX")
        st.write("- El nombre del archivo no coincide con el título en PLEX")
        st.write("- La película no ha sido escaneada por PLEX")
        st.write("- El archivo está en una ubicación no monitoreada por PLEX")
        
        # Sugerencias para mejorar la búsqueda
        st.markdown("**💡 Sugerencias:**")
        st.write("- Verifica que el archivo esté en una biblioteca de PLEX")
        st.write("- Asegúrate de que PLEX haya escaneado la biblioteca")
        st.write("- El nombre del archivo debería coincidir con el título en PLEX")


def render_scan_results(duplicados: List[List[Dict]], show_plex_info: bool = True) -> None:
    """
    Renderiza los resultados del escaneo
    
    Args:
        duplicados: Lista de grupos de duplicados
        show_plex_info: Si mostrar información de PLEX
    """
    if not duplicados:
        st.info("ℹ️ No se encontraron duplicados")
        return
    
    st.success(f"🎯 Se encontraron {len(duplicados)} grupos de duplicados")
    
    for i, grupo in enumerate(duplicados):
        render_duplicate_group(grupo, i, show_plex_info)
        st.markdown("---")


def _play_video(pelicula: Dict) -> None:
    """
    Reproduce un video usando el reproductor del sistema o embebido
    
    Args:
        pelicula: Diccionario con información de la película
    """
    from src.settings.settings import Settings
    
    settings = Settings()
    show_embedded = settings.get("ui.show_embedded_players", False)
    video_path = pelicula.get('archivo', '')
    
    if not video_path:
        st.error("❌ No se encontró la ruta del archivo")
        return
    
    if show_embedded:
        _show_embedded_player(pelicula)
    else:
        _open_with_system_player(video_path)


def _show_embedded_player(pelicula: Dict) -> None:
    """
    Muestra un reproductor embebido
    
    Args:
        pelicula: Diccionario con información de la película
    """
    from src.settings.settings import Settings
    
    settings = Settings()
    start_time = settings.get("ui.video_start_time_seconds", 900)  # 15 minutos por defecto
    
    video_path = pelicula.get('archivo', '')
    if not video_path:
        st.error("❌ No se encontró la ruta del archivo")
        return
    
    st.markdown("### 🎬 Reproductor Embebido")
    
    # Convertir ruta de Windows a formato web
    if video_path.startswith('\\\\'):
        # Ruta UNC - convertir a formato web
        web_path = video_path.replace('\\\\', 'file:///').replace('\\', '/')
    else:
        web_path = f"file:///{video_path.replace('\\', '/')}"
    
    # Mostrar controles de tiempo
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Inicio:** {start_time // 60}:{start_time % 60:02d}")
    with col2:
        new_start = st.number_input("Minuto de inicio", min_value=0, value=start_time // 60, key=f"start_{pelicula.get('archivo', '')}")
        start_seconds = new_start * 60
    
    # Mostrar reproductor HTML5
    st.video(web_path, start_time=start_seconds)
    
    # Sidebar con frame del minuto específico
    with st.sidebar:
        st.markdown("### 📸 Frame Preview")
        st.write(f"**Archivo:** {pelicula.get('nombre', 'N/A')}")
        st.write(f"**Tiempo:** {start_seconds // 60}:{start_seconds % 60:02d}")
        
        # Aquí podrías añadir lógica para extraer un frame específico
        # Por ahora mostramos información
        st.info("💡 Frame preview no implementado aún")


def _open_with_system_player(video_path: str) -> None:
    """
    Abre el video con el reproductor del sistema
    
    Args:
        video_path: Ruta del archivo de video
    """
    import subprocess
    import os
    import platform
    
    try:
        if platform.system() == "Windows":
            os.startfile(video_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", video_path])
        else:  # Linux
            subprocess.run(["xdg-open", video_path])
        
        st.success(f"🎬 Abriendo: {os.path.basename(video_path)}")
    except Exception as e:
        st.error(f"❌ Error abriendo video: {e}")


def render_plex_library_selector(libraries: List[Dict]) -> Optional[str]:
    """
    Renderiza el selector de biblioteca PLEX
    
    Args:
        libraries: Lista de bibliotecas disponibles
        
    Returns:
        str: Nombre de la biblioteca seleccionada o None
    """
    if not libraries:
        st.warning("⚠️ No se encontraron bibliotecas de películas en PLEX")
        return None
    
    library_names = [lib['title'] for lib in libraries if lib.get('type') == 'movie']
    if not library_names:
        st.warning("⚠️ No se encontraron bibliotecas de películas en PLEX")
        return None
    
    return st.selectbox(
        "📚 Seleccionar Biblioteca",
        library_names,
        help="Biblioteca de PLEX para analizar"
    )
