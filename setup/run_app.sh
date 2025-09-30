#!/bin/bash

echo "🎬 Iniciando Detector de Películas Duplicadas..."
echo "🌐 Abriendo navegador automáticamente..."
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "💡 Instala Python3 desde https://python.org"
    exit 1
fi

# Verificar si Streamlit está instalado
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit no está instalado"
    echo "💡 Instalando dependencias..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
fi

# Ejecutar la aplicación
echo "✅ Ejecutando aplicación..."
python3 main.py
