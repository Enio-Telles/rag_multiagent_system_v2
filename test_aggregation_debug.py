#!/usr/bin/env python3

from src.agents.aggregation_agent import AggregationAgent
from src.agents.expansion_agent import ExpansionAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config

config = Config()
llm = OllamaClient()

# Test expansion first
expansion_agent = ExpansionAgent(llm, config)
print('🔍 Testing expansion of identical products...')

produtos_expandidos = []
for i in range(3):
    result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
    produtos_expandidos.append(result['result'])
    categoria = result['result'].get('categoria_principal', 'N/A')
    material = result['result'].get('material_predominante', 'N/A')
    palavras = result['result'].get('palavras_chave_fiscais', [])
    print(f'Product {i+1}:')
    print(f'  Categoria: {categoria}')
    print(f'  Material: {material}')
    print(f'  Palavras-chave: {palavras[:3]}')  # First 3 keywords
    print()

print(f'🎲 Testing aggregation of {len(produtos_expandidos)} products...')
aggregation_agent = AggregationAgent(llm, config)
result = aggregation_agent.run(produtos_expandidos)

grupos = result['result']['grupos']
print(f'Groups created: {len(grupos)}')
print(f'Expected: 1 group (all identical)')
print(f'Reduction: {result["result"]["estatisticas"].get("reducao_percentual", 0):.1f}%')

for grupo in grupos:
    grupo_id = grupo['grupo_id']
    tamanho = grupo['tamanho'] 
    rep_idx = grupo['representante_idx']
    print(f'  Group {grupo_id}: {tamanho} members, representante={rep_idx}')

# Check if expansion results are actually identical
print('\n🔬 Checking if expanded products are identical...')
for i, produto in enumerate(produtos_expandidos):
    texto_completo = f"{produto['categoria_principal']} {produto['material_predominante']} {produto['descricao_expandida']} {' '.join(produto['palavras_chave_fiscais'])}"
    print(f'Product {i+1} full text length: {len(texto_completo)}')
    print(f'  First 100 chars: {texto_completo[:100]}...')
