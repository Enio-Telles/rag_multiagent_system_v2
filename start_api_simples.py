#!/usr/bin/env python3
"""
Script para iniciar a API de revisão
"""

import subprocess
import sys
import os

def main():
    # Garantir que estamos no diretório correto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Comando para iniciar a API
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.api.review_api:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    
    print("🚀 Iniciando API de Revisão...")
    print(f"📁 Diretório: {os.getcwd()}")
    print(f"🔧 Comando: {' '.join(cmd)}")
    print("📡 URL: http://localhost:8000")
    print("📄 Docs: http://localhost:8000/api/docs")
    print("-" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⏹️ API interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
