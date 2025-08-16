#!/usr/bin/env python3
"""
Teste direto do CESTAgent para verificar normalização
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_cest_agent_direct():
    print("Testando CESTAgent diretamente...")
    
    config = Config()
    llm_client = OllamaClient()
    cest_agent = CESTAgent(llm_client, config)
    
    # Simular entrada
    produto_expandido = {
        "produto_original": "CHIP TIM PRÉ PLANO NAKED 4G",
        "descricao_expandida": "Cartão SIM para telecomunicações móveis 4G da operadora TIM"
    }
    
    ncm_resultado = {
        "ncm_recomendado": "85235290",
        "confianca": 0.9
    }
    
    context = {"structured_context": "NCM 85235290 - Cartões inteligentes"}
    
    print(f"\nTestando classificação CEST...")
    print(f"Produto: {produto_expandido['produto_original']}")
    print(f"NCM: {ncm_resultado['ncm_recomendado']}")
    
    try:
        resultado = cest_agent.run(produto_expandido, ncm_resultado, context)
        cest_result = resultado['result']
        
        print(f"\nResultado CEST:")
        print(f"tem_cest: {cest_result.get('tem_cest')}")
        print(f"cest_recomendado: '{cest_result.get('cest_recomendado')}'")
        print(f"confianca: {cest_result.get('confianca')}")
        print(f"justificativa: {cest_result.get('justificativa')}")
        
        # Verificar se está no formato correto
        cest = cest_result.get('cest_recomendado')
        if cest == "21.064.00":
            print("✅ CEST está no formato correto!")
        elif cest == "2106400":
            print("❌ CEST precisa ser normalizado")
        else:
            print(f"⚠️ CEST inesperado: '{cest}'")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cest_agent_direct()
