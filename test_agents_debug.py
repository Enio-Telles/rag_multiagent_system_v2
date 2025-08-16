#!/usr/bin/env python3

from src.agents.ncm_agent import NCMAgent
from src.agents.cest_agent import CESTAgent
from src.agents.reconciler_agent import ReconcilerAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config

config = Config()
llm = OllamaClient()

print('🧪 Testing agents individually...')

# Test ExpansionAgent
from src.agents.expansion_agent import ExpansionAgent
expansion_agent = ExpansionAgent(llm, config)
expansion_result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
produto_expandido = expansion_result['result']

print('✅ ExpansionAgent completed')
print(f'   Categoria: {produto_expandido["categoria_principal"]}')

# Test NCMAgent
ncm_agent = NCMAgent(llm, config)
context = {
    "structured_context": "Nenhum contexto estruturado específico disponível.",
    "semantic_context": []
}

print('🎯 Testing NCMAgent...')
ncm_result = ncm_agent.run(produto_expandido, context)
print(f'✅ NCMAgent completed')
print(f'   NCM: {ncm_result["result"].get("ncm_recomendado", "ERROR")}')
print(f'   Confiança: {ncm_result["result"].get("confianca", 0)}')

# Test CESTAgent  
cest_agent = CESTAgent(llm, config)
print('📊 Testing CESTAgent...')
cest_result = cest_agent.run(produto_expandido, ncm_result['result'], context)
print(f'✅ CESTAgent completed')
print(f'   CEST: {cest_result["result"].get("cest_recomendado", "ERROR")}')
print(f'   Tem CEST: {cest_result["result"].get("tem_cest", "ERROR")}')

# Test ReconcilerAgent
reconciler_agent = ReconcilerAgent(llm, config)
print('🔍 Testing ReconcilerAgent...')
reconciler_result = reconciler_agent.run(produto_expandido, ncm_result['result'], cest_result['result'], context)
print(f'✅ ReconcilerAgent completed')

final_result = reconciler_result['result']
print(f'   Final NCM: {final_result["classificacao_final"].get("ncm", "ERROR")}')
print(f'   Final CEST: {final_result["classificacao_final"].get("cest", "ERROR")}')
print(f'   Consistente: {final_result["auditoria"].get("consistente", "ERROR")}')
print(f'   Conflitos: {final_result["auditoria"].get("conflitos_identificados", [])}')

# Check raw LLM responses
print('\n🔬 Testing raw LLM response...')
test_prompt = """Determine o código CEST para o seguinte produto:

PRODUTO:
CHIP TIM PRÉ PLANO NAKED 4G

NCM DETERMINADO:
85235290

Forneça sua análise no formato JSON especificado:
{
  "tem_cest": true/false,
  "cest_recomendado": "<código CEST ou null>",
  "confianca": <número de 0 a 1>,
  "justificativa": "<explicação detalhada>",
  "cest_alternativos": []
}"""

response = llm.generate(prompt=test_prompt, temperature=0.2)
print(f'Raw LLM response: {response["response"][:500]}...')
