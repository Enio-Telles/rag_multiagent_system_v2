#!/usr/bin/env python3
"""
Teste específico para verificar classificação de CHIP TIM
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_chip_tim_classification():
    print("Testando classificação do CHIP TIM...")
    
    router = HybridRouter()
    
    # Produto específico mencionado pelo usuário
    test_product = [{"descricao_produto": "CHIP TIM PRÉ PLANO NAKED 4G"}]
    
    print(f"\n=== Classificando: {test_product[0]['descricao_produto']} ===")
    
    try:
        resultados = router.classify_products(test_product)
        
        if resultados and len(resultados) > 0:
            resultado = resultados[0]
            ncm = resultado.get('ncm_classificado', 'N/A')
            cest = resultado.get('cest_classificado', 'N/A')
            confianca = resultado.get('confianca_consolidada', 0)
            
            print(f"\nResultado atual do sistema:")
            print(f"NCM: {ncm}")
            print(f"CEST: {cest}")
            print(f"Confiança: {confianca:.2f}")
            
            print(f"\nResultado esperado:")
            print(f"NCM: 85235290 (8523.52.90)")
            print(f"CEST: 21.064.00")
            
            # Verificar se está correto
            ncm_esperado = "85235290"
            cest_esperado = "21.064.00"
            
            if ncm == ncm_esperado:
                print("✅ NCM correto!")
            else:
                print(f"❌ NCM incorreto. Esperado: {ncm_esperado}, Obtido: {ncm}")
                
            if cest == cest_esperado:
                print("✅ CEST correto!")
            else:
                print(f"❌ CEST incorreto. Esperado: {cest_esperado}, Obtido: {cest}")
                
            # Mostrar justificativa
            if 'justificativa' in resultado:
                print(f"\nJustificativa: {resultado['justificativa']}")
                
        else:
            print("❌ Nenhum resultado retornado")
            
    except Exception as e:
        print(f"❌ Erro durante classificação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chip_tim_classification()
