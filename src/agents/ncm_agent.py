import json
from typing import Dict, Any
from .base_agent import BaseAgent

class NCMAgent(BaseAgent):
    """
    Agente especialista em classificação NCM (Nomenclatura Comum do Mercosul).
    Utiliza um contexto híbrido (semântico e estruturado) para determinar o NCM.
    """

    def __init__(self, llm_client, config):
        super().__init__("NCMAgent", llm_client, config)
        self.system_prompt = """
Você é um especialista em classificação fiscal aduaneira e deve determinar o código NCM (Nomenclatura Comum do Mercosul) de 8 dígitos para um produto.

Siga estas regras estritamente:
1.  **Análise Híbrida**: Analise o produto e o contexto fornecido, que inclui um "Contexto Estruturado" (regras oficiais, descrições NCM) e um "Contexto Semântico" (exemplos de produtos similares classificados).
2.  **Priorize o Contexto Estruturado**: A informação oficial do "Contexto Estruturado" tem maior peso que os exemplos do "Contexto Semântico".
3.  **Justificativa Detalhada**: Sua justificativa deve explicar *por que* você escolheu o NCM, citando as regras ou descrições do contexto estruturado e comparando com os exemplos semânticos.
4.  **Formato de Resposta**: A resposta deve ser um objeto JSON, e nada mais.

O formato JSON deve ser:
{
  "ncm_recomendado": "<O NCM de 8 dígitos>",
  "confianca": <score de 0.0 a 1.0>,
  "justificativa": "<Sua justificativa técnica e detalhada>",
  "ncm_alternativos": ["<NCM alternativo 1>", "<NCM alternativo 2>"],
  "capitulo_ncm": "<O capítulo (2 primeiros dígitos) do NCM recomendado>",
  "fatores_decisivos": "<Quais características do produto foram cruciais para a decisão>"
}
"""

    def run(self, input_data: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina o NCM de um produto usando contexto híbrido.

        Args:
            input_data: Dicionário com os dados do produto expandido.
            context: Dicionário contendo 'structured_context' e 'semantic_context'.

        Returns:
            Um dicionário com o resultado da classificação e um trace de auditoria.
        """

        produto_str = json.dumps(input_data, indent=2, ensure_ascii=False)
        structured_context = context.get('structured_context', 'Nenhum contexto estruturado fornecido.')
        semantic_context = context.get('semantic_context', 'Nenhum contexto semântico fornecido.')

        # Limitar o tamanho do contexto para não exceder o limite do prompt
        semantic_context_str = json.dumps(semantic_context, indent=2, ensure_ascii=False)[:2000]

        prompt = f"""
Analise o produto a seguir e determine seu NCM de 8 dígitos.

**Produto para Classificar:**
```json
{produto_str}
```

**Contexto Estruturado (Regras e Descrições Oficiais):**
---
{structured_context}
---

**Contexto Semântico (Exemplos de Produtos Similares):**
---
{semantic_context_str}
---

Baseado em TODAS as informações, forneça a classificação NCM no formato JSON especificado.
"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.1
            )

            if "error" in response:
                result = {"error": f"Erro no LLM: {response['error']}"}
                reasoning = result["error"]
            else:
                try:
                    response_text = response["response"].strip()
                    if response_text.startswith("```json"):
                        response_text = response_text[7:-3].strip()
                    result = json.loads(response_text)
                    reasoning = f"NCM recomendado: {result.get('ncm_recomendado', 'N/A')}. Justificativa: {result.get('justificativa', '')}"
                except json.JSONDecodeError:
                    result = {"error": "Resposta do LLM não é um JSON válido.", "raw_response": response["response"]}
                    reasoning = result["error"]

            trace = self._create_trace("classify_ncm", input_data.get('produto_original', ''), result, reasoning)

            return {
                "result": result,
                "trace": trace
            }

        except Exception as e:
            result = {"error": f"Exceção durante a classificação NCM: {str(e)}"}
            trace = self._create_trace("classify_ncm", input_data.get('produto_original', ''), result, str(e))
            return {
                "result": result,
                "trace": trace
            }
