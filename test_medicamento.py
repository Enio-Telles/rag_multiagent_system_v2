#!/usr/bin/env python3
"""Teste específico para medicamentos"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_medicamento():
    print("=== TESTE MEDICAMENTO PANTOPRAZOL ===")
    
    config = Config()
    llm_client = OllamaClient(config.OLLAMA_URL, config.OLLAMA_MODEL)
    agent = CESTAgent(llm_client, config)
    
    produto_expandido = {
        'produto_original': 'PANTOPRAZOL 40MG C/28CP',
        'descricao_expandida': 'Medicamento pantoprazol 40mg com 28 comprimidos para tratamento de problemas gástricos'
    }
    
    ncm_resultado = {
        'ncm_recomendado': '30049090'  # NCM de medicamento
    }
    
    context = {
        'structured_context': 'Produto farmacêutico - medicamento para tratamento gástrico'
    }
    
    print(f"Produto: {produto_expandido['produto_original']}")
    print(f"NCM: {ncm_resultado['ncm_recomendado']}")
    
    resultado = agent.run(produto_expandido, ncm_resultado, context)
    
    if 'result' in resultado:
        result = resultado['result']
        print(f"\nRESULTADO CESTAGENT:")
        print(f"Tem CEST: {result.get('tem_cest')}")
        print(f"CEST: {result.get('cest_recomendado')}")
        print(f"Confiança: {result.get('confianca')}")
        print(f"Justificativa: {result.get('justificativa')}")
        print(f"Alternativos: {result.get('cest_alternativos')}")
        
        # Verificar se é um CEST da categoria 13.xxx.xx
        cest = result.get('cest_recomendado')
        if cest and cest.startswith('13.'):
            print(f"✅ CEST correto para medicamento!")
        elif cest:
            print(f"❌ CEST incorreto! Medicamentos devem usar categoria 13.xxx.xx, obtido: {cest}")
        else:
            print(f"❌ Nenhum CEST retornado!")

if __name__ == "__main__":
    test_medicamento()
