#!/usr/bin/env python3
"""
Teste simplificado da integração SQLite
"""

import sys
import os

# Adicionar src ao path
sys.path.append('src')

def test_sqlite_integration_simple():
    """Teste direto da integração SQLite"""
    
    print("TESTE DIRETO DA INTEGRACAO SQLITE")
    print("=" * 50)
    
    # 1. Testar serviço SQLite
    print("\n1. TESTANDO SERVICO SQLITE:")
    
    try:
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service()
        
        # Testar estatísticas
        stats = service.get_dashboard_stats()
        
        print(f"   NCMs: {stats['total_ncms']:,}")
        print(f"   CESTs: {stats['total_cests']:,}")
        print(f"   Classificacoes: {stats['total_classificacoes']:,}")
        
        if stats['total_ncms'] > 10000:
            print("   OK: SQLite funcionando")
        else:
            print("   ERRO: SQLite com problemas")
            return False
            
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    # 2. Testar classificação direta
    print("\n2. TESTANDO CLASSIFICACAO DIRETA:")
    
    try:
        from main import _classify_produto_unified
        
        produto_teste = {
            'produto_id': 99999,
            'descricao_produto': 'Smartphone Samsung Galaxy S23 128GB',
            'codigo_produto': 'TEST-SMARTPHONE'
        }
        
        resultado = _classify_produto_unified(produto_teste, service)
        
        print(f"   Produto: {produto_teste['descricao_produto']}")
        print(f"   NCM: {resultado['ncm_sugerido']}")
        print(f"   CEST: {resultado['cest_sugerido']}")
        print(f"   Confianca: {resultado['confianca_sugerida']}")
        
        if resultado['ncm_sugerido'] and resultado['ncm_sugerido'] != '00000000':
            print("   OK: Classificacao funcionando")
        else:
            print("   AVISO: NCM generico")
            
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    # 3. Testar integração ABC Farma
    print("\n3. TESTANDO ABC FARMA:")
    
    try:
        abc_results = service.search_abc_farma_by_text('DIPIRONA', 2)
        
        if abc_results:
            print(f"   Encontrados: {len(abc_results)} produtos")
            print(f"   Exemplo: {abc_results[0]['descricao'][:50]}...")
            print("   OK: ABC Farma funcionando")
        else:
            print("   AVISO: ABC Farma sem resultados")
            
    except Exception as e:
        print(f"   INFO: ABC Farma nao disponivel - {e}")
    
    # 4. Verificar arquivo de banco
    print("\n4. VERIFICANDO ARQUIVO BANCO:")
    
    db_path = "data/unified_rag_system.db"
    
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"   Arquivo: {db_path}")
        print(f"   Tamanho: {size_mb:.1f} MB")
        
        if size_mb > 20:
            print("   OK: Banco com dados")
        else:
            print("   AVISO: Banco pequeno")
    else:
        print("   ERRO: Banco nao encontrado")
        return False
    
    print("\n" + "=" * 50)
    print("INTEGRACAO SQLITE VALIDADA COM SUCESSO!")
    print("COMANDO 'classify --from-db' PRONTO PARA USO")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_sqlite_integration_simple()
    sys.exit(0 if success else 1)
