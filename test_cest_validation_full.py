#!/usr/bin/env python3
"""
Script para testar a validação CEST com alguns produtos de exemplo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter
import json

def test_cest_validation():
    print("Testando validação CEST com produtos selecionados...")
    
    router = HybridRouter()
    
    # Produtos de teste - medicamentos que devem ter CEST
    test_products = [
        {"descricao_produto": "PARACETAMOL 500MG COMPRIMIDO"},
        {"descricao_produto": "DIPIRONA SODICA 500MG COMPRIMIDO"},
        {"descricao_produto": "IBUPROFENO 600MG COMPRIMIDO"}
    ]
    
    print(f"\n=== Classificando {len(test_products)} produtos ===")
    
    try:
        # Processar todos os produtos de uma vez
        resultados = router.classify_products(test_products)
        
        if resultados:
            print(f"\n=== Resultados da Classificação ===")
            for i, resultado in enumerate(resultados, 1):
                produto = test_products[i-1]["descricao_produto"]
                ncm = resultado.get('ncm_classificado', 'N/A')
                cest = resultado.get('cest_classificado', 'N/A')
                confianca = resultado.get('confianca_consolidada', 0)
                
                print(f"\n--- Produto {i}: {produto} ---")
                print(f"NCM: {ncm}")
                print(f"CEST: {cest}")
                print(f"Confiança: {confianca:.2f}")
                
                # Validar formato CEST se presente
                if cest and cest != 'N/A' and cest is not None:
                    cest_str = str(cest)
                    cest_limpo = cest_str.replace('.', '')
                    
                    if len(cest_limpo) == 7 and cest_limpo.isdigit():
                        print("✅ CEST em formato correto (7 dígitos)")
                    else:
                        print(f"❌ CEST em formato incorreto: '{cest}' (esperado: SS.III.DD)")
                else:
                    print("ℹ️ Produto sem CEST")
                    
                # Mostrar auditoria se disponível
                if 'auditoria' in resultado:
                    auditoria = resultado['auditoria']
                    print(f"Auditoria: {auditoria}")
                    
                # Mostrar justificativa se disponível
                if 'justificativa' in resultado:
                    justificativa = resultado['justificativa']
                    print(f"Justificativa: {justificativa[:100]}{'...' if len(justificativa) > 100 else ''}")
        else:
            print("❌ Nenhum resultado retornado")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cest_validation()
