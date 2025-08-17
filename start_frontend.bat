@echo off
echo 🚀 Iniciando Frontend React - Fase 3
echo ====================================

cd frontend

echo 📦 Instalando dependencias...
call npm install

echo 🔧 Configurando ambiente de desenvolvimento...

echo 🌐 Iniciando servidor de desenvolvimento...
echo Frontend estara disponivel em: http://localhost:3000
echo API Backend deve estar rodando em: http://localhost:8000
echo.
echo Funcionalidades implementadas:
echo - ✅ Sistema de autenticacao
echo - ✅ Gestao multi-empresa
echo - ✅ Dashboard com metricas
echo - ✅ Layout responsivo com Material-UI
echo - ✅ Navegacao protegida
echo.

call npm start
