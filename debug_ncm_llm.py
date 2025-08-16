#!/usr/bin/env python3

from src.llm.ollama_client import OllamaClient
import json

llm = OllamaClient()

system_prompt = """Você é um especialista em classificação fiscal NCM (Nomenclatura Comum do Mercosul).

Sua tarefa é analisar um produto e determinar seu código NCM correto com base em:
1. CONHECIMENTO ESTRUTURADO: Mapeamento oficial NCM com descrições
2. CONHECIMENTO SEMÂNTICO: Exemplos similares de produtos já classificados

PRINCÍPIOS DE CLASSIFICAÇÃO NCM:
- A classificação segue a estrutura por hierarquia de especificidade: Capítulo (2 dígitos) > Posição (4 dígitos) > Subposição (6 dígitos) > Item (8 dígitos)
- por exemplo: o código ncm é estruturado com 8 dígitos: os primeiros dígitos representam categorias mais abrangentes, enquanto os últimos produtos mais específicos: por exemplo, o código 8407.3 abrange os códigos 8407.31, 8407.31.10 e 8407.31.90.
- Priorize sempre a função principal do produto sobre características secundárias
- Considere material predominante quando relevante para a classificação
- Use as Regras Gerais Interpretativas (RGI) da nomenclatura

FORMATO DE RESPOSTA:
{
  "ncm_recomendado": "<código NCM de 8 dígitos>",
  "confianca": <número de 0 a 1>,
  "justificativa": "<explicação detalhada da classificação>",
  "ncm_alternativos": [
    {"ncm": "<código>", "razao": "<por que poderia ser esta opção>"}
  ],
  "fatores_decisivos": ["<fator 1>", "<fator 2>", "..."]
}"""

prompt = """Analise o seguinte produto e determine seu código NCM:

PRODUTO PARA CLASSIFICAR:
- Descrição Original: CHIP TIM PRÉ PLANO NAKED 4G
- Categoria: Componente Eletrônico 
- Material: Silício
- Descrição Expandida: Chip de processamento pré-programado para uso em dispositivos móveis, especificamente para tecnologia de rede 4G.
- Características: chip, silício, 4G
- Aplicações: comunicação móvel, tecnologia sem fio
- Palavras-chave: chip, TIM, 4G, móvel

CONHECIMENTO ESTRUTURADO DISPONÍVEL:
Nenhum contexto estruturado específico disponível.

CONHECIMENTO SEMÂNTICO (Exemplos similares):


Forneça sua análise no formato JSON especificado."""

print('🧪 Testing NCM LLM response...')
response = llm.generate(prompt=prompt, system=system_prompt, temperature=0.2)

print(f'Response keys: {response.keys()}')
print(f'Response status: {"SUCCESS" if "error" not in response else "ERROR"}')
print('\n--- RAW RESPONSE ---')
print(response["response"])
print('\n--- PARSING TEST ---')

try:
    parsed = json.loads(response["response"])
    print('✅ JSON parsing: SUCCESS')
    print(f'NCM: {parsed.get("ncm_recomendado")}')
    print(f'Confiança: {parsed.get("confianca")}')
except json.JSONDecodeError as e:
    print(f'❌ JSON parsing: FAILED - {e}')
    
    # Try to extract JSON
    raw_response = response["response"]
    start = raw_response.find('{')
    end = raw_response.rfind('}') + 1
    
    if start != -1 and end > start:
        json_part = raw_response[start:end]
        print(f'\nExtracted JSON part:\n{json_part}')
        try:
            parsed = json.loads(json_part)
            print('✅ Extracted JSON parsing: SUCCESS')
            print(f'NCM: {parsed.get("ncm_recomendado")}')
        except json.JSONDecodeError as e2:
            print(f'❌ Extracted JSON parsing: FAILED - {e2}')
    else:
        print('❌ No JSON structure found in response')
