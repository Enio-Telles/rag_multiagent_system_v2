# Script de validação completa do sistema
import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print('🧪 VALIDAÇÃO COMPLETA DO SISTEMA')
print('=' * 50)

try:
    # 1. Imports básicos
    from config import Config
    from orchestrator.hybrid_router import HybridRouter
    print('✅ Imports básicos funcionais')
    
    # 2. Inicialização
    config = Config()
    router = HybridRouter()
    print('✅ Sistema inicializado')
    
    # 3. Verificar arquivos
    assert config.FAISS_INDEX_FILE.exists(), 'Índice FAISS não encontrado'
    assert config.METADATA_DB_FILE.exists(), 'Metadata DB não encontrado'
    print('✅ Arquivos essenciais presentes')
    
    # 4. Teste de classificação mínima
    produtos_teste = [{'produto_id': 999, 'descricao_produto': 'Teste validação', 'codigo_produto': 'TESTE'}]
    resultados = router.classify_products(produtos_teste)
    assert len(resultados) == 1, 'Falha na classificação'
    print('✅ Classificação funcional')
    
    print('🎉 SISTEMA COMPLETAMENTE VALIDADO!')
    
except Exception as e:
    print(f'❌ Erro na validação: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
