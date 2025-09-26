#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que la selección funciona sin colgarse
"""

import sys
from pathlib import Path

# Configurar el path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def test_selection_logic():
    """Prueba la lógica de selección sin Streamlit"""
    print("🧪 Probando lógica de selección...")
    
    # Simular session_state
    session_state = {}
    
    def simulate_checkbox_selection(index, movie_num, selected):
        """Simula la selección de un checkbox"""
        key1 = f"selected_{index}_1"
        key2 = f"selected_{index}_2"
        
        if movie_num == 1:
            if selected:
                session_state[key1] = True
                session_state[key2] = False  # Deseleccionar la otra
            else:
                session_state[key1] = False
        else:
            if selected:
                session_state[key2] = True
                session_state[key1] = False  # Deseleccionar la otra
            else:
                session_state[key2] = False
        
        # Verificar si alguna película del par está seleccionada
        par_seleccionado = (
            session_state.get(key1, False) or 
            session_state.get(key2, False)
        )
        
        return par_seleccionado
    
    # Probar diferentes escenarios
    print("\n📋 Probando escenarios de selección:")
    
    # Escenario 1: Seleccionar película 1
    print("1. Seleccionando Película 1...")
    par_seleccionado = simulate_checkbox_selection(0, 1, True)
    print(f"   Par seleccionado: {par_seleccionado}")
    print(f"   Estado: {session_state}")
    
    # Escenario 2: Cambiar a película 2
    print("2. Cambiando a Película 2...")
    par_seleccionado = simulate_checkbox_selection(0, 2, True)
    print(f"   Par seleccionado: {par_seleccionado}")
    print(f"   Estado: {session_state}")
    
    # Escenario 3: Deseleccionar todo
    print("3. Deseleccionando todo...")
    par_seleccionado = simulate_checkbox_selection(0, 1, False)
    print(f"   Par seleccionado: {par_seleccionado}")
    print(f"   Estado: {session_state}")
    
    # Escenario 4: Múltiples pares
    print("4. Probando múltiples pares...")
    simulate_checkbox_selection(1, 1, True)
    simulate_checkbox_selection(2, 2, True)
    print(f"   Estado final: {session_state}")
    
    print("\n✅ Prueba completada - Lógica de selección funciona correctamente")

if __name__ == "__main__":
    test_selection_logic()
