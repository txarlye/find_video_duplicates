#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mejorar los métodos de renombrado para manejar rutas UNC
"""

def fix_rename_file_method():
    """Mejora el método _rename_file para manejar rutas UNC"""
    
    # Leer el archivo actual
    with open('src/app/streamlit_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Método original
    old_method = '''    def _rename_file(self, file_path: str, new_name: str):
        """Renombra un archivo"""
        try:
            if not new_name:
                st.error("❌ Nombre no puede estar vacío")
                return
            
            # Obtener directorio y extensión
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_path = os.path.join(directory, f"{new_name}{extension}")
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            st.success(f"✅ Archivo renombrado: {os.path.basename(new_path)}")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error renombrando archivo: {e}")'''
    
    # Método mejorado
    new_method = '''    def _rename_file(self, file_path: str, new_name: str):
        """Renombra un archivo con soporte para rutas UNC"""
        try:
            if not new_name:
                st.error("❌ Nombre no puede estar vacío")
                return
            
            # Obtener directorio y extensión
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_path = os.path.join(directory, f"{new_name}{extension}")
            
            # Verificar si es una ruta UNC
            is_unc = file_path.startswith('\\\\')
            
            if is_unc:
                # Para rutas UNC, usar manejo especial
                try:
                    # Intentar renombrar directamente
                    os.rename(file_path, new_path)
                    st.success(f"✅ Archivo renombrado: {os.path.basename(new_path)}")
                    st.rerun()
                except Exception as unc_error:
                    st.warning(f"⚠️ Error con ruta UNC: {unc_error}")
                    st.info("💡 Intentando con método alternativo...")
                    
                    # Método alternativo para UNC
                    try:
                        import shutil
                        shutil.move(file_path, new_path)
                        st.success(f"✅ Archivo renombrado (método alternativo): {os.path.basename(new_path)}")
                        st.rerun()
                    except Exception as alt_error:
                        st.error(f"❌ Error con método alternativo: {alt_error}")
                        st.error("💡 Verifica que tienes permisos de escritura en la ruta UNC")
            else:
                # Para rutas locales, usar método normal
                os.rename(file_path, new_path)
                st.success(f"✅ Archivo renombrado: {os.path.basename(new_path)}")
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error renombrando archivo: {e}")'''
    
    # Reemplazar en el contenido
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Método _rename_file mejorado")
    else:
        print("⚠️ Método _rename_file no encontrado exactamente")
    
    return content

def fix_create_edition_method():
    """Mejora el método _create_edition para manejar rutas UNC"""
    
    # Leer el archivo actual
    with open('src/app/streamlit_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Método original
    old_method = '''    def _create_edition(self, file_path: str, selected_movie: str, edition_name: str):
        """Crea una edición diferente de una película"""
        try:
            if not edition_name:
                st.error("❌ Nombre de edición no puede estar vacío")
                return
            
            # Extraer título y año de la película seleccionada
            # Formato: "Título (Año)"
            import re
            match = re.match(r"(.+?)\\s*\\((\\d{4})\\)", selected_movie)
            if not match:
                st.error("❌ Formato de película no válido")
                return
            
            title, year = match.groups()
            
            # Crear nuevo nombre con edición
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_name = f"{title} ({year}) {{edition-{edition_name}}}{extension}"
            new_path = os.path.join(directory, new_name)
            
            # Renombrar archivo
            os.rename(file_path, new_path)
            st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
            st.info("💡 Reinicia Plex para que detecte la nueva edición")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error creando edición: {e}")'''
    
    # Método mejorado
    new_method = '''    def _create_edition(self, file_path: str, selected_movie: str, edition_name: str):
        """Crea una edición diferente de una película con soporte para rutas UNC"""
        try:
            if not edition_name:
                st.error("❌ Nombre de edición no puede estar vacío")
                return
            
            # Extraer título y año de la película seleccionada
            # Formato: "Título (Año)"
            import re
            match = re.match(r"(.+?)\\s*\\((\\d{4})\\)", selected_movie)
            if not match:
                st.error("❌ Formato de película no válido")
                return
            
            title, year = match.groups()
            
            # Crear nuevo nombre con edición
            directory = os.path.dirname(file_path)
            extension = os.path.splitext(file_path)[1]
            new_name = f"{title} ({year}) {{edition-{edition_name}}}{extension}"
            new_path = os.path.join(directory, new_name)
            
            # Verificar si es una ruta UNC
            is_unc = file_path.startswith('\\\\')
            
            if is_unc:
                # Para rutas UNC, usar manejo especial
                try:
                    # Intentar renombrar directamente
                    os.rename(file_path, new_path)
                    st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
                    st.info("💡 Reinicia Plex para que detecte la nueva edición")
                    st.rerun()
                except Exception as unc_error:
                    st.warning(f"⚠️ Error con ruta UNC: {unc_error}")
                    st.info("💡 Intentando con método alternativo...")
                    
                    # Método alternativo para UNC
                    try:
                        import shutil
                        shutil.move(file_path, new_path)
                        st.success(f"✅ Edición creada (método alternativo): {os.path.basename(new_path)}")
                        st.info("💡 Reinicia Plex para que detecte la nueva edición")
                        st.rerun()
                    except Exception as alt_error:
                        st.error(f"❌ Error con método alternativo: {alt_error}")
                        st.error("💡 Verifica que tienes permisos de escritura en la ruta UNC")
            else:
                # Para rutas locales, usar método normal
                os.rename(file_path, new_path)
                st.success(f"✅ Edición creada: {os.path.basename(new_path)}")
                st.info("💡 Reinicia Plex para que detecte la nueva edición")
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error creando edición: {e}")'''
    
    # Reemplazar en el contenido
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Método _create_edition mejorado")
    else:
        print("⚠️ Método _create_edition no encontrado exactamente")
    
    return content

def main():
    """Función principal"""
    print("🔧 Mejorando métodos de renombrado para rutas UNC")
    print("=" * 60)
    
    # Leer el archivo actual
    with open('src/app/streamlit_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar mejoras
    content = fix_rename_file_method()
    content = fix_create_edition_method()
    
    # Escribir el archivo mejorado
    with open('src/app/streamlit_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Métodos de renombrado mejorados para rutas UNC")
    print("💡 Ahora manejan correctamente tanto rutas locales como UNC")
    print("🔄 Usan shutil.move como método alternativo para rutas UNC")

if __name__ == "__main__":
    main()
