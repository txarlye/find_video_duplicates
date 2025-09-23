#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Streamlit principal - Detector de Películas Duplicadas
"""

import streamlit as st
import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Importar el gestor principal
try:
    from src.app.UI.Streamlit.streamlit_manager import run_streamlit_app
except ImportError as e:
    st.error(f"❌ Error de importación: {e}")
    st.error("💡 Asegúrate de ejecutar la aplicación desde el directorio raíz del proyecto")
    st.stop()

# Configurar página
st.set_page_config(
    page_title="🎬 Utilidades Plex",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ejecutar la aplicación
run_streamlit_app()