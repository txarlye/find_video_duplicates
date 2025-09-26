#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para las funcionalidades de navegación de pares
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.utils.ui_components import (
    PairNavigationManager, 
    PairListManager, 
    PairDetailViewer, 
    DuplicatePairsManager
)

def test_navigation_manager():
    """Prueba el gestor de navegación"""
    print("🧪 Probando PairNavigationManager...")
    
    # Crear gestor
    nav_manager = PairNavigationManager()
    
    # Datos de prueba
    test_pairs = [
        {'Ruta 1': '/test/movie1.mkv', 'Ruta 2': '/test/movie1_copy.mkv', 'Tamaño 1': 1000, 'Tamaño 2': 1000},
        {'Ruta 1': '/test/movie2.mkv', 'Ruta 2': '/test/movie2_copy.mkv', 'Tamaño 1': 2000, 'Tamaño 2': 2000},
        {'Ruta 1': '/test/movie3.mkv', 'Ruta 2': '/test/movie3_copy.mkv', 'Tamaño 1': 3000, 'Tamaño 2': 3000}
    ]
    
    # Establecer lista de pares
    nav_manager.set_pairs_list(test_pairs)
    
    # Verificar estado inicial
    assert nav_manager.get_total_pairs() == 3
    assert nav_manager.get_current_index() == 0
    
    # Verificar par actual
    current_pair = nav_manager.get_current_pair()
    assert current_pair is not None
    assert current_pair['Ruta 1'] == '/test/movie1.mkv'
    
    print("✅ PairNavigationManager: OK")

def test_list_manager():
    """Prueba el gestor de lista"""
    print("🧪 Probando PairListManager...")
    
    # Crear gestor
    list_manager = PairListManager()
    
    # Datos de prueba
    test_pairs = [
        {'Ruta 1': '/test/movie1.mkv', 'Ruta 2': '/test/movie1_copy.mkv', 'Tamaño 1': 1000, 'Tamaño 2': 1000},
        {'Ruta 1': '/test/movie2.mkv', 'Ruta 2': '/test/movie2_copy.mkv', 'Tamaño 1': 2000, 'Tamaño 2': 2000}
    ]
    
    # Establecer lista
    list_manager.set_pairs_list(test_pairs)
    
    # Verificar lista
    pairs = list_manager.get_pairs_list()
    assert len(pairs) == 2
    assert pairs[0]['Ruta 1'] == '/test/movie1.mkv'
    
    print("✅ PairListManager: OK")

def test_detail_viewer():
    """Prueba el visor de detalles"""
    print("🧪 Probando PairDetailViewer...")
    
    # Crear gestor
    detail_viewer = PairDetailViewer()
    
    # Datos de prueba
    test_pair = {
        'Ruta 1': '/test/movie1.mkv',
        'Ruta 2': '/test/movie1_copy.mkv',
        'Tamaño 1': 1000,
        'Tamaño 2': 1000,
        'Similitud': 95.5
    }
    
    # Establecer par actual
    detail_viewer.set_current_pair(test_pair)
    
    # Verificar par actual
    current_pair = detail_viewer.get_current_pair()
    assert current_pair is not None
    assert current_pair['Ruta 1'] == '/test/movie1.mkv'
    assert current_pair['Similitud'] == 95.5
    
    print("✅ PairDetailViewer: OK")

def test_duplicate_pairs_manager():
    """Prueba el gestor principal"""
    print("🧪 Probando DuplicatePairsManager...")
    
    # Crear gestor principal
    pairs_manager = DuplicatePairsManager()
    
    # Datos de prueba
    test_pairs = [
        {'Ruta 1': '/test/movie1.mkv', 'Ruta 2': '/test/movie1_copy.mkv', 'Tamaño 1': 1000, 'Tamaño 2': 1000},
        {'Ruta 1': '/test/movie2.mkv', 'Ruta 2': '/test/movie2_copy.mkv', 'Tamaño 1': 2000, 'Tamaño 2': 2000}
    ]
    
    # Establecer lista de pares
    pairs_manager.set_pairs_list(test_pairs)
    
    # Verificar que se estableció en todos los gestores
    assert pairs_manager.navigation.get_total_pairs() == 2
    assert pairs_manager.list_manager.get_pairs_list() == test_pairs
    
    # Verificar par actual
    current_pair = pairs_manager.navigation.get_current_pair()
    assert current_pair is not None
    assert current_pair['Ruta 1'] == '/test/movie1.mkv'
    
    print("✅ DuplicatePairsManager: OK")

def test_navigation_flow():
    """Prueba el flujo de navegación"""
    print("🧪 Probando flujo de navegación...")
    
    # Crear gestor
    nav_manager = PairNavigationManager()
    
    # Datos de prueba
    test_pairs = [
        {'Ruta 1': '/test/movie1.mkv', 'Ruta 2': '/test/movie1_copy.mkv'},
        {'Ruta 1': '/test/movie2.mkv', 'Ruta 2': '/test/movie2_copy.mkv'},
        {'Ruta 1': '/test/movie3.mkv', 'Ruta 2': '/test/movie3_copy.mkv'}
    ]
    
    nav_manager.set_pairs_list(test_pairs)
    
    # Verificar estado inicial
    assert nav_manager.get_current_index() == 0
    assert nav_manager.get_current_pair()['Ruta 1'] == '/test/movie1.mkv'
    
    # Simular navegación (sin st.rerun())
    # Ir al siguiente par
    nav_manager.go_to_pair(1)
    assert nav_manager.get_current_index() == 1
    assert nav_manager.get_current_pair()['Ruta 1'] == '/test/movie2.mkv'
    
    # Ir al último par
    nav_manager.go_to_pair(2)
    assert nav_manager.get_current_index() == 2
    assert nav_manager.get_current_pair()['Ruta 1'] == '/test/movie3.mkv'
    
    # Volver al primero
    nav_manager.go_to_pair(0)
    assert nav_manager.get_current_index() == 0
    assert nav_manager.get_current_pair()['Ruta 1'] == '/test/movie1.mkv'
    
    print("✅ Flujo de navegación: OK")

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de navegación de pares...")
    print("=" * 50)
    
    try:
        test_navigation_manager()
        test_list_manager()
        test_detail_viewer()
        test_duplicate_pairs_manager()
        test_navigation_flow()
        
        print("=" * 50)
        print("🎉 ¡Todas las pruebas pasaron correctamente!")
        print("✅ Las funcionalidades de navegación están listas para usar")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
