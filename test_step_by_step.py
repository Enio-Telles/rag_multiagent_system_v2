#!/usr/bin/env python3
"""Teste step-by-step do fluxo completo"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_step_by_step():
    print("=== TESTE STEP-BY-STEP DO FLUXO ===")
    
    router = HybridRouter()
    router._initialize_vector_store()
    
    # Simular produto CHIP TIM
    produtos = [{
        'produto': 'CHIP TIM PRÉ PLANO NAKED 4G',
        'descricao_produto': 'Chip TIM pré-pago plano Naked 4G'
    }]
    
    # Testar expansão
    print("\n🔍 ETAPA 1: EXPANSÃO")
    expansion_result = router.expansion_agent.run('Chip TIM pré-pago plano Naked 4G')
    print(f"Expansão: {expansion_result}")
    
    produto_expandido = expansion_result['result']
    
    # Testar NCM
    print("\n🧠 ETAPA 2: CLASSIFICAÇÃO NCM")
    context = {
        "structured_context": "Nenhum contexto estruturado específico disponível.",
        "semantic_context": router._get_semantic_context(produto_expandido['descricao_expandida'])
    }
    
    ncm_result = router.ncm_agent.run(produto_expandido, context)
    print(f"NCM Result: {ncm_result}")
    
    # Atualizar contexto
    ncm_determinado = ncm_result['result'].get('ncm_recomendado', '')
    context['structured_context'] = router._get_structured_context(ncm_determinado)
    
    # Testar CEST  
    print("\n💰 ETAPA 3: CLASSIFICAÇÃO CEST")
    cest_result = router.cest_agent.run(produto_expandido, ncm_result['result'], context)
    print(f"CEST Result: {cest_result}")
    
    # Testar Reconciliação
    print("\n⚖️ ETAPA 4: RECONCILIAÇÃO")
    reconciliation_result = router.reconciler_agent.run(
        produto_expandido, 
        ncm_result['result'], 
        cest_result['result'], 
        context
    )
    print(f"Reconciliation Result: {reconciliation_result}")
    
    # Verificar resultado final
    classificacao = reconciliation_result['result']['classificacao_final']
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"   NCM: {classificacao.get('ncm')}")
    print(f"   CEST: {classificacao.get('cest')}")
    print(f"   Confiança: {classificacao.get('confianca_consolidada')}")

if __name__ == "__main__":
    test_step_by_step()
