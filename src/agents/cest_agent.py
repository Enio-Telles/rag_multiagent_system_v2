# ============================================================================
# src/agents/cest_agent.py - Agente Especialista em CEST
# ============================================================================

import json
from typing import Dict, Any
from .base_agent import BaseAgent

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

FORMATO DO CÓDIGO CEST:
- CEST SEMPRE tem 7 dígitos no formato SS.III.DD
- SS = Segmento Econômico (2 dígitos)
- III = Item dentro do segmento (3 dígitos)  
- DD = Diferenciação ou agrupamento (2 dígitos)
- Exemplos válidos: 01.034.00, 03.002.00, 17.003.01, 21.064.00
- NÃO confundir com NCM que tem formato XXXX.XX.XX

CASOS ESPECÍFICOS IMPORTANTES:

MEDICAMENTOS (NCM 3004.xx.xx):
- NCM 3004.xx.xx (medicamentos): SEMPRE usar CESTs da categoria 13.xxx.xx
- 13.001.00: Medicamentos de referência - positiva
- 13.001.01: Medicamentos de referência - negativa  
- 13.001.02: Medicamentos de referência - neutra
- 13.002.00: Medicamentos genérico - positiva
- 13.002.01: Medicamentos genérico - negativa
- 13.002.02: Medicamentos genérico - neutra
- 13.003.00: Medicamentos similar - positiva
- 13.003.01: Medicamentos similar - negativa
- 13.003.02: Medicamentos similar - neutra
- 13.004.00: Outros tipos de medicamentos - positiva
- 13.004.01: Outros tipos de medicamentos - negativa
- 13.004.02: Outros tipos de medicamentos - neutra

TELECOMUNICAÇÕES (NCM 8523.52.xx):
- CHIPS de celular, SIM CARDS, CHIPS TIM/VIVO/CLARO: SEMPRE usar CEST 21.064.00
- Cartões inteligentes para telecomunicações (SIM cards): CEST 21.064.00
- Smart cards genéricos (não SIM): CEST 21.063.00

FORMATO DE RESPOSTA:
{
  "tem_cest": <true/false>,
  "cest_recomendado": "<código CEST no formato SS.III.DD ou null>",
  "confianca": <número de 0 a 1>,
  "justificativa": "<explicação detalhada>",
  "cest_alternativos": ["<CEST alternativo 1>", "<CEST alternativo 2>", "..."]
}"""

    def run(self, produto_expandido: Dict, ncm_resultado: Dict, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Determina o código CEST para o produto."""
        import time
        
        # Registrar consulta CEST se rastreamento estiver ativo
        consulta_id = None
        if hasattr(self, 'consulta_metadados_service') and self.consulta_metadados_service:
            try:
                ncm_determinado = ncm_resultado.get('ncm_recomendado', '')
                descricao_produto = produto_expandido.get('descricao_produto', '')
                consulta_id = self.registrar_consulta_database(
                    tipo_consulta="cest_mapping",
                    fonte_dados="cest_base",
                    query=f"Mapeamento CEST para NCM {ncm_determinado}: {descricao_produto[:500]}",
                    contexto={
                        "ncm_base": ncm_determinado,
                        "confianca_ncm": ncm_resultado.get('confianca', 0.0),
                        "categoria_principal": produto_expandido.get('expansion_data', {}).get('categoria_principal'),
                        "tem_contexto_estruturado": bool(context and context.get("structured_context"))
                    }
                )
            except Exception as e:
                print(f"Aviso: Erro ao registrar consulta CEST: {e}")
        
        tempo_inicio = time.time()
        
        # Acessar dados de expansão flexivelmente
        expansion_data = produto_expandido.get('expansion_data', {})
        produto_original = produto_expandido.get('descricao_produto', expansion_data.get('produto_original', 'N/A'))
        
        prompt = f"""Determine o código CEST para o seguinte produto:

PRODUTO:
{produto_original}

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
                    # Tentar extrair JSON da resposta
                    raw_response = response["response"]
                    start = raw_response.find('{')
                    end = raw_response.rfind('}') + 1
                    
                    if start != -1 and end > start:
                        json_part = raw_response[start:end]
                        try:
                            result = json.loads(json_part)
                            reasoning = f"CEST determinado: {result.get('cest_recomendado')} (tem_cest: {result.get('tem_cest')}) (JSON extraído)"
                        except json.JSONDecodeError:
                            result = {
                                "tem_cest": False,
                                "cest_recomendado": None,
                                "confianca": 0.1,
                                "justificativa": "Resposta do LLM não estava em formato JSON válido",
                                "cest_alternativos": []
                            }
                            reasoning = "JSON inválido na resposta do LLM"
                    else:
                        result = {
                            "tem_cest": False,
                            "cest_recomendado": None,
                            "confianca": 0.1,
                            "justificativa": "Resposta do LLM não estava em formato JSON válido",
                            "cest_alternativos": []
                        }
                        reasoning = "JSON inválido na resposta do LLM"
                
                # Validar formato do CEST
                if result.get("tem_cest") and result.get("cest_recomendado"):
                    cest_recomendado = result["cest_recomendado"]
                    if not self._validar_formato_cest(cest_recomendado):
                        result["tem_cest"] = False
                        result["cest_recomendado"] = None
                        result["confianca"] = 0.1
                        result["justificativa"] = f"CEST '{cest_recomendado}' não está no formato correto SS.III.DD (7 dígitos)"
                        reasoning = f"CEST '{cest_recomendado}' inválido - formato incorreto"
                    else:
                        # Normalizar formato para SS.III.DD se válido
                        result["cest_recomendado"] = self._normalizar_formato_cest(cest_recomendado)
                
                # Validar formato dos CESTs alternativos
                if result.get("cest_alternativos"):
                    result["cest_alternativos"] = [
                        self._normalizar_formato_cest(cest) for cest in result["cest_alternativos"] 
                        if self._validar_formato_cest(cest)
                    ]
            
            # Finalizar rastreamento da consulta
            if consulta_id:
                try:
                    tempo_execucao = int((time.time() - tempo_inicio) * 1000)
                    num_alternativos = len(result.get('cest_alternativos', []))
                    qualidade_score = result.get('confianca', 0.0)
                    
                    self.finalizar_consulta_database(
                        consulta_id=consulta_id,
                        tempo_execucao_ms=tempo_execucao,
                        resultados_encontrados=1 if result.get('tem_cest') else 0,
                        qualidade_score=qualidade_score,
                        metadata_resultados={
                            "tem_cest": result.get('tem_cest'),
                            "cest_classificado": result.get('cest_recomendado'),
                            "num_alternativos": num_alternativos,
                            "ncm_origem": ncm_resultado.get('ncm_recomendado')
                        }
                    )
                except Exception as e:
                    print(f"Aviso: Erro ao finalizar rastreamento CEST: {e}")
            
            # Acessar dados de expansão flexivelmente para trace
            expansion_data = produto_expandido.get('expansion_data', {})
            produto_original = produto_expandido.get('descricao_produto', expansion_data.get('produto_original', 'N/A'))
            
            trace = self._create_trace("classify_cest", 
                                     f"{produto_original} -> NCM {ncm_resultado.get('ncm_recomendado')}", 
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
            
            # Finalizar rastreamento em caso de exceção
            if consulta_id:
                try:
                    tempo_execucao = int((time.time() - tempo_inicio) * 1000)
                    self.finalizar_consulta_database(
                        consulta_id=consulta_id,
                        tempo_execucao_ms=tempo_execucao,
                        resultados_encontrados=0,
                        qualidade_score=0.0,
                        metadata_resultados={
                            "erro": str(e),
                            "ncm_origem": ncm_resultado.get('ncm_recomendado')
                        }
                    )
                except Exception as e2:
                    print(f"Aviso: Erro ao finalizar rastreamento CEST (exceção): {e2}")
            
            # Acessar dados de expansão flexivelmente para trace
            expansion_data = produto_expandido.get('expansion_data', {})
            produto_original = produto_expandido.get('descricao_produto', expansion_data.get('produto_original', 'N/A'))
            
            trace = self._create_trace("classify_cest", 
                                     f"{produto_original} -> NCM {ncm_resultado.get('ncm_recomendado')}", 
                                     result, f"Exceção: {e}")
            
            return {
                "result": result,
                "trace": trace
            }

    def _validar_formato_cest(self, cest: str) -> bool:
        """Valida se o CEST está no formato correto SS.III.DD (7 dígitos)."""
        if not cest:
            return False
        
        # Remover pontos para validação
        cest_limpo = cest.replace('.', '')
        
        # Deve ter exatamente 7 dígitos
        if len(cest_limpo) != 7:
            return False
        
        # Deve ser todos dígitos
        if not cest_limpo.isdigit():
            return False
        
        # Formato original deve seguir SS.III.DD
        if '.' in cest:
            partes = cest.split('.')
            if len(partes) != 3:
                return False
            if len(partes[0]) != 2 or len(partes[1]) != 3 or len(partes[2]) != 2:
                return False
        
        return True

    def _normalizar_formato_cest(self, cest: str) -> str:
        """Normaliza o CEST para o formato SS.III.DD."""
        if not cest:
            return cest
            
        # Remover pontos
        cest_limpo = cest.replace('.', '')
        
        # Se já tem 7 dígitos, formatar como SS.III.DD
        if len(cest_limpo) == 7 and cest_limpo.isdigit():
            return f"{cest_limpo[:2]}.{cest_limpo[2:5]}.{cest_limpo[5:7]}"
        
        # Se já está no formato correto, retornar como está
        return cest
