#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración opcional para streamlit-player
"""

# Para instalar streamlit-player opcionalmente:
# pip install streamlit-player

# Luego descomenta las siguientes líneas en streamlit_manager.py:

# try:
#     from streamlit_player import st_player
#     STREAMLIT_PLAYER_AVAILABLE = True
# except ImportError:
#     STREAMLIT_PLAYER_AVAILABLE = False
#     st_player = None

# Y usa st_player en lugar de st.video para mejor compatibilidad
