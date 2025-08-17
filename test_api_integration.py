"""
Teste de Integração das APIs com Sistema SQLite Unificado
Verifica se todas as APIs funcionam corretamente com o banco unificado
"""

import sys
import requests
import json
import time
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.append('src')

from services.unified_sqlite_service import get_unified_service

def test_unified_service():
    """Testa o serviço unificado diretamente"""
    print("🔍 TESTE 1: Serviço SQLite Unificado")
    print("-" * 50)
    
    try:
        # Inicializar serviço
        unified_service = get_unified_service("data/unified_rag_system.db")
        
        # Teste 1: Contar registros
        counts = unified_service.contar_registros()
        print(f"✅ Contadores obtidos: {len(counts)} tabelas")
        for tabela, count in counts.items():
            print(f"   - {tabela}: {count:,}")
        
        # Teste 2: Buscar NCMs
        ncms = unified_service.buscar_ncms_por_nivel(2, 5)
        print(f"✅ NCMs encontrados: {len(ncms)}")
        
        # Teste 3: Buscar CESTs
        if ncms:
            codigo_ncm = ncms[0]['codigo_ncm']
            cests = unified_service.buscar_cests_para_ncm(codigo_ncm)
            print(f"✅ CESTs para NCM {codigo_ncm}: {len(cests)}")
        
        # Teste 4: Dashboard stats
        stats = unified_service.get_dashboard_stats()
        print(f"✅ Dashboard stats obtidas: {len(stats)} métricas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do serviço: {e}")
        return False

def test_api_endpoints():
    """Testa os endpoints das APIs"""
    print("\n🌐 TESTE 2: Endpoints das APIs")
    print("-" * 50)
    
    # URLs base das APIs
    api_urls = {
        'unified': 'http://localhost:8000',
        'review': 'http://localhost:8001'
    }
    
    results = {}
    
    for api_name, base_url in api_urls.items():
        print(f"\n🔍 Testando API {api_name.upper()} ({base_url})")
        
        endpoints_to_test = []
        
        if api_name == 'unified':
            endpoints_to_test = [
                '/api/v1/sistema/health',
                '/api/v1/sistema/status',
                '/api/v1/ncm/buscar?nivel=2&limite=5',
                '/api/v1/dashboard/stats'
            ]
        else:  # review API
            endpoints_to_test = [
                '/api/health',
                '/api/sistema/status',
                '/api/classificacoes/pendentes?limite=5'
            ]
        
        api_results = []
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint}"
                start_time = time.time()
                
                response = requests.get(url, timeout=10)
                tempo_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {endpoint} - {tempo_ms}ms - {response.status_code}")
                    api_results.append({'endpoint': endpoint, 'status': 'OK', 'tempo_ms': tempo_ms})
                else:
                    print(f"   ⚠️  {endpoint} - {response.status_code}")
                    api_results.append({'endpoint': endpoint, 'status': f'HTTP {response.status_code}'})
                    
            except requests.exceptions.ConnectionError:
                print(f"   ❌ {endpoint} - Conexão falhou (API não está rodando?)")
                api_results.append({'endpoint': endpoint, 'status': 'CONEXAO_FALHOU'})
            except Exception as e:
                print(f"   ❌ {endpoint} - Erro: {e}")
                api_results.append({'endpoint': endpoint, 'status': f'ERRO: {e}'})
        
        results[api_name] = api_results
    
    return results

def test_integration_workflow():
    """Testa fluxo completo de integração"""
    print("\n🔄 TESTE 3: Fluxo de Integração Completo")
    print("-" * 50)
    
    try:
        unified_service = get_unified_service("data/unified_rag_system.db")
        
        # Teste 1: Criar classificação
        print("📝 Criando classificação de teste...")
        produto_data = {
            'produto_id': 99999,
            'descricao_produto': 'Produto de teste integração API',
            'descricao_completa': 'Teste completo de integração das APIs',
            'codigo_produto': 'TEST-API-001',
            'ncm_sugerido': '85171231',
            'cest_sugerido': '2104700',
            'confianca_sugerida': 0.95,
            'justificativa_sistema': 'Teste de integração automático',
            'data_classificacao': datetime.now()
        }
        
        classificacao_id = unified_service.criar_classificacao(produto_data)
        print(f"✅ Classificação criada: ID {classificacao_id}")
        
        # Teste 2: Buscar classificação
        classificacao = unified_service.buscar_classificacao_por_id(classificacao_id)
        print(f"✅ Classificação recuperada: {classificacao['descricao_produto']}")
        
        # Teste 3: Aplicar revisão
        dados_revisao = {
            'status_revisao': 'APROVADO',
            'revisado_por': 'TESTE_AUTOMATICO',
            'justificativa_correcao': 'Aprovado automaticamente para teste',
            'data_revisao': datetime.now()
        }
        
        sucesso_revisao = unified_service.revisar_classificacao(classificacao_id, dados_revisao)
        print(f"✅ Revisão aplicada: {sucesso_revisao}")
        
        # Teste 4: Adicionar explicação
        explicacao_data = {
            'produto_id': 99999,
            'classificacao_id': classificacao_id,
            'agente_nome': 'test_agent',
            'explicacao_detalhada': 'Explicação de teste para integração',
            'nivel_confianca': 0.95,
            'tempo_processamento_ms': 50,
            'rag_consultado': True,
            'golden_set_utilizado': False,
            'data_explicacao': datetime.now()
        }
        
        explicacao_id = unified_service.salvar_explicacao_agente(explicacao_data)
        print(f"✅ Explicação salva: ID {explicacao_id}")
        
        # Teste 5: Registrar consulta
        consulta_data = {
            'agente_nome': 'test_agent',
            'produto_id': 99999,
            'tipo_consulta': 'TEST_INTEGRATION',
            'query_original': 'teste de integração',
            'total_resultados_encontrados': 5,
            'tempo_consulta_ms': 25,
            'consulta_bem_sucedida': True,
            'data_consulta': datetime.now()
        }
        
        consulta_id = unified_service.registrar_consulta_agente(consulta_data)
        print(f"✅ Consulta registrada: ID {consulta_id}")
        
        # Teste 6: Registrar interação web
        interacao_data = {
            'sessao_usuario': 'TEST_SESSION',
            'tipo_interacao': 'TESTE_INTEGRACAO',
            'endpoint_acessado': '/test/integration',
            'metodo_http': 'POST',
            'dados_entrada': {'teste': 'integração'},
            'dados_saida': {'resultado': 'sucesso'},
            'tempo_processamento_ms': 100,
            'sucesso': True,
            'codigo_resposta': 200,
            'data_interacao': datetime.now()
        }
        
        unified_service.registrar_interacao_web(interacao_data)
        print(f"✅ Interação web registrada")
        
        print(f"\n🎉 FLUXO DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no fluxo de integração: {e}")
        return False

def test_performance():
    """Testa performance do sistema integrado"""
    print("\n⚡ TESTE 4: Performance do Sistema")
    print("-" * 50)
    
    try:
        unified_service = get_unified_service("data/unified_rag_system.db")
        
        # Teste de múltiplas consultas
        operacoes = [
            ('Buscar NCMs nível 2', lambda: unified_service.buscar_ncms_por_nivel(2, 10)),
            ('Buscar NCMs nível 4', lambda: unified_service.buscar_ncms_por_nivel(4, 10)),
            ('Dashboard stats', lambda: unified_service.get_dashboard_stats()),
            ('Contar registros', lambda: unified_service.contar_registros()),
            ('Buscar pendentes', lambda: unified_service.buscar_classificacoes_pendentes(10))
        ]
        
        tempos = []
        for nome, operacao in operacoes:
            start_time = time.time()
            resultado = operacao()
            tempo_ms = int((time.time() - start_time) * 1000)
            tempos.append(tempo_ms)
            
            print(f"   ⏱️  {nome}: {tempo_ms}ms")
        
        tempo_medio = sum(tempos) / len(tempos)
        print(f"\n📊 Performance Summary:")
        print(f"   - Tempo médio: {tempo_medio:.1f}ms")
        print(f"   - Tempo máximo: {max(tempos)}ms")
        print(f"   - Tempo mínimo: {min(tempos)}ms")
        print(f"   - Status: {'EXCELENTE' if tempo_medio < 50 else 'BOM' if tempo_medio < 200 else 'LENTO'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False

def generate_report(results):
    """Gera relatório dos testes"""
    print("\n📋 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_data = {
        'timestamp': timestamp,
        'data_execucao': datetime.now().isoformat(),
        'resultados': results,
        'resumo': {
            'total_testes': len(results),
            'testes_aprovados': sum(1 for r in results.values() if r),
            'testes_falharam': sum(1 for r in results.values() if not r)
        }
    }
    
    # Salvar relatório
    report_file = f"relatorio_teste_integracao_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"📁 Relatório salvo: {report_file}")
    
    # Exibir resumo
    resumo = report_data['resumo']
    print(f"✅ Testes aprovados: {resumo['testes_aprovados']}")
    print(f"❌ Testes falharam: {resumo['testes_falharam']}")
    
    sucesso_total = resumo['testes_falharam'] == 0
    print(f"\n🎯 STATUS GERAL: {'APROVADO' if sucesso_total else 'FALHAS DETECTADAS'}")
    
    return sucesso_total

def main():
    """Executa todos os testes de integração"""
    print("🚀 TESTE DE INTEGRAÇÃO - APIs com SQLite Unificado")
    print("=" * 60)
    print(f"📅 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Executar testes
    results = {}
    
    results['servico_unificado'] = test_unified_service()
    results['endpoints_api'] = test_api_endpoints()
    results['fluxo_integracao'] = test_integration_workflow()
    results['performance'] = test_performance()
    
    # Gerar relatório
    sucesso_geral = generate_report(results)
    
    print(f"\n🏁 Teste concluído: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if sucesso_geral else 1

if __name__ == "__main__":
    sys.exit(main())
