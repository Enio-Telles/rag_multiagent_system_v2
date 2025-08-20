import json
from typing import Dict, Any
from .base_agent import BaseAgent

class ExpansionAgent(BaseAgent):
    """
    Agente responsável por expandir a descrição de um produto,
    enriquecendo-a com informações técnicas e fiscais inferidas.
    """

    def __init__(self, llm_client, config):
        super().__init__("ExpansionAgent", llm_client, config)
        self.system_prompt = """
Você é um especialista em análise de produtos para fins fiscais. Sua tarefa é analisar a descrição de um produto e expandi-la para um formato JSON estruturado.

Extraia as seguintes informações:
- "produto_original": A descrição original do produto.
- "categoria_principal": A categoria geral do produto (ex: "Eletrônicos", "Alimentos", "Vestuário", "Ferramentas").
- "material_predominante": O material principal do produto (ex: "Plástico", "Aço Inoxidável", "Algodão", "Madeira").
- "descricao_expandida": Uma descrição mais detalhada e técnica do produto, ideal para classificação fiscal.
- "caracteristicas_tecnicas": Uma lista de características técnicas relevantes (ex: ["Voltagem: 110V", "Capacidade: 128GB", "Resolução: 4K"]).
- "aplicacoes_uso": Uma lista de possíveis aplicações ou usos do produto.
- "palavras_chave_fiscais": Uma lista de palavras-chave relevantes para a classificação fiscal (ex: ["smartphone", "comunicação", "eletrônico"]).
- "confianca": Um score de confiança (0.0 a 1.0) na qualidade da expansão.

Responda APENAS com o objeto JSON. Não inclua texto adicional ou markdown.
"""

    def run(self, input_data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Expande a descrição de um produto usando o LLM.

        Args:
            input_data: A descrição original do produto (string).
            context: Contexto adicional (não utilizado neste agente).

        Returns:
            Um dicionário com o resultado da expansão e um trace de auditoria.
        """
        prompt = f"Analise e expanda a seguinte descrição de produto: '{input_data}'"

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.3
            )

            if "error" in response:
                result = {"error": f"Erro no LLM: {response['error']}"}
                reasoning = result["error"]
            else:
                try:
                    # Tenta carregar a resposta JSON, limpando quaisquer caracteres extras
                    response_text = response["response"].strip()
                    if response_text.startswith("```json"):
                        response_text = response_text[7:-3].strip()

                    result = json.loads(response_text)
                    # Garante que a descrição original esteja no resultado
                    if 'produto_original' not in result:
                        result['produto_original'] = input_data
                    reasoning = "Expansão bem-sucedida a partir da análise do LLM."
                except json.JSONDecodeError:
                    result = {"error": "Resposta do LLM não é um JSON válido.", "raw_response": response["response"]}
                    reasoning = result["error"]

            trace = self._create_trace("expand_description", input_data, result, reasoning)

            return {
                "result": result,
                "trace": trace
            }

        except Exception as e:
            result = {"error": f"Exceção durante a expansão: {str(e)}"}
            trace = self._create_trace("expand_description", input_data, result, str(e))
            return {
                "result": result,
                "trace": trace
            }
