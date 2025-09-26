#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la integración de las funcionalidades de navegación
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_imports():
    """Prueba que todos los imports funcionen correctamente"""
    print("🧪 Probando imports...")
    
    try:
        from src.utils.ui_components import DuplicatePairsManager
        print("✅ DuplicatePairsManager importado correctamente")
        
        from src.app.streamlit_manager import StreamlitAppManager
        print("✅ StreamlitAppManager importado correctamente")
        
        # Verificar que el gestor de pares esté disponible
        manager = StreamlitAppManager()
        if hasattr(manager, 'pairs_manager'):
            print("✅ pairs_manager inicializado correctamente")
        else:
            print("❌ pairs_manager no encontrado")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_pairs_manager_functionality():
    """Prueba la funcionalidad del gestor de pares"""
    print("🧪 Probando funcionalidad del gestor de pares...")
    
    try:
        from src.utils.ui_components import DuplicatePairsManager
        
        # Crear gestor
        pairs_manager = DuplicatePairsManager()
        
        # Datos de prueba
        test_pairs = [
            {
                'Ruta 1': '/test/movie1.mkv',
                'Ruta 2': '/test/movie1_copy.mkv',
                'Tamaño 1': 1000,
                'Tamaño 2': 1000,
                'Similitud': 95.5
            },
            {
                'Ruta 1': '/test/movie2.mkv',
                'Ruta 2': '/test/movie2_copy.mkv',
                'Tamaño 1': 2000,
                'Tamaño 2': 2000,
                'Similitud': 88.2
            }
        ]
        
        # Establecer lista de pares
        pairs_manager.set_pairs_list(test_pairs)
        
        # Verificar funcionalidades
        assert pairs_manager.navigation.get_total_pairs() == 2
        assert pairs_manager.list_manager.get_pairs_list() == test_pairs
        
        # Verificar navegación
        current_pair = pairs_manager.navigation.get_current_pair()
        assert current_pair is not None
        assert current_pair['Ruta 1'] == '/test/movie1.mkv'
        
        # Verificar que se puede cambiar de par
        pairs_manager.navigation.go_to_pair(1)
        current_pair = pairs_manager.navigation.get_current_pair()
        assert current_pair['Ruta 1'] == '/test/movie2.mkv'
        
        print("✅ Funcionalidad del gestor de pares: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad del gestor: {e}")
        return False

def test_streamlit_manager_integration():
    """Prueba la integración con StreamlitAppManager"""
    print("🧪 Probando integración con StreamlitAppManager...")
    
    try:
        from src.app.streamlit_manager import StreamlitAppManager
        
        # Crear manager
        manager = StreamlitAppManager()
        
        # Verificar que tiene el gestor de pares
        assert hasattr(manager, 'pairs_manager')
        assert manager.pairs_manager is not None
        
        # Verificar que es del tipo correcto
        from src.utils.ui_components import DuplicatePairsManager
        assert isinstance(manager.pairs_manager, DuplicatePairsManager)
        
        print("✅ Integración con StreamlitAppManager: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de integración...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_pairs_manager_functionality,
        test_streamlit_manager_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Error inesperado en {test.__name__}: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron correctamente!")
        print("✅ La integración está lista para usar")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores")

if __name__ == "__main__":
    main()
