# -*- coding: utf-8 -*-
"""
Funciones de ayuda para configuración en Streamlit
"""

import streamlit as st
from typing import Dict, Any, Optional
from src.settings.settings import Settings


def render_plex_config_tab(settings: Settings) -> Dict[str, Any]:
    """
    Renderiza la pestaña de configuración de PLEX
    
    Args:
        settings: Instancia de configuración
        
    Returns:
        dict: Configuración actualizada de PLEX
    """
    st.subheader("🎬 Configuración PLEX")
    
    # Estado de PLEX
    plex_enabled = st.checkbox(
        "🔗 Habilitar PLEX",
        value=settings.get_plex_enabled(),
        help="Activar integración con PLEX Media Server",
        key="plex_enabled_config"
    )
    
    if plex_enabled:
        # Credenciales de PLEX
        st.markdown("**Credenciales de PLEX:**")
        
        plex_user = st.text_input(
            "👤 Usuario PLEX",
            value=settings.get_plex_user(),
            help="Usuario de PLEX Media Server",
            key="plex_user_config"
        )
        
        plex_pass = st.text_input(
            "🔑 Contraseña PLEX",
            value=settings.get_plex_pass(),
            type="password",
            help="Contraseña de PLEX Media Server",
            key="plex_pass_config"
        )
        
        plex_token = st.text_input(
            "🎫 Token PLEX",
            value=settings.get_plex_token(),
            type="password",
            help="Token de acceso de PLEX (recomendado)",
            key="plex_token_config"
        )
        
        plex_server_ip = st.text_input(
            "🌐 IP del Servidor PLEX",
            value=settings.get_plex_server_ip(),
            help="IP o nombre del servidor PLEX",
            key="plex_server_ip_config"
        )
        
        # Configuración de PLEX
        st.markdown("**Opciones de PLEX:**")
        
        use_plex_detection = st.checkbox(
            "🎯 Usar detección PLEX",
            value=settings.get_plex_use_detection(),
            help="Usar PLEX para detectar duplicados directamente",
            key="use_plex_detection_config"
        )
        
        use_plex_metadata = st.checkbox(
            "📊 Usar metadatos PLEX",
            value=settings.get_plex_use_metadata(),
            help="Usar metadatos de PLEX para mejorar la detección",
            key="use_plex_metadata_config"
        )
        
        prefer_plex_titles = st.checkbox(
            "📝 Preferir títulos de PLEX",
            value=settings.get_plex_prefer_titles(),
            help="Usar títulos de PLEX en lugar de nombres de archivo",
            key="prefer_plex_titles_config"
        )
        
        prefer_plex_years = st.checkbox(
            "📅 Preferir años de PLEX",
            value=settings.get_plex_prefer_years(),
            help="Usar años de PLEX en lugar de extraídos del archivo",
            key="prefer_plex_years_config"
        )
        
        prefer_plex_duration = st.checkbox(
            "⏱️ Preferir duración de PLEX",
            value=settings.get_plex_prefer_duration(),
            help="Usar duración de PLEX en lugar de analizar archivo",
            key="prefer_plex_duration_config"
        )
        
        # Botón para guardar configuración
        if st.button("💾 Guardar Configuración PLEX", type="primary"):
            try:
                settings.set_plex_enabled(plex_enabled)
                settings.set_plex_use_detection(use_plex_detection)
                settings.set_plex_use_metadata(use_plex_metadata)
                settings.set_plex_prefer_titles(prefer_plex_titles)
                settings.set_plex_prefer_years(prefer_plex_years)
                settings.set_plex_prefer_duration(prefer_plex_duration)
                
                st.success("✅ Configuración de PLEX guardada")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error guardando configuración: {e}")
        
        return {
            'enabled': plex_enabled,
            'user': plex_user,
            'pass': plex_pass,
            'token': plex_token,
            'server_ip': plex_server_ip,
            'use_detection': use_plex_detection,
            'use_metadata': use_plex_metadata,
            'prefer_titles': prefer_plex_titles,
            'prefer_years': prefer_plex_years,
            'prefer_duration': prefer_plex_duration
        }
    else:
        return {
            'enabled': False,
            'user': '',
            'pass': '',
            'token': '',
            'server_ip': '',
            'use_detection': False,
            'use_metadata': False,
            'prefer_titles': False,
            'prefer_years': False,
            'prefer_duration': False
        }


def render_debug_config_tab(settings: Settings) -> Dict[str, Any]:
    """
    Renderiza la pestaña de configuración de debug
    
    Args:
        settings: Instancia de configuración
        
    Returns:
        dict: Configuración de debug
    """
    st.subheader("🐛 Configuración Debug")
    
    debug_enabled = st.checkbox(
        "🔧 Modo Debug",
        value=settings.get_debug_enabled(),
        help="Activar modo debug (no elimina archivos, los mueve a carpeta debug)",
        key="debug_enabled_config"
    )
    
    debug_folder = st.text_input(
        "📁 Carpeta Debug",
        value=settings.get_debug_folder(),
        help="Carpeta donde se moverán los archivos en modo debug",
        key="debug_folder_config"
    )
    
    if st.button("💾 Guardar Configuración Debug", type="primary"):
        try:
            settings.set_debug_enabled(debug_enabled)
            settings.set_debug_folder(debug_folder)
            st.success("✅ Configuración de debug guardada")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error guardando configuración: {e}")
    
    return {
        'enabled': debug_enabled,
        'folder': debug_folder
    }


def render_ui_config_tab(settings: Settings) -> Dict[str, Any]:
    """
    Renderiza la pestaña de configuración de UI
    
    Args:
        settings: Instancia de configuración
        
    Returns:
        dict: Configuración de UI
    """
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
    
    # Configuración de detección
    st.markdown("**🔍 Detección de Duplicados:**")
    
    duration_tolerance = st.number_input(
        "⏱️ Tolerancia de duración (minutos)",
        min_value=0,
        max_value=60,
        value=settings.get("detection.duration_tolerance_minutes", 1),
        help="Diferencia máxima en minutos para considerar duplicados",
        key="duration_tolerance_config"
    )
    
    similarity_threshold = st.slider(
        "🎯 Umbral de similitud",
        min_value=0.0,
        max_value=1.0,
        value=settings.get("detection.similarity_threshold", 0.8),
        step=0.1,
        help="Umbral de similitud para considerar duplicados (0.0 = muy estricto, 1.0 = muy permisivo)",
        key="similarity_threshold_config"
    )
    
    # Botón para guardar configuración
    if st.button("💾 Guardar Configuración UI", type="primary"):
        try:
            settings.set("ui.show_video_players", show_video_players)
            settings.set("ui.show_embedded_players", show_embedded_players)
            settings.set("ui.video_start_time_seconds", video_start_time * 60)
            settings.set("detection.duration_tolerance_minutes", duration_tolerance)
            settings.set("detection.similarity_threshold", similarity_threshold)
            
            st.success("✅ Configuración de UI guardada")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error guardando configuración: {e}")
    
    return {
        'show_video_players': show_video_players,
        'show_embedded_players': show_embedded_players,
        'video_start_time': video_start_time * 60,
        'duration_tolerance': duration_tolerance,
        'similarity_threshold': similarity_threshold
    }


def render_telegram_config_tab(settings: Settings) -> Dict[str, Any]:
    """
    Renderiza la pestaña de configuración de Telegram
    
    Args:
        settings: Instancia de configuración
        
    Returns:
        dict: Configuración de Telegram
    """
    st.subheader("📱 Configuración Telegram")
    
    telegram_enabled = st.checkbox(
        "📤 Habilitar Telegram",
        value=settings.get_telegram_enabled(),
        help="Activar notificaciones por Telegram",
        key="telegram_enabled_config"
    )
    
    if telegram_enabled:
        bot_token = st.text_input(
            "🤖 Token del Bot",
            value=settings.get_telegram_bot_token(),
            type="password",
            help="Token del bot de Telegram",
            key="telegram_bot_token_config"
        )
        
        channel_id = st.text_input(
            "📢 ID del Canal",
            value=settings.get_telegram_channel_id(),
            help="ID del canal de Telegram",
            key="telegram_channel_id_config"
        )
        
        if st.button("💾 Guardar Configuración Telegram", type="primary"):
            try:
                settings.set_telegram_enabled(telegram_enabled)
                settings.set_telegram_bot_token(bot_token)
                settings.set_telegram_channel_id(channel_id)
                st.success("✅ Configuración de Telegram guardada")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error guardando configuración: {e}")
        
        return {
            'enabled': telegram_enabled,
            'bot_token': bot_token,
            'channel_id': channel_id
        }
    else:
        return {
            'enabled': False,
            'bot_token': '',
            'channel_id': ''
        }
