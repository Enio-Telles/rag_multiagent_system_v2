#!/usr/bin/env python3

from src.agents.expansion_agent import ExpansionAgent
from src.agents.ncm_agent import NCMAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config
import json

config = Config()
llm = OllamaClient()

print('🔬 Step-by-step debugging...')

# Step 1: Get expansion result
expansion_agent = ExpansionAgent(llm, config)
expansion_result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
produto_expandido = expansion_result['result']

print('✅ ExpansionAgent result:')
for key, value in produto_expandido.items():
    print(f'  {key}: {value}')

# Step 2: Simulate exact context passed to NCMAgent
context = {
    "structured_context": "Nenhum contexto estruturado específico disponível.",
    "semantic_context": []
}

print(f'\n🎯 Context passed to NCMAgent:')
print(f'  structured_context: {context["structured_context"]}')
print(f'  semantic_context: {len(context["semantic_context"])} items')

# Step 3: Test NCMAgent with exact same data
ncm_agent = NCMAgent(llm, config)

# Let's manually build the prompt that NCMAgent will use
contexto_estruturado = ""
if context and "structured_context" in context:
    estruturado = context["structured_context"]
    contexto_estruturado = f"""
CONHECIMENTO ESTRUTURADO DISPONÍVEL:
{estruturado}
"""

contexto_semantico = ""
if context and "semantic_context" in context:
    semantico = context["semantic_context"]
    if semantico:
        contexto_semantico = "\nCONHECIMENTO SEMÂNTICO (Exemplos similares):\n"
        for i, exemplo in enumerate(semantico[:3], 1):
            contexto_semantico += f"{i}. NCM {exemplo['metadata'].get('ncm', 'N/A')}: {exemplo['text'][:200]}...\n"

prompt = f"""Analise o seguinte produto e determine seu código NCM:

PRODUTO PARA CLASSIFICAR:
- Descrição Original: {produto_expandido['produto_original']}
- Categoria: {produto_expandido['categoria_principal']} 
- Material: {produto_expandido['material_predominante']}
- Descrição Expandida: {produto_expandido['descricao_expandida']}
- Características: {', '.join(produto_expandido['caracteristicas_tecnicas'])}
- Aplicações: {', '.join(produto_expandido['aplicacoes_uso'])}
- Palavras-chave: {', '.join(produto_expandido['palavras_chave_fiscais'])}

{contexto_estruturado}
{contexto_semantico}

Forneça sua análise no formato JSON especificado."""

print(f'\n📝 Exact prompt being sent to LLM:')
print('=' * 80)
print(prompt)
print('=' * 80)

# Step 4: Test raw LLM call with same prompt  
response = llm.generate(
    prompt=prompt,
    system=ncm_agent.system_prompt,
    temperature=0.2
)

print(f'\n🤖 Raw LLM response:')
print(response["response"])

print(f'\n🧪 JSON parsing test:')
try:
    result = json.loads(response["response"])
    print('✅ JSON parsing: SUCCESS')
    print(f'   NCM: {result.get("ncm_recomendado")}')
    print(f'   Confiança: {result.get("confianca")}')
except json.JSONDecodeError as e:
    print(f'❌ JSON parsing: FAILED - {e}')

# Step 5: Test actual NCMAgent.run()
print(f'\n🎯 Testing actual NCMAgent.run():')
ncm_result = ncm_agent.run(produto_expandido, context)
final_result = ncm_result['result']
print(f'   NCM: {final_result.get("ncm_recomendado")}')
print(f'   Confiança: {final_result.get("confianca")}')
print(f'   Trace reasoning: {ncm_result["trace"]["reasoning"]}')
