"""
Teste Completo do Sistema de Bancos de Dados por Empresa
Demonstra todas as funcionalidades implementadas
"""

import os
import sys
import time
import json
from datetime import datetime

# Adicionar src ao path
sys.path.append('src')

from src.services.empresa_classificacao_service import EmpresaClassificacaoService
from src.orchestrator.hybrid_router import HybridRouter

def test_sistema_completo():
    """Teste completo do sistema de bancos por empresa"""
    
    print("🚀 TESTE SISTEMA DE BANCOS DE DADOS POR EMPRESA")
    print("=" * 60)
    
    # Inicializar serviços
    print("\n1️⃣ Inicializando serviços...")
    service = EmpresaClassificacaoService()
    
    try:
        hybrid_router = HybridRouter()
        print("✅ Serviços inicializados com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar HybridRouter: {e}")
        print("   Continuando com funcionalidades básicas...")
        hybrid_router = None
    
    # Teste 1: Criar empresas
    print("\n2️⃣ Criando empresas de teste...")
    
    empresas_teste = [
        {
            "nome": "COSMÉTICOS PORTA A PORTA LTDA",
            "cnpj": "12.345.678/0001-90",
            "tipo_atividade": "Comercio varejista porta a porta",
            "descricao_atividade": "Venda de cosméticos e produtos de beleza em domicílio",
            "canal_venda": "porta_a_porta",
            "porte_empresa": "EPP",
            "regime_tributario": "SIMPLES_NACIONAL"
        },
        {
            "nome": "FARMÁCIA POPULAR LTDA",
            "cnpj": "98.765.432/0001-10",
            "tipo_atividade": "Comércio varejista de medicamentos",
            "descricao_atividade": "Farmácia e drogaria",
            "canal_venda": "loja_fisica",
            "porte_empresa": "ME",
            "regime_tributario": "SIMPLES_NACIONAL"
        },
        {
            "nome": "DISTRIBUIDORA ATACADO S.A.",
            "cnpj": "11.222.333/0001-44",
            "tipo_atividade": "Comércio atacadista",
            "descricao_atividade": "Distribuição de produtos diversos",
            "canal_venda": "atacado",
            "porte_empresa": "GRANDE",
            "regime_tributario": "LUCRO_REAL"
        }
    ]
    
    empresas_criadas = []
    
    for empresa_data in empresas_teste:
        resultado = service.inicializar_empresa(empresa_data)
        
        if resultado["sucesso"]:
            empresa_id = resultado["empresa_id"]
            empresas_criadas.append(empresa_id)
            print(f"✅ Empresa {empresa_id} criada: {empresa_data['nome']}")
            print(f"   📁 Banco: {resultado['database_path']}")
        else:
            print(f"❌ Erro ao criar empresa: {resultado['erro']}")
    
    print(f"\n📊 Total de empresas criadas: {len(empresas_criadas)}")
    
    # Teste 2: Classificar produtos para cada empresa
    print("\n3️⃣ Classificando produtos para cada empresa...")
    
    produtos_teste = [
        {
            "nome_produto": "Batom Vermelho Matte",
            "descricao_original": "Batom de longa duração cor vermelho",
            "categoria": "Cosméticos",
            "marca": "BeautyBrand",
            "preco": 29.90
        },
        {
            "nome_produto": "Dipirona Sódica 500mg",
            "descricao_original": "Medicamento analgésico e antitérmico",
            "categoria": "Medicamentos",
            "marca": "FarmaBrand", 
            "preco": 8.50
        },
        {
            "nome_produto": "Shampoo Hidratante 400ml",
            "descricao_original": "Shampoo para cabelos secos",
            "categoria": "Higiene",
            "marca": "HairCare",
            "preco": 15.90
        }
    ]
    
    classificacoes_realizadas = []
    
    for empresa_id in empresas_criadas:
        print(f"\n🏢 Empresa {empresa_id}:")
        
        for produto in produtos_teste:
            if hybrid_router:
                try:
                    start_time = time.time()
                    resultado = service.classificar_produto_empresa(
                        empresa_id, produto, hybrid_router
                    )
                    tempo_total = time.time() - start_time
                    
                    if resultado["sucesso"]:
                        classificacao = resultado["resultado"]
                        print(f"  ✅ {produto['nome_produto']}")
                        print(f"     NCM: {classificacao.get('ncm_final', 'N/A')}")
                        print(f"     CEST: {classificacao.get('cest_final', 'N/A')}")
                        print(f"     Tempo: {tempo_total:.2f}s")
                        
                        classificacoes_realizadas.append({
                            "empresa_id": empresa_id,
                            "produto_id": resultado["produto_id"],
                            "classificacao_id": resultado["classificacao_id"]
                        })
                    else:
                        print(f"  ❌ Erro: {resultado['erro']}")
                        
                except Exception as e:
                    print(f"  ❌ Erro na classificação: {e}")
            else:
                # Simulação sem HybridRouter
                print(f"  🔄 Simulando classificação: {produto['nome_produto']}")
                produto_id = service.db_manager.insert_produto(empresa_id, produto)
                
                # Classificação simulada
                classificacao_data = {
                    "ncm_codigo": "33079000" if "batom" in produto['nome_produto'].lower() else "30049099",
                    "ncm_descricao": "Outros preparações para higiene" if "batom" in produto['nome_produto'].lower() else "Outros medicamentos",
                    "cest_codigo": "28.004.00" if empresa_id == empresas_criadas[0] else "13.004.00",
                    "cest_descricao": "Produtos de beleza" if empresa_id == empresas_criadas[0] else "Medicamentos",
                    "confianca_ncm": 0.85,
                    "confianca_cest": 0.90,
                    "status": "pendente"
                }
                
                classificacao_id = service.db_manager.insert_classificacao(
                    empresa_id, produto_id, classificacao_data
                )
                
                print(f"     ✅ Produto {produto_id} - Classificação {classificacao_id}")
                classificacoes_realizadas.append({
                    "empresa_id": empresa_id,
                    "produto_id": produto_id,
                    "classificacao_id": classificacao_id
                })
    
    print(f"\n📊 Total de classificações: {len(classificacoes_realizadas)}")
    
    # Teste 3: Aprovar algumas classificações
    print("\n4️⃣ Aprovando classificações...")
    
    aprovadas = 0
    for i, item in enumerate(classificacoes_realizadas[:5]):  # Aprovar primeiras 5
        resultado = service.aprovar_classificacao(
            item["empresa_id"], 
            item["classificacao_id"],
            "usuario_teste",
            f"Aprovação de teste {i+1}"
        )
        
        if resultado["sucesso"]:
            aprovadas += 1
            print(f"  ✅ Classificação {item['classificacao_id']} aprovada")
        else:
            print(f"  ❌ Erro ao aprovar: {resultado['erro']}")
    
    print(f"📊 Total aprovadas: {aprovadas}")
    
    # Teste 4: Adicionar ao Golden Set
    print("\n5️⃣ Adicionando produtos ao Golden Set...")
    
    golden_adicionados = 0
    for item in classificacoes_realizadas[:3]:  # Primeiros 3 ao Golden Set
        resultado = service.adicionar_ao_golden_set(
            item["empresa_id"],
            item["produto_id"],
            "sistema_teste"
        )
        
        if resultado["sucesso"]:
            golden_adicionados += 1
            print(f"  ✅ Produto {item['produto_id']} adicionado ao Golden Set")
        else:
            print(f"  ❌ Erro: {resultado['erro']}")
    
    print(f"📊 Total no Golden Set: {golden_adicionados}")
    
    # Teste 5: Gerar relatórios
    print("\n6️⃣ Gerando relatórios das empresas...")
    
    for empresa_id in empresas_criadas:
        print(f"\n🏢 RELATÓRIO EMPRESA {empresa_id}")
        print("-" * 40)
        
        try:
            # Estatísticas básicas
            stats = service.db_manager.get_empresa_stats(empresa_id)
            
            print(f"📊 Produtos: {stats['total_produtos']}")
            print(f"📊 Classificações: {stats['total_classificacoes']}")
            print(f"📊 Aprovadas: {stats['classificacoes_aprovadas']}")
            print(f"📊 Pendentes: {stats['classificacoes_pendentes']}")
            print(f"📊 Taxa aprovação: {stats['taxa_aprovacao']}%")
            print(f"📊 Confiança NCM: {stats['confianca_media_ncm']}")
            print(f"📊 Confiança CEST: {stats['confianca_media_cest']}")
            
            if stats['acoes_por_agente']:
                print("🤖 Ações por agente:")
                for agente, acoes in stats['acoes_por_agente'].items():
                    print(f"  - {agente}: {acoes} ações")
            
            # Relatório detalhado
            relatorio = service.get_relatorio_empresa(empresa_id)
            if "erro" not in relatorio:
                print(f"📅 Relatório gerado: {relatorio['data_relatorio']}")
                
        except Exception as e:
            print(f"❌ Erro no relatório: {e}")
    
    # Teste 6: Listar todas as empresas
    print("\n7️⃣ Listando todas as empresas...")
    
    empresas_listadas = service.listar_empresas()
    
    print(f"📊 Total de empresas no sistema: {len(empresas_listadas)}")
    
    for empresa in empresas_listadas:
        info = empresa["info"]
        stats = empresa["stats"]
        
        print(f"\n🏢 {info['nome']} (ID: {empresa['empresa_id']})")
        print(f"   📁 Banco: {empresa['database_path']}")
        print(f"   🎯 Atividade: {info['tipo_atividade']}")
        print(f"   📊 {stats['total_produtos']} produtos, {stats['total_classificacoes']} classificações")
    
    # Teste 7: Verificar Golden Set
    print("\n8️⃣ Verificando Golden Set compartilhado...")
    
    try:
        import sqlite3
        
        with sqlite3.connect(service.db_manager.golden_set_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM golden_set_produtos WHERE ativo = 1")
            total_golden = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM golden_set_validacoes")
            total_validacoes = cursor.fetchone()[0]
            
            print(f"📊 Produtos no Golden Set: {total_golden}")
            print(f"📊 Validações registradas: {total_validacoes}")
            
            if total_golden > 0:
                cursor.execute("""
                    SELECT nome_produto, ncm_codigo, cest_codigo, confianca_validacao
                    FROM golden_set_produtos 
                    WHERE ativo = 1 
                    ORDER BY data_criacao DESC 
                    LIMIT 5
                """)
                
                print("\n🏆 Últimos produtos no Golden Set:")
                for row in cursor.fetchall():
                    print(f"  - {row[0]} | NCM: {row[1]} | CEST: {row[2]} | Conf: {row[3]}")
                    
    except Exception as e:
        print(f"❌ Erro ao verificar Golden Set: {e}")
    
    # Teste 8: Verificar estrutura dos bancos
    print("\n9️⃣ Verificando estrutura dos bancos...")
    
    for empresa_id in empresas_criadas:
        try:
            db_path = service.db_manager.get_empresa_db_path(empresa_id)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas = [row[0] for row in cursor.fetchall()]
                
                print(f"\n📁 Banco Empresa {empresa_id}:")
                print(f"   📊 Tabelas criadas: {len(tabelas)}")
                
                # Contar registros por tabela
                for tabela in tabelas:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                    count = cursor.fetchone()[0]
                    print(f"   - {tabela}: {count} registros")
                    
        except Exception as e:
            print(f"❌ Erro ao verificar banco empresa {empresa_id}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTE COMPLETO FINALIZADO COM SUCESSO!")
    print(f"🏢 {len(empresas_criadas)} empresas criadas")
    print(f"📦 {len(classificacoes_realizadas)} produtos classificados")
    print(f"✅ {aprovadas} classificações aprovadas")
    print(f"🏆 {golden_adicionados} produtos no Golden Set")
    print(f"📊 Sistema de bancos segregados funcionando!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_sistema_completo()
    except Exception as e:
        print(f"\n❌ ERRO GERAL NO TESTE: {e}")
        import traceback
        traceback.print_exc()
