# Script PowerShell para iniciar a API de Review
Write-Host "🚀 Iniciando API de Review do Sistema RAG..." -ForegroundColor Green
Write-Host ""

# Configurar ambiente
$env:PYTHONPATH = "src"
$pythonExe = "C:/Users/eniot/OneDrive/Desenvolvimento/Projetos/rag_multiagent_system/venv/Scripts/python.exe"

# Verificar se dependências estão instaladas
Write-Host "🔍 Verificando dependências..." -ForegroundColor Yellow
try {
    & $pythonExe -c "import fastapi, uvicorn; print('✅ Dependências verificadas')"
} catch {
    Write-Host "❌ Erro: FastAPI ou uvicorn não instalados" -ForegroundColor Red
    Write-Host "Instalando dependências..." -ForegroundColor Yellow
    & $pythonExe -m pip install fastapi "uvicorn[standard]"
}

Write-Host ""
Write-Host "🌐 Iniciando servidor em http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "📖 Documentação em http://127.0.0.1:8000/api/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Usar o comando setup-review --start-api que já existe
& $pythonExe src/main.py setup-review --start-api
