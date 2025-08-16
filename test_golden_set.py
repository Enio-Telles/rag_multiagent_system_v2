#!/usr/bin/env python3
"""
Teste do sistema Golden Set
"""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from database.connection import SessionLocal, create_tables
from database.models import ClassificacaoRevisao, GoldenSetEntry
from feedback.review_service import ReviewService
from sqlalchemy import func
from datetime import datetime

def test_golden_set():
    """Testa a funcionalidade do Golden Set"""
    
    print("🔄 Criando/verificando tabelas...")
    create_tables()
    
    db = SessionLocal()
    review_service = ReviewService()
    
    try:
        # Verificar se há classificações pendentes
        count_pendentes = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
        ).count()
        
        print(f"📊 Classificações pendentes: {count_pendentes}")
        
        # Verificar se há classificações aprovadas
        count_aprovadas = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.status_revisao == "APROVADO"
        ).count()
        
        print(f"✅ Classificações aprovadas: {count_aprovadas}")
        
        # Verificar entradas no Golden Set
        count_golden = db.query(GoldenSetEntry).count()
        print(f"🏆 Entradas no Golden Set: {count_golden}")
        
        if count_aprovadas == 0:
            # Aprovar uma classificação para teste
            print("\n🧪 Criando uma classificação aprovada para teste...")
            
            primeira_pendente = db.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
            ).first()
            
            if primeira_pendente:
                primeira_pendente.status_revisao = "APROVADO"
                primeira_pendente.revisado_por = "Teste Automático"
                primeira_pendente.data_revisao = datetime.now()
                db.commit()
                
                print(f"✅ Produto {primeira_pendente.produto_id} aprovado para teste")
                
                # Tentar adicionar ao Golden Set
                print("\n🏆 Testando adição ao Golden Set...")
                
                try:
                    resultado = review_service.adicionar_ao_golden_set(
                        db=db,
                        produto_id=primeira_pendente.produto_id,
                        justificativa="Teste automático da funcionalidade",
                        revisado_por="Sistema de Teste"
                    )
                    
                    print(f"✅ Resultado: {resultado}")
                    
                except Exception as e:
                    print(f"❌ Erro ao adicionar ao Golden Set: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Não há classificações pendentes para teste")
        else:
            # Tentar adicionar uma classificação aprovada ao Golden Set
            classificacao_aprovada = db.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == "APROVADO"
            ).first()
            
            if classificacao_aprovada:
                print(f"\n🏆 Testando adição da classificação {classificacao_aprovada.produto_id} ao Golden Set...")
                
                try:
                    resultado = review_service.adicionar_ao_golden_set(
                        db=db,
                        produto_id=classificacao_aprovada.produto_id,
                        justificativa="Teste da funcionalidade Golden Set",
                        revisado_por="Sistema de Teste"
                    )
                    
                    print(f"✅ Resultado: {resultado}")
                    
                except Exception as e:
                    print(f"❌ Erro ao adicionar ao Golden Set: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Verificar entradas no Golden Set após teste
        count_golden_final = db.query(GoldenSetEntry).count()
        print(f"\n📊 Entradas no Golden Set após teste: {count_golden_final}")
        
        if count_golden_final > count_golden:
            print("🎉 Golden Set funcionando corretamente!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_golden_set()
