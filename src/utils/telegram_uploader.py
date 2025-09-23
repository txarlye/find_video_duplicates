#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidad para subir películas a Telegram
"""

import os
import logging
import requests
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from src.settings.settings import settings
from src.utils.imdb_service import IMDBService

class TelegramUploader:
    """Clase para manejar la subida de archivos a Telegram"""
    
    def __init__(self):
        """Inicializa el uploader de Telegram"""
        self.logger = logging.getLogger(__name__)
        
        # Obtener configuración desde settings
        self.bot_token = settings.get_telegram_bot_token()
        self.channel_id = settings.get_telegram_channel_id()
        self.max_file_size = settings.get_telegram_max_file_size()
        
        # URL base de la API de Telegram
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Inicializar servicio de IMDB
        self.imdb_service = IMDBService()
        
        # Verificar configuración
        if not self.bot_token or self.bot_token == "your_telegram_bot_token_here":
            self.logger.warning("⚠️ Token de Telegram no configurado")
        if not self.channel_id or self.channel_id == "your_telegram_channel_id_here":
            self.logger.warning("⚠️ ID de canal de Telegram no configurado")
    
    def verificar_configuracion(self) -> bool:
        """Verifica que la configuración de Telegram esté completa"""
        if not self.bot_token or self.bot_token == "your_telegram_bot_token_here":
            return False
        if not self.channel_id or self.channel_id == "your_telegram_channel_id_here":
            return False
        return True
    
    def obtener_info_bot(self) -> Dict:
        """Obtiene información del bot"""
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Error obteniendo info del bot: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error conectando con Telegram: {str(e)}")
            return {}
    
    def obtener_info_canal(self) -> Dict:
        """Obtiene información del canal"""
        try:
            response = requests.get(f"{self.api_url}/getChat", 
                                  params={"chat_id": self.channel_id}, 
                                  timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Error obteniendo info del canal: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error obteniendo info del canal: {str(e)}")
            return {}
    
    def subir_archivo(self, archivo_path: str, titulo: str = None, 
                     descripcion: str = None, thumbnail_path: str = None, 
                     usar_imdb: bool = False, max_reintentos: int = 3) -> bool:
        """
        Sube un archivo a Telegram con reintentos automáticos
        
        Args:
            archivo_path: Ruta del archivo a subir
            titulo: Título de la película
            descripcion: Descripción adicional
            thumbnail_path: Ruta de la imagen thumbnail
            usar_imdb: Si usar información de IMDB
            max_reintentos: Número máximo de reintentos
            
        Returns:
            True si se subió correctamente, False en caso contrario
        """
        # Implementar reintentos automáticos
        for intento in range(max_reintentos):
            try:
                if intento > 0:
                    self.logger.info(f"🔄 Reintento {intento + 1}/{max_reintentos} para {archivo_path}")
                    # Esperar antes del reintento (exponencial backoff)
                    import time
                    time.sleep(2 ** intento)  # 2, 4, 8 segundos
                
                resultado = self._subir_archivo_interno(archivo_path, titulo, descripcion, thumbnail_path, usar_imdb)
                if resultado:
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error en intento {intento + 1}: {str(e)}")
                if intento == max_reintentos - 1:
                    self.logger.error(f"❌ Falló después de {max_reintentos} intentos")
                    return False
        
        return False
    
    def _subir_archivo_interno(self, archivo_path: str, titulo: str = None, 
                             descripcion: str = None, thumbnail_path: str = None, 
                             usar_imdb: bool = False) -> bool:
        """
        Método interno para subir archivo (sin reintentos)
        """
        try:
            archivo = Path(archivo_path)
            if not archivo.exists():
                self.logger.error(f"Archivo no encontrado: {archivo_path}")
                return False
            
            # Verificar tamaño del archivo
            file_size = archivo.stat().st_size
            if file_size > self.max_file_size:
                self.logger.warning(f"Archivo muy grande: {file_size} bytes (máximo: {self.max_file_size})")
                return False
            
            # Verificar límites específicos de Telegram
            # Límite real de Telegram es 2GB, pero recomendamos 1.5GB para evitar problemas
            telegram_max_size = 1.5 * 1024 * 1024 * 1024  # 1.5GB límite recomendado
            if file_size > telegram_max_size:
                self.logger.error(f"❌ Archivo excede límite recomendado de Telegram: {file_size / (1024**3):.2f} GB > 1.5 GB")
                self.logger.info("💡 Recomendación: Comprime el archivo o divídelo en partes más pequeñas")
                return False
            
            # Verificar límite absoluto de Telegram (2GB)
            telegram_absolute_max = 2 * 1024 * 1024 * 1024  # 2GB límite absoluto
            if file_size > telegram_absolute_max:
                self.logger.error(f"❌ Archivo excede límite absoluto de Telegram: {file_size / (1024**3):.2f} GB > 2 GB")
                return False
            
            # Verificar si debe subirse directamente como archivo genérico
            if self._debe_subir_como_archivo_generico(archivo, file_size):
                self.logger.info(f"📁 Subiendo directamente como archivo genérico: {archivo.name}")
                return self._subir_como_archivo_generico(archivo, titulo or archivo.stem)
            
            # Crear copia temporal si el nombre es muy largo
            archivo_para_subir = archivo_path
            nombre_para_imdb = archivo.stem
            
            if len(archivo.name) > 100:  # Si el nombre es muy largo
                self.logger.info(f"📝 Nombre muy largo detectado ({len(archivo.name)} caracteres), creando copia temporal")
                archivo_para_subir, nombre_para_imdb = self._crear_copia_temporal(archivo_path)
            
            # Obtener información de IMDB si está habilitado
            imdb_info = None
            if usar_imdb and settings.get_imdb_enabled():
                try:
                    # Usar el nombre corto para buscar en IMDB
                    titulo_archivo, ano = self.imdb_service.extraer_titulo_y_ano(nombre_para_imdb)
                    if titulo_archivo:
                        imdb_info = self.imdb_service.buscar_pelicula(titulo_archivo, ano)
                        if imdb_info:
                            self.logger.info(f"✅ Información de IMDB obtenida para: {titulo_archivo}")
                        else:
                            self.logger.warning(f"⚠️ No se encontró información en IMDB para: {titulo_archivo}")
                except Exception as e:
                    self.logger.error(f"Error obteniendo información de IMDB: {str(e)}")
            
            # Preparar datos del archivo
            archivo_final = Path(archivo_para_subir)
            
            # Para archivos grandes (>100MB), usar subida por chunks
            if file_size > 100 * 1024 * 1024:  # 100MB
                self.logger.info(f"Archivo grande detectado ({file_size / (1024**2):.1f} MB), usando subida optimizada")
                resultado = self._subir_archivo_grande(archivo_final, caption, imdb_info)
            else:
                resultado = self._subir_archivo_normal(archivo_final, caption, imdb_info)
            
            # Limpiar archivo temporal si se creó
            if archivo_para_subir != archivo_path:
                self._limpiar_archivo_temporal(archivo_para_subir)
            
            return resultado
                    
        except Exception as e:
            self.logger.error(f"Error subiendo archivo {archivo_path}: {str(e)}")
            return False
    
    def _subir_archivo_normal(self, archivo: Path, caption: str, imdb_info: Dict = None) -> bool:
        """
        Sube un archivo normal (no grande)
        """
        try:
            with open(archivo, 'rb') as file:
                files = {'document': (archivo.name, file, 'application/octet-stream')}
                
                # Preparar parámetros
                params = {
                    'chat_id': self.channel_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                # Subir archivo
                self.logger.info(f"Subiendo archivo: {archivo.name}")
                response = requests.post(f"{self.api_url}/sendDocument", 
                                      files=files, 
                                      data=params, 
                                      timeout=3600)  # 1 hora timeout para archivos grandes
                
                if response.status_code == 200:
                    self.logger.info(f"✅ Archivo subido: {archivo.name}")
                    return True
                else:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get('error_code', 'Unknown')
                    error_description = error_data.get('description', 'Unknown error')
                    
                    # Si es error de formato, intentar como archivo genérico
                    if error_code == 400 and ("format" in error_description.lower() or "codec" in error_description.lower()):
                        self.logger.warning(f"⚠️ Error de formato detectado, intentando como archivo genérico...")
                        return self._subir_como_archivo_generico(archivo, caption)
                    
                    # Mensajes de error más específicos
                    if error_code == 413:
                        self.logger.error(f"❌ Archivo demasiado grande")
                    elif error_code == 429:
                        self.logger.error(f"❌ Rate limit excedido - espera antes de subir más archivos")
                    elif error_code == 400:
                        self.logger.error(f"❌ Formato de archivo no soportado o archivo corrupto")
                    elif error_code == 403:
                        self.logger.error(f"❌ Bot sin permisos para subir archivos al canal")
                    else:
                        self.logger.error(f"❌ Error subiendo archivo: {response.status_code} - {error_code}: {error_description}")
                    
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error subiendo archivo normal {archivo}: {str(e)}")
            return False
    
    def _debe_subir_como_archivo_generico(self, archivo: Path, file_size: int) -> bool:
        """
        Determina si un archivo debe subirse directamente como archivo genérico
        
        Reglas:
        - Archivos .mkv: Siempre como archivo genérico
        - Archivos > 1.5GB: Siempre como archivo genérico
        """
        # Regla 1: Archivos .mkv siempre como archivo genérico
        if archivo.suffix.lower() == '.mkv':
            self.logger.info(f"📁 Archivo .mkv detectado: {archivo.name} - Subiendo como archivo genérico")
            return True
        
        # Regla 2: Archivos > 1.5GB como archivo genérico
        tamaño_gb = file_size / (1024**3)
        if tamaño_gb > 1.5:
            self.logger.info(f"📁 Archivo grande detectado: {tamaño_gb:.2f}GB - Subiendo como archivo genérico")
            return True
        
        return False
    
    def _subir_como_archivo_generico(self, archivo: Path, caption: str) -> bool:
        """
        Sube el archivo como archivo genérico (no como video)
        """
        try:
            self.logger.info(f"📁 Subiendo como archivo genérico: {archivo.name}")
            
            with open(archivo, 'rb') as file:
                # Usar 'document' con tipo genérico
                files = {'document': (archivo.name, file, 'application/octet-stream')}
                
                # Preparar parámetros
                params = {
                    'chat_id': self.channel_id,
                    'caption': f"📁 {caption}\n\n⚠️ Subido como archivo genérico (formato no soportado como video)",
                    'parse_mode': 'Markdown'
                }
                
                # Subir archivo
                response = requests.post(f"{self.api_url}/sendDocument", 
                                      files=files, 
                                      data=params, 
                                      timeout=3600)
                
                if response.status_code == 200:
                    self.logger.info(f"✅ Archivo genérico subido: {archivo.name}")
                    return True
                else:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get('error_code', 'Unknown')
                    error_description = error_data.get('description', 'Unknown error')
                    self.logger.error(f"❌ Error subiendo archivo genérico: {response.status_code} - {error_code}: {error_description}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error subiendo archivo genérico {archivo}: {str(e)}")
            return False
    
    def _crear_copia_temporal(self, archivo_path: str) -> tuple[str, str]:
        """
        Crea una copia temporal del archivo con nombre corto para la subida
        
        Returns:
            tuple: (ruta_archivo_temporal, nombre_corto_para_imdb)
        """
        try:
            archivo_original = Path(archivo_path)
            
            # Extraer información básica del archivo original
            nombre_original = archivo_original.stem  # Sin extensión
            extension = archivo_original.suffix
            
            # Crear nombre corto para IMDB (máximo 50 caracteres)
            nombre_corto = self._crear_nombre_corto(nombre_original)
            
            # Crear nombre de archivo temporal
            nombre_temporal = f"{nombre_corto}{extension}"
            
            # Crear directorio temporal
            temp_dir = Path(tempfile.gettempdir()) / "telegram_uploads"
            temp_dir.mkdir(exist_ok=True)
            
            # Ruta del archivo temporal
            archivo_temporal = temp_dir / nombre_temporal
            
            # Copiar archivo original a temporal
            self.logger.info(f"📁 Creando copia temporal: {archivo_temporal.name}")
            shutil.copy2(archivo_original, archivo_temporal)
            
            return str(archivo_temporal), nombre_corto
            
        except Exception as e:
            self.logger.error(f"Error creando copia temporal: {str(e)}")
            return archivo_path, Path(archivo_path).stem
    
    def _crear_nombre_corto(self, nombre_original: str) -> str:
        """
        Crea un nombre corto y limpio para el archivo
        """
        # Limpiar caracteres problemáticos
        nombre_limpio = nombre_original
        
        # Remover patrones comunes problemáticos
        patrones_a_remover = [
            r'\([^)]*\)',  # Paréntesis y contenido
            r'\[[^\]]*\]',  # Corchetes y contenido
            r'\.{2,}',      # Múltiples puntos
            r'[._-]{2,}',   # Múltiples separadores
        ]
        
        import re
        for patron in patrones_a_remover:
            nombre_limpio = re.sub(patron, '', nombre_limpio)
        
        # Limpiar caracteres especiales
        nombre_limpio = re.sub(r'[^\w\s-]', '', nombre_limpio)
        
        # Limpiar espacios múltiples
        nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio).strip()
        
        # Limitar a 50 caracteres
        if len(nombre_limpio) > 50:
            nombre_limpio = nombre_limpio[:50].rsplit(' ', 1)[0]  # Cortar en palabra completa
        
        # Si queda vacío, usar nombre genérico
        if not nombre_limpio:
            nombre_limpio = "pelicula"
        
        return nombre_limpio
    
    def _limpiar_archivo_temporal(self, archivo_temporal: str):
        """
        Limpia el archivo temporal después de la subida
        """
        try:
            if os.path.exists(archivo_temporal):
                os.remove(archivo_temporal)
                self.logger.info(f"🗑️ Archivo temporal eliminado: {archivo_temporal}")
        except Exception as e:
            self.logger.warning(f"Error eliminando archivo temporal: {str(e)}")
    
    def _subir_archivo_grande(self, archivo_path: str, caption: str, imdb_info: Dict = None) -> bool:
        """
        Sube un archivo grande usando subida optimizada
        """
        try:
            archivo = Path(archivo_path)
            file_size = archivo.stat().st_size
            
            self.logger.info(f"Subiendo archivo grande: {archivo.name} ({file_size / (1024**2):.1f} MB)")
            
            # Usar requests con stream=True para archivos grandes
            with open(archivo, 'rb') as file:
                files = {'document': (archivo.name, file, 'application/octet-stream')}
                
                params = {
                    'chat_id': self.channel_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                # Subir con configuración optimizada para archivos grandes
                response = requests.post(
                    f"{self.api_url}/sendDocument", 
                    files=files, 
                    data=params, 
                    timeout=7200,  # 2 horas para archivos muy grandes
                    stream=True,   # Stream para archivos grandes
                    headers={'Connection': 'keep-alive'}  # Mantener conexión
                )
                
                if response.status_code == 200:
                    self.logger.info(f"✅ Archivo grande subido: {archivo.name}")
                    return True
                else:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get('error_code', 'Unknown')
                    error_description = error_data.get('description', 'Unknown error')
                    
                    # Si es error de formato, intentar como archivo genérico
                    if error_code == 400 and ("format" in error_description.lower() or "codec" in error_description.lower()):
                        self.logger.warning(f"⚠️ Error de formato en archivo grande, intentando como archivo genérico...")
                        return self._subir_como_archivo_generico(archivo, caption)
                    
                    self.logger.error(f"Error subiendo archivo grande: {response.status_code} - {error_code}: {error_description}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error subiendo archivo grande {archivo_path}: {str(e)}")
            return False
    
    def _crear_caption(self, titulo: str, descripcion: str, archivo: Path) -> str:
        """Crea el caption para el archivo"""
        caption_parts = []
        
        if titulo:
            caption_parts.append(f"🎬 <b>{titulo}</b>")
        
        # Información del archivo
        file_size_mb = archivo.stat().st_size / (1024 * 1024)
        caption_parts.append(f"📁 {archivo.name}")
        caption_parts.append(f"💾 {file_size_mb:.1f} MB")
        
        if descripcion:
            caption_parts.append(f"📝 {descripcion}")
        
        return "\n".join(caption_parts)
    
    def subir_multiples_archivos(self, archivos: List[Dict]) -> Dict:
        """
        Sube múltiples archivos a Telegram
        
        Args:
            archivos: Lista de diccionarios con información de archivos
            
        Returns:
            Diccionario con resultados de la subida
        """
        resultados = {
            'exitosos': 0,
            'fallidos': 0,
            'archivos_procesados': [],
            'errores': []
        }
        
        for archivo_info in archivos:
            archivo_path = archivo_info.get('archivo', '')
            titulo = archivo_info.get('titulo', '')
            descripcion = archivo_info.get('descripcion', '')
            
            if self.subir_archivo(archivo_path, titulo, descripcion):
                resultados['exitosos'] += 1
                resultados['archivos_procesados'].append({
                    'archivo': archivo_path,
                    'estado': 'exitoso'
                })
            else:
                resultados['fallidos'] += 1
                resultados['errores'].append({
                    'archivo': archivo_path,
                    'error': 'Error en la subida'
                })
        
        return resultados
