from src.agents.expansion_agent import ExpansionAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config
import json

print("🧪 Teste detalhado do ExpansionAgent")
print("=" * 50)

try:
    config = Config()
    llm = OllamaClient()
    
    # Teste direto do LLM primeiro
    prompt = """Analise e expanda a seguinte descrição de produto:

PRODUTO: "Refrigerante Coca-Cola 350ml lata"

FORMATO DE RESPOSTA:
{
  "produto_original": "<descrição original>",
  "categoria_principal": "<tipo/categoria do produto>",
  "material_predominante": "<material principal>",
  "descricao_expandida": "<descrição técnica expandida>",
  "caracteristicas_tecnicas": ["<característica 1>", "<característica 2>", "..."],
  "aplicacoes_uso": ["<uso 1>", "<uso 2>", "..."],
  "palavras_chave_fiscais": ["<termo 1>", "<termo 2>", "..."]
}

Forneça a resposta no formato JSON especificado."""

    print("📤 Enviando prompt para LLM...")
    response = llm.generate(prompt)
    
    if response.get('error'):
        print(f"❌ Erro do LLM: {response['error']}")
    else:
        print(f"📥 Resposta bruta do LLM:")
        raw_response = response.get('response', '')
        print(f"   Tamanho: {len(raw_response)} caracteres")
        print(f"   Primeiros 500 chars: {raw_response[:500]}...")
        
        try:
            parsed = json.loads(raw_response)
            print("✅ JSON válido!")
            print(f"   Chaves presentes: {list(parsed.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido: {e}")
            print("🔍 Tentando encontrar JSON na resposta...")
            
            # Buscar por { } na resposta
            start = raw_response.find('{')
            end = raw_response.rfind('}') + 1
            if start != -1 and end > start:
                json_part = raw_response[start:end]
                print(f"   JSON encontrado: {json_part[:200]}...")
                try:
                    parsed = json.loads(json_part)
                    print("✅ JSON extraído com sucesso!")
                    print(f"   Chaves: {list(parsed.keys())}")
                except:
                    print("❌ Ainda não é JSON válido")
        
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()
