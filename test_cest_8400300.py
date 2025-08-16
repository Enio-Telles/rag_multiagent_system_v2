#!/usr/bin/env python3
"""
Teste para verificar se CEST "8400300" está passando pela validação
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_cest_validation_specific():
    print("Testando validação específica do CEST '8400300'...")
    
    config = Config()
    llm_client = OllamaClient()
    cest_agent = CESTAgent(llm_client, config)
    
    # Testar CESTs específicos
    test_cases = [
        "8400300",    # O que está sendo retornado incorretamente
        "21.063.00",  # CEST válido para smart cards
        "21.064.00",  # CEST correto para SIM cards
        "84.003.00",  # Versão com pontos do CEST incorreto
    ]
    
    print("\n=== Teste de Validação de Formatos ===")
    for cest in test_cases:
        result = cest_agent._validar_formato_cest(cest)
        print(f"CEST: '{cest}' -> Válido: {result}")
        
        if result:
            print(f"  ✅ PASSOU na validação")
        else:
            print(f"  ❌ REJEITADO pela validação")
    
    print(f"\n=== Análise ===")
    print(f"O CEST '8400300' {'PASSOU' if cest_agent._validar_formato_cest('8400300') else 'FOI REJEITADO'} na validação")
    print(f"O CEST '21.064.00' {'PASSOU' if cest_agent._validar_formato_cest('21.064.00') else 'FOI REJEITADO'} na validação")

if __name__ == "__main__":
    test_cest_validation_specific()
