#!/usr/bin/env python3
"""
API simples para testar o retorno de dados do PostgreSQL
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from feedback.review_service import ReviewService
import uvicorn

app = FastAPI(title="Teste de Dados PostgreSQL")

@app.get("/test-postgres-data")
def test_postgres_data(db: Session = Depends(get_db)):
    """Testa se os dados do PostgreSQL estão sendo retornados"""
    review_service = ReviewService()
    
    # Buscar produto específico com dados do PostgreSQL
    from database.models import ClassificacaoRevisao
    produto = db.query(ClassificacaoRevisao).filter(
        ClassificacaoRevisao.produto_id == 1769  # Produto que sabemos que tem dados
    ).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return {
        "produto_id": produto.produto_id,
        "descricao_produto": produto.descricao_produto,
        "codigo_produto": produto.codigo_produto,
        "codigo_barra": produto.codigo_barra,
        "ncm_original": produto.ncm_original,
        "cest_original": produto.cest_original,
        "ncm_sugerido": produto.ncm_sugerido,
        "cest_sugerido": produto.cest_sugerido,
        "status_revisao": produto.status_revisao
    }

@app.get("/test-next-pendente")
def test_next_pendente(db: Session = Depends(get_db)):
    """Testa o próximo pendente"""
    review_service = ReviewService()
    resultado = review_service.obter_proximo_pendente(db)
    return resultado

if __name__ == "__main__":
    print("🚀 Iniciando API de teste...")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
