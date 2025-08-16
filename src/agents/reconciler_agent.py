# ============================================================================
# src/agents/reconciler_agent.py - Agente de Reconciliação e Auditoria
# ============================================================================

import json
from typing import Dict, Any
from .base_agent import BaseAgent

class ReconcilerAgent(BaseAgent):
    """
    Agente responsável por reconciliar os resultados de NCM e CEST,
    verificar consistência e produzir resultado final auditado.
    """
    
    def __init__(self, llm_client, config):
        super().__init__("ReconcilerAgent", llm_client, config)
        
        self.system_prompt = """Você é um auditor especialista em classificação fiscal que reconcilia classificações NCM e CEST.

Sua tarefa é:
1. Verificar consistência entre NCM e CEST propostos
2. Identificar possíveis conflitos ou inconsistências
3. Propor correções se necessário
4. Calcular confiança final consolidada

CRITÉRIOS DE VERIFICAÇÃO:
- CEST deve ser compatível com o NCM (verificar se o CEST existe para aquele NCM)
- Confiança baixa em qualquer classificação deve ser sinalizada
- Conflitos entre agentes devem ser destacados e resolvidos

FORMATO DE RESPOSTA:
{
  "classificacao_final": {
    "ncm": "<código NCM final>",
    "cest": "<código CEST final ou null>",
    "confianca_consolidada": <número de 0 a 1>
  },
  "auditoria": {
    "consistente": <true/false>,
    "conflitos_identificados": ["<conflito 1>", "<conflito 2>", "..."],
    "ajustes_realizados": ["<ajuste 1>", "<ajuste 2>", "..."],
    "alertas": ["<alerta 1>", "<alerta 2>", "..."]
  },
  "justificativa_final": "<explicação consolidada da classificação>"
}"""

    def run(self, produto_expandido: Dict, ncm_resultado: Dict, cest_resultado: Dict, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Reconcilia os resultados de NCM e CEST."""
        
        # Acessar dados de expansão flexivelmente
        expansion_data = produto_expandido.get('expansion_data', {})
        produto_original = produto_expandido.get('descricao_produto', expansion_data.get('produto_original', 'N/A'))
        
        prompt = f"""Reconcilie a seguinte classificação fiscal:

PRODUTO:
{produto_original}

RESULTADO NCM:
- NCM Recomendado: {ncm_resultado.get('ncm_recomendado')}
- Confiança: {ncm_resultado.get('confianca')}
- Justificativa: {ncm_resultado.get('justificativa')}

RESULTADO CEST:
- Tem CEST: {cest_resultado.get('tem_cest')}
- CEST Recomendado: {cest_resultado.get('cest_recomendado')}
- Confiança: {cest_resultado.get('confianca')}
- Justificativa: {cest_resultado.get('justificativa')}

CONTEXTO ESTRUTURADO DISPONÍVEL:
{context.get('structured_context', 'Nenhum contexto estruturado disponível') if context else 'Nenhum contexto disponível'}

Forneça sua análise de reconciliação no formato JSON especificado."""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.1  # Baixa temperatura para consistência
            )
            
            if "error" in response:
                # Fallback: usar resultados originais sem modificação
                result = {
                    "classificacao_final": {
                        "ncm": ncm_resultado.get('ncm_recomendado', '00000000'),
                        "cest": self._normalizar_formato_cest(cest_resultado.get('cest_recomendado')),
                        "confianca_consolidada": min(ncm_resultado.get('confianca', 0), cest_resultado.get('confianca', 0))
                    },
                    "auditoria": {
                        "consistente": False,
                        "conflitos_identificados": [f"Erro no LLM de reconciliação: {response['error']}"],
                        "ajustes_realizados": [],
                        "alertas": ["Reconciliação automática falhou - usando resultados originais"]
                    },
                    "justificativa_final": f"Classificação sem reconciliação devido a erro: {response['error']}"
                }
                reasoning = f"Erro na reconciliação: {response['error']}"
            else:
                try:
                    result = json.loads(response["response"])
                    # Normalizar CEST se presente
                    if result.get('classificacao_final', {}).get('cest'):
                        cest = result['classificacao_final']['cest']
                        result['classificacao_final']['cest'] = self._normalizar_formato_cest(cest)
                    reasoning = f"Reconciliação concluída - Consistente: {result.get('auditoria', {}).get('consistente', False)}"
                except json.JSONDecodeError:
                    # Tentar extrair JSON da resposta
                    raw_response = response["response"]
                    start = raw_response.find('{')
                    end = raw_response.rfind('}') + 1
                    
                    if start != -1 and end > start:
                        json_part = raw_response[start:end]
                        try:
                            result = json.loads(json_part)
                            # Normalizar CEST se presente
                            if result.get('classificacao_final', {}).get('cest'):
                                cest = result['classificacao_final']['cest']
                                result['classificacao_final']['cest'] = self._normalizar_formato_cest(cest)
                            reasoning = f"Reconciliação concluída - Consistente: {result.get('auditoria', {}).get('consistente', False)} (JSON extraído)"
                        except json.JSONDecodeError:
                            # Fallback para JSON inválido
                            result = {
                                "classificacao_final": {
                                    "ncm": ncm_resultado.get('ncm_recomendado', '00000000'),
                                    "cest": self._normalizar_formato_cest(cest_resultado.get('cest_recomendado')),
                                    "confianca_consolidada": 0.5
                                },
                                "auditoria": {
                                    "consistente": False,
                                    "conflitos_identificados": ["Resposta de reconciliação em formato inválido"],
                                    "ajustes_realizados": [],
                                    "alertas": ["JSON inválido na reconciliação"]
                                },
                                "justificativa_final": "Classificação sem reconciliação adequada"
                            }
                            reasoning = "JSON inválido na resposta de reconciliação"
                    else:
                        # Fallback para JSON inválido
                        result = {
                            "classificacao_final": {
                                "ncm": ncm_resultado.get('ncm_recomendado', '00000000'),
                                "cest": self._normalizar_formato_cest(cest_resultado.get('cest_recomendado')),
                                "confianca_consolidada": 0.5
                            },
                            "auditoria": {
                                "consistente": False,
                                "conflitos_identificados": ["Resposta de reconciliação em formato inválido"],
                                "ajustes_realizados": [],
                                "alertas": ["JSON inválido na reconciliação"]
                            },
                            "justificativa_final": "Classificação sem reconciliação adequada"
                        }
                        reasoning = "JSON inválido na resposta de reconciliação"
            
            trace = self._create_trace("reconcile_classification", 
                                     f"NCM {ncm_resultado.get('ncm_recomendado')} + CEST {cest_resultado.get('cest_recomendado')}", 
                                     result, reasoning)
            
            return {
                "result": result,
                "trace": trace
            }
            
        except Exception as e:
            result = {
                "classificacao_final": {
                    "ncm": ncm_resultado.get('ncm_recomendado', '00000000'),
                    "cest": self._normalizar_formato_cest(cest_resultado.get('cest_recomendado')),
                    "confianca_consolidada": 0.0
                },
                "auditoria": {
                    "consistente": False,
                    "conflitos_identificados": [f"Exceção na reconciliação: {e}"],
                    "ajustes_realizados": [],
                    "alertas": ["Falha completa na reconciliação"]
                },
                "justificativa_final": f"Classificação sem reconciliação devido a exceção: {e}"
            }
            
            trace = self._create_trace("reconcile_classification", 
                                     f"NCM {ncm_resultado.get('ncm_recomendado')} + CEST {cest_resultado.get('cest_recomendado')}", 
                                     result, f"Exceção: {e}")
            
            return {
                "result": result,
                "trace": trace
            }

    def _normalizar_formato_cest(self, cest: str) -> str:
        """Normaliza o CEST para o formato SS.III.DD."""
        if not cest:
            return cest
            
        # Remover pontos
        cest_limpo = str(cest).replace('.', '')
        
        # Se já tem 7 dígitos, formatar como SS.III.DD
        if len(cest_limpo) == 7 and cest_limpo.isdigit():
            return f"{cest_limpo[:2]}.{cest_limpo[2:5]}.{cest_limpo[5:7]}"
        
        # Se já está no formato correto, retornar como está
        return cest
