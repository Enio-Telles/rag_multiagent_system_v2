from src.agents.expansion_agent import ExpansionAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config

print("🧪 Teste do ExpansionAgent")
print("=" * 40)

try:
    config = Config()
    llm = OllamaClient()
    agent = ExpansionAgent(llm, config)
    
    print("✅ ExpansionAgent criado")
    
    # Teste com produto simples
    resultado = agent.run("Refrigerante Coca-Cola 350ml lata")
    
    print("📤 Resultado do ExpansionAgent:")
    print(f"   Status: {'✅ Sucesso' if 'result' in resultado else '❌ Erro'}")
    
    if 'result' in resultado:
        result = resultado['result']
        print(f"   Produto original: {result.get('produto_original', 'N/A')}")
        print(f"   Categoria: {result.get('categoria_principal', 'N/A')}")
        print(f"   Material: {result.get('material_predominante', 'N/A')}")
        print(f"   Palavras-chave: {result.get('palavras_chave_fiscais', 'N/A')}")
        
        # Verificar se tem todas as chaves necessárias
        chaves_necessarias = ['produto_original', 'categoria_principal', 'material_predominante', 
                             'descricao_expandida', 'caracteristicas_tecnicas', 'aplicacoes_uso', 
                             'palavras_chave_fiscais']
        chaves_faltando = [chave for chave in chaves_necessarias if chave not in result]
        
        if chaves_faltando:
            print(f"⚠️ Chaves faltando: {chaves_faltando}")
        else:
            print("✅ Todas as chaves necessárias presentes")
    
    if 'trace' in resultado:
        print(f"   Trace: {resultado['trace'].get('reasoning', 'N/A')}")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
