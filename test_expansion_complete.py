from src.agents.expansion_agent import ExpansionAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config
import json

config = Config()
llm = OllamaClient()
agent = ExpansionAgent(llm, config)

print("🧪 Teste completo ExpansionAgent")
print("=" * 40)

resultado = agent.run("Refrigerante Coca-Cola 350ml lata")

if 'result' in resultado:
    result = resultado['result']
    print("📋 Resultado completo:")
    for chave, valor in result.items():
        print(f"   {chave}: {valor}")
    
    print(f"\n🔍 Tem palavras_chave_fiscais? {'palavras_chave_fiscais' in result}")
    if 'palavras_chave_fiscais' in result:
        print(f"   Valor: {result['palavras_chave_fiscais']}")
        print(f"   Tipo: {type(result['palavras_chave_fiscais'])}")
