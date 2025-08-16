#!/usr/bin/env python3
"""
Teste detalhado do fluxo completo para verificar onde a formatação CEST é perdida
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_chip_tim_detailed():
    print("Testando CHIP TIM com logs detalhados...")
    
    router = HybridRouter()
    
    # Produto específico
    test_product = [{"descricao_produto": "CHIP TIM PRÉ PLANO NAKED 4G"}]
    
    print(f"\n=== Processando: {test_product[0]['descricao_produto']} ===")
    
    # Salvar log detalhado modificando temporariamente o router
    original_classify_products = router.classify_products
    
    def classify_products_with_logs(produtos):
        print("\n🔍 Iniciando classificação...")
        resultados = original_classify_products(produtos)
        
        if resultados and len(resultados) > 0:
            resultado = resultados[0]
            print(f"\n📋 Resultado final:")
            print(f"  NCM: {resultado.get('ncm_classificado')}")
            print(f"  CEST: {resultado.get('cest_classificado')}")
            print(f"  Confiança: {resultado.get('confianca_consolidada')}")
            
            # Verificar se há informações de auditoria que revelem o processamento
            if 'auditoria' in resultado:
                print(f"  Auditoria: {resultado['auditoria']}")
                
        return resultados
    
    # Substituir temporariamente
    router.classify_products = classify_products_with_logs
    
    try:
        resultados = router.classify_products(test_product)
        
        if resultados:
            resultado = resultados[0]
            cest = resultado.get('cest_classificado')
            
            print(f"\n🎯 Análise final:")
            if cest == "21.064.00":
                print("✅ CEST está correto e formatado!")
            elif cest == "2106400":
                print("❌ CEST está correto mas sem formatação")
            else:
                print(f"⚠️ CEST inesperado: '{cest}'")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chip_tim_detailed()
