#!/usr/bin/env python3
"""
Teste para simular um CEST inválido e verificar se é rejeitado
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.cest_agent import CESTAgent
from llm.ollama_client import OllamaClient
from config import Config
import json

def test_invalid_cest_rejection():
    print("Testando rejeição de CEST inválido...")
    
    config = Config()
    llm_client = OllamaClient()
    cest_agent = CESTAgent(llm_client, config)
    
    # Simular um resultado com CEST inválido
    print("\n=== Teste de Validação Interna ===")
    
    # Resultado simulado com CEST inválido (formato NCM)
    resultado_invalido = {
        "tem_cest": True,
        "cest_recomendado": "3302.10",  # Formato NCM incorreto
        "confianca": 0.8,
        "justificativa": "Teste com formato incorreto",
        "cest_alternativos": ["3302.11", "01.034.00"]  # Mix de formatos
    }
    
    print(f"Resultado antes da validação: {resultado_invalido}")
    
    # Aplicar validação manualmente
    if resultado_invalido.get("tem_cest") and resultado_invalido.get("cest_recomendado"):
        cest_recomendado = resultado_invalido["cest_recomendado"]
        if not cest_agent._validar_formato_cest(cest_recomendado):
            resultado_invalido["tem_cest"] = False
            resultado_invalido["cest_recomendado"] = None
            resultado_invalido["confianca"] = 0.1
            resultado_invalido["justificativa"] = f"CEST '{cest_recomendado}' não está no formato correto SS.III.DD (7 dígitos)"
    
    # Validar CESTs alternativos
    if resultado_invalido.get("cest_alternativos"):
        resultado_invalido["cest_alternativos"] = [
            cest for cest in resultado_invalido["cest_alternativos"] 
            if cest_agent._validar_formato_cest(cest)
        ]
    
    print(f"Resultado após validação: {resultado_invalido}")
    
    # Verificar se a validação funcionou
    if not resultado_invalido["tem_cest"] and resultado_invalido["cest_recomendado"] is None:
        print("✅ CEST inválido foi rejeitado corretamente!")
    else:
        print("❌ CEST inválido não foi rejeitado!")
        
    # Verificar CESTs alternativos
    cest_alt = resultado_invalido["cest_alternativos"]
    print(f"CESTs alternativos após validação: {cest_alt}")
    if len(cest_alt) == 1 and cest_alt[0] == "01.034.00":
        print("✅ Apenas CESTs válidos foram mantidos nos alternativos!")
    else:
        print("❌ Validação dos CESTs alternativos falhou!")

if __name__ == "__main__":
    test_invalid_cest_rejection()
