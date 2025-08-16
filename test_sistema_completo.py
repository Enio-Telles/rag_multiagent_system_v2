from src.orchestrator.hybrid_router import HybridRouter

print("🧪 TESTE DE DIAGNÓSTICO COMPLETO DO SISTEMA")
print("=" * 50)

try:
    router = HybridRouter()
    print("✅ Sistema inicializado com sucesso!")
    
    stats = router.vector_store.get_stats()
    print(f"📚 Produtos indexados: {stats['total_vectors']:,}")
    print(f"📏 Dimensão dos vetores: {stats['dimension']}")
    print(f"🗄️ Registros de metadados: {stats['metadata_records']:,}")
    print(f"⚙️ Tipo de índice: {stats['index_type']}")
    
    # Teste rápido de classificação
    print("\n🧪 Teste de classificação rápida:")
    produtos_teste = [{
        'produto_id': 9999, 
        'descricao_produto': 'Refrigerante Coca-Cola 350ml lata', 
        'codigo_produto': 'TESTE001'
    }]
    
    resultados = router.classify_products(produtos_teste)
    resultado = resultados[0]
    
    print(f"🎯 NCM classificado: {resultado['ncm_classificado']}")
    print(f"🎯 CEST classificado: {resultado['cest_classificado']}")
    print(f"📊 Confiança: {resultado['confianca_consolidada']:.3f}")
    print(f"✅ Auditoria consistente: {resultado['auditoria']['consistente']}")
    
    print("\n🎉 SISTEMA COMPLETAMENTE FUNCIONAL!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
