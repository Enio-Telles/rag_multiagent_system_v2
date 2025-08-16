#!/usr/bin/env python3
"""
src/main.py
Ponto de entrada principal do Sistema de Classificação Fiscal Agêntico

Comandos disponíveis:
- ingest: Executa a ingestão e vetorização da base de conhecimento
- classify: Classifica produtos da base de dados 
- test-mapping: Testa o banco de mapeamento estruturado
- test-rag: Testa o sistema de busca semântica
"""

import sys
import argparse
import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from config import Config
from orchestrator.hybrid_router import HybridRouter

def command_ingest(args):
    """Executa o processo de ingestão e vetorização."""
    print("🚀 COMANDO: INGEST")
    print("=" * 60)
    
    router = HybridRouter()
    success = router.ingest_knowledge()
    
    if success:
        print("\n✅ INGESTÃO CONCLUÍDA COM SUCESSO!")
        print("📁 Arquivos gerados:")
        print(f"   - Índice FAISS: {router.config.FAISS_INDEX_FILE}")
        print(f"   - Metadados: {router.config.METADATA_DB_FILE}")
    else:
        print("\n❌ FALHA NA INGESTÃO!")
        return 1
    
    return 0

def command_classify(args):
    """Executa a classificação de produtos."""
    print("🎯 COMANDO: CLASSIFY")
    print("=" * 60)
    
    router = HybridRouter()
    
    # Opções de fonte de dados
    if args.from_db or args.from_db_postgresql:
        force_postgresql = getattr(args, 'from_db_postgresql', False)
        db_type = "PostgreSQL" if force_postgresql else "base de dados (com fallback)"
        print(f"📊 Carregando produtos da {db_type}...")
        
        try:
            produtos_df = router.data_loader.load_produtos_from_db(force_postgresql=force_postgresql)
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return 1
        
        # Limitar quantidade se especificado
        if args.limit:
            produtos_df = produtos_df.head(args.limit)
            print(f"📋 Limitando a {args.limit} produtos para teste.")
        
        produtos = produtos_df.to_dict('records')
        
    elif args.from_file:
        print(f"📁 Carregando produtos do arquivo: {args.from_file}")
        try:
            with open(args.from_file, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar arquivo: {e}")
            return 1
            
    else:
        # Produtos de exemplo para teste
        produtos = [
            {"produto_id": 1, "descricao_produto": "Refrigerante Coca-Cola 350ml lata", "codigo_produto": "COCA350"},
            {"produto_id": 2, "descricao_produto": "Smartphone Samsung Galaxy A54 128GB", "codigo_produto": "GALAXY54"},
            {"produto_id": 3, "descricao_produto": "Parafuso de aço inoxidável M6 x 20mm", "codigo_produto": "PAR-M6-20"}
        ]
        print("🧪 Usando produtos de exemplo para teste.")
    
    print(f"📦 Classificando {len(produtos)} produtos...")
    
    # Executar classificação
    resultados = router.classify_products(produtos)
    
    # Salvar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = router.config.PROCESSED_DATA_DIR / f"classificacao_{timestamp}.json"
    
    # Garantir que o diretório existe
    router.config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    # Criar também versão CSV para análise
    csv_file = output_file.with_suffix('.csv')
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_csv(csv_file, index=False, encoding='utf-8')
    
    # Estatísticas
    print(f"\n📊 ESTATÍSTICAS DA CLASSIFICAÇÃO:")
    print("=" * 60)
    
    total = len(resultados)
    com_ncm = sum(1 for r in resultados if r.get('ncm_classificado', '00000000') != '00000000')
    com_cest = sum(1 for r in resultados if r.get('cest_classificado'))
    
    # Converter confiança para float para comparação segura
    def get_confianca_float(resultado):
        confianca = resultado.get('confianca_consolidada', 0)
        try:
            return float(confianca) if confianca is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    confianca_alta = sum(1 for r in resultados if get_confianca_float(r) > 0.7)
    
    print(f"📋 Total de produtos: {total}")
    print(f"🎯 Com NCM válido: {com_ncm} ({com_ncm/total*100:.1f}%)")
    print(f"📊 Com CEST: {com_cest} ({com_cest/total*100:.1f}%)")
    print(f"✅ Alta confiança (>0.7): {confianca_alta} ({confianca_alta/total*100:.1f}%)")
    
    print(f"\n💾 Resultados salvos:")
    print(f"   - JSON: {output_file}")
    print(f"   - CSV: {csv_file}")
    
    # Mostrar alguns exemplos
    print(f"\n🎯 EXEMPLOS DE CLASSIFICAÇÃO:")
    print("=" * 60)
    
    for i, resultado in enumerate(resultados[:3]):
        print(f"{i+1}. {resultado.get('descricao_produto', 'N/A')}")
        print(f"   NCM: {resultado.get('ncm_classificado', 'N/A')}")
        print(f"   CEST: {resultado.get('cest_classificado', 'Nenhum')}")
        print(f"   Confiança: {resultado.get('confianca_consolidada', 0):.2f}")
        print(f"   Grupo: {resultado.get('grupo_id', 'N/A')} | Representante: {resultado.get('eh_representante', False)}")
        print()
    
    return 0

def command_test_mapping(args):
    """Executa teste do banco de mapeamento."""
    print("🧪 COMANDO: TEST-MAPPING")
    print("=" * 60)
    
    # Importar e executar o teste
    try:
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        from test_mapping import MappingTester
        
        tester = MappingTester()
        success = tester.run_comprehensive_test()
        
        return 0 if success else 1
        
    except ImportError as e:
        print(f"❌ Erro ao importar teste de mapeamento: {e}")
        return 1

def command_test_rag(args):
    """Executa teste do sistema RAG."""
    print("🧪 COMANDO: TEST-RAG")
    print("=" * 60)
    
    config = Config()
    
    # Verificar se os arquivos necessários existem
    if not config.FAISS_INDEX_FILE.exists():
        print("❌ Índice FAISS não encontrado. Execute 'python main.py ingest' primeiro.")
        return 1
    
    if not config.METADATA_DB_FILE.exists():
        print("❌ Base de metadados não encontrada. Execute 'python main.py ingest' primeiro.")
        return 1
    
    try:
        from vectorstore.faiss_store import FaissMetadataStore
        
        # Inicializar vector store
        print("📚 Inicializando sistema RAG...")
        vector_store = FaissMetadataStore(config.VECTOR_DIMENSION)
        vector_store.load_index(str(config.FAISS_INDEX_FILE))
        vector_store.initialize_metadata_db(str(config.METADATA_DB_FILE))
        
        print("✅ Sistema RAG carregado com sucesso!")
        
        # ========================================================================
        # TESTE 1: BUSCA SEMÂNTICA GERAL
        # ========================================================================
        print(f"\n🔍 TESTE 1: BUSCA SEMÂNTICA GERAL")
        print("=" * 60)
        
        queries_teste = [
            "refrigerante de cola",
            "parafusos de metal",
            "smartphone celular",
            "água mineral",
            "café torrado"
        ]
        
        for query in queries_teste:
            print(f"\n🎯 Busca: '{query}'")
            results = vector_store.search(query, k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    ncm = metadata.get('ncm', 'N/A')
                    score = result['score']
                    text = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                    
                    print(f"   {i}. NCM {ncm} | Score: {score:.3f}")
                    print(f"      {text}")
            else:
                print(f"   ❌ Nenhum resultado encontrado para '{query}'")
        
        # ========================================================================
        # TESTE 2: BUSCA HÍBRIDA FILTRADA
        # ========================================================================
        print(f"\n🎯 TESTE 2: BUSCA HÍBRIDA FILTRADA")
        print("=" * 60)
        
        # Teste com filtro de NCM específico
        test_cases = [
            ("refrigerante", {"ncm": "22021000"}),  # Águas, incluindo águas minerais
            ("café", {"ncm": "09011100"}),  # Café não torrado, não descafeinado
            ("telefone", {"ncm": "85171200"}),  # Telefones para redes celulares
            ("parafuso", {"ncm": "73181500"})   # Parafusos de ferro ou aço
        ]
        
        for query, metadata_filter in test_cases:
            print(f"\n🔍 Busca: '{query}' | Filtro: {metadata_filter}")
            
            # Busca sem filtro
            results_sem_filtro = vector_store.search(query, k=5)
            
            # Busca com filtro
            results_com_filtro = vector_store.search(query, k=5, metadata_filter=metadata_filter)
            
            print(f"   📊 Resultados sem filtro: {len(results_sem_filtro)}")
            print(f"   📊 Resultados com filtro: {len(results_com_filtro)}")
            
            if results_com_filtro:
                print("   🎯 Top 2 resultados filtrados:")
                for i, result in enumerate(results_com_filtro[:2], 1):
                    metadata = result['metadata']
                    score = result['score']
                    text = result['text'][:80] + "..." if len(result['text']) > 80 else result['text']
                    print(f"      {i}. Score: {score:.3f} | {text}")
            else:
                print(f"   ⚠️ Nenhum resultado encontrado com filtro {metadata_filter}")
        
        # ========================================================================
        # TESTE 3: ANÁLISE DE COBERTURA DO ÍNDICE
        # ========================================================================
        print(f"\n📊 TESTE 3: ANÁLISE DE COBERTURA")
        print("=" * 60)
        
        # Buscar estatísticas do banco de metadados
        import sqlite3
        conn = sqlite3.connect(str(config.METADATA_DB_FILE))
        cursor = conn.cursor()
        
        # Total de chunks
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        
        # NCMs únicos
        cursor.execute("""
            SELECT COUNT(DISTINCT json_extract(metadata, '$.ncm')) 
            FROM chunks 
            WHERE json_extract(metadata, '$.ncm') IS NOT NULL
        """)
        ncms_unicos = cursor.fetchone()[0]
        
        # Produtos com GTIN
        cursor.execute("""
            SELECT COUNT(*) 
            FROM chunks 
            WHERE json_extract(metadata, '$.codigo_barra') IS NOT NULL 
            AND json_extract(metadata, '$.codigo_barra') != ''
        """)
        produtos_com_gtin = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   📦 Total de chunks indexados: {total_chunks:,}")
        print(f"   🎯 NCMs únicos representados: {ncms_unicos:,}")
        print(f"   🏷️ Produtos com GTIN: {produtos_com_gtin:,}")
        print(f"   📊 Cobertura GTIN: {produtos_com_gtin/total_chunks*100:.1f}%")
        
        print(f"\n✅ TESTE RAG CONCLUÍDO COM SUCESSO!")
        return 0
        
    except Exception as e:
        print(f"❌ ERRO no teste RAG: {e}")
        import traceback
        traceback.print_exc()
        return 1

def create_directory_structure():
    """Cria a estrutura de diretórios necessária."""
    config = Config()
    
    directories = [
        config.DATA_DIR,
        config.RAW_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.KNOWLEDGE_BASE_DIR,
        config.FEEDBACK_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("📁 Estrutura de diretórios criada/verificada.")

def command_setup_review(args):
    """Configura o sistema de revisão humana (Fase 4)."""
    print("👥 COMANDO: SETUP-REVIEW")
    print("=" * 60)
    
    try:
        # Determinar quais ações executar
        do_create = args.create_tables or args.force_recreate
        do_import = args.import_data
        do_start_api = args.start_api

        # Se nenhum argumento específico for fornecido, executar todas as ações
        is_default_run = not (do_create or do_import or do_start_api)
        
        if is_default_run:
            print("ℹ️ Nenhum argumento específico fornecido. Executando fluxo padrão: create-tables -> import-data -> start-api")
            do_create = True
            do_import = True
            do_start_api = True

        if do_create:
            from database.connection import create_tables, test_connection
            from database.models import Base
            from database.connection import engine
            
            if not test_connection():
                print("❌ Erro: Não foi possível conectar ao banco de dados")
                return 1
            
            if args.force_recreate:
                print("⚠️  ATENÇÃO: Dropando todas as tabelas existentes...")
                print("   Isso irá apagar todos os dados existentes!")
                confirmacao = input("   Digite 'CONFIRMO' para continuar: ")
                
                if confirmacao != 'CONFIRMO':
                    print("❌ Operação cancelada pelo usuário.")
                    return 1
                
                print("🗑️ Dropando tabelas existentes...")
                Base.metadata.drop_all(bind=engine)
                print("✅ Tabelas dropadas com sucesso!")
            
            print("🔧 Criando tabelas do banco de dados...")
            create_tables()
            print("✅ Tabelas criadas com sucesso!")
        
        if do_import:
            print("📥 Importando classificações existentes...")
            from database.connection import SessionLocal
            from feedback.review_service import ReviewService
            import glob
            
            # Buscar arquivos JSON de classificação
            # Determinar o diretório correto baseado na localização do script
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data" / "processed"
            pattern = str(data_dir / "classificacao_*.json")
            json_files = glob.glob(pattern)
            
            if json_files:
                arquivo_mais_recente = max(json_files, key=lambda f: Path(f).stat().st_mtime)
                print(f"📂 Importando: {Path(arquivo_mais_recente).name}")
                
                review_service = ReviewService()
                db = SessionLocal()
                
                try:
                    resultado = review_service.importar_classificacoes_json(
                        db=db,
                        caminho_arquivo=arquivo_mais_recente
                    )
                    
                    print(f"✅ Importação concluída!")
                    print(f"   📊 Total: {resultado['total']}")
                    print(f"   ✅ Importadas: {resultado['importadas']}")
                    print(f"   ❌ Erros: {resultado['erros']}")
                    
                finally:
                    db.close()
            else:
                print("⚠️ Nenhum arquivo de classificação encontrado")
        
        if do_start_api:
            print("🚀 Iniciando API de revisão...")
            try:
                import uvicorn
                
                logger.info("API iniciada em http://localhost:8000")
                logger.info("Documentação disponível em http://localhost:8000/api/docs")
                logger.info("Pressione Ctrl+C para parar")
                
                # Usar string de import para habilitar reload
                uvicorn.run("api.review_api:app", host="0.0.0.0", port=8000, reload=True)
                
            except KeyboardInterrupt:
                print("\n👋 API encerrada pelo usuário")
            except ImportError:
                print("❌ Erro: FastAPI/Uvicorn não instalados")
                print("   Execute: pip install fastapi uvicorn")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro na configuração de revisão: {e}")
        return 1

def command_golden_set(args):
    """Gerencia o Golden Set (Fase 5)."""
    print("🏆 COMANDO: GOLDEN-SET")
    print("=" * 60)
    
    try:
        from database.connection import SessionLocal, test_connection
        from feedback.continuous_learning import ContinuousLearningScheduler, GoldenSetManager
        from database.models import GoldenSetEntry
        
        if not test_connection():
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return 1
        
        config = Config()
        
        if args.status or not any([args.update, args.force]):
            print("📊 Status do Golden Set:")
            
            db = SessionLocal()
            try:
                total_entradas = db.query(GoldenSetEntry).count()
                nao_retreinadas = db.query(GoldenSetEntry).filter(
                    GoldenSetEntry.incluido_em_retreinamento == False
                ).count()
                
                print(f"   📈 Total de entradas: {total_entradas}")
                print(f"   🆕 Novas (não retreinadas): {nao_retreinadas}")
                
                # Verificar índices
                golden_manager = GoldenSetManager(config)
                if golden_manager.verificar_indice_existe():
                    print("   📂 Índice Golden Set: ✅")
                else:
                    print("   📂 Índice Golden Set: ❌ (não encontrado)")
                
            finally:
                db.close()
        
        if args.update or args.force:
            print("🔄 Atualizando Golden Set...")
            
            scheduler = ContinuousLearningScheduler(config)
            db = SessionLocal()
            
            try:
                resultado = scheduler.executar_retreinamento(db, force=args.force)
                
                if resultado['status'] == 'sucesso':
                    print(f"🎉 Atualização concluída!")
                    print(f"   📊 Total de entradas: {resultado['total_entradas']}")
                    print(f"   📂 Índice salvo em: {resultado['caminho_indice']}")
                else:
                    print(f"ℹ️ {resultado.get('message', 'Atualização não necessária')}")
                
            finally:
                db.close()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro no Golden Set: {e}")
        return 1

def command_test_phases(args):
    """Testa as fases 4 e 5 completas."""
    print("🧪 COMANDO: TEST-PHASES")
    print("=" * 60)
    
    try:
        # Importar o script de teste
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from test_fases_4_5 import main as test_main
        
        success = test_main()
        
        if success:
            print("\n🎉 TODOS OS TESTES DAS FASES 4 E 5 PASSARAM!")
            return 0
        else:
            print("\n⚠️ Alguns testes falharam")
            return 1
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return 1

def main():
    """Função principal com parser de argumentos."""
    parser = argparse.ArgumentParser(
        description="Sistema de Classificação Fiscal Agêntico",
        epilog="""
Exemplos de uso:
  python main.py ingest                            # Processar e vetorizar base de conhecimento
  python main.py classify --from-db --limit 100   # Classificar 100 produtos da BD (com fallback SQLite)
  python main.py classify --from-db-postgresql --limit 100  # Classificar 100 produtos diretamente do PostgreSQL
  python main.py classify --from-file produtos.json        # Classificar produtos de arquivo
  python main.py test-mapping                      # Testar banco de mapeamento NCM
  python main.py test-rag                          # Testar sistema de busca semântica
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando ingest
    parser_ingest = subparsers.add_parser('ingest', help='Processar e vetorizar base de conhecimento')
    
    # Comando classify
    parser_classify = subparsers.add_parser('classify', help='Classificar produtos com NCM/CEST')
    classify_group = parser_classify.add_mutually_exclusive_group()
    classify_group.add_argument('--from-db', action='store_true', 
                                help='Carregar produtos da base de dados (com fallback SQLite)')
    classify_group.add_argument('--from-db-postgresql', action='store_true', 
                                help='Carregar produtos diretamente do PostgreSQL (força conexão)')
    classify_group.add_argument('--from-file', type=str, metavar='ARQUIVO',
                                help='Carregar produtos de arquivo JSON')
    parser_classify.add_argument('--limit', type=int, metavar='N',
                                help='Limitar processamento a N produtos (apenas --from-db/--from-db-postgresql)')
    
    # Comando test-mapping
    parser_test_mapping = subparsers.add_parser('test-mapping', 
                                               help='Testar banco de mapeamento estruturado')
    
    # Comando test-rag
    parser_test_rag = subparsers.add_parser('test-rag', 
                                          help='Testar sistema de busca semântica')
    
    # Comandos das Fases 4 e 5
    parser_setup_review = subparsers.add_parser('setup-review', 
                                               help='Configurar sistema de revisão humana (Fase 4)')
    parser_setup_review.add_argument('--create-tables', action='store_true',
                                    help='Criar tabelas no banco de dados')
    parser_setup_review.add_argument('--force-recreate', action='store_true',
                                    help='Dropar e recriar todas as tabelas (cuidado: apaga dados!)')
    parser_setup_review.add_argument('--import-data', action='store_true',
                                    help='Importar classificações existentes')
    parser_setup_review.add_argument('--start-api', action='store_true',
                                    help='Iniciar API de revisão')
    
    parser_golden_set = subparsers.add_parser('golden-set',
                                            help='Gerenciar Golden Set (Fase 5)')
    parser_golden_set.add_argument('--update', action='store_true',
                                  help='Atualizar índice Golden Set')
    parser_golden_set.add_argument('--force', action='store_true',
                                  help='Forçar atualização mesmo com poucas entradas')
    parser_golden_set.add_argument('--status', action='store_true',
                                  help='Verificar status do Golden Set')
    
    parser_test_phases = subparsers.add_parser('test-phases',
                                             help='Testar fases 4 e 5 completas')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Criar estrutura de diretórios
    create_directory_structure()
    
    # Executar comando
    try:
        if args.command == 'ingest':
            return command_ingest(args)
        elif args.command == 'classify':
            return command_classify(args)
        elif args.command == 'test-mapping':
            return command_test_mapping(args)
        elif args.command == 'test-rag':
            return command_test_rag(args)
        elif args.command == 'setup-review':
            return command_setup_review(args)
        elif args.command == 'golden-set':
            return command_golden_set(args)
        elif args.command == 'test-phases':
            return command_test_phases(args)
        else:
            print(f"❌ Comando desconhecido: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏸️ Operação interrompida pelo usuário.")
        return 1
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())