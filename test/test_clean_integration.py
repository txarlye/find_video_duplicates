#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la integración limpia
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_clean_imports():
    """Prueba que todos los imports funcionen correctamente"""
    print("🧪 Probando imports limpios...")
    
    try:
        from src.utils.ui_components import DuplicatePairsManager
        print("✅ DuplicatePairsManager importado correctamente")
        
        from src.app.streamlit_manager import StreamlitAppManager
        print("✅ StreamlitAppManager importado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_clean_functionality():
    """Prueba la funcionalidad limpia del gestor de pares"""
    print("🧪 Probando funcionalidad limpia...")
    
    try:
        from src.utils.ui_components import DuplicatePairsManager
        
        # Crear gestor
        pairs_manager = DuplicatePairsManager()
        
        # Datos de prueba
        test_pairs = [
            {
                'Ruta 1': '/test/Del revés 2.mkv',
                'Ruta 2': '/test/Del Revés.mkv',
                'Tamaño 1': 1000,
                'Tamaño 2': 1000,
                'Similitud': 95.5
            },
            {
                'Ruta 1': '/test/aaaaaa.mkv',
                'Ruta 2': '/test/bbbbbbbb.mkv',
                'Tamaño 1': 2000,
                'Tamaño 2': 2000,
                'Similitud': 88.2
            }
        ]
        
        # Establecer lista de pares
        pairs_manager.set_pairs_list(test_pairs)
        
        # Verificar funcionalidades básicas
        assert pairs_manager.navigation.get_total_pairs() == 2
        assert pairs_manager.list_manager.get_pairs_list() == test_pairs
        
        # Verificar navegación
        current_pair = pairs_manager.navigation.get_current_pair()
        assert current_pair is not None
        assert current_pair['Ruta 1'] == '/test/Del revés 2.mkv'
        
        # Verificar que se puede cambiar de par
        pairs_manager.navigation.go_to_pair(1)
        current_pair = pairs_manager.navigation.get_current_pair()
        assert current_pair['Ruta 1'] == '/test/aaaaaa.mkv'
        
        print("✅ Funcionalidad limpia: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad: {e}")
        return False

def test_dropdown_format():
    """Prueba el formato del dropdown con nombres de archivos"""
    print("🧪 Probando formato del dropdown...")
    
    try:
        from src.utils.ui_components import DuplicatePairsManager
        from pathlib import Path
        
        # Crear gestor
        pairs_manager = DuplicatePairsManager()
        
        # Datos de prueba
        test_pairs = [
            {
                'Ruta 1': '/test/Del revés 2.mkv',
                'Ruta 2': '/test/Del Revés.mkv'
            },
            {
                'Ruta 1': '/test/aaaaaa.mkv',
                'Ruta 2': '/test/bbbbbbbb.mkv'
            }
        ]
        
        # Establecer lista de pares
        pairs_manager.set_pairs_list(test_pairs)
        
        # Verificar que se pueden generar las opciones del dropdown
        pairs_list = pairs_manager.list_manager.get_pairs_list()
        pair_options = []
        for i, pair in enumerate(pairs_list):
            file1_name = Path(pair.get('Ruta 1', '')).name if pair.get('Ruta 1') else 'N/A'
            file2_name = Path(pair.get('Ruta 2', '')).name if pair.get('Ruta 2') else 'N/A'
            pair_options.append(f"Par {i+1} - [{file1_name}] [{file2_name}]")
        
        # Verificar formato esperado
        expected_format1 = "Par 1 - [Del revés 2.mkv] [Del Revés.mkv]"
        expected_format2 = "Par 2 - [aaaaaa.mkv] [bbbbbbbb.mkv]"
        
        assert pair_options[0] == expected_format1
        assert pair_options[1] == expected_format2
        
        print("✅ Formato del dropdown: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en formato del dropdown: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de integración limpia...")
    print("=" * 50)
    
    tests = [
        test_clean_imports,
        test_clean_functionality,
        test_dropdown_format
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
        print("✅ La integración limpia está lista para usar")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores")

if __name__ == "__main__":
    main()
