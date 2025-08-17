#!/usr/bin/env python3
"""
Script para buscar produtos com dados reais do PostgreSQL
"""

import sqlite3

def buscar_produtos_postgres():
    """Busca produtos que têm dados do PostgreSQL"""
    print("🔍 Buscando produtos com dados reais do PostgreSQL...")
    
    conn = sqlite3.connect('data/unified_rag_system.db')
    cursor = conn.cursor()
    
    # Buscar produtos que têm dados do PostgreSQL
    cursor.execute('''
        SELECT produto_id, descricao_produto, codigo_produto, codigo_barra, 
               ncm_original, cest_original, status_revisao 
        FROM classificacoes_revisao 
        WHERE ncm_original IS NOT NULL 
        AND status_revisao = "PENDENTE_REVISAO"
        LIMIT 3
    ''')
    
    resultados = cursor.fetchall()
    print(f"📊 Produtos com dados do PostgreSQL ({len(resultados)}):")
    
    for i, resultado in enumerate(resultados, 1):
        print(f"\n🔸 Produto {i}:")
        print(f"   - Produto ID: {resultado[0]}")
        print(f"   - Descrição: {resultado[1][:50] if resultado[1] else 'N/A'}...")
        print(f"   - Código Produto: {resultado[2] or 'N/A'}")
        print(f"   - Código Barra: {resultado[3] or 'N/A'}")
        print(f"   - NCM Original: {resultado[4] or 'N/A'}")
        print(f"   - CEST Original: {resultado[5] or 'N/A'}")
    
    conn.close()
    return resultados

if __name__ == "__main__":
    buscar_produtos_postgres()
