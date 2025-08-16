#!/usr/bin/env python3
"""
Teste da função de normalização de CEST
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config

def test_cest_normalization():
    print("Testando normalização de formato CEST...")
    
    config = Config()
    llm_client = OllamaClient()
    cest_agent = CESTAgent(llm_client, config)
    
    # Testar normalização
    test_cases = [
        ("2106400", "21.064.00"),    # Sem pontos -> com pontos
        ("21.064.00", "21.064.00"),  # Já formatado -> manter
        ("1234567", "12.345.67"),    # Genérico sem pontos
        ("01.034.00", "01.034.00"),  # Já correto
        ("", ""),                    # Vazio
        ("invalid", "invalid"),      # Inválido
    ]
    
    print("\n=== Teste de Normalização ===")
    for input_cest, expected in test_cases:
        result = cest_agent._normalizar_formato_cest(input_cest)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_cest}' -> '{result}' (esperado: '{expected}')")

if __name__ == "__main__":
    test_cest_normalization()
