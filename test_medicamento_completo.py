#!/usr/bin/env python3
"""Teste medicamento no sistema completo"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.hybrid_router import HybridRouter

def test_medicamento_completo():
    print("=== TESTE MEDICAMENTO NO SISTEMA COMPLETO ===")
    
    router = HybridRouter()
    router._initialize_vector_store()
    
    # Produto medicamento
    produtos = [{
        'produto': 'PANTOPRAZOL 40MG C/28CP',
        'descricao_produto': 'Medicamento pantoprazol 40mg com 28 comprimidos'
    }]
    
    print("Executando classificação...")
    resultados = router.classify_products(produtos)
    
    if resultados and len(resultados) > 0:
        resultado = resultados[0]
        ncm = resultado.get('ncm_classificado')
        cest = resultado.get('cest_classificado')
        confianca = resultado.get('confianca_consolidada')
        
        print(f"\nRESULTADO SISTEMA COMPLETO:")
        print(f"NCM: {ncm}")
        print(f"CEST: {cest}")
        print(f"Confiança: {confianca}")
        
        # Verificações
        if ncm and ncm.startswith('3004'):
            print(f"✅ NCM correto para medicamento!")
        else:
            print(f"❌ NCM incorreto! Medicamentos devem usar 3004.xx.xx, obtido: {ncm}")
            
        if cest and cest.startswith('13.'):
            print(f"✅ CEST correto para medicamento!")
        elif cest:
            print(f"❌ CEST incorreto! Medicamentos devem usar 13.xxx.xx, obtido: {cest}")
        else:
            print(f"❌ Nenhum CEST retornado!")
            
        # Verificar formato CEST
        if cest and len(cest) == 8 and cest.count('.') == 2:
            print(f"✅ Formato CEST correto (SS.III.DD)!")
        elif cest:
            print(f"❌ Formato CEST incorreto! Deve ser SS.III.DD, obtido: {cest}")
            
        print(f"\nJustificativa: {resultado.get('justificativa')}")

if __name__ == "__main__":
    test_medicamento_completo()
