#!/usr/bin/env python3
"""
Script para testar a importação de dados
"""

from src.database.connection import SessionLocal
from src.feedback.review_service import ReviewService
import glob
from pathlib import Path

def test_import():
    # Buscar arquivos JSON de classificação
    json_files = glob.glob('data/processed/classificacao_*.json')
    
    if json_files:
        arquivo_mais_recente = max(json_files, key=lambda f: Path(f).stat().st_mtime)
        print(f'📂 Arquivo mais recente: {Path(arquivo_mais_recente).name}')
        
        review_service = ReviewService()
        db = SessionLocal()
        
        try:
            resultado = review_service.importar_classificacoes_json(
                db=db,
                caminho_arquivo=arquivo_mais_recente
            )
            
            print('✅ Importação concluída!')
            print(f'   📊 Total: {resultado["total"]}')
            print(f'   ✅ Importadas: {resultado["importadas"]}')
            print(f'   ❌ Erros: {resultado["erros"]}')
            
        finally:
            db.close()
    else:
        print('⚠️ Nenhum arquivo de classificação encontrado')

if __name__ == "__main__":
    test_import()
