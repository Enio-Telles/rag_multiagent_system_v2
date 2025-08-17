#!/usr/bin/env python3
"""
Teste específico para produtos farmacêuticos com ABC Farma
"""

import sys
import os

# Adicionar src ao path
sys.path.append('src')

from services.unified_sqlite_service import get_unified_service

def test_pharmaceutical_classification():
    """Testa classificação de produtos farmacêuticos"""
    
    # Produtos farmacêuticos para teste
    test_products = [
        "Dipirona Sódica 500mg 20 comprimidos",
        "Paracetamol 750mg 10 comprimidos",
        "Amoxicilina 500mg 21 cápsulas",
        "Vitamina C 1g 30 comprimidos efervescentes"
    ]
    
    unified_service = get_unified_service()
    
    print("🧪 TESTE DE PRODUTOS FARMACÊUTICOS")
    print("=" * 60)
    
    for i, produto in enumerate(test_products, 1):
        print(f"\n{i}. Produto: {produto}")
        
        # Buscar na ABC Farma
        try:
            abc_results = unified_service.search_abc_farma_by_text(produto, limit=3)
            if abc_results:
                print(f"   ✅ Encontrados {len(abc_results)} produtos ABC Farma:")
                for j, result in enumerate(abc_results, 1):
                    print(f"      {j}. {result['descricao'][:80]}...")
                    print(f"         NCM: {result['ncm']} | Lab: {result['laboratorio']}")
                    if result['principio_ativo']:
                        print(f"         Princípio Ativo: {result['principio_ativo']}")
            else:
                print("   ❌ Nenhum produto encontrado no ABC Farma")
        except Exception as e:
            print(f"   ⚠️  Erro na busca ABC Farma: {e}")
    
    # Testar busca por princípio ativo
    print(f"\n🔍 TESTE DE BUSCA POR PRINCÍPIO ATIVO")
    print("=" * 60)
    
    principios_teste = ["DIPIRONA", "PARACETAMOL", "AMOXICILINA"]
    
    for principio in principios_teste:
        print(f"\nBuscando por: {principio}")
        try:
            results = unified_service.search_abc_farma_by_principio_ativo(principio, limit=3)
            if results:
                print(f"   ✅ {len(results)} produtos encontrados:")
                for j, result in enumerate(results, 1):
                    print(f"      {j}. {result['descricao'][:60]}...")
                    print(f"         NCM: {result['ncm']} | Lab: {result['laboratorio']}")
            else:
                print("   ❌ Nenhum produto encontrado")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

if __name__ == "__main__":
    test_pharmaceutical_classification()
