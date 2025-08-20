import json
from typing import Dict, Any
from .base_agent import BaseAgent

class ReconcilerAgent(BaseAgent):
    """
    Agente final do pipeline, responsável por reconciliar e auditar as
    classificações dos agentes NCM e CEST.
    """

    def __init__(self, llm_client, config):
        super().__init__("ReconcilerAgent", llm_client, config)
        self.system_prompt = """
Você é um auditor fiscal sênior. Sua função é revisar as recomendações de classificação de NCM e CEST para um produto e produzir uma classificação final e auditada.

**Regras de Auditoria:**
1.  **Consistência NCM-CEST**: Verifique se o CEST recomendado é aplicável ao NCM recomendado, usando o "Contexto Estruturado" como fonte da verdade.
2.  **Confiança Consolidada**: Calcule uma confiança final. Se houver inconsistências ou baixa confiança dos agentes anteriores, a confiança final deve ser menor.
3.  **Ajustes**: Se o CEST for inconsistente com o NCM, sugira um CEST alternativo do contexto ou remova o CEST. Não altere o NCM.
4.  **Justificativa Final**: Forneça uma justificativa clara para a classificação final, explicando quaisquer ajustes realizados.

**Formato de Resposta JSON Obrigatório:**
{
  "classificacao_final": {
    "ncm": "<NCM final de 8 dígitos>",
    "cest": "<CEST final ou null se não aplicável/inconsistente>",
    "confianca_consolidada": <score de 0.0 a 1.0>
  },
  "auditoria": {
    "consistente": <true/false>,
    "conflitos_identificados": ["<Descrição do conflito 1>"],
    "ajustes_realizados": ["<Descrição do ajuste 1>"],
    "alertas": ["<Alertas sobre a classificação, ex: baixa confiança>"]
  },
  "justificativa_final": "<Justificativa detalhada da decisão final.>"
}
"""

    def run(self, produto_expandido: Dict, ncm_result: Dict, cest_result: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconcilia as classificações de NCM e CEST.

        Args:
            produto_expandido: Dicionário com dados do produto.
            ncm_result: Resultado do NCMAgent.
            cest_result: Resultado do CESTAgent.
            context: Dicionário com 'structured_context'.

        Returns:
            Um dicionário com a classificação final e um trace de auditoria.
        """

        produto_str = json.dumps(produto_expandido, indent=2, ensure_ascii=False)
        ncm_str = json.dumps(ncm_result, indent=2, ensure_ascii=False)
        cest_str = json.dumps(cest_result, indent=2, ensure_ascii=False)
        structured_context = context.get('structured_context', 'Nenhum contexto estruturado fornecido.')

        prompt = f"""
Audite e reconcilie a seguinte classificação fiscal.

**Produto:**
```json
{produto_str}
```

**Recomendação do Agente NCM:**
```json
{ncm_str}
```

**Recomendação do Agente CEST:**
```json
{cest_str}
```

**Contexto Estruturado para Validação (Fonte da Verdade):**
---
{structured_context}
---

Baseado em TODAS as informações, forneça a auditoria e a classificação final no formato JSON especificado.
"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.0
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
                    reasoning = f"Reconciliação completa. Consistente: {result.get('auditoria', {}).get('consistente', 'N/A')}."
                except json.JSONDecodeError:
                    result = {"error": "Resposta do LLM não é um JSON válido.", "raw_response": response["response"]}
                    reasoning = result["error"]

            trace = self._create_trace("reconcile_classification", produto_expandido.get('produto_original', ''), result, reasoning)

            return {
                "result": result,
                "trace": trace
            }

        except Exception as e:
            result = {"error": f"Exceção durante a reconciliação: {str(e)}"}
            trace = self._create_trace("reconcile_classification", produto_expandido.get('produto_original', ''), result, str(e))
            return {
                "result": result,
                "trace": trace
            }
