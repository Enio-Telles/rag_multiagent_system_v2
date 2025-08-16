#!/usr/bin/env python3
"""Teste final simples"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_final():
    router = HybridRouter()
    router._initialize_vector_store()
    
    produtos = [{
        'produto': 'CHIP TIM PRÉ PLANO NAKED 4G',
        'descricao_produto': 'Chip TIM pré-pago plano Naked 4G'
    }]
    
    resultados = router.classify_products(produtos)
    
    if resultados and len(resultados) > 0:
        resultado = resultados[0]
        ncm_obtido = resultado.get('ncm_classificado')
        cest_obtido = resultado.get('cest_classificado')
        confianca = resultado.get('confianca_consolidada')
        
        print(f"RESULTADO FINAL:")
        print(f"NCM: {ncm_obtido}")
        print(f"CEST: {cest_obtido}")
        print(f"Confiança: {confianca}")
        
        # Verificação
        ncm_esperado = '85235290'
        cest_esperado = '21.064.00'
        
        print(f"\nVERIFICAÇÃO:")
        if ncm_obtido == ncm_esperado:
            print(f"✅ NCM correto!")
        else:
            print(f"❌ NCM incorreto. Esperado: {ncm_esperado}, Obtido: {ncm_obtido}")
            
        if cest_obtido == cest_esperado:
            print(f"✅ CEST correto!")
        else:
            print(f"❌ CEST incorreto. Esperado: {cest_esperado}, Obtido: {cest_obtido}")
            
        if ncm_obtido == ncm_esperado and cest_obtido == cest_esperado:
            print(f"\n🎉 SUCESSO! Classificação correta implementada!")
        else:
            print(f"\n⚠️ Ainda há problemas na classificação.")

if __name__ == "__main__":
    test_final()
