#!/usr/bin/env python3
"""Teste individual de cada produto"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_produtos_individuais():
    print("=== TESTE INDIVIDUAL DE PRODUTOS ===")
    
    router = HybridRouter()
    router._initialize_vector_store()
    
    produtos_teste = [
        {
            'nome': 'PANTOPRAZOL',
            'produto': 'PANTOPRAZOL 40MG C/28CP',
            'descricao_produto': 'Medicamento pantoprazol 40mg com 28 comprimidos para problemas gástricos'
        },
        {
            'nome': 'CHIP TIM',
            'produto': 'CHIP TIM PRÉ PLANO NAKED 4G',  
            'descricao_produto': 'Chip TIM pré-pago plano Naked 4G para telefonia móvel'
        }
    ]
    
    for produto_info in produtos_teste:
        print(f"\n{'='*50}")
        print(f"TESTANDO: {produto_info['nome']}")
        print(f"{'='*50}")
        
        # Testar produto individual
        resultado = router.classify_products([{
            'produto': produto_info['produto'],
            'descricao_produto': produto_info['descricao_produto']
        }])
        
        if resultado and len(resultado) > 0:
            r = resultado[0]
            ncm = r.get('ncm_classificado', 'N/A')
            cest = r.get('cest_classificado', 'N/A')
            confianca = r.get('confianca_consolidada', 'N/A')
            
            print(f"NCM: {ncm}")
            print(f"CEST: {cest}")
            print(f"Confiança: {confianca}")
            
            # Verificações
            if produto_info['nome'] == 'PANTOPRAZOL':
                if ncm.startswith('3004'):
                    print(f"✅ NCM correto para medicamento")
                else:
                    print(f"❌ NCM incorreto: {ncm} (deveria ser 3004.xx.xx)")
                    
                if cest and cest.startswith('13.'):
                    print(f"✅ CEST correto para medicamento")
                else:
                    print(f"❌ CEST incorreto: {cest} (deveria ser 13.xxx.xx)")
                    
            elif produto_info['nome'] == 'CHIP TIM':
                if ncm.startswith('8523'):
                    print(f"✅ NCM correto para SIM card")
                else:
                    print(f"❌ NCM incorreto: {ncm} (deveria ser 8523.xx.xx)")
                    
                if cest == '21.064.00':
                    print(f"✅ CEST correto para SIM card")
                else:
                    print(f"❌ CEST incorreto: {cest} (deveria ser 21.064.00)")
            
            print(f"Justificativa: {r.get('justificativa', 'N/A')[:200]}...")

if __name__ == "__main__":
    test_produtos_individuais()
