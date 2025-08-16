# Script PowerShell para iniciar a API de Review
Write-Host "Iniciando API de Review do Sistema RAG..." -ForegroundColor Green
Write-Host ""

# Configurar ambiente
$env:PYTHONPATH = "src"
$pythonExe = "venv\Scripts\python.exe"

# Verificar se dependencias estao instaladas
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
try {
    & $pythonExe -c "import fastapi, uvicorn; print('Dependencias verificadas')"
} catch {
    Write-Host "Erro: FastAPI ou uvicorn nao instalados" -ForegroundColor Red
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    & $pythonExe -m pip install fastapi uvicorn[standard]
}

Write-Host ""
Write-Host "Iniciando servidor em http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Documentacao em http://127.0.0.1:8000/api/docs" -ForegroundColor Cyan
Write-Host "Interface Web em http://127.0.0.1:8000/static/interface_revisao.html" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Usar o comando setup-review --start-api que ja existe (sem hot reload)
& $pythonExe src/main.py setup-review --start-api
