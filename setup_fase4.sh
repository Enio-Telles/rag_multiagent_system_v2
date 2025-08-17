#!/bin/bash

# Script de Setup Rápido - Fase 4
# Sistema RAG Multi-Agent - Frontend

echo "🚀 Iniciando setup da Fase 4..."
echo "================================="

# Navegar para o diretório frontend
cd frontend

echo "📦 Instalando dependências..."
npm install

# Verificar se a instalação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
    echo ""
    echo "🎯 Páginas da Fase 4 implementadas:"
    echo "   • Produtos (/produtos)"
    echo "   • Classificação (/classificacao)" 
    echo "   • Aprovação (/aprovacao)"
    echo "   • Auditoria (/auditoria)"
    echo ""
    echo "🏃‍♂️ Para iniciar o servidor de desenvolvimento:"
    echo "   npm start"
    echo ""
    echo "🌐 A aplicação estará disponível em:"
    echo "   http://localhost:3000"
    echo ""
    echo "✨ Fase 4 pronta para uso!"
else
    echo "❌ Erro na instalação das dependências"
    echo "Verifique sua conexão com a internet e tente novamente"
    exit 1
fi
