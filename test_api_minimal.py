#!/usr/bin/env python3
"""
Teste mínimo da API para identificar problemas
"""

import sys
import os

# Adicionar o diretório raiz do projeto ao path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Teste básico de importações"""
    print("Testando importações...")
    
    try:
        from src.api.review_api import app
        print("✅ Import da API bem-sucedido")
    except Exception as e:
        print(f"❌ Erro no import da API: {e}")
        return False
    
    try:
        from src.feedback.review_service import ReviewService
        print("✅ Import do ReviewService bem-sucedido")
    except Exception as e:
        print(f"❌ Erro no import do ReviewService: {e}")
        return False
    
    return True

def test_service_basic():
    """Teste básico do serviço"""
    print("\nTestando ReviewService básico...")
    
    try:
        from src.feedback.review_service import ReviewService
        from src.database.connection import SessionLocal
        
        service = ReviewService()
        print("✅ ReviewService instanciado com sucesso")
        
        # Teste de listagem com sessão do banco
        db = SessionLocal()
        try:
            classificacoes = service.listar_classificacoes(
                db=db,
                page=1,
                limit=1
            )
            print(f"✅ Listagem funcionando: {len(classificacoes)} items")
        finally:
            db.close()
        
        return True
    except Exception as e:
        print(f"❌ Erro no ReviewService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Teste dos endpoints da API"""
    print("\nTestando endpoints da API...")
    
    try:
        from fastapi.testclient import TestClient
        from src.api.review_api import app
        
        client = TestClient(app)
        
        # Teste básico da rota raiz
        response = client.get("/")
        print(f"✅ Rota raiz: {response.status_code}")
        
        # Teste da rota de listagem
        response = client.get("/api/v1/classificacoes")
        print(f"✅ Rota listagem: {response.status_code}")
        
        # Teste da nova rota proximo-pendente
        response = client.get("/api/v1/classificacoes/proximo-pendente")
        print(f"✅ Rota proximo-pendente: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Teste Diagnóstico da API ===")
    
    success = True
    success &= test_imports()
    success &= test_service_basic()
    success &= test_api_endpoints()
    
    if success:
        print("\n✅ Todos os testes passaram!")
    else:
        print("\n❌ Alguns testes falharam!")
