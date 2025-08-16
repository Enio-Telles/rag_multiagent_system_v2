#!/usr/bin/env python3
"""
Servidor de teste simples para identificar o problema
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def run_server():
    """Executa o servidor com configuração mínima"""
    try:
        print("Importando FastAPI...")
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        print("Criando app mínimo...")
        app = FastAPI(title="Test API")
        
        @app.get("/")
        async def root():
            return {"message": "API está funcionando!"}
        
        @app.get("/test")
        async def test():
            return {"status": "OK", "data": "Teste básico"}
        
        print("Importando uvicorn...")
        import uvicorn
        
        print("Iniciando servidor na porta 8001...")
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_server()
