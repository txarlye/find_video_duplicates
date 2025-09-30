#!/bin/bash
echo "🚀 Iniciando Servidor Local de Telegram Bot API"
echo "📡 Puerto: 8081"
echo "🔗 URL: http://localhost:8081"
echo ""

# Iniciar contenedor
docker-compose up -d

echo "✅ Servidor iniciado"
echo "📋 Para ver logs: docker-compose logs -f"
echo "🛑 Para detener: docker-compose down"
