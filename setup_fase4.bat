@echo off
REM Script de Setup Rápido - Fase 4
REM Sistema RAG Multi-Agent - Frontend

echo 🚀 Iniciando setup da Fase 4...
echo =================================

REM Navegar para o diretório frontend
cd frontend

echo 📦 Instalando dependências...
call npm install

REM Verificar se a instalação foi bem-sucedida
if %errorlevel% == 0 (
    echo ✅ Dependências instaladas com sucesso!
    echo.
    echo 🎯 Páginas da Fase 4 implementadas:
    echo    • Produtos ^(/produtos^)
    echo    • Classificação ^(/classificacao^)
    echo    • Aprovação ^(/aprovacao^)
    echo    • Auditoria ^(/auditoria^)
    echo.
    echo 🏃‍♂️ Para iniciar o servidor de desenvolvimento:
    echo    npm start
    echo.
    echo 🌐 A aplicação estará disponível em:
    echo    http://localhost:3000
    echo.
    echo ✨ Fase 4 pronta para uso!
    pause
) else (
    echo ❌ Erro na instalação das dependências
    echo Verifique sua conexão com a internet e tente novamente
    pause
    exit /b 1
)
