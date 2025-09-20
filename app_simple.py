#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Streamlit refactorizada y mantenible
"""

import streamlit as st
import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Importar el gestor principal
try:
    from src.app.streamlit_manager import StreamlitAppManager
except ImportError as e:
    st.error(f"❌ Error de importación: {e}")
    st.error("💡 Asegúrate de ejecutar la aplicación desde el directorio raíz del proyecto")
    st.stop()

# Configurar página
st.set_page_config(
    page_title="🎬 Detector de Películas Duplicadas",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Crear y ejecutar la aplicación
app_manager = StreamlitAppManager()
app_manager.run()
