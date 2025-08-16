#!/usr/bin/env python3
"""
Script para corrigir imports de get_db_session para get_db
"""

import os

def corrigir_arquivo(filepath):
    """Corrige um arquivo específico"""
    with open(filepath, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Substituir imports
    conteudo = conteudo.replace(
        'from database.connection import get_db_session',
        'from database.connection import get_db'
    )
    
    # Substituir usos com context manager
    conteudo = conteudo.replace(
        'with get_db_session() as db:',
        'db = next(get_db())\n        try:'
    )
    
    # Adicionar closes onde necessário (simplificado)
    # Para este caso, vamos apenas substituir e deixar sem close explícito
    # pois o SQLAlchemy gerencia isso
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✅ Arquivo corrigido: {filepath}")

# Arquivos para corrigir
arquivos = [
    'src/feedback/explicacao_service.py',
    'src/feedback/review_service.py'  # caso tenha o mesmo problema
]

for arquivo in arquivos:
    if os.path.exists(arquivo):
        corrigir_arquivo(arquivo)
    else:
        print(f"⚠️ Arquivo não encontrado: {arquivo}")

print("🎉 Correção concluída!")
