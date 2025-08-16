#!/usr/bin/env python3
"""
Teste da hierarquia NCM - Demonstração de busca hierárquica
"""

import sys
from pathlib import Path

# Adicionar o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

import json
from config import Config

def test_ncm_hierarchy():
    """Testa a busca hierárquica de NCMs."""
    config = Config()
    
    # Carregar a base de conhecimento
    with open(config.NCM_MAPPING_FILE, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
    
    # Criar um índice por código NCM para busca rápida
    ncm_index = {item['ncm_codigo']: item for item in knowledge_base}
    
    # Exemplos de teste
    test_cases = [
        "8407.3",      # Código parcial
        "8407.31",     # Código mais específico
        "8407.31.10",  # Código completo
        "3815.12",     # Outro exemplo parcial
        "3815.12.10",  # Código completo
    ]
    
    print("🔍 TESTE DE HIERARQUIA NCM")
    print("=" * 50)
    
    for test_code in test_cases:
        print(f"\n🎯 Testando código: {test_code}")
        
        # Normalizar código
        normalized = test_code.replace(".", "")
        
        # Buscar na base
        if normalized in ncm_index:
            item = ncm_index[normalized]
            print(f"  ✅ Encontrado: {item['codigo_original']}")
            print(f"  📝 Descrição: {item['descricao_oficial'][:80]}...")
            print(f"  🎯 CESTs: {len(item['cests_associados'])}")
            print(f"  🛍️ Produtos: {len(item['gtins_exemplos'])}")
        else:
            print("  ❌ Não encontrado")
    
    print("\n" + "=" * 50)
    print("📊 ESTATÍSTICAS DA HIERARQUIA:")
    
    # Contar por nível hierárquico
    nivel_counts = {}
    for item in knowledge_base:
        nivel = item.get('nivel_hierarquico', len(item['ncm_codigo']))
        nivel_counts[nivel] = nivel_counts.get(nivel, 0) + 1
    
    for nivel in sorted(nivel_counts.keys()):
        print(f"  Nível {nivel}: {nivel_counts[nivel]:,} códigos")

if __name__ == "__main__":
    test_ncm_hierarchy()
