#!/usr/bin/env python3

from src.agents.expansion_agent import ExpansionAgent
from src.agents.ncm_agent import NCMAgent  
from src.agents.cest_agent import CESTAgent
from src.agents.reconciler_agent import ReconcilerAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config
import json

config = Config()
llm = OllamaClient()

print('🔬 Testing ReconcilerAgent specifically...')

# Get realistic inputs
expansion_agent = ExpansionAgent(llm, config)
expansion_result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
produto_expandido = expansion_result['result']

context = {
    "structured_context": "Nenhum contexto estruturado específico disponível.",
    "semantic_context": []
}

ncm_agent = NCMAgent(llm, config)
ncm_result = ncm_agent.run(produto_expandido, context)

cest_agent = CESTAgent(llm, config)
cest_result = cest_agent.run(produto_expandido, ncm_result['result'], context)

print('✅ Inputs ready:')
print(f'   NCM: {ncm_result["result"].get("ncm_recomendado")}')
print(f'   CEST: {cest_result["result"].get("cest_recomendado")}')

# Now test ReconcilerAgent
reconciler_agent = ReconcilerAgent(llm, config)

# Build the exact prompt ReconcilerAgent will use
ncm_resultado = ncm_result['result']
cest_resultado = cest_result['result']

prompt = f"""Reconcilie a seguinte classificação fiscal:

PRODUTO:
{produto_expandido['produto_original']}

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

print(f'\n📝 ReconcilerAgent prompt:')
print('=' * 80)
print(prompt)
print('=' * 80)

# Test raw LLM response
response = llm.generate(
    prompt=prompt,
    system=reconciler_agent.system_prompt,
    temperature=0.1
)

print(f'\n🤖 Raw LLM response:')
print(response["response"])

print(f'\n🧪 JSON parsing test:')
try:
    result = json.loads(response["response"])
    print('✅ JSON parsing: SUCCESS')
    print(f'   Final NCM: {result["classificacao_final"].get("ncm")}')
    print(f'   Consistente: {result["auditoria"].get("consistente")}')
except json.JSONDecodeError as e:
    print(f'❌ JSON parsing: FAILED - {e}')

# Test actual ReconcilerAgent.run()
print(f'\n🎯 Testing actual ReconcilerAgent.run():')
reconciler_result = reconciler_agent.run(produto_expandido, ncm_resultado, cest_resultado, context)
final_result = reconciler_result['result']
print(f'   Final NCM: {final_result["classificacao_final"].get("ncm")}')
print(f'   Consistente: {final_result["auditoria"].get("consistente")}')
print(f'   Conflitos: {final_result["auditoria"].get("conflitos_identificados", [])}')
print(f'   Trace reasoning: {reconciler_result["trace"]["reasoning"]}')
