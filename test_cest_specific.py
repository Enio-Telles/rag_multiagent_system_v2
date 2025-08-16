#!/usr/bin/env python3
"""
Script para testar alguns produtos específicos e verificar se CEST está correto
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter
from config import Config

def test_specific_products():
    print("Testando produtos específicos com validação CEST...")
    
    router = HybridRouter()
    
    # Produtos de teste que anteriormente geravam CEST incorreto
    test_products = [
        {"descricao_produto": "PARACETAMOL 500MG COMPRIMIDO"},
        {"descricao_produto": "DIPIRONA SODICA 500MG COMPRIMIDO"},
        {"descricao_produto": "IBUPROFENO 600MG COMPRIMIDO"},
        {"descricao_produto": "OMEPRAZOL 20MG CAPSULA"},
        {"descricao_produto": "AMOXICILINA 500MG CAPSULA"}
    ]
    
    print(f"\n=== Testando {len(test_products)} produtos ===")
    
    for i, produto_dict in enumerate(test_products, 1):
        produto = produto_dict["descricao_produto"]
        print(f"\n--- Produto {i}: {produto} ---")
        
        try:
            # Processar produto
            resultado = router.classify_products([produto_dict])
            
            if resultado and len(resultado) > 0:
                result = resultado[0]
                ncm = result.get('ncm_recomendado', 'N/A')
                cest = result.get('cest_recomendado', 'N/A')
                tem_cest = result.get('tem_cest', False)
                
                print(f"NCM: {ncm}")
                print(f"CEST: {cest} (tem_cest: {tem_cest})")
                
                # Verificar formato do CEST
                if tem_cest and cest and cest != 'N/A':
                    cest_limpo = str(cest).replace('.', '')
                    if len(cest_limpo) == 7 and cest_limpo.isdigit():
                        print("✅ CEST em formato correto (7 dígitos)")
                    else:
                        print(f"❌ CEST em formato incorreto: '{cest}'")
                else:
                    print("ℹ️ Produto sem CEST")
                    
            else:
                print("❌ Erro: Nenhum resultado retornado")
                
        except Exception as e:
            print(f"❌ Erro durante classificação: {e}")

if __name__ == "__main__":
    test_specific_products()
