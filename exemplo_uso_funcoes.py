"""
Exemplo Prático: Como usar o Sistema SQLite Unificado
Demonstra a sintaxe correta para usar as funções da linha 99 do relatório
"""

import sys
sys.path.append('src')

from services.unified_sqlite_service import get_unified_service

# Para usar a função da linha 99 do relatório:
# service.buscar_ncms_por_nivel(nivel=4, limite=10)

def exemplo_uso_correto():
    """Demonstra como usar corretamente as funções do sistema"""
    
    print("💡 EXEMPLO CORRETO DE USO DAS FUNÇÕES")
    print("=" * 45)
    
    # 1. Primeiro: obter o serviço
    print("1️⃣ Obtendo o serviço unificado:")
    service = get_unified_service("data/unified_rag_system.db")
    print("   ✅ Serviço inicializado")
    
    # 2. Agora: usar a função da linha 99
    print("\n2️⃣ Executando: service.buscar_ncms_por_nivel(nivel=4, limite=10)")
    resultado = service.buscar_ncms_por_nivel(nivel=4, limite=10)
    print(f"   ✅ Resultado: {len(resultado)} NCMs encontrados")
    
    # 3. Exibir alguns resultados
    print("\n3️⃣ Primeiros resultados:")
    for i, ncm in enumerate(resultado[:5], 1):
        print(f"   {i}. NCM {ncm['codigo_ncm']}: {ncm['descricao_oficial'][:60]}...")
    
    # 4. Outras funções do relatório
    print("\n4️⃣ Testando outras funções do relatório:")
    
    # Da linha 102: busca por padrão
    smartphones = service.buscar_ncms_por_padrao("smartphone", limite=5)
    print(f"   📱 Smartphones: {len(smartphones)} NCMs encontrados")
    
    # Da linha 105: relacionamentos NCM-CEST
    if smartphones:
        cests = service.buscar_cests_para_ncm(smartphones[0]['codigo_ncm'])
        print(f"   🎯 CESTs relacionados: {len(cests)} encontrados")
    
    # Da linha 110: criar classificação
    produto_data = {
        'produto_id': 88888,
        'descricao_produto': 'Exemplo de produto para teste',
        'ncm_sugerido': '85171231',
        'confianca_sugerida': 0.95
    }
    
    classificacao_id = service.criar_classificacao(produto_data)
    print(f"   📝 Nova classificação: ID {classificacao_id}")
    
    print("\n✅ TODAS AS FUNÇÕES DO RELATÓRIO FUNCIONANDO!")

if __name__ == "__main__":
    exemplo_uso_correto()
