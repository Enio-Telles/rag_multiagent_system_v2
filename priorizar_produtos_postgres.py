#!/usr/bin/env python3
"""
Script para priorizar produtos com dados do PostgreSQL na interface
"""

import sqlite3
from datetime import datetime

def priorizar_produtos_postgres():
    """Move produtos com dados do PostgreSQL para o topo da lista"""
    print("🔄 Priorizando produtos com dados do PostgreSQL...")
    
    conn = sqlite3.connect('data/unified_rag_system.db')
    cursor = conn.cursor()
    
    # 1. Buscar produtos com dados do PostgreSQL
    cursor.execute('''
        SELECT produto_id, descricao_produto, ncm_original, cest_original
        FROM classificacoes_revisao 
        WHERE ncm_original IS NOT NULL 
        AND status_revisao = "PENDENTE_REVISAO"
        ORDER BY produto_id
        LIMIT 5
    ''')
    
    produtos_postgres = cursor.fetchall()
    print(f"📊 Encontrados {len(produtos_postgres)} produtos com dados PostgreSQL:")
    
    for produto in produtos_postgres:
        print(f"   - ID {produto[0]}: {produto[1][:40]}... (NCM: {produto[2]}, CEST: {produto[3]})")
    
    # 2. Limpar estado de ordenação para forçar nova seleção
    cursor.execute('DELETE FROM estado_ordenacao')
    
    # 3. Criar um estado que force a seleção de um produto com dados PostgreSQL
    # Vou pegar o primeiro produto com dados e simular que é o próximo na sequência
    if produtos_postgres:
        produto_target = produtos_postgres[0]
        descricao = produto_target[1] or ""
        
        # Encontrar primeira letra válida
        primeira_letra = 'A'
        for char in descricao.upper():
            if char.isalpha():
                primeira_letra = char
                break
        
        # Inserir estado que force a seleção deste produto
        cursor.execute('''
            INSERT INTO estado_ordenacao 
            (ultima_letra_usada, ultimo_produto_id, data_atualizacao)
            VALUES (?, ?, ?)
        ''', ('Z', produto_target[0], datetime.now().isoformat()))  # Use 'Z' para forçar voltar ao 'A'
        
        print(f"✅ Estado de ordenação configurado para priorizar produto {produto_target[0]}")
        print(f"   Primeira letra: {primeira_letra}")
    
    # 4. Verificar estatísticas
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE status_revisao = "PENDENTE_REVISAO"')
    total_pendentes = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM classificacoes_revisao WHERE status_revisao = "PENDENTE_REVISAO" AND ncm_original IS NOT NULL')
    pendentes_com_dados = cursor.fetchone()[0]
    
    print(f"\n📈 Estatísticas:")
    print(f"   - Total pendentes: {total_pendentes}")
    print(f"   - Pendentes com dados PostgreSQL: {pendentes_com_dados}")
    print(f"   - Porcentagem com dados: {(pendentes_com_dados/total_pendentes)*100:.1f}%")
    
    conn.commit()
    conn.close()
    
    return produtos_postgres

def testar_ordenacao_manual():
    """Testa a lógica de ordenação manualmente"""
    print("\n🧪 Testando lógica de ordenação manual...")
    
    conn = sqlite3.connect('data/unified_rag_system.db')
    cursor = conn.cursor()
    
    # Simular o que o método obter_proximo_pendente faz
    cursor.execute('SELECT ultima_letra_usada FROM estado_ordenacao ORDER BY data_atualizacao DESC LIMIT 1')
    estado = cursor.fetchone()
    ultima_letra = estado[0] if estado else ""
    
    print(f"📋 Última letra usada: '{ultima_letra}'")
    
    # Buscar produtos pendentes agrupados por letra
    cursor.execute('''
        SELECT produto_id, descricao_produto, ncm_original, cest_original
        FROM classificacoes_revisao 
        WHERE status_revisao = "PENDENTE_REVISAO"
        ORDER BY descricao_produto
    ''')
    
    produtos = cursor.fetchall()
    
    # Agrupar por primeira letra
    produtos_por_letra = {}
    for produto in produtos:
        descricao = produto[1] or ""
        primeira_letra = 'Z'
        for char in descricao.upper():
            if char.isalpha():
                primeira_letra = char
                break
        
        if primeira_letra not in produtos_por_letra:
            produtos_por_letra[primeira_letra] = []
        produtos_por_letra[primeira_letra].append(produto)
    
    print(f"\n📊 Produtos por letra:")
    for letra in sorted(produtos_por_letra.keys()):
        produtos_letra = produtos_por_letra[letra]
        com_dados = len([p for p in produtos_letra if p[2] is not None])  # ncm_original não é None
        print(f"   - {letra}: {len(produtos_letra)} produtos ({com_dados} com dados PostgreSQL)")
        
        # Mostrar primeiro produto de cada letra que tem dados PostgreSQL
        for produto in produtos_letra:
            if produto[2] is not None:  # Tem NCM original
                print(f"     ✅ {produto[0]}: {produto[1][:30]}... (NCM: {produto[2]})")
                break
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Configurando priorização de produtos com dados PostgreSQL...")
    print("="*70)
    
    produtos = priorizar_produtos_postgres()
    testar_ordenacao_manual()
    
    print("\n" + "="*70)
    print("✅ Configuração concluída!")
    print("🌐 Agora inicie a API e teste a interface web")
    print("   - A interface deve priorizar produtos com dados reais do PostgreSQL")
    print("   - Os campos NCM original, CEST original e código produto devem aparecer")
