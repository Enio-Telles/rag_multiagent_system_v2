#!/usr/bin/env python3
"""
Teste da nova funcionalidade de ordenação alfabética
"""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from database.connection import SessionLocal, create_tables
from database.models import EstadoOrdenacao, ClassificacaoRevisao
from feedback.review_service import ReviewService

def test_ordenacao_alfabetica():
    """Testa a nova funcionalidade de ordenação alfabética"""
    
    print("🔄 Criando tabelas (incluindo nova tabela EstadoOrdenacao)...")
    create_tables()
    
    db = SessionLocal()
    review_service = ReviewService()
    
    try:
        # Verificar quantos produtos pendentes existem
        count = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
        ).count()
        
        print(f"📊 Total de produtos pendentes: {count}")
        
        if count == 0:
            print("⚠️ Não há produtos pendentes para testar")
            return
        
        # Verificar estado atual da ordenação
        estado = db.query(EstadoOrdenacao).first()
        if estado:
            print(f"📍 Estado atual: Última letra = '{estado.ultima_letra_usada}', Produto ID = {estado.ultimo_produto_id}")
        else:
            print("📍 Nenhum estado de ordenação encontrado (será criado)")
        
        print("\n🧪 Testando sequência de 5 produtos...")
        
        # Testar sequência de produtos
        for i in range(5):
            print(f"\n--- Teste {i+1} ---")
            
            proximo = review_service.obter_proximo_pendente(db)
            
            if proximo:
                info_ordenacao = proximo.get('_ordenacao_info', {})
                print(f"✅ Produto: {proximo['descricao_produto'][:60]}...")
                print(f"📝 ID: {proximo['produto_id']}")
                print(f"🔤 Letra anterior: '{info_ordenacao.get('letra_anterior', '')}'")
                print(f"🔤 Letra atual: '{info_ordenacao.get('letra_atual', '')}'")
                print(f"🔤 Primeira letra do produto: '{info_ordenacao.get('primeira_letra_produto', '')}'")
            else:
                print("❌ Nenhum produto encontrado")
                break
        
        # Mostrar distribuição por letras
        print("\n📊 Distribuição de produtos por primeira letra:")
        
        produtos = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
        ).all()
        
        import string
        import unicodedata
        
        def primeira_letra_valida(texto):
            if not texto:
                return "?"
            texto_norm = unicodedata.normalize('NFD', texto.upper())
            texto_sem_acento = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
            for char in texto_sem_acento:
                if char in string.ascii_uppercase:
                    return char
            return "?"
        
        distribuicao = {}
        for produto in produtos:
            letra = primeira_letra_valida(produto.descricao_produto)
            distribuicao[letra] = distribuicao.get(letra, 0) + 1
        
        for letra in sorted(distribuicao.keys()):
            print(f"   {letra}: {distribuicao[letra]} produtos")
        
        print(f"\n✅ Teste concluído! Total de letras disponíveis: {len(distribuicao)}")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_ordenacao_alfabetica()
