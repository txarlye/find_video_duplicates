#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de datos de escaneo para persistencia
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class ScanDataManager:
    """Gestor para guardar y cargar datos de escaneo"""
    
    def __init__(self, data_dir: str = "scan_data"):
        """
        Inicializa el gestor de datos
        
        Args:
            data_dir: Directorio donde guardar los archivos de datos
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def save_scan_data(self, pairs_data: List[Dict[str, Any]], scan_path: str, 
                      scan_date: Optional[datetime] = None) -> str:
        """
        Guarda los datos del escaneo
        
        Args:
            pairs_data: Lista de pares de duplicados
            scan_path: Ruta que se escaneó
            scan_date: Fecha del escaneo (por defecto ahora)
            
        Returns:
            Ruta del archivo guardado
        """
        if scan_date is None:
            scan_date = datetime.now()
        
        # Crear estructura de datos
        scan_data = {
            'metadata': {
                'scan_path': scan_path,
                'scan_date': scan_date.isoformat(),
                'total_pairs': len(pairs_data),
                'version': '1.0'
            },
            'pairs_data': pairs_data
        }
        
        # Generar nombre de archivo
        timestamp = scan_date.strftime("%Y%m%d_%H%M%S")
        safe_path = scan_path.replace('\\', '_').replace('/', '_').replace(':', '_')
        filename = f"scan_{timestamp}_{safe_path[:50]}.json"
        file_path = self.data_dir / filename
        
        # Guardar archivo
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(scan_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Datos de escaneo guardados: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando datos: {e}")
            raise
    
    def load_scan_data(self, file_path: str) -> Dict[str, Any]:
        """
        Carga los datos del escaneo
        
        Args:
            file_path: Ruta del archivo a cargar
            
        Returns:
            Diccionario con los datos del escaneo
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                scan_data = json.load(f)
            
            self.logger.info(f"📂 Datos de escaneo cargados: {file_path}")
            return scan_data
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando datos: {e}")
            raise
    
    def get_available_scans(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de escaneos disponibles
        
        Returns:
            Lista de diccionarios con información de escaneos
        """
        scans = []
        
        for file_path in self.data_dir.glob("scan_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                scans.append({
                    'file_path': str(file_path),
                    'scan_path': metadata.get('scan_path', 'N/A'),
                    'scan_date': metadata.get('scan_date', 'N/A'),
                    'total_pairs': metadata.get('total_pairs', 0),
                    'filename': file_path.name
                })
            except Exception as e:
                self.logger.warning(f"⚠️ Error leyendo archivo {file_path}: {e}")
                continue
        
        # Ordenar por fecha (más reciente primero)
        scans.sort(key=lambda x: x.get('scan_date', ''), reverse=True)
        return scans
    
    def delete_scan_data(self, file_path: str) -> bool:
        """
        Elimina un archivo de datos de escaneo
        
        Args:
            file_path: Ruta del archivo a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            Path(file_path).unlink()
            self.logger.info(f"🗑️ Archivo de escaneo eliminado: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def export_scan_summary(self, scan_data: Dict[str, Any], output_path: str) -> bool:
        """
        Exporta un resumen del escaneo a un archivo de texto
        
        Args:
            scan_data: Datos del escaneo
            output_path: Ruta donde guardar el resumen
            
        Returns:
            True si se exportó correctamente
        """
        try:
            metadata = scan_data.get('metadata', {})
            pairs_data = scan_data.get('pairs_data', [])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== RESUMEN DE ESCANEO DE DUPLICADOS ===\n\n")
                f.write(f"Ruta escaneada: {metadata.get('scan_path', 'N/A')}\n")
                f.write(f"Fecha de escaneo: {metadata.get('scan_date', 'N/A')}\n")
                f.write(f"Total de pares: {metadata.get('total_pairs', 0)}\n\n")
                
                f.write("=== LISTA DE PARES ===\n\n")
                for i, pair in enumerate(pairs_data, 1):
                    f.write(f"Par {i}:\n")
                    f.write(f"  Película 1: {pair.get('Peli 1', 'N/A')}\n")
                    f.write(f"  Película 2: {pair.get('Peli 2', 'N/A')}\n")
                    f.write(f"  Tamaño 1: {pair.get('Tamaño 1', 'N/A')} GB\n")
                    f.write(f"  Tamaño 2: {pair.get('Tamaño 2', 'N/A')} GB\n")
                    f.write(f"  Similitud: {pair.get('Similitud', 'N/A')}\n")
                    f.write("\n")
            
            self.logger.info(f"📄 Resumen exportado: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error exportando resumen: {e}")
            return False
