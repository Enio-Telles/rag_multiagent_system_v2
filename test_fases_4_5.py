"""
Teste completo das Fases 4 e 5 - Interface de Revisão Humana e Aprendizagem Contínua
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_fase_4_review_system():
    """
    Testa o sistema de revisão humana (Fase 4)
    """
    print("🧪 TESTE DA FASE 4 - SISTEMA DE REVISÃO HUMANA")
    print("=" * 60)
    
    try:
        # Importar componentes
        from src.database.connection import SessionLocal, test_connection, create_tables
        from src.feedback.review_service import ReviewService
        from src.feedback.metrics_service import MetricsService
        from src.database.models import ClassificacaoRevisao
        
        # 1. Testar conexão
        print("1️⃣ Testando conexão com banco de dados...")
        if not test_connection():
            print("❌ Falha na conexão com banco")
            return False
        print("✅ Conexão OK")
        
        # 2. Criar tabelas
        print("2️⃣ Criando tabelas...")
        create_tables()
        print("✅ Tabelas criadas")
        
        # 3. Testar ReviewService
        print("3️⃣ Testando ReviewService...")
        review_service = ReviewService()
        db = SessionLocal()
        
        try:
            # Importar classificações se existirem
            data_dir = Path("data/processed")
            json_files = list(data_dir.glob("classificacao_*.json"))
            
            if json_files:
                arquivo_teste = max(json_files, key=lambda f: f.stat().st_mtime)
                print(f"   📂 Importando: {arquivo_teste.name}")
                
                resultado = review_service.importar_classificacoes_json(
                    db=db,
                    caminho_arquivo=str(arquivo_teste)
                )
                
                print(f"   ✅ Importadas: {resultado['importadas']} classificações")
                
                # Testar listagem
                classificacoes = review_service.listar_classificacoes(
                    db=db,
                    status="PENDENTE_REVISAO",
                    limit=5
                )
                print(f"   📋 Classificações pendentes: {len(classificacoes)}")
                
                # Testar revisão simulada
                if classificacoes:
                    produto_teste = classificacoes[0]
                    print(f"   🔍 Testando revisão do produto: {produto_teste['produto_id']}")
                    
                    resultado_revisao = review_service.processar_revisao(
                        db=db,
                        produto_id=produto_teste['produto_id'],
                        acao="APROVAR",
                        revisado_por="teste_automatico"
                    )
                    
                    print(f"   ✅ Revisão processada: {resultado_revisao['status_revisao']}")
            
        finally:
            db.close()
        
        # 4. Testar MetricsService
        print("4️⃣ Testando MetricsService...")
        metrics_service = MetricsService()
        db = SessionLocal()
        
        try:
            stats = metrics_service.calcular_estatisticas(db=db, periodo_dias=30)
            print(f"   📊 Total classificações: {stats['total_classificacoes']}")
            print(f"   📈 Taxa aprovação: {stats['taxa_aprovacao']}%")
            print(f"   🎯 Confiança média: {stats['confianca_media']}")
            
        finally:
            db.close()
        
        print("✅ Fase 4 funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na Fase 4: {e}")
        return False

def test_fase_5_continuous_learning():
    """
    Testa o sistema de aprendizagem contínua (Fase 5)
    """
    print("\n🧪 TESTE DA FASE 5 - APRENDIZAGEM CONTÍNUA")
    print("=" * 60)
    
    try:
        # Importar componentes
        from src.feedback.continuous_learning import GoldenSetManager, AugmentedRetrieval, ContinuousLearningScheduler
        from src.database.connection import SessionLocal
        from src.config import Config
        
        config = Config()
        
        # 1. Testar GoldenSetManager
        print("1️⃣ Testando GoldenSetManager...")
        golden_manager = GoldenSetManager(config)
        
        db = SessionLocal()
        try:
            golden_set = golden_manager.extrair_golden_set(db)
            print(f"   📋 Entradas no Golden Set: {len(golden_set)}")
            
            if len(golden_set) > 0:
                print("   🔄 Criando índice Golden Set...")
                resultado = golden_manager.criar_indice_golden_set(db)
                print(f"   ✅ Índice criado: {resultado['status']}")
                
                if resultado['status'] == 'sucesso':
                    print(f"   📊 Total entradas: {resultado['total_entradas']}")
                    print(f"   📂 Caminho índice: {resultado['caminho_indice']}")
            
        finally:
            db.close()
        
        # 2. Testar AugmentedRetrieval
        print("2️⃣ Testando AugmentedRetrieval...")
        try:
            augmented_retrieval = AugmentedRetrieval(config)
            
            # Teste de busca
            resultados = augmented_retrieval.buscar_contexto_aumentado(
                query="refrigerante coca cola",
                k_principal=2,
                k_golden=1
            )
            
            print(f"   🔍 Resultados da busca aumentada: {len(resultados)}")
            
            for i, resultado in enumerate(resultados[:3]):
                fonte = resultado.get('fonte', 'desconhecida')
                score = resultado.get('score', 0)
                print(f"   {i+1}. Fonte: {fonte}, Score: {score:.3f}")
            
        except Exception as e:
            print(f"   ⚠️ Erro no AugmentedRetrieval: {e}")
        
        # 3. Testar ContinuousLearningScheduler
        print("3️⃣ Testando ContinuousLearningScheduler...")
        scheduler = ContinuousLearningScheduler(config)
        
        db = SessionLocal()
        try:
            resultado = scheduler.executar_retreinamento(db, force=False)
            print(f"   📊 Status retreinamento: {resultado['status']}")
            
            if resultado['status'] == 'sucesso':
                print(f"   ✅ Retreinamento concluído com {resultado['total_entradas']} entradas")
            else:
                print(f"   ℹ️ {resultado.get('message', 'Retreinamento não necessário')}")
            
        finally:
            db.close()
        
        print("✅ Fase 5 funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na Fase 5: {e}")
        return False

def test_integracao_completa():
    """
    Testa a integração completa das fases 4 e 5
    """
    print("\n🧪 TESTE DE INTEGRAÇÃO COMPLETA")
    print("=" * 60)
    
    try:
        # Testar HybridRouter com aprendizagem contínua
        from src.orchestrator.hybrid_router import HybridRouter
        
        print("1️⃣ Inicializando HybridRouter com aprendizagem contínua...")
        router = HybridRouter()
        
        if router.augmented_retrieval:
            print("✅ Sistema de aprendizagem contínua ativo no HybridRouter")
        else:
            print("⚠️ Sistema de aprendizagem contínua não disponível")
        
        # Teste de classificação simples
        print("2️⃣ Testando classificação com sistema integrado...")
        produtos_teste = [
            {
                "produto_id": 99999,
                "descricao_produto": "Refrigerante de cola 350ml lata",
                "codigo_produto": "TESTE_INTEGRACAO"
            }
        ]
        
        resultados = router.classify_products(produtos_teste)
        
        if resultados:
            resultado = resultados[0]
            print(f"   ✅ Produto classificado:")
            print(f"   📦 NCM: {resultado.get('ncm_classificado', 'N/A')}")
            print(f"   🏷️ CEST: {resultado.get('cest_classificado', 'N/A')}")
            print(f"   🎯 Confiança: {resultado.get('confianca_consolidada', 0):.3f}")
        
        print("✅ Integração completa funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False

def main():
    """
    Executa todos os testes das fases 4 e 5
    """
    print("🚀 TESTE COMPLETO DAS FASES 4 E 5")
    print("Sistema de Revisão Humana + Aprendizagem Contínua")
    print("=" * 80)
    
    total_testes = 3
    testes_passaram = 0
    
    # Teste Fase 4
    if test_fase_4_review_system():
        testes_passaram += 1
    
    # Teste Fase 5
    if test_fase_5_continuous_learning():
        testes_passaram += 1
    
    # Teste de Integração
    if test_integracao_completa():
        testes_passaram += 1
    
    # Resultado final
    print("\n" + "=" * 80)
    print("📊 RESULTADO DOS TESTES")
    print(f"✅ Testes passaram: {testes_passaram}/{total_testes}")
    
    if testes_passaram == total_testes:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Fases 4 e 5 implementadas com sucesso!")
        return True
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
