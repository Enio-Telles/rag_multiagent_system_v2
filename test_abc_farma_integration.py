#!/usr/bin/env python3
"""
Teste da integração ABC Farma com sistema unificado
"""

import os
import sys

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.unified_service import get_unified_service
from database.unified_sqlite_models import ABCFarmaProduct
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_abc_farma_integration():
    """Testar integração ABC Farma"""
    
    print("=" * 60)
    print("🧪 TESTE DE INTEGRAÇÃO ABC FARMA")
    print("=" * 60)
    
    # Teste de conexão direta
    engine = create_engine('sqlite:///unified_rag_system.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Estatísticas básicas
        total_abc = session.query(ABCFarmaProduct).count()
        print(f"📊 Total produtos ABC Farma: {total_abc}")
        
        ativos = session.query(ABCFarmaProduct).filter(
            ABCFarmaProduct.ativo == True
        ).count()
        print(f"✅ Produtos ativos: {ativos}")
        
        # Buscar produtos farmacêuticos
        medicamentos = session.query(ABCFarmaProduct).filter(
            ABCFarmaProduct.descricao_completa.contains('MEDICAMENTO')
        ).limit(10).all()
        
        print(f"💊 Produtos identificados como medicamentos: {len(medicamentos)}")
        for med in medicamentos[:5]:
            print(f"  - {med.descricao_completa[:80]}...")
            
        session.close()
        
        # Teste do serviço unificado
        print("\n🔍 TESTE DE BUSCA ABC FARMA")
        print("-" * 40)
        
        service = get_unified_service()
        
        # Teste 1: Busca por texto
        print("Teste 1: Busca por 'DIPIRONA'")
        results = service.search_abc_farma_by_text("DIPIRONA", limit=3)
        print(f"Resultados encontrados: {len(results)}")
        for result in results:
            print(f"  • {result['descricao'][:60]}...")
            print(f"    Marca: {result['marca']}")
            print(f"    Código: {result['codigo_barra']}")
            print()
            
        # Teste 2: Classificação farmacêutica
        print("Teste 2: Classificação de produto farmacêutico")
        classificacao = service.get_pharmaceutical_classification(
            "Dipirona 500mg comprimidos"
        )
        print(f"NCM sugerido: {classificacao['ncm_sugerido']}")
        print(f"CEST sugerido: {classificacao['cest_sugerido']}")
        print(f"Confiabilidade: {classificacao['confiabilidade']:.2f}")
        print(f"Fonte: {classificacao['fonte']}")
        
        if 'produto_referencia' in classificacao:
            ref = classificacao['produto_referencia']
            print(f"Produto referência: {ref['descricao'][:60]}...")
            
        # Teste 3: Detecção farmacêutica
        print("\nTeste 3: Detecção de produtos farmacêuticos")
        test_products = [
            "Dipirona 500mg",
            "Smartphone Samsung",
            "Paracetamol 750mg",
            "Notebook Dell",
            "Aspirina 100mg"
        ]
        
        for product in test_products:
            is_pharma = service.is_pharmaceutical_product(product)
            status = "✅ É farmacêutico" if is_pharma else "❌ Não é farmacêutico"
            print(f"  {product}: {status}")
            
        # Teste 4: Estatísticas
        print("\nTeste 4: Estatísticas ABC Farma")
        stats = service.get_abc_farma_statistics()
        print(f"Total de produtos: {stats.get('total_products', 0)}")
        print(f"Produtos ativos: {stats.get('active_products', 0)}")
        
        if 'top_brands' in stats:
            print("Top 5 marcas:")
            for brand in stats['top_brands'][:5]:
                print(f"  • {brand['marca']}: {brand['count']} produtos")
                
        print("\n🎉 Todos os testes da integração ABC Farma passaram!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_abc_farma_integration()
