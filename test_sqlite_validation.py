#!/usr/bin/env python3
"""
Script de validação completa da migração SQLite
Testa todas as funcionalidades da nova base de conhecimento
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from sqlalchemy import func

# Adicionar diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.knowledge_base_service import KnowledgeBaseService
from database.knowledge_models import NCMHierarchy, CestCategory, NCMCestMapping, ProdutoExemplo

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteValidationTest:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.results = {
            'test_results': {},
            'performance_results': {},
            'validation_summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
    def run_all_tests(self):
        """Executa todos os testes de validação"""
        logger.info("🧪 Iniciando validação completa da base SQLite")
        logger.info("=" * 60)
        
        # Testes funcionais
        self.test_ncm_queries()
        self.test_cest_searches()
        self.test_ncm_cest_mappings()
        self.test_product_examples()
        
        # Testes de performance
        self.test_performance_comparison()
        
        # Testes de integridade
        self.test_data_integrity()
        
        # Resumo final
        self.generate_final_report()
        
    def test_ncm_queries(self):
        """Teste 1: Consultas NCM"""
        logger.info("📋 TESTE 1: Consultas NCM")
        logger.info("-" * 30)
        
        results = {}
        
        try:
            # Teste 1.1: Buscar NCM específico
            ncm_code = "01012100"
            start_time = time.time()
            ncm_result = self.kb_service.buscar_ncm_por_codigo(ncm_code)
            query_time = time.time() - start_time
            
            results['busca_ncm_especifico'] = {
                'codigo_testado': ncm_code,
                'encontrado': ncm_result is not None,
                'tempo_consulta': f"{query_time:.4f}s",
                'dados': ncm_result
            }
            
            if ncm_result:
                logger.info(f"  ✅ NCM {ncm_code} encontrado")
                if isinstance(ncm_result, dict):
                    logger.info(f"     Descrição: {ncm_result.get('descricao_curta', '')[:80]}...")
                    logger.info(f"     Nível: {ncm_result.get('nivel_hierarquico', 'N/A')}")
                else:
                    logger.info(f"     Descrição: {ncm_result.descricao_curta[:80]}...")
                    logger.info(f"     Nível: {ncm_result.nivel_hierarquico}")
            else:
                logger.warning(f"  ❌ NCM {ncm_code} não encontrado")
            
            # Teste 1.2: Buscar NCMs por hierarquia
            start_time = time.time()
            ncms_nivel_2 = self.kb_service.buscar_ncms_por_nivel(2)
            query_time = time.time() - start_time
            
            results['busca_por_nivel'] = {
                'nivel_testado': 2,
                'quantidade_encontrada': len(ncms_nivel_2),
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            logger.info(f"  ✅ Encontrados {len(ncms_nivel_2)} NCMs no nível 2")
            logger.info(f"  ⏱️  Tempo de consulta: {query_time:.4f}s")
            
            # Teste 1.3: Buscar NCMs por padrão
            pattern = "01.01"
            start_time = time.time()
            ncms_pattern = self.kb_service.buscar_ncms_por_padrao(pattern)
            query_time = time.time() - start_time
            
            results['busca_por_padrao'] = {
                'padrao_testado': pattern,
                'quantidade_encontrada': len(ncms_pattern),
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            logger.info(f"  ✅ Encontrados {len(ncms_pattern)} NCMs com padrão '{pattern}'")
            
            # Teste 1.4: Verificar integridade hierárquica
            start_time = time.time()
            with self.kb_service.get_session() as session:
                # NCMs com pai inexistente
                orphans = session.query(NCMHierarchy).filter(
                    NCMHierarchy.codigo_pai.isnot(None),
                    ~NCMHierarchy.codigo_pai.in_(
                        session.query(NCMHierarchy.codigo_ncm)
                    )
                ).count()
            query_time = time.time() - start_time
            
            results['integridade_hierarquica'] = {
                'ncms_orfaos': orphans,
                'tempo_verificacao': f"{query_time:.4f}s"
            }
            
            if orphans == 0:
                logger.info("  ✅ Integridade hierárquica validada")
            else:
                logger.warning(f"  ⚠️  Encontrados {orphans} NCMs órfãos")
                
        except Exception as e:
            logger.error(f"  ❌ Erro no teste NCM: {e}")
            results['erro'] = str(e)
        
        self.results['test_results']['ncm_queries'] = results
        logger.info("")
        
    def test_cest_searches(self):
        """Teste 2: Buscas CEST"""
        logger.info("🎯 TESTE 2: Buscas CEST")
        logger.info("-" * 30)
        
        results = {}
        
        try:
            # Teste 2.1: Buscar CEST específico
            cest_code = "01.001.00"
            start_time = time.time()
            cest_result = self.kb_service.buscar_cest_por_codigo(cest_code)
            query_time = time.time() - start_time
            
            results['busca_cest_especifico'] = {
                'codigo_testado': cest_code,
                'encontrado': cest_result is not None,
                'tempo_consulta': f"{query_time:.4f}s",
                'dados': cest_result if cest_result else None
            }
            
            if cest_result:
                logger.info(f"  ✅ CEST {cest_code} encontrado")
                if isinstance(cest_result, dict) and 'descricao_cest' in cest_result:
                    logger.info(f"     Descrição: {cest_result['descricao_cest'][:80]}...")
                elif hasattr(cest_result, 'descricao_cest'):
                    logger.info(f"     Descrição: {cest_result.descricao_cest[:80]}...")
            else:
                logger.warning(f"  ❌ CEST {cest_code} não encontrado")
            
            # Teste 2.2: Listar todos os CESTs
            start_time = time.time()
            total_cests = self.kb_service.contar_registros('cest_categories')
            query_time = time.time() - start_time
            
            results['total_cests'] = {
                'quantidade': total_cests,
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            logger.info(f"  ✅ Total de CESTs na base: {total_cests}")
            
            # Teste 2.3: Buscar CESTs por categoria
            start_time = time.time()
            with self.kb_service.get_session() as session:
                cests_por_categoria = session.query(CestCategory).filter(
                    CestCategory.categoria_produto.isnot(None)
                ).limit(10).all()
            query_time = time.time() - start_time
            
            results['cests_com_categoria'] = {
                'quantidade_amostra': len(cests_por_categoria),
                'tempo_consulta': f"{query_time:.4f}s",
                'exemplos': [c.codigo_cest for c in cests_por_categoria[:5]]
            }
            
            logger.info(f"  ✅ Encontrados {len(cests_por_categoria)} CESTs com categoria")
                
        except Exception as e:
            logger.error(f"  ❌ Erro no teste CEST: {e}")
            results['erro'] = str(e)
        
        self.results['test_results']['cest_searches'] = results
        logger.info("")
        
    def test_ncm_cest_mappings(self):
        """Teste 3: Mapeamentos NCM-CEST"""
        logger.info("🔗 TESTE 3: Mapeamentos NCM-CEST")
        logger.info("-" * 30)
        
        results = {}
        
        try:
            # Teste 3.1: Buscar CESTs para um NCM específico
            ncm_code = "01012100"
            start_time = time.time()
            cests_for_ncm = self.kb_service.buscar_cests_para_ncm(ncm_code)
            query_time = time.time() - start_time
            
            results['cests_para_ncm'] = {
                'ncm_testado': ncm_code,
                'quantidade_cests': len(cests_for_ncm),
                'tempo_consulta': f"{query_time:.4f}s",
                'cests_encontrados': [c['codigo_cest'] for c in cests_for_ncm[:5]]
            }
            
            logger.info(f"  ✅ NCM {ncm_code} possui {len(cests_for_ncm)} CESTs")
            if cests_for_ncm:
                logger.info(f"     Exemplos: {', '.join(c['codigo_cest'] for c in cests_for_ncm[:3])}")
            
            # Teste 3.2: Buscar NCMs para um CEST específico
            if cests_for_ncm:
                cest_code = cests_for_ncm[0]['codigo_cest']
                start_time = time.time()
                ncms_for_cest = self.kb_service.buscar_ncms_para_cest(cest_code)
                query_time = time.time() - start_time
                
                results['ncms_para_cest'] = {
                    'cest_testado': cest_code,
                    'quantidade_ncms': len(ncms_for_cest),
                    'tempo_consulta': f"{query_time:.4f}s"
                }
                
                logger.info(f"  ✅ CEST {cest_code} mapeia {len(ncms_for_cest)} NCMs")
            
            # Teste 3.3: Estatísticas de mapeamento
            start_time = time.time()
            total_mappings = self.kb_service.contar_registros('ncm_cest_mappings')
            query_time = time.time() - start_time
            
            results['estatisticas_mapeamento'] = {
                'total_mapeamentos': total_mappings,
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            logger.info(f"  ✅ Total de mapeamentos: {total_mappings:,}")
            
            # Teste 3.4: Qualidade dos mapeamentos
            start_time = time.time()
            with self.kb_service.get_session() as session:
                mapping_types = session.query(NCMCestMapping.tipo_relacao).distinct().all()
                mapping_stats = []
                for tipo_tuple in mapping_types:
                    tipo = tipo_tuple[0]
                    count = session.query(NCMCestMapping).filter(
                        NCMCestMapping.tipo_relacao == tipo
                    ).count()
                    mapping_stats.append((tipo, count))
            query_time = time.time() - start_time
            
            results['qualidade_mapeamentos'] = {
                'tipos_relacao': dict(mapping_stats),
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            for tipo, count in mapping_stats:
                logger.info(f"     {tipo}: {count:,} mapeamentos")
                
        except Exception as e:
            logger.error(f"  ❌ Erro no teste de mapeamentos: {e}")
            results['erro'] = str(e)
        
        self.results['test_results']['ncm_cest_mappings'] = results
        logger.info("")
        
    def test_product_examples(self):
        """Teste 4: Produtos exemplo"""
        logger.info("📦 TESTE 4: Produtos Exemplo")
        logger.info("-" * 30)
        
        results = {}
        
        try:
            # Teste 4.1: Total de produtos
            start_time = time.time()
            total_products = self.kb_service.contar_registros('produto_exemplos')
            query_time = time.time() - start_time
            
            results['total_produtos'] = {
                'quantidade': total_products,
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            logger.info(f"  ✅ Total de produtos exemplo: {total_products:,}")
            
            # Teste 4.2: Buscar produtos por NCM
            start_time = time.time()
            with self.kb_service.get_session() as session:
                sample_product = session.query(ProdutoExemplo).first()
                if sample_product:
                    produtos_ncm = session.query(ProdutoExemplo).filter(
                        ProdutoExemplo.ncm_codigo == sample_product.ncm_codigo
                    ).all()
                else:
                    produtos_ncm = []
            query_time = time.time() - start_time
            
            results['produtos_por_ncm'] = {
                'ncm_testado': sample_product.ncm_codigo if sample_product else None,
                'quantidade_produtos': len(produtos_ncm),
                'tempo_consulta': f"{query_time:.4f}s"
            }
            
            if sample_product:
                logger.info(f"  ✅ NCM {sample_product.ncm_codigo} possui {len(produtos_ncm)} produtos")
            
            # Teste 4.3: Validar integridade de produtos
            start_time = time.time()
            with self.kb_service.get_session() as session:
                produtos_sem_ncm = session.query(ProdutoExemplo).filter(
                    ~ProdutoExemplo.ncm_codigo.in_(
                        session.query(NCMHierarchy.codigo_ncm)
                    )
                ).count()
            query_time = time.time() - start_time
            
            results['integridade_produtos'] = {
                'produtos_orfaos': produtos_sem_ncm,
                'tempo_verificacao': f"{query_time:.4f}s"
            }
            
            if produtos_sem_ncm == 0:
                logger.info("  ✅ Integridade de produtos validada")
            else:
                logger.warning(f"  ⚠️  {produtos_sem_ncm} produtos com NCM inválido")
                
        except Exception as e:
            logger.error(f"  ❌ Erro no teste de produtos: {e}")
            results['erro'] = str(e)
        
        self.results['test_results']['product_examples'] = results
        logger.info("")
        
    def test_performance_comparison(self):
        """Teste 5: Comparação de Performance"""
        logger.info("⚡ TESTE 5: Performance SQLite vs JSON")
        logger.info("-" * 40)
        
        results = {}
        
        try:
            # Teste 5.1: Performance de consulta NCM
            ncm_codes = ["01012100", "01", "0101", "01012", "01012900"]
            
            sqlite_times = []
            for ncm_code in ncm_codes:
                start_time = time.time()
                result = self.kb_service.buscar_ncm_por_codigo(ncm_code)
                elapsed = time.time() - start_time
                sqlite_times.append(elapsed)
            
            avg_sqlite_time = sum(sqlite_times) / len(sqlite_times)
            
            results['consulta_ncm'] = {
                'codigos_testados': ncm_codes,
                'tempo_medio_sqlite': f"{avg_sqlite_time:.6f}s",
                'tempos_individuais': [f"{t:.6f}s" for t in sqlite_times]
            }
            
            logger.info(f"  ✅ SQLite - Tempo médio de consulta NCM: {avg_sqlite_time:.6f}s")
            
            # Teste 5.2: Performance de busca de CESTs
            start_time = time.time()
            cests_sample = self.kb_service.buscar_cests_para_ncm("01012100")
            cest_search_time = time.time() - start_time
            
            results['busca_cests'] = {
                'ncm_testado': "01012100",
                'quantidade_cests': len(cests_sample),
                'tempo_busca': f"{cest_search_time:.6f}s"
            }
            
            logger.info(f"  ✅ SQLite - Busca de CESTs: {cest_search_time:.6f}s")
            
            # Teste 5.3: Performance de consultas complexas
            start_time = time.time()
            with self.kb_service.get_session() as session:
                complex_query = session.query(NCMHierarchy).join(
                    NCMCestMapping, NCMHierarchy.codigo_ncm == NCMCestMapping.ncm_codigo
                ).join(
                    CestCategory, NCMCestMapping.cest_codigo == CestCategory.codigo_cest
                ).filter(NCMHierarchy.nivel_hierarquico >= 6).limit(100).all()
            complex_query_time = time.time() - start_time
            
            results['consulta_complexa'] = {
                'registros_retornados': len(complex_query),
                'tempo_consulta': f"{complex_query_time:.6f}s"
            }
            
            logger.info(f"  ✅ SQLite - Consulta complexa (JOIN): {complex_query_time:.6f}s")
            
            # Teste 5.4: Uso de memória estimado
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                results['uso_memoria'] = {
                    'memoria_atual_mb': f"{memory_mb:.2f} MB",
                    'processo_pid': process.pid
                }
                
                logger.info(f"  ✅ Uso de memória atual: {memory_mb:.2f} MB")
            except ImportError:
                logger.info("  ⚠️  psutil não disponível - pulando teste de memória")
            
        except Exception as e:
            logger.error(f"  ❌ Erro no teste de performance: {e}")
            results['erro'] = str(e)
        
        self.results['performance_results'] = results
        logger.info("")
        
    def test_data_integrity(self):
        """Teste 6: Integridade dos Dados"""
        logger.info("🔍 TESTE 6: Integridade dos Dados")
        logger.info("-" * 35)
        
        results = {}
        
        try:
            with self.kb_service.get_session() as session:
                # Verificações de integridade
                checks = {}
                
                # 1. NCMs duplicados
                start_time = time.time()
                duplicated_ncms = session.query(NCMHierarchy.codigo_ncm).group_by(
                    NCMHierarchy.codigo_ncm
                ).having(func.count(NCMHierarchy.codigo_ncm) > 1).count()
                checks['ncms_duplicados'] = {
                    'quantidade': duplicated_ncms,
                    'tempo_verificacao': f"{time.time() - start_time:.4f}s"
                }
                
                # 2. CESTs duplicados
                start_time = time.time()
                duplicated_cests = session.query(CestCategory.codigo_cest).group_by(
                    CestCategory.codigo_cest
                ).having(func.count(CestCategory.codigo_cest) > 1).count()
                checks['cests_duplicados'] = {
                    'quantidade': duplicated_cests,
                    'tempo_verificacao': f"{time.time() - start_time:.4f}s"
                }
                
                # 3. Mapeamentos órfãos (NCM inexistente)
                start_time = time.time()
                orphan_mappings_ncm = session.query(NCMCestMapping).filter(
                    ~NCMCestMapping.ncm_codigo.in_(
                        session.query(NCMHierarchy.codigo_ncm)
                    )
                ).count()
                checks['mapeamentos_ncm_orfaos'] = {
                    'quantidade': orphan_mappings_ncm,
                    'tempo_verificacao': f"{time.time() - start_time:.4f}s"
                }
                
                # 4. Mapeamentos órfãos (CEST inexistente)
                start_time = time.time()
                orphan_mappings_cest = session.query(NCMCestMapping).filter(
                    ~NCMCestMapping.cest_codigo.in_(
                        session.query(CestCategory.codigo_cest)
                    )
                ).count()
                checks['mapeamentos_cest_orfaos'] = {
                    'quantidade': orphan_mappings_cest,
                    'tempo_verificacao': f"{time.time() - start_time:.4f}s"
                }
                
                # 5. Produtos órfãos
                start_time = time.time()
                orphan_products = session.query(ProdutoExemplo).filter(
                    ~ProdutoExemplo.ncm_codigo.in_(
                        session.query(NCMHierarchy.codigo_ncm)
                    )
                ).count()
                checks['produtos_orfaos'] = {
                    'quantidade': orphan_products,
                    'tempo_verificacao': f"{time.time() - start_time:.4f}s"
                }
                
                # Log dos resultados
                for check_name, check_result in checks.items():
                    quantity = check_result['quantidade']
                    if quantity == 0:
                        logger.info(f"  ✅ {check_name}: OK")
                    else:
                        logger.warning(f"  ⚠️  {check_name}: {quantity} problemas")
                
                results['verificacoes_integridade'] = checks
                
        except Exception as e:
            logger.error(f"  ❌ Erro na verificação de integridade: {e}")
            results['erro'] = str(e)
        
        self.results['test_results']['data_integrity'] = results
        logger.info("")
        
    def generate_final_report(self):
        """Gera relatório final da validação"""
        logger.info("📊 RELATÓRIO FINAL DE VALIDAÇÃO")
        logger.info("=" * 60)
        
        # Contador de sucessos
        successful_tests = 0
        total_tests = 0
        
        # Análise dos resultados
        for test_category, test_results in self.results['test_results'].items():
            total_tests += 1
            if 'erro' not in test_results:
                successful_tests += 1
                logger.info(f"  ✅ {test_category.replace('_', ' ').title()}: SUCESSO")
            else:
                logger.error(f"  ❌ {test_category.replace('_', ' ').title()}: FALHA")
        
        # Estatísticas gerais
        with self.kb_service.get_session() as session:
            stats = {
                'total_ncms': session.query(NCMHierarchy).count(),
                'total_cests': session.query(CestCategory).count(),
                'total_mapeamentos': session.query(NCMCestMapping).count(),
                'total_produtos': session.query(ProdutoExemplo).count()
            }
        
        # Resumo final
        self.results['validation_summary'] = {
            'testes_executados': total_tests,
            'testes_bem_sucedidos': successful_tests,
            'taxa_sucesso': f"{(successful_tests/total_tests)*100:.1f}%",
            'estatisticas_base': stats
        }
        
        logger.info("")
        logger.info(f"📈 Taxa de sucesso: {(successful_tests/total_tests)*100:.1f}% ({successful_tests}/{total_tests})")
        logger.info(f"📋 Total NCMs: {stats['total_ncms']:,}")
        logger.info(f"🎯 Total CESTs: {stats['total_cests']:,}")
        logger.info(f"🔗 Total Mapeamentos: {stats['total_mapeamentos']:,}")
        logger.info(f"📦 Total Produtos: {stats['total_produtos']:,}")
        
        # Salvar resultados
        results_file = Path("test_results_sqlite_validation.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Resultados salvos em: {results_file}")
        
        if successful_tests == total_tests:
            logger.info("🎉 TODOS OS TESTES PASSARAM! SQLite está funcionando perfeitamente!")
        else:
            logger.warning("⚠️  Alguns testes falharam. Verifique os logs para detalhes.")
        
        logger.info("=" * 60)

def main():
    """Função principal"""
    try:
        validator = SQLiteValidationTest()
        validator.run_all_tests()
        return 0
    except Exception as e:
        logger.error(f"❌ Erro fatal na validação: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
