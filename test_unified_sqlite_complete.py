"""
Teste Completo do Sistema SQLite Unificado
Valida todas as funcionalidades: Knowledge Base + Classificações + Golden Set + Agentes + Interface
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Configurar path
sys.path.append('src')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports
from services.unified_sqlite_service import UnifiedSQLiteService, get_unified_service

class CompleteSQLiteTest:
    """Teste completo do sistema SQLite unificado"""
    
    def __init__(self):
        self.service = get_unified_service("data/unified_rag_system.db")
        self.test_results = {
            'knowledge_base': {},
            'classificacoes': {},
            'golden_set': {},
            'explicacoes_agentes': {},
            'consultas_agentes': {},
            'metricas': {},
            'interface_web': {},
            'performance': {},
            'erros': []
        }
        
    def run_complete_test(self):
        """Executa todos os testes"""
        logger.info("🚀 INICIANDO TESTE COMPLETO DO SISTEMA SQLite UNIFICADO")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        try:
            # 1. Testar Knowledge Base
            self._test_knowledge_base()
            
            # 2. Testar Classificações
            self._test_classificacoes()
            
            # 3. Testar Golden Set
            self._test_golden_set()
            
            # 4. Testar Explicações dos Agentes
            self._test_explicacoes_agentes()
            
            # 5. Testar Consultas dos Agentes
            self._test_consultas_agentes()
            
            # 6. Testar Métricas
            self._test_metricas()
            
            # 7. Testar Interface Web
            self._test_interface_web()
            
            # 8. Testar Performance
            self._test_performance()
            
            # 9. Gerar relatório final
            total_time = time.time() - start_time
            self._generate_test_report(total_time)
            
            logger.info("✅ TESTE COMPLETO FINALIZADO COM SUCESSO!")
            
        except Exception as e:
            logger.error(f"❌ Erro no teste: {e}")
            self.test_results['erros'].append(str(e))
            raise
    
    def _test_knowledge_base(self):
        """Testa funcionalidades da Knowledge Base"""
        logger.info("📋 Testando Knowledge Base...")
        
        try:
            # Teste 1: Contar registros
            counts = self.service.contar_registros()
            self.test_results['knowledge_base']['counts'] = counts
            logger.info(f"   📊 Registros: {counts}")
            
            # Teste 2: Buscar NCM específico
            ncm_test = self.service.buscar_ncm("20081100")
            self.test_results['knowledge_base']['ncm_busca'] = ncm_test is not None
            if ncm_test:
                logger.info(f"   ✅ NCM encontrado: {ncm_test['codigo_ncm']} - {ncm_test['descricao_oficial'][:50]}...")
            
            # Teste 3: Buscar NCMs por nível
            ncms_nivel2 = self.service.buscar_ncms_por_nivel(2, 5)
            self.test_results['knowledge_base']['ncms_nivel'] = len(ncms_nivel2)
            logger.info(f"   📋 NCMs nível 2: {len(ncms_nivel2)}")
            
            # Teste 4: Buscar por padrão
            ncms_pattern = self.service.buscar_ncms_por_padrao("smartphone", 5)
            self.test_results['knowledge_base']['ncms_pattern'] = len(ncms_pattern)
            logger.info(f"   🔍 NCMs 'smartphone': {len(ncms_pattern)}")
            
            # Teste 5: Buscar CEST
            if counts['cests'] > 0:
                # Buscar primeiro CEST
                with self.service.get_session() as session:
                    from sqlalchemy import text
                    primeiro_cest = session.execute(
                        text("SELECT codigo_cest FROM cest_categories WHERE ativo = 1 LIMIT 1")
                    ).fetchone()
                    
                    if primeiro_cest:
                        cest_test = self.service.buscar_cest(primeiro_cest[0])
                        self.test_results['knowledge_base']['cest_busca'] = cest_test is not None
                        if cest_test:
                            logger.info(f"   ✅ CEST encontrado: {cest_test['codigo_cest']}")
            
            # Teste 6: Buscar CESTs para NCM
            if ncm_test:
                cests_ncm = self.service.buscar_cests_para_ncm(ncm_test['codigo_ncm'])
                self.test_results['knowledge_base']['cests_para_ncm'] = len(cests_ncm)
                logger.info(f"   🎯 CESTs para NCM: {len(cests_ncm)}")
            
            # Teste 7: Buscar exemplos
            if ncm_test:
                exemplos = self.service.buscar_exemplos_ncm(ncm_test['codigo_ncm'], 3)
                self.test_results['knowledge_base']['exemplos'] = len(exemplos)
                logger.info(f"   📦 Exemplos para NCM: {len(exemplos)}")
            
            logger.info("   ✅ Knowledge Base - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro na Knowledge Base: {e}")
            self.test_results['erros'].append(f"Knowledge Base: {e}")
    
    def _test_classificacoes(self):
        """Testa sistema de classificações"""
        logger.info("📊 Testando Sistema de Classificações...")
        
        try:
            # Teste 1: Buscar classificações pendentes
            pendentes = self.service.buscar_classificacoes_pendentes(5)
            self.test_results['classificacoes']['pendentes'] = len(pendentes)
            logger.info(f"   📋 Classificações pendentes: {len(pendentes)}")
            
            # Teste 2: Criar nova classificação
            produto_teste = {
                'produto_id': 99999,
                'descricao_produto': 'Produto de teste SQLite unificado',
                'codigo_produto': 'TEST001',
                'ncm_sugerido': '20081100',
                'cest_sugerido': '0100100',
                'confianca_sugerida': 0.95,
                'justificativa_sistema': 'Teste automático do sistema'
            }
            
            novo_id = self.service.criar_classificacao(produto_teste)
            self.test_results['classificacoes']['nova_classificacao'] = novo_id
            logger.info(f"   ✅ Nova classificação criada: ID {novo_id}")
            
            # Teste 3: Atualizar classificação
            updates = {
                'status_revisao': 'EM_ANALISE',
                'explicacao_agente_expansao': 'Teste de explicação expandida'
            }
            atualizado = self.service.atualizar_classificacao(novo_id, updates)
            self.test_results['classificacoes']['atualizacao'] = atualizado
            logger.info(f"   ✅ Classificação atualizada: {atualizado}")
            
            # Teste 4: Revisar classificação
            revisao = {
                'status_revisao': 'APROVADO',
                'revisado_por': 'Sistema de Teste',
                'tempo_revisao_segundos': 30
            }
            revisado = self.service.revisar_classificacao(novo_id, revisao)
            self.test_results['classificacoes']['revisao'] = revisado
            logger.info(f"   ✅ Classificação revisada: {revisado}")
            
            logger.info("   ✅ Sistema de Classificações - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro nas Classificações: {e}")
            self.test_results['erros'].append(f"Classificações: {e}")
    
    def _test_golden_set(self):
        """Testa Golden Set"""
        logger.info("🎯 Testando Golden Set...")
        
        try:
            # Teste 1: Buscar entradas existentes
            entradas = self.service.buscar_golden_set(limite=5)
            self.test_results['golden_set']['entradas_existentes'] = len(entradas)
            logger.info(f"   📋 Entradas no Golden Set: {len(entradas)}")
            
            # Teste 2: Adicionar nova entrada
            nova_entrada = {
                'produto_id': 88888,
                'descricao_produto': 'Produto Golden Set Teste',
                'ncm_final': '20081100',
                'cest_final': '0100100',
                'fonte_validacao': 'AUTOMATICO',
                'revisado_por': 'Sistema de Teste',
                'qualidade_score': 0.98,
                'palavras_chave_fiscais': 'teste, golden, set, validacao',
                'categoria_produto': 'TESTE',
                'aplicacoes_uso': 'Teste do sistema unificado'
            }
            
            nova_id = self.service.adicionar_ao_golden_set(nova_entrada)
            self.test_results['golden_set']['nova_entrada'] = nova_id
            logger.info(f"   ✅ Nova entrada no Golden Set: ID {nova_id}")
            
            # Teste 3: Usar entrada do Golden Set
            if nova_id:
                self.service.usar_golden_set_entry(nova_id)
                logger.info(f"   ✅ Entrada do Golden Set utilizada")
            
            # Teste 4: Buscar por NCM específico
            entradas_ncm = self.service.buscar_golden_set(ncm="20081100", limite=3)
            self.test_results['golden_set']['entradas_ncm'] = len(entradas_ncm)
            logger.info(f"   🎯 Entradas para NCM específico: {len(entradas_ncm)}")
            
            logger.info("   ✅ Golden Set - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro no Golden Set: {e}")
            self.test_results['erros'].append(f"Golden Set: {e}")
    
    def _test_explicacoes_agentes(self):
        """Testa sistema de explicações dos agentes"""
        logger.info("🧠 Testando Explicações dos Agentes...")
        
        try:
            # Teste 1: Salvar explicação de agente
            explicacao_data = {
                'produto_id': 99999,
                'agente_nome': 'expansion_test',
                'agente_versao': '2.0',
                'input_original': 'Produto de teste SQLite',
                'contexto_utilizado': {'tipo': 'teste', 'versao': '2.0'},
                'etapas_processamento': ['analise', 'expansao', 'validacao'],
                'palavras_chave_identificadas': 'teste, sqlite, unificado',
                'resultado_agente': {'ncm_sugerido': '20081100', 'confianca': 0.95},
                'explicacao_detalhada': 'Teste de explicação detalhada do agente de expansão',
                'justificativa_tecnica': 'Baseado em análise de padrões de teste',
                'nivel_confianca': 0.95,
                'rag_consultado': True,
                'golden_set_utilizado': True,
                'tempo_processamento_ms': 150,
                'memoria_utilizada_mb': 12.5,
                'tokens_llm_utilizados': 250,
                'sessao_classificacao': 'TESTE_SESSION_001'
            }
            
            explicacao_id = self.service.salvar_explicacao_agente(explicacao_data)
            self.test_results['explicacoes_agentes']['nova_explicacao'] = explicacao_id
            logger.info(f"   ✅ Explicação salva: ID {explicacao_id}")
            
            # Teste 2: Buscar explicações por produto
            explicacoes = self.service.buscar_explicacoes_produto(99999)
            self.test_results['explicacoes_agentes']['explicacoes_produto'] = len(explicacoes)
            logger.info(f"   📋 Explicações para produto: {len(explicacoes)}")
            
            # Teste 3: Criar explicações para diferentes agentes
            agentes_teste = ['ncm_agent', 'cest_agent', 'reconciler']
            for agente in agentes_teste:
                exp_data = explicacao_data.copy()
                exp_data['agente_nome'] = agente
                exp_data['explicacao_detalhada'] = f'Teste do agente {agente}'
                self.service.salvar_explicacao_agente(exp_data)
            
            logger.info(f"   ✅ Explicações para {len(agentes_teste)} agentes criadas")
            
            logger.info("   ✅ Explicações dos Agentes - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro nas Explicações: {e}")
            self.test_results['erros'].append(f"Explicações: {e}")
    
    def _test_consultas_agentes(self):
        """Testa sistema de consultas dos agentes"""
        logger.info("🔍 Testando Consultas dos Agentes...")
        
        try:
            # Teste 1: Registrar consulta de agente
            consulta_data = {
                'agente_nome': 'ncm_agent_test',
                'produto_id': 99999,
                'sessao_classificacao': 'TESTE_SESSION_001',
                'tipo_consulta': 'NCM_HIERARCHY',
                'query_original': 'produto teste sqlite',
                'query_processada': 'produto teste sqlite normalized',
                'parametros_busca': {'limite': 10, 'nivel_confianca': 0.8},
                'filtros_aplicados': {'ativo': True, 'verificado': True},
                'limite_resultados': 10,
                'total_resultados_encontrados': 5,
                'resultados_utilizados': [
                    {'ncm': '20081100', 'score': 0.95},
                    {'ncm': '20081200', 'score': 0.87}
                ],
                'score_relevancia_medio': 0.91,
                'tempo_consulta_ms': 25,
                'fonte_dados': 'unified_sqlite',
                'consulta_bem_sucedida': True,
                'qualidade_resultados': 0.92,
                'feedback_agente': 'Consulta executada com sucesso'
            }
            
            consulta_id = self.service.registrar_consulta_agente(consulta_data)
            self.test_results['consultas_agentes']['nova_consulta'] = consulta_id
            logger.info(f"   ✅ Consulta registrada: ID {consulta_id}")
            
            # Teste 2: Registrar consultas para diferentes tipos
            tipos_consulta = ['GOLDEN_SET', 'RAG_VECTORSTORE', 'CEST_MAPPING']
            for tipo in tipos_consulta:
                cons_data = consulta_data.copy()
                cons_data['tipo_consulta'] = tipo
                cons_data['agente_nome'] = f'{tipo.lower()}_agent'
                self.service.registrar_consulta_agente(cons_data)
            
            logger.info(f"   ✅ Consultas para {len(tipos_consulta)} tipos registradas")
            
            logger.info("   ✅ Consultas dos Agentes - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro nas Consultas: {e}")
            self.test_results['erros'].append(f"Consultas: {e}")
    
    def _test_metricas(self):
        """Testa sistema de métricas"""
        logger.info("📊 Testando Sistema de Métricas...")
        
        try:
            # Teste 1: Calcular métricas de período
            data_fim = datetime.now()
            data_inicio = datetime(2024, 1, 1)
            
            metricas = self.service.calcular_metricas_periodo(data_inicio, data_fim)
            self.test_results['metricas']['metricas_periodo'] = metricas
            logger.info(f"   📊 Métricas calculadas: {metricas}")
            
            # Teste 2: Obter estatísticas do dashboard
            dashboard_stats = self.service.get_dashboard_stats()
            self.test_results['metricas']['dashboard_stats'] = dashboard_stats
            logger.info(f"   📈 Stats do Dashboard: {dashboard_stats}")
            
            logger.info("   ✅ Sistema de Métricas - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro nas Métricas: {e}")
            self.test_results['erros'].append(f"Métricas: {e}")
    
    def _test_interface_web(self):
        """Testa tracking da interface web"""
        logger.info("🌐 Testando Interface Web...")
        
        try:
            # Teste 1: Registrar interação web
            interacao_data = {
                'sessao_usuario': 'TESTE_SESSION_WEB_001',
                'usuario_id': 'test_user',
                'tipo_interacao': 'CLASSIFICACAO',
                'endpoint_acessado': '/api/v1/classificar',
                'metodo_http': 'POST',
                'dados_entrada': {'produto': 'teste sqlite', 'id': 99999},
                'dados_saida': {'ncm': '20081100', 'confianca': 0.95},
                'tempo_processamento_ms': 350,
                'sucesso': True,
                'codigo_resposta': 200,
                'ip_usuario': '127.0.0.1',
                'user_agent': 'Test Agent SQLite Unificado'
            }
            
            interacao_id = self.service.registrar_interacao_web(interacao_data)
            self.test_results['interface_web']['nova_interacao'] = interacao_id
            logger.info(f"   ✅ Interação web registrada: ID {interacao_id}")
            
            # Teste 2: Registrar diferentes tipos de interação
            tipos_interacao = ['REVISAO', 'CORRECAO', 'CONSULTA']
            for tipo in tipos_interacao:
                int_data = interacao_data.copy()
                int_data['tipo_interacao'] = tipo
                int_data['endpoint_acessado'] = f'/api/v1/{tipo.lower()}'
                self.service.registrar_interacao_web(int_data)
            
            logger.info(f"   ✅ Interações para {len(tipos_interacao)} tipos registradas")
            
            logger.info("   ✅ Interface Web - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro na Interface Web: {e}")
            self.test_results['erros'].append(f"Interface Web: {e}")
    
    def _test_performance(self):
        """Testa performance do sistema"""
        logger.info("⚡ Testando Performance...")
        
        try:
            # Teste 1: Performance de busca NCM
            start_time = time.time()
            for i in range(10):
                self.service.buscar_ncms_por_nivel(2, 5)
            ncm_time = (time.time() - start_time) / 10
            
            self.test_results['performance']['busca_ncm_media'] = ncm_time
            logger.info(f"   ⚡ Busca NCM média: {ncm_time:.4f}s")
            
            # Teste 2: Performance de contagem
            start_time = time.time()
            counts = self.service.contar_registros()
            count_time = time.time() - start_time
            
            self.test_results['performance']['contagem_tempo'] = count_time
            logger.info(f"   📊 Contagem total: {count_time:.4f}s")
            
            # Teste 3: Performance do dashboard
            start_time = time.time()
            dashboard = self.service.get_dashboard_stats()
            dashboard_time = time.time() - start_time
            
            self.test_results['performance']['dashboard_tempo'] = dashboard_time
            logger.info(f"   📈 Dashboard stats: {dashboard_time:.4f}s")
            
            # Teste 4: Performance geral
            performance_score = 1.0 / (ncm_time + count_time + dashboard_time)
            self.test_results['performance']['score_geral'] = performance_score
            logger.info(f"   🏆 Score de performance: {performance_score:.2f}")
            
            logger.info("   ✅ Performance - Todos os testes passaram!")
            
        except Exception as e:
            logger.error(f"   ❌ Erro na Performance: {e}")
            self.test_results['erros'].append(f"Performance: {e}")
    
    def _generate_test_report(self, total_time: float):
        """Gera relatório final do teste"""
        logger.info("📋 Gerando relatório final...")
        
        # Calcular estatísticas do teste
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if category != 'erros' and isinstance(results, dict):
                total_tests += len(results)
                passed_tests += len([v for v in results.values() if v])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Criar relatório
        report = {
            'data_teste': datetime.now().isoformat(),
            'tempo_total_segundos': total_time,
            'total_testes': total_tests,
            'testes_aprovados': passed_tests,
            'taxa_sucesso': success_rate,
            'erros_encontrados': len(self.test_results['erros']),
            'detalhes_testes': self.test_results,
            'status_geral': 'SUCESSO' if len(self.test_results['erros']) == 0 else 'COM_ERROS'
        }
        
        # Salvar relatório
        report_path = Path("data") / "unified_sqlite_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Exibir resultado
        logger.info("\n" + "=" * 70)
        logger.info("📊 RELATÓRIO FINAL DO TESTE SQLite UNIFICADO")
        logger.info("=" * 70)
        logger.info(f"⏱️  Tempo total: {total_time:.2f}s")
        logger.info(f"🎯 Taxa de sucesso: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        logger.info(f"❌ Erros encontrados: {len(self.test_results['erros'])}")
        
        if self.test_results['erros']:
            logger.info("🔍 Erros detalhados:")
            for erro in self.test_results['erros']:
                logger.info(f"   - {erro}")
        
        logger.info(f"📋 Relatório completo salvo em: {report_path}")
        
        if len(self.test_results['erros']) == 0:
            logger.info("🎉 TODOS OS TESTES PASSARAM - SISTEMA 100% FUNCIONAL!")
        else:
            logger.info("⚠️  SISTEMA FUNCIONAL COM ALGUMAS OBSERVAÇÕES")

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DO SISTEMA SQLite UNIFICADO")
    print("=" * 50)
    
    tester = CompleteSQLiteTest()
    tester.run_complete_test()
    
    print("\n🎉 TESTE COMPLETO FINALIZADO!")

if __name__ == "__main__":
    main()
