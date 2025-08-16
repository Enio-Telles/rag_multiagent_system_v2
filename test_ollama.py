from src.llm.ollama_client import OllamaClient

print("🧪 Teste de conectividade Ollama")
print("=" * 40)

try:
    llm = OllamaClient()
    print("✅ Cliente Ollama criado")
    
    # Teste simples
    response = llm.generate("Responda apenas: 'teste ok'")
    print(f"📤 Resposta do Ollama: {response}")
    
    if response.get('error'):
        print(f"❌ Erro: {response['error']}")
    else:
        print("✅ Ollama funcionando!")
        
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
    print("🔍 Verifique se o Ollama está rodando: ollama serve")
