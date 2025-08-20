# ============================================================================
# src/agents/cest_agent.py - Agente Especialista em CEST
# ============================================================================

import json
from typing import Dict, Any
from agents.base_agent import BaseAgent

class CESTAgent(BaseAgent):
    """
    Agente especialista em classificação CEST.
    Determina o código CEST baseado no NCM e características do produto.
    """
    
    def __init__(self, llm_client, config):
        super().__init__("CESTAgent", llm_client, config)
        
        self.system_prompt = """Você é um especialista em classificação CEST (Código Especificador da Substituição Tributária).

Sua tarefa é determinar o código CEST correto para um produto já classificado com NCM.

PRINCÍPIOS CEST:
1. CEST só se aplica a produtos sujeitos à Substituição Tributária
2. Nem todos os NCMs possuem CEST correspondente
3. CEST é mais específico que NCM para fins tributários
4. Medicamentos, bebidas, combustíveis são principais categorias

FORMATO DE RESPOSTA:
{
  "tem_cest": <true/false>,
  "cest_recomendado": "<código CEST ou null>",
  "confianca": <número de 0 a 1>,
  "justificativa": "<explicação detalhada>",
  "cest_alternativos": ["<CEST alternativo 1>", "<CEST alternativo 2>", "..."]
}"""

    def run(self, produto_expandido: Dict, ncm_resultado: Dict, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Determina o código CEST para o produto."""
        
        prompt = f"""Determine o código CEST para o seguinte produto:

PRODUTO:
{produto_expandido['produto_original']}

NCM DETERMINADO:
{ncm_resultado.get('ncm_recomendado', 'Não determinado')}

CARACTERÍSTICAS EXPANDIDAS:
{produto_expandido.get('descricao_expandida', 'Nenhuma característica adicional')}

CONTEXTO ESTRUTURADO DISPONÍVEL:
{context.get('structured_context', 'Nenhum contexto estruturado disponível') if context else 'Nenhum contexto disponível'}

Forneça sua análise no formato JSON especificado."""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.2
            )
            
            if "error" in response:
                result = {
                    "tem_cest": False,
                    "cest_recomendado": None,
                    "confianca": 0.0,
                    "justificativa": f"Erro no LLM: {response['error']}",
                    "cest_alternativos": []
                }
                reasoning = f"Erro na classificação CEST: {response['error']}"
            else:
                try:
                    result = json.loads(response["response"])
                    reasoning = f"CEST determinado: {result.get('cest_recomendado')} (tem_cest: {result.get('tem_cest')})"
                except json.JSONDecodeError:
                    result = {
                        "tem_cest": False,
                        "cest_recomendado": None,
                        "confianca": 0.1,
                        "justificativa": "Resposta do LLM não estava em formato JSON válido",
                        "cest_alternativos": []
                    }
                    reasoning = "JSON inválido na resposta do LLM"
            
            trace = self._create_trace("classify_cest", 
                                     f"{produto_expandido['produto_original']} -> NCM {ncm_resultado.get('ncm_recomendado')}", 
                                     result, reasoning)
            
            return {
                "result": result,
                "trace": trace
            }
            
        except Exception as e:
            result = {
                "tem_cest": False,
                "cest_recomendado": None,
                "confianca": 0.0,
                "justificativa": f"Exceção durante classificação CEST: {e}",
                "cest_alternativos": []
            }
            
            trace = self._create_trace("classify_cest", 
                                     f"{produto_expandido['produto_original']} -> NCM {ncm_resultado.get('ncm_recomendado')}", 
                                     result, f"Exceção: {e}")
            
            return {
                "result": result,
                "trace": trace
            }
