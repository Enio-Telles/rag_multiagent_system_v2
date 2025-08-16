#!/usr/bin/env python3
"""
Teste do Sistema de Explicações dos Agentes
Valida o funcionamento completo das explicações e Golden Set enriquecido
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from config import Config
from orchestrator.hybrid_router import HybridRouter
from database.connection import get_db
from database.models import ClassificacaoRevisao, ExplicacaoAgente, GoldenSetEntry
from feedback.explicacao_service import ExplicacaoService
from feedback.review_service import ReviewService

def testar_classificacao_com_explicacoes():
    """Testa classificação de um produto com explicações detalhadas"""
    print("🧪 TESTE: Classificação com Explicações dos Agentes")
    print("=" * 60)
    
    try:
        # Inicializar sistema
        config = Config()
        router = HybridRouter()
        
        # Produto de teste
        produto_teste = {
            "id": 9999,
            "produto_id": 9999,
            "descricao_produto": "Smartphone Samsung Galaxy A54 128GB 5G Tela 6.4 polegadas",
            "codigo_produto": "SAMSUNG-A54-128"
        }
        
        print(f"📱 Produto de teste: {produto_teste['descricao_produto']}")
        print("\n🔄 Executando classificação com explicações...")
        
        # Classificar com explicações
        resultado = router.classify_product_with_explanations(produto_teste, salvar_explicacoes=True)
        
        print("\n✅ RESULTADO DA CLASSIFICAÇÃO:")
        print(f"📋 NCM: {resultado.get('ncm_classificado', 'N/A')}")
        print(f"🏷️ CEST: {resultado.get('cest_classificado', 'N/A')}")
        print(f"📊 Confiança: {resultado.get('confianca_consolidada', 0.0):.3f}")
        print(f"📝 Justificativa: {resultado.get('justificativa_final', 'N/A')[:100]}...")
        
        # Verificar explicações
        explicacoes = resultado.get('explicacoes_agentes', {})
        print(f"\n🤖 EXPLICAÇÕES DOS AGENTES ({len(explicacoes)} encontradas):")
        
        for agente_nome, explicacao in explicacoes.items():
            print(f"\n  🔸 {agente_nome.upper()}:")
            print(f"    📖 Explicação: {explicacao.get('explicacao_detalhada', 'N/A')[:80]}...")
            print(f"    🎯 Confiança: {explicacao.get('nivel_confianca', 0.0):.3f}")
            print(f"    ⏱️ Tempo: {explicacao.get('tempo_processamento_ms', 0)}ms")
            print(f"    🔤 Palavras-chave: {explicacao.get('palavras_chave_identificadas', 'N/A')[:50]}...")
        
        return resultado
        
    except Exception as e:
        print(f"❌ ERRO no teste de classificação: {e}")
        return None

def testar_servico_explicacoes(produto_id: int):
    """Testa o serviço de explicações"""
    print(f"\n🧪 TESTE: Serviço de Explicações (Produto {produto_id})")
    print("=" * 60)
    
    try:
        explicacao_service = ExplicacaoService()
        
        # Obter explicações do produto
        explicacoes = explicacao_service.obter_explicacoes_produto(produto_id)
        
        print(f"📊 Total de explicações encontradas: {len(explicacoes)}")
        
        for exp in explicacoes:
            print(f"\n  🤖 Agente: {exp['agente_nome']}")
            print(f"    📝 Explicação: {exp['explicacao_detalhada'][:100]}...")
            print(f"    🎯 Confiança: {exp['nivel_confianca']}")
            print(f"    🔤 Palavras-chave: {exp['palavras_chave']}")
            print(f"    ⏱️ Tempo: {exp['tempo_processamento_ms']}ms")
            print(f"    🧠 Tokens: {exp['tokens_utilizados']}")
            print(f"    📊 RAG usado: {exp['rag_consultado']}")
            print(f"    🏆 Golden Set usado: {exp['golden_set_utilizado']}")
        
        # Testar explicação por agente específico
        print(f"\n🔍 Testando explicação do agente NCM...")
        exp_ncm = explicacao_service.obter_explicacao_por_agente(produto_id, "ncm")
        
        if exp_ncm:
            print(f"✅ Explicação NCM encontrada: {exp_ncm['explicacao_detalhada'][:80]}...")
        else:
            print("❌ Explicação NCM não encontrada")
        
        return explicacoes
        
    except Exception as e:
        print(f"❌ ERRO no teste de serviço: {e}")
        return []

def testar_golden_set_enriquecido(produto_id: int):
    """Testa adição ao Golden Set com dados enriquecidos"""
    print(f"\n🧪 TESTE: Golden Set Enriquecido (Produto {produto_id})")
    print("=" * 60)
    
    try:
        review_service = ReviewService()
        
        db = next(get_db())
        # Adicionar ao Golden Set
        resultado = review_service.adicionar_ao_golden_set(
            db=db,
            produto_id=produto_id,
            justificativa="Produto de teste com explicações detalhadas dos agentes",
            revisado_por="Sistema de Teste"
        )
        
        print(f"📊 Resultado da adição:")
        print(f"  ✅ Sucesso: {resultado['success']}")
        print(f"  📝 Mensagem: {resultado['message']}")
        
        if resultado['success']:
            golden_set_id = resultado['golden_set_id']
            
            # Verificar dados incluídos
            dados = resultado.get('dados_incluidos', {})
            print(f"\n🎯 DADOS ENRIQUECIDOS INCLUÍDOS:")
            print(f"  📝 Descrição original: {dados.get('descricao_original', 'N/A')[:50]}...")
            print(f"  📖 Descrição completa: {dados.get('descricao_completa', 'N/A')[:50]}...")
            print(f"  📋 NCM final: {dados.get('ncm_final', 'N/A')}")
            print(f"  🏷️ CEST final: {dados.get('cest_final', 'N/A')}")
            print(f"  🏷️ GTIN validado: {dados.get('gtin_validado', 'N/A')}")
            print(f"  🔤 Palavras-chave: {dados.get('palavras_chave', 'N/A')}")
            print(f"  📂 Categoria: {dados.get('categoria', 'N/A')}")
            print(f"  🔧 Material: {dados.get('material', 'N/A')}")
            
            # Verificar entrada no banco
            entrada = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.id == golden_set_id
            ).first()
            
            if entrada:
                print(f"\n📊 ENTRADA NO BANCO:")
                print(f"  🆔 ID: {entrada.id}")
                print(f"  📦 Produto ID: {entrada.produto_id}")
                print(f"  🎯 Categoria: {entrada.categoria_produto}")
                print(f"  🔧 Material: {entrada.material_predominante}")
                print(f"  🎪 Aplicações: {entrada.aplicacoes_uso}")
                print(f"  🔬 Características: {entrada.caracteristicas_tecnicas}")
                print(f"  📍 Contexto: {entrada.contexto_uso}")
                print(f"  🔤 Palavras-chave: {entrada.palavras_chave_fiscais}")
                
                # Verificar explicações incluídas
                print(f"\n🤖 EXPLICAÇÕES INCLUÍDAS:")
                print(f"  🔍 Expansão: {'✅' if entrada.explicacao_expansao else '❌'}")
                print(f"  🎲 Agregação: {'✅' if entrada.explicacao_agregacao else '❌'}")
                print(f"  📋 NCM: {'✅' if entrada.explicacao_ncm else '❌'}")
                print(f"  🏷️ CEST: {'✅' if entrada.explicacao_cest else '❌'}")
                print(f"  🔄 Reconciliação: {'✅' if entrada.explicacao_reconciliacao else '❌'}")
                
        return resultado
        
    except Exception as e:
        print(f"❌ ERRO no teste de Golden Set: {e}")
        return None

def testar_relatorio_agentes():
    """Testa geração de relatórios de performance dos agentes"""
    print(f"\n🧪 TESTE: Relatórios de Performance dos Agentes")
    print("=" * 60)
    
    try:
        explicacao_service = ExplicacaoService()
        agentes = ["expansion", "aggregation", "ncm", "cest", "reconciler"]
        
        for agente in agentes:
            print(f"\n📊 Relatório do agente: {agente.upper()}")
            
            relatorio = explicacao_service.gerar_relatorio_agente(agente, periodo_dias=30)
            
            if "erro" not in relatorio:
                print(f"  🎯 Total execuções: {relatorio['total_execucoes']}")
                print(f"  ⏱️ Tempo médio: {relatorio['tempo_medio_ms']}ms")
                print(f"  💾 Memória média: {relatorio['memoria_media_mb']}MB")
                print(f"  🧠 Tokens total: {relatorio['tokens_total']}")
                print(f"  📊 Confiança média: {relatorio['confianca_media']}")
                print(f"  🔍 Uso RAG: {relatorio['uso_rag_percent']}%")
                print(f"  🏆 Uso Golden Set: {relatorio['uso_golden_set_percent']}%")
            else:
                print(f"  ❌ Erro: {relatorio['erro']}")
        
    except Exception as e:
        print(f"❌ ERRO no teste de relatórios: {e}")

def main():
    """Executa todos os testes do sistema de explicações"""
    print("🚀 INICIANDO TESTES DO SISTEMA DE EXPLICAÇÕES DOS AGENTES")
    print("=" * 80)
    
    # Teste 1: Classificação com explicações
    resultado_classificacao = testar_classificacao_com_explicacoes()
    
    if resultado_classificacao:
        produto_id = resultado_classificacao.get('id', 9999)
        
        # Teste 2: Serviço de explicações
        explicacoes = testar_servico_explicacoes(produto_id)
        
        # Teste 3: Golden Set enriquecido
        resultado_golden = testar_golden_set_enriquecido(produto_id)
        
        # Teste 4: Relatórios de performance
        testar_relatorio_agentes()
        
        print("\n🎉 RESUMO DOS TESTES:")
        print("=" * 40)
        print(f"✅ Classificação com explicações: {'OK' if resultado_classificacao else 'ERRO'}")
        print(f"✅ Serviço de explicações: {'OK' if explicacoes else 'ERRO'}")
        print(f"✅ Golden Set enriquecido: {'OK' if resultado_golden else 'ERRO'}")
        print(f"✅ Sistema completo: {'FUNCIONAL' if all([resultado_classificacao, explicacoes, resultado_golden]) else 'COM PROBLEMAS'}")
        
    else:
        print("\n❌ FALHA CRÍTICA: Não foi possível classificar produto com explicações")
    
    print("\n🏁 TESTES CONCLUÍDOS")

if __name__ == "__main__":
    main()
