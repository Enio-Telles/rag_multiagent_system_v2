#!/usr/bin/env python3
"""
Script para verificar dados diretamente no SQLite
"""

import sqlite3

def verificar_dados_sqlite():
    """Verifica se os dados do PostgreSQL estão no SQLite"""
    print("🔍 Verificando dados diretamente no SQLite...")
    
    conn = sqlite3.connect('data/unified_rag_system.db')
    cursor = conn.cursor()
    
    # Verificar dados pendentes
    cursor.execute('''
        SELECT produto_id, descricao_produto, codigo_produto, codigo_barra, 
               ncm_original, cest_original, status_revisao 
        FROM classificacoes_revisao 
        WHERE status_revisao = "PENDENTE_REVISAO" 
        LIMIT 5
    ''')
    
    resultados = cursor.fetchall()
    
    print(f"📊 Encontrados {len(resultados)} produtos pendentes:")
    
    for i, resultado in enumerate(resultados, 1):
        print(f"\n🔸 Produto {i}:")
        print(f"   - Produto ID: {resultado[0]}")
        print(f"   - Descrição: {resultado[1][:50] if resultado[1] else 'N/A'}...")
        print(f"   - Código Produto: {resultado[2] or 'N/A'}")
        print(f"   - Código Barra: {resultado[3] or 'N/A'}")
        print(f"   - NCM Original: {resultado[4] or 'N/A'}")
        print(f"   - CEST Original: {resultado[5] or 'N/A'}")
        print(f"   - Status: {resultado[6]}")
    
    # Estatísticas gerais
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE codigo_produto IS NOT NULL')
    com_codigo = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE ncm_original IS NOT NULL')
    com_ncm = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE cest_original IS NOT NULL')
    com_cest = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE status_revisao = "PENDENTE_REVISAO"')
    pendentes = cursor.fetchone()[0]
    
    print(f"\n📈 Estatísticas dos dados:")
    print(f"   - Com código produto: {com_codigo}")
    print(f"   - Com NCM original: {com_ncm}")
    print(f"   - Com CEST original: {com_cest}")
    print(f"   - Pendentes revisão: {pendentes}")
    
    conn.close()
    
    return len(resultados) > 0

if __name__ == "__main__":
    verificar_dados_sqlite()
