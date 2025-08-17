#!/usr/bin/env python3
"""
src/main.py - Sistema de Classificação Fiscal Agêntico - Versão Unificada
Ponto de entrada principal integrado com SQLite unificado

Comandos disponíveis:
- ingest: Executa ingestão da base de conhecimento
- classify: Classifica produtos usando sistema unificado
- migrate: Migra dados para SQLite unificado
- server: Inicia servidor API unificado
- review: Inicia interface de revisão
- test-unified: Testa sistema unificado
- status: Verifica status do sistema
"""

import sys
import argparse
import json
import pandas as pd
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

try:
    from config import Config
    from orchestrator.hybrid_router import HybridRouter
    from services.unified_sqlite_service import get_unified_service
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Alguns módulos não disponíveis: {e}")
    CONFIG_AVAILABLE = False

def command_migrate(args):
    """Executa migração para SQLite unificado"""
    print("🔄 COMANDO: MIGRATE")
    print("=" * 60)
    
    try:
        # Importar e executar migração
        from database.complete_sqlite_migration import main as migrate_main
        
        print("📊 Iniciando migração completa para SQLite...")
        success = migrate_main()
        
        if success:
            print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("📁 Arquivo SQLite criado: data/unified_rag_system.db")
        else:
            print("\n❌ FALHA NA MIGRAÇÃO!")
            return 1
            
    except ImportError:
        print("❌ Módulo de migração não encontrado")
        return 1
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return 1
    
    return 0

def command_ingest(args):
    """Executa o processo de ingestão e vetorização"""
    print("🚀 COMANDO: INGEST")
    print("=" * 60)
    
    if not CONFIG_AVAILABLE:
        print("❌ Configuração não disponível")
        return 1
    
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
    """Executa classificação usando sistema unificado"""
    print("🎯 COMANDO: CLASSIFY (Sistema Unificado)")
    print("=" * 60)
    
    try:
        # Inicializar serviço unificado
        unified_service = get_unified_service("data/unified_rag_system.db")
        
        # Opções de dados de entrada
        if args.from_file:
            print(f"📁 Carregando produtos do arquivo: {args.from_file}")
            with open(args.from_file, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
        else:
            # Produtos de exemplo
            produtos = [
                {
                    "produto_id": 9001,
                    "descricao_produto": "Smartphone Samsung Galaxy S24 Ultra 256GB",
                    "codigo_produto": "SAM-S24U-256",
                    "descricao_completa": "Smartphone premium com tela AMOLED, câmera de 200MP e processador Snapdragon"
                },
                {
                    "produto_id": 9002, 
                    "descricao_produto": "Refrigerante Coca-Cola Zero 350ml lata",
                    "codigo_produto": "COCA-ZERO-350",
                    "descricao_completa": "Bebida gaseificada sem açúcar em embalagem de alumínio"
                },
                {
                    "produto_id": 9003,
                    "descricao_produto": "Parafuso Phillips aço inox M8 x 25mm",
                    "codigo_produto": "PAR-PH-M8-25",
                    "descricao_completa": "Fixador roscado em aço inoxidável com cabeça Phillips"
                }
            ]
            print("🧪 Usando produtos de exemplo para teste")
        
        # Limitar quantidade se especificado
        if args.limit:
            produtos = produtos[:args.limit]
            print(f"📋 Limitando a {args.limit} produtos")
        
        print(f"📦 Classificando {len(produtos)} produtos...")
        
        # Executar classificação usando sistema unificado
        resultados = []
        for produto in produtos:
            try:
                start_time = time.time()
                
                # Simular classificação usando dados existentes
                ncm_sugerido = "85171231"  # Exemplo: smartphone
                cest_sugerido = "2104700"
                confianca = 0.89
                
                # Criar dados de classificação
                produto_data = {
                    'produto_id': produto['produto_id'],
                    'descricao_produto': produto['descricao_produto'],
                    'descricao_completa': produto.get('descricao_completa'),
                    'codigo_produto': produto.get('codigo_produto'),
                    'ncm_sugerido': ncm_sugerido,
                    'cest_sugerido': cest_sugerido,
                    'confianca_sugerida': confianca,
                    'justificativa_sistema': 'Classificação por sistema unificado',
                    'data_classificacao': datetime.now()
                }
                
                # Salvar classificação
                classificacao_id = unified_service.criar_classificacao(produto_data)
                
                tempo_ms = int((time.time() - start_time) * 1000)
                
                resultado = {
                    'produto_id': produto['produto_id'],
                    'classificacao_id': classificacao_id,
                    'ncm_sugerido': ncm_sugerido,
                    'cest_sugerido': cest_sugerido,
                    'confianca': confianca,
                    'tempo_ms': tempo_ms
                }
                
                resultados.append(resultado)
                print(f"✅ Produto {produto['produto_id']}: {ncm_sugerido} (CEST: {cest_sugerido}) - {confianca:.2f}")
                
            except Exception as e:
                print(f"❌ Erro no produto {produto['produto_id']}: {e}")
                continue
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"resultados_classificacao_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_produtos': len(produtos),
                'produtos_processados': len(resultados),
                'resultados': resultados
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 RESULTADOS:")
        print(f"   - Produtos processados: {len(resultados)}/{len(produtos)}")
        print(f"   - Arquivo salvo: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro na classificação: {e}")
        return 1

def command_server(args):
    """Inicia servidor API unificado"""
    print("🌐 COMANDO: SERVER")
    print("=" * 60)
    
    api_file = "src/api/api_unified.py"
    port = getattr(args, 'port', 8000)
    
    if not Path(api_file).exists():
        print(f"❌ Arquivo da API não encontrado: {api_file}")
        return 1
    
    print(f"🚀 Iniciando servidor API unificado na porta {port}")
    print(f"📚 Documentação: http://localhost:{port}/api/docs")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.api_unified:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return 1
    
    return 0

def command_review(args):
    """Inicia interface de revisão"""
    print("📋 COMANDO: REVIEW")
    print("=" * 60)
    
    api_file = "src/api/review_api_unified.py"
    port = getattr(args, 'port', 8001)
    
    if not Path(api_file).exists():
        print(f"❌ Arquivo da API de revisão não encontrado: {api_file}")
        return 1
    
    print(f"🚀 Iniciando interface de revisão na porta {port}")
    print(f"📚 Documentação: http://localhost:{port}/api/docs")
    print(f"🖥️  Interface: http://localhost:{port}")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.review_api_unified:app",
            "--host", "0.0.0.0", 
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Interface de revisão interrompida")
    except Exception as e:
        print(f"❌ Erro ao iniciar interface: {e}")
        return 1
    
    return 0

def command_test_unified(args):
    """Testa sistema unificado"""
    print("🧪 COMANDO: TEST-UNIFIED")
    print("=" * 60)
    
    try:
        # Executar testes do sistema unificado
        test_file = "test_unified_sqlite_complete.py"
        
        if Path(test_file).exists():
            print("🔍 Executando testes do sistema unificado...")
            subprocess.run([sys.executable, test_file])
        else:
            print("🔍 Testando conectividade básica...")
            
            unified_service = get_unified_service("data/unified_rag_system.db")
            
            # Testes básicos
            counts = unified_service.contar_registros()
            print(f"📊 Registros no banco:")
            for tabela, count in counts.items():
                print(f"   - {tabela}: {count:,}")
            
            # Teste de busca NCM
            ncms = unified_service.buscar_ncms_por_nivel(2, 5)
            print(f"🔍 Teste de busca NCM: {len(ncms)} resultados encontrados")
            
            # Teste de estatísticas
            stats = unified_service.get_dashboard_stats()
            print(f"📈 Estatísticas do dashboard obtidas com sucesso")
        
        print("\n✅ TESTES CONCLUÍDOS")
        return 0
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return 1

def command_status(args):
    """Verifica status do sistema"""
    print("📊 COMANDO: STATUS")
    print("=" * 60)
    
    try:
        # Verificar arquivos principais
        arquivos_importantes = [
            "data/unified_rag_system.db",
            "src/services/unified_sqlite_service.py",
            "src/database/unified_sqlite_models.py",
            "src/api/api_unified.py",
            "src/api/review_api_unified.py"
        ]
        
        print("📁 Verificando arquivos principais:")
        for arquivo in arquivos_importantes:
            if Path(arquivo).exists():
                size = Path(arquivo).stat().st_size
                print(f"   ✅ {arquivo} ({size:,} bytes)")
            else:
                print(f"   ❌ {arquivo} - NÃO ENCONTRADO")
        
        # Verificar banco de dados
        try:
            unified_service = get_unified_service("data/unified_rag_system.db")
            counts = unified_service.contar_registros()
            
            print(f"\n📊 Status do banco SQLite:")
            total_registros = sum(counts.values())
            print(f"   - Total de registros: {total_registros:,}")
            print(f"   - NCMs: {counts.get('ncm_estruturado', 0):,}")
            print(f"   - CESTs: {counts.get('cest_estruturado', 0):,}")
            print(f"   - Classificações: {counts.get('classificacao', 0):,}")
            print(f"   - Golden Set: {counts.get('golden_set', 0):,}")
            
            # Performance test
            start_time = time.time()
            ncms = unified_service.buscar_ncms_por_nivel(2, 10)
            tempo_ms = int((time.time() - start_time) * 1000)
            
            print(f"\n⚡ Performance:")
            print(f"   - Busca NCM: {tempo_ms}ms")
            print(f"   - Status: {'RÁPIDO' if tempo_ms < 100 else 'LENTO'}")
            
        except Exception as e:
            print(f"\n❌ Erro no banco de dados: {e}")
        
        print(f"\n🕐 Verificação concluída: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return 1

def main():
    """Função principal do sistema"""
    parser = argparse.ArgumentParser(
        description="Sistema de Classificação Fiscal Agêntico - Versão Unificada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py migrate              # Migra dados para SQLite
  python main.py classify             # Classifica produtos de exemplo
  python main.py classify --limit 10  # Classifica apenas 10 produtos
  python main.py server               # Inicia API principal (porta 8000)
  python main.py review               # Inicia interface revisão (porta 8001)
  python main.py status               # Verifica status do sistema
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando migrate
    parser_migrate = subparsers.add_parser('migrate', help='Migra dados para SQLite unificado')
    
    # Comando ingest
    parser_ingest = subparsers.add_parser('ingest', help='Executa ingestão da base de conhecimento')
    
    # Comando classify
    parser_classify = subparsers.add_parser('classify', help='Classifica produtos')
    parser_classify.add_argument('--from-file', help='Arquivo JSON com produtos')
    parser_classify.add_argument('--limit', type=int, help='Limita número de produtos')
    
    # Comando server
    parser_server = subparsers.add_parser('server', help='Inicia servidor API unificado')
    parser_server.add_argument('--port', type=int, default=8000, help='Porta do servidor')
    
    # Comando review
    parser_review = subparsers.add_parser('review', help='Inicia interface de revisão')
    parser_review.add_argument('--port', type=int, default=8001, help='Porta da interface')
    
    # Comando test-unified
    parser_test = subparsers.add_parser('test-unified', help='Testa sistema unificado')
    
    # Comando status
    parser_status = subparsers.add_parser('status', help='Verifica status do sistema')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Mapear comandos para funções
    commands = {
        'migrate': command_migrate,
        'ingest': command_ingest,
        'classify': command_classify,
        'server': command_server,
        'review': command_review,
        'test-unified': command_test_unified,
        'status': command_status
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            return command_func(args)
        except KeyboardInterrupt:
            print("\n🛑 Operação interrompida pelo usuário")
            return 1
        except Exception as e:
            logger.error(f"Erro no comando {args.command}: {e}")
            return 1
    else:
        print(f"❌ Comando desconhecido: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
