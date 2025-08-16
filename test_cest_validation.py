#!/usr/bin/env python3
"""
Script para testar a validação de formato CEST
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_cest_format_validation():
    print("Testando validação de formato CEST...")
    
    # Inicializar o agent
    config = Config()
    llm_client = OllamaClient()
    cest_agent = CESTAgent(llm_client, config)
    
    # Testar validação de formato
    test_cases = [
        "01.034.00",  # Válido
        "03.002.00",  # Válido  
        "17.003.01",  # Válido
        "3510110",    # Válido (sem pontos)
        "3302.10",    # Inválido (formato NCM)
        "12345",      # Inválido (muito curto)
        "123456789",  # Inválido (muito longo)
        "abc.def.gh", # Inválido (não numérico)
        "12.34.567",  # Inválido (formato incorreto)
        "",           # Inválido (vazio)
        None          # Inválido (None)
    ]
    
    print("\n=== Testes de Validação de Formato CEST ===")
    for cest in test_cases:
        if cest is None:
            result = cest_agent._validar_formato_cest(cest)
            print(f"CEST: None -> Válido: {result}")
        else:
            result = cest_agent._validar_formato_cest(cest)
            print(f"CEST: '{cest}' -> Válido: {result}")
    
    # Testar um produto real
    print("\n=== Teste com Produto Real ===")
    produto_expandido = {
        "produto_original": "PARACETAMOL 500MG COMPRIMIDO",
        "descricao_expandida": "Medicamento analgésico e antitérmico"
    }
    
    ncm_resultado = {
        "ncm_recomendado": "3004.90.99",
        "confianca": 0.9
    }
    
    try:
        resultado = cest_agent.run(produto_expandido, ncm_resultado)
        print(f"Produto: {produto_expandido['produto_original']}")
        print(f"NCM: {ncm_resultado['ncm_recomendado']}")
        print(f"Resultado CEST: {resultado['result']}")
    except Exception as e:
        print(f"Erro durante teste: {e}")

if __name__ == "__main__":
    test_cest_format_validation()
