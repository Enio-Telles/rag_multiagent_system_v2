#!/usr/bin/env python3
"""Teste de reprocessamento para validar correções"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_reprocessamento():
    print("=== TESTE DE REPROCESSAMENTO COM CORREÇÕES ===")
    
    router = HybridRouter()
    router._initialize_vector_store()
    
    # Produtos de teste: medicamentos e telecomunicações
    produtos_teste = [
        {
            'produto': 'PANTOPRAZOL 40MG C/28CP',
            'descricao_produto': 'Medicamento pantoprazol 40mg com 28 comprimidos para problemas gástricos'
        },
        {
            'produto': 'CHIP TIM PRÉ PLANO NAKED 4G',  
            'descricao_produto': 'Chip TIM pré-pago plano Naked 4G para telefonia móvel'
        },
        {
            'produto': 'OMEPRAZOL 20MG C/30CP',
            'descricao_produto': 'Medicamento omeprazol 20mg com 30 comprimidos'
        }
    ]
    
    print(f"Processando {len(produtos_teste)} produtos de teste...")
    resultados = router.classify_products(produtos_teste)
    
    # Salvar resultados com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_saida = f"data/processed/teste_correcoes_{timestamp}.json"
    
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Resultados salvos em: {arquivo_saida}")
    
    # Verificar correções
    print(f"\n=== VERIFICAÇÃO DAS CORREÇÕES ===")
    
    for i, resultado in enumerate(resultados):
        produto = resultado.get('produto', 'N/A')
        ncm = resultado.get('ncm_classificado', 'N/A')
        cest = resultado.get('cest_classificado', 'N/A')
        
        print(f"\n{i+1}. {produto}")
        print(f"   NCM: {ncm}")
        print(f"   CEST: {cest}")
        
        # Verificações específicas
        if 'PANTOPRAZOL' in produto or 'OMEPRAZOL' in produto:
            # Medicamentos
            if ncm.startswith('3004'):
                print(f"   ✅ NCM correto para medicamento")
            else:
                print(f"   ❌ NCM incorreto para medicamento")
                
            if cest and cest.startswith('13.'):
                print(f"   ✅ CEST correto para medicamento")
            else:
                print(f"   ❌ CEST incorreto para medicamento (deveria ser 13.xxx.xx)")
                
        elif 'CHIP' in produto:
            # Telecomunicações
            if ncm.startswith('8523'):
                print(f"   ✅ NCM correto para SIM card")
            else:
                print(f"   ❌ NCM incorreto para SIM card")
                
            if cest == '21.064.00':
                print(f"   ✅ CEST correto para SIM card")
            else:
                print(f"   ❌ CEST incorreto para SIM card (deveria ser 21.064.00)")
        
        # Verificar formato CEST
        if cest and '.' in cest and len(cest) == 8:
            print(f"   ✅ Formato CEST correto (SS.III.DD)")
        elif cest:
            print(f"   ❌ Formato CEST incorreto: {cest}")

if __name__ == "__main__":
    test_reprocessamento()
