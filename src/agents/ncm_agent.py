# ============================================================================
# src/agents/ncm_agent.py - Agente Especialista em NCM
# ============================================================================

import json
from typing import Dict, Any
from .base_agent import BaseAgent

class NCMAgent(BaseAgent):
    """
    Agente especialista em classificação NCM.
    Utiliza conhecimento estruturado e semântico para determinar o código NCM correto.
    """
    
    def __init__(self, llm_client, config):
        super().__init__("NCMAgent", llm_client, config)
        
        self.system_prompt = """Você é um especialista em classificação fiscal NCM (Nomenclatura Comum do Mercosul).

Sua tarefa é analisar um produto e determinar seu código NCM correto com base em:
1. CONHECIMENTO ESTRUTURADO: Mapeamento oficial NCM com descrições
2. CONHECIMENTO SEMÂNTICO: Exemplos similares de produtos já classificados

PRINCÍPIOS DE CLASSIFICAÇÃO NCM:
- A classificação segue a estrutura por hierarquia de especificidade: Capítulo (2 dígitos) > Posição (4 dígitos) > Subposição (6 dígitos) > Item (8 dígitos)
- por exemplo: o código ncm é estruturado com 8 dígitos: os primeiros dígitos representam categorias mais abrangentes, enquanto os últimos produtos mais específicos: por exemplo, o código 8407.3 abrange os códigos 8407.31, 8407.31.10 e 8407.31.90.
- Priorize sempre a função principal do produto sobre características secundárias
- Considere material predominante quando relevante para a classificação
- Use as Regras Gerais Interpretativas (RGI) da nomenclatura

CASOS ESPECÍFICOS IMPORTANTES:
- CHIPS de celular, SIM CARDS, CHIPS TIM/VIVO/CLARO: SEMPRE NCM 85235290 (8523.52.90)
- Cartões inteligentes para telecomunicações: NCM 85235290 
- Smart cards genéricos: também NCM 85235290 mas podem variar conforme aplicação
- Produtos com "CHIP", "SIM", operadoras de telefonia: verificar se é cartão SIM

FORMATO DE RESPOSTA:
{
  "ncm_recomendado": "<código NCM de 8 dígitos>",
  "confianca": <número de 0 a 1>,
  "justificativa": "<explicação detalhada da classificação>",
  "ncm_alternativos": [
    {"ncm": "<código>", "razao": "<por que poderia ser esta opção>"}
  ],
  "fatores_decisivos": ["<fator 1>", "<fator 2>", "..."]
}"""

    def run(self, produto_expandido: Dict, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classifica o NCM do produto usando contexto estruturado e semântico."""
        import time
        
        # Registrar consulta hierárquica NCM se rastreamento estiver ativo
        consulta_id = None
        if hasattr(self, 'consulta_metadados_service') and self.consulta_metadados_service:
            try:
                descricao_produto = produto_expandido.get('descricao_produto', '')
                consulta_id = self.registrar_consulta_database(
                    tipo_consulta="ncm_hierarchy",
                    fonte_dados="ncm_base",
                    query=f"Classificação NCM para: {descricao_produto[:500]}",
                    contexto={
                        "categoria_principal": produto_expandido.get('expansion_data', {}).get('categoria_principal'),
                        "material_predominante": produto_expandido.get('expansion_data', {}).get('material_predominante'),
                        "tem_contexto_estruturado": bool(context and context.get("structured_context")),
                        "tem_contexto_semantico": bool(context and context.get("semantic_context"))
                    }
                )
            except Exception as e:
                print(f"Aviso: Erro ao registrar consulta NCM: {e}")
        
        tempo_inicio = time.time()
        
        # Construir contexto estruturado
        contexto_estruturado = ""
        if context and "structured_context" in context:
            estruturado = context["structured_context"]
            contexto_estruturado = f"""
CONHECIMENTO ESTRUTURADO DISPONÍVEL:
{estruturado}
"""

        # Construir contexto semântico  
        contexto_semantico = ""
        if context and "semantic_context" in context:
            semantico = context["semantic_context"]
            if semantico:
                contexto_semantico = "\nCONHECIMENTO SEMÂNTICO (Exemplos similares):\n"
                for i, exemplo in enumerate(semantico[:3], 1):  # Limitar a 3 exemplos
                    contexto_semantico += f"{i}. NCM {exemplo['metadata'].get('ncm', 'N/A')}: {exemplo['text'][:200]}...\n"

        # Construir prompt principal  
        expansion_data = produto_expandido.get('expansion_data', {})
        
        prompt = f"""Analise o seguinte produto e determine seu código NCM:

PRODUTO PARA CLASSIFICAR:
- Descrição Original: {produto_expandido.get('descricao_produto', expansion_data.get('produto_original', 'N/A'))}
- Categoria: {expansion_data.get('categoria_principal', 'N/A')} 
- Material: {expansion_data.get('material_predominante', 'N/A')}
- Descrição Expandida: {produto_expandido.get('descricao_expandida', 'N/A')}
- Características: {', '.join(expansion_data.get('caracteristicas_tecnicas', []))}
- Aplicações: {', '.join(expansion_data.get('aplicacoes_uso', []))}
- Palavras-chave: {', '.join(expansion_data.get('palavras_chave_fiscais', []))}

{contexto_estruturado}
{contexto_semantico}

Forneça sua análise no formato JSON especificado."""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.2
            )
            
            if "error" in response:
                result = {
                    "ncm_recomendado": "00000000",
                    "confianca": 0.0,
                    "justificativa": f"Erro no LLM: {response['error']}",
                    "ncm_alternativos": [],
                    "fatores_decisivos": []
                }
                reasoning = f"Erro na classificação: {response['error']}"
            else:
                try:
                    result = json.loads(response["response"])
                    reasoning = f"NCM classificado: {result.get('ncm_recomendado')} com confiança {result.get('confianca')}"
                except json.JSONDecodeError:
                    # Tentar extrair JSON da resposta
                    raw_response = response["response"]
                    start = raw_response.find('{')
                    end = raw_response.rfind('}') + 1
                    
                    if start != -1 and end > start:
                        json_part = raw_response[start:end]
                        try:
                            result = json.loads(json_part)
                            reasoning = f"NCM classificado: {result.get('ncm_recomendado')} com confiança {result.get('confianca')} (JSON extraído)"
                        except json.JSONDecodeError:
                            result = {
                                "ncm_recomendado": "99999999",
                                "confianca": 0.1,
                                "justificativa": "Resposta do LLM não estava em formato JSON válido",
                                "ncm_alternativos": [],
                                "fatores_decisivos": []
                            }
                            reasoning = "JSON inválido na resposta do LLM"
                    else:
                        result = {
                            "ncm_recomendado": "99999999",
                            "confianca": 0.1,
                            "justificativa": "Resposta do LLM não estava em formato JSON válido",
                            "ncm_alternativos": [],
                            "fatores_decisivos": []
                        }
                        reasoning = "JSON inválido na resposta do LLM"
            
            trace = self._create_trace("classify_ncm", 
                                     produto_expandido.get('descricao_produto', 
                                     produto_expandido.get('expansion_data', {}).get('produto_original', 'N/A')), 
                                     result, reasoning)
            
            return {
                "result": result,
                "trace": trace
            }
            
        except Exception as e:
            result = {
                "ncm_recomendado": "00000000",
                "confianca": 0.0,
                "justificativa": f"Exceção durante classificação: {e}",
                "ncm_alternativos": [],
                "fatores_decisivos": []
            }
            reasoning = f"Exceção: {e}"
            
        # Finalizar rastreamento da consulta
        if consulta_id:
            try:
                tempo_execucao = int((time.time() - tempo_inicio) * 1000)
                num_alternativos = len(result.get('ncm_alternativos', []))
                qualidade_score = result.get('confianca', 0.0)
                
                self.finalizar_consulta_database(
                    consulta_id=consulta_id,
                    tempo_execucao_ms=tempo_execucao,
                    resultados_encontrados=1 + num_alternativos,  # NCM principal + alternativos
                    qualidade_score=qualidade_score,
                    metadata_resultados={
                        "ncm_classificado": result.get('ncm_recomendado'),
                        "num_alternativos": num_alternativos,
                        "fatores_decisivos": result.get('fatores_decisivos', []),
                        "contexto_utilizado": {
                            "estruturado": bool(contexto_estruturado),
                            "semantico": bool(contexto_semantico)
                        }
                    }
                )
            except Exception as e:
                print(f"Aviso: Erro ao finalizar rastreamento NCM: {e}")
            
            trace = self._create_trace("classify_ncm", 
                                     produto_expandido.get('descricao_produto', 
                                     produto_expandido.get('expansion_data', {}).get('produto_original', 'N/A')), 
                                     result, reasoning)
            
            return {
                "result": result,
                "trace": trace
            }
