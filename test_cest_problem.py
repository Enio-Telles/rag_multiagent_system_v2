#!/usr/bin/env python3
"""Teste focado no problema do CEST"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_cest_problem():
    print("Testando problema do CEST...")
    
    router = HybridRouter()
    router._initialize_vector_store()
    
    # Produto de teste
    produtos = [{
        'produto': 'CHIP TIM PRÉ PLANO NAKED 4G',
        'descricao_produto': 'Chip TIM pré-pago plano Naked 4G'
    }]
    
    print("Executando classificação em lote...")
    resultados = router.classify_products(produtos)
    
    if resultados and len(resultados) > 0:
        resultado = resultados[0]
        print(f"NCM: {resultado.get('ncm_classificado')}")
        print(f"CEST: {resultado.get('cest_classificado')}")
        print(f"Confiança: {resultado.get('confianca_consolidada')}")
        print(f"Grupo ID: {resultado.get('grupo_id')}")
        print(f"É representante: {resultado.get('eh_representante')}")
        
        # Verificar cache
        if hasattr(router, 'classification_cache'):
            print(f"Cache keys: {list(router.classification_cache.keys())}")
            
            for key, cached in router.classification_cache.items():
                print(f"\n=== CACHE {key} ===")
                print(f"CEST result: {cached.get('cest', {}).get('result', {})}")
                print(f"Reconciliation result: {cached.get('reconciliation', {}).get('result', {})}")
        
        print(f"\nAuditoria: {resultado.get('auditoria')}")
        print(f"Justificativa: {resultado.get('justificativa')}")
    else:
        print("Nenhum resultado obtido!")

if __name__ == "__main__":
    test_cest_problem()
