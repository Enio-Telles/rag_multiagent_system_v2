# ============================================================================
# src/agents/expansion_agent.py - Agente de Expansão de Descrição
# ============================================================================

import json
import hashlib
from typing import Dict, Any
from .base_agent import BaseAgent

class ExpansionAgent(BaseAgent):
    """
    Agente responsável por expandir e enriquecer as descrições dos produtos
    com informações técnicas, materiais, características e usos.
    """
    
    def __init__(self, llm_client, config):
        super().__init__("ExpansionAgent", llm_client, config)
        
        # Cache para garantir consistência em produtos idênticos
        self.expansion_cache = {}
        
        self.system_prompt = """Você é um especialista em descrição técnica de produtos para classificação fiscal.

Sua tarefa é analisar uma descrição de produto e expandi-la com informações técnicas relevantes que ajudem na classificação NCM/CEST.

DIRETRIZES:
1. Identifique o tipo de produto, material principal, função e características técnicas
2. Adicione informações sobre composição, dimensões aproximadas, processo de fabricação quando relevante
3. Mencione aplicações e usos típicos
4. Use terminologia técnica precisa da nomenclatura fiscal
5. Mantenha objetividade - foque em características físicas e funcionais
6. NÃO invente informações específicas como marcas, modelos ou especificações não inferíveis

FORMATO DE RESPOSTA:
{
  "produto_original": "<descrição original>",
  "categoria_principal": "<tipo/categoria do produto>",
  "material_predominante": "<material principal>",
  "descricao_expandida": "<descrição técnica expandida>",
  "caracteristicas_tecnicas": ["<característica 1>", "<característica 2>", "..."],
  "aplicacoes_uso": ["<uso 1>", "<uso 2>", "..."],
  "palavras_chave_fiscais": ["<termo 1>", "<termo 2>", "..."]
}"""

    def run(self, produto_descricao: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Expande a descrição do produto com informações técnicas."""
        
        # Extrair descrição completa do contexto se disponível
        descricao_completa = None
        if context and isinstance(context, dict):
            descricao_completa = context.get('descricao_completa') or context.get('descricao_produto_completa')
        
        # Criar chave de cache considerando ambas as descrições (evitar colisões)
        cache_key = hashlib.md5(f"{produto_descricao.strip().lower()}||{descricao_completa or ''}".encode()).hexdigest()
        if cache_key in self.expansion_cache:
            cached_result = self.expansion_cache[cache_key]
            trace = self._create_trace("expand_description", produto_descricao, cached_result, "Resultado do cache")
            return {
                "result": cached_result,
                "trace": trace
            }
        
        # Construir prompt considerando descrição completa quando disponível
        if descricao_completa:
            prompt = f"""Analise e expanda a seguinte descrição de produto:

PRODUTO: "{produto_descricao}"
DESCRIÇÃO COMPLETA: "{descricao_completa}"

Use a descrição completa como contexto adicional para entender melhor o produto e fornecer uma análise mais precisa.

Forneça a resposta no formato JSON especificado."""
        else:
            prompt = f"""Analise e expanda a seguinte descrição de produto:

PRODUTO: "{produto_descricao}"

Forneça a resposta no formato JSON especificado."""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.1  # Lower temperature for more deterministic results
            )
            
            if "error" in response:
                result = {
                    "produto_original": produto_descricao,
                    "categoria_principal": "Não classificado",
                    "material_predominante": "Não identificado", 
                    "descricao_expandida": produto_descricao,
                    "caracteristicas_tecnicas": [],
                    "aplicacoes_uso": [],
                    "palavras_chave_fiscais": []
                }
                reasoning = f"Erro no LLM: {response['error']}"
            else:
                try:
                    # Tentar parsing direto primeiro
                    result = json.loads(response["response"])
                    # Corrigir chaves com erro de digitação
                    result = self._normalize_keys(result)
                    reasoning = "Descrição expandida com sucesso usando LLM"
                except json.JSONDecodeError:
                    # Tentar extrair JSON da resposta
                    raw_response = response["response"]
                    start = raw_response.find('{')
                    end = raw_response.rfind('}') + 1
                    
                    if start != -1 and end > start:
                        json_part = raw_response[start:end]
                        try:
                            result = json.loads(json_part)
                            # Corrigir chaves com erro de digitação
                            result = self._normalize_keys(result)
                            reasoning = "JSON extraído da resposta do LLM"
                        except json.JSONDecodeError:
                            # Fallback se o JSON extraído também não for válido
                            result = self._create_fallback_result(produto_descricao, raw_response)
                            reasoning = "Fallback: resposta do LLM não continha JSON válido"
                    else:
                        # Fallback se não encontrar JSON na resposta
                        result = self._create_fallback_result(produto_descricao, raw_response)
                        reasoning = "Fallback: nenhum JSON encontrado na resposta"
            
            trace = self._create_trace("expand_description", produto_descricao, result, reasoning)
            
            # Salvar no cache para produtos idênticos
            self.expansion_cache[cache_key] = result
            
            return {
                "result": result,
                "trace": trace
            }
            
        except Exception as e:
            # Fallback completo em caso de erro
            result = self._create_fallback_result(produto_descricao, str(e))
            
            trace = self._create_trace("expand_description", produto_descricao, result, f"Exceção: {e}")
            
            # Salvar no cache mesmo em caso de erro para evitar repetir falhas
            self.expansion_cache[cache_key] = result
            
            return {
                "result": result,
                "trace": trace
            }
    
    def _normalize_keys(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza chaves que podem ter erros de digitação do LLM."""
        # Corrigir erro comum: palavras_chave_fiscales -> palavras_chave_fiscais
        if 'palavras_chave_fiscales' in result:
            result['palavras_chave_fiscais'] = result.pop('palavras_chave_fiscales')
        
        # Garantir que todas as chaves necessárias existam
        required_keys = [
            'produto_original', 'categoria_principal', 'material_predominante',
            'descricao_expandida', 'caracteristicas_tecnicas', 'aplicacoes_uso',
            'palavras_chave_fiscais'
        ]
        
        for key in required_keys:
            if key not in result:
                # Definir valores padrão para chaves faltando
                if key in ['caracteristicas_tecnicas', 'aplicacoes_uso', 'palavras_chave_fiscais']:
                    result[key] = []
                else:
                    result[key] = "Não especificado"
        
        return result
    
    def _create_fallback_result(self, produto_descricao: str, error_info: str) -> Dict[str, Any]:
        """Cria resultado fallback quando o parsing JSON falha."""
        return {
            "produto_original": produto_descricao,
            "categoria_principal": "Análise incompleta",
            "material_predominante": "Não identificado",
            "descricao_expandida": produto_descricao,
            "caracteristicas_tecnicas": [],
            "aplicacoes_uso": [],
            "palavras_chave_fiscais": []
        }