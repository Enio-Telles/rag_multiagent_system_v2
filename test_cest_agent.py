#!/usr/bin/env python3
"""Teste isolado do CESTAgent"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_cest_agent():
    print("Testando CESTAgent isoladamente...")
    
    # Criar exatamente como no HybridRouter
    config = Config()
    print(f"Config OLLAMA_URL: {repr(config.OLLAMA_URL)}")
    print(f"Config OLLAMA_MODEL: {repr(config.OLLAMA_MODEL)}")
    
    llm_client = OllamaClient(config.OLLAMA_URL, config.OLLAMA_MODEL)
    print(f"LLM Client base_url: {repr(llm_client.base_url)}")
    print(f"LLM Client model: {repr(llm_client.model)}")
    
    # Testar LLM diretamente primeiro
    print("\nTestando LLM diretamente...")
    test_response = llm_client.generate("Diga apenas: ok", system="Seja conciso")
    print(f"Resposta direta do LLM: {test_response}")
    
    # Agora testar o agente
    print("\nCriando CESTAgent...")
    agent = CESTAgent(llm_client, config)
def test_cest_agent():
    print("Testando CESTAgent isoladamente...")
    
    config = Config()
    llm_client = OllamaClient(config)
    agent = CESTAgent(llm_client, config)
    
    produto_expandido = {
        'produto_original': 'CHIP TIM PRÉ PLANO NAKED 4G',
        'descricao_expandida': 'Chip TIM pré-pago plano Naked 4G para telefonia móvel. SIM card para ativação de linha móvel pré-paga.'
    }
    
    ncm_resultado = {
        'ncm_recomendado': '85235290'
    }
    
    context = {
        'structured_context': 'Produto de telecomunicações, especificamente SIM card para telefonia móvel'
    }
    
    resultado = agent.run(produto_expandido, ncm_resultado, context)
    print(f"Produto: {produto_expandido['produto_original']}")
    print(f"NCM usado: {ncm_resultado['ncm_recomendado']}")
    print(f"Resultado completo: {resultado}")
    
    if 'result' in resultado:
        print(f"\nRESULTADO:")
        print(f"CEST encontrado: {resultado['result'].get('cest_recomendado')}")
        print(f"Tem CEST: {resultado['result'].get('tem_cest')}")
        print(f"Confiança: {resultado['result'].get('confianca')}")
        print(f"Justificativa: {resultado['result'].get('justificativa')}")
    
if __name__ == "__main__":
    test_cest_agent()
