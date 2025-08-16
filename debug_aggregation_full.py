#!/usr/bin/env python3

from src.agents.expansion_agent import ExpansionAgent
from src.agents.aggregation_agent import AggregationAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config

config = Config()
llm = OllamaClient()

print('🔬 Debug: Full AggregationAgent test...')

# Get 3 identical expansions
expansion_agent = ExpansionAgent(llm, config)
produtos_expandidos = []
for i in range(3):
    result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
    produtos_expandidos.append(result['result'])

print(f'✅ Got {len(produtos_expandidos)} expanded products')

# Test AggregationAgent directly
aggregation_agent = AggregationAgent(llm, config)

# Add some debug prints to see what's happening
print(f'🧪 Testing AggregationAgent.run()...')

# Call the run method
result = aggregation_agent.run(produtos_expandidos)
grupos = result['result']['grupos']

print(f'📊 Results:')
print(f'   Groups created: {len(grupos)}')
print(f'   Reduction: {result["result"]["estatisticas"].get("reducao_percentual", 0):.1f}%')

for grupo in grupos:
    print(f'   Group {grupo["grupo_id"]}: {grupo["tamanho"]} members, rep={grupo["representante_idx"]}')
    print(f'      Members: {grupo["membros"]}')

# Check the trace for more info
print(f'\n🔍 Trace reasoning: {result["trace"]["reasoning"]}')
