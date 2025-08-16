# Script PowerShell otimizado para iniciar a API sem hot reload
Write-Host "Iniciando API de Review do Sistema RAG (Modo Producao)" -ForegroundColor Green
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
Write-Host "Iniciando servidor em http://localhost:8000" -ForegroundColor Cyan
Write-Host "Documentacao em http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "Interface web em http://localhost:8000/static/interface_revisao.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Usar uvicorn diretamente sem hot reload para estabilidade
try {
    Write-Host "Modo Producao: Hot reload desabilitado para maxima estabilidade" -ForegroundColor Magenta
    & $pythonExe -m uvicorn api.review_api:app --host 0.0.0.0 --port 8000
} catch {
    Write-Host ""
    Write-Host "API encerrada pelo usuario" -ForegroundColor Green
}

Write-Host ""
Write-Host "Script finalizado" -ForegroundColor Green
