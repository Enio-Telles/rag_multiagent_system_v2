@echo off
echo 🚀 Iniciando API de Review do Sistema RAG...
echo.

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Configurar PYTHONPATH
set PYTHONPATH=src

REM Verificar se FastAPI e uvicorn estão instalados
python -c "import fastapi, uvicorn; print('✅ Dependências verificadas')" || (
    echo ❌ Erro: FastAPI ou uvicorn não instalados
    echo Instalando dependências...
    pip install fastapi uvicorn[standard]
)

REM Iniciar servidor
echo.
echo 🌐 Iniciando servidor em http://127.0.0.1:8000
echo 📖 Documentação em http://127.0.0.1:8000/api/docs
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python -c "import uvicorn; from api.review_api import app; uvicorn.run(app, host='127.0.0.1', port=8000)"

pause
