#!/usr/bin/env python3
"""
Script de Extração PostgreSQL → SQLite com Classificação Completa
Extrai dados do PostgreSQL, classifica usando sistema unificado e salva tudo no SQLite
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Adicionar src ao path
sys.path.append('src')

try:
    from config import Config
    from ingestion.data_loader import DataLoader
    from services.unified_sqlite_service import get_unified_service
    from main import _classify_produto_unified, sanitize_text_for_windows
    
    print("✅ Imports realizados com sucesso")
except ImportError as e:
    print(f"❌ Erro de import: {e}")
    sys.exit(1)

def extrair_e_classificar_postgresql():
    """Extrai dados do PostgreSQL e classifica no SQLite"""
    print("🚀 EXTRAÇÃO POSTGRESQL → CLASSIFICAÇÃO SQLITE")
    print("=" * 60)
    
    # 1. Inicializar serviços
    print("\n1️⃣ INICIALIZANDO SERVIÇOS:")
    
    try:
        data_loader = DataLoader()
        unified_service = get_unified_service("data/unified_rag_system.db")
        print("✅ Serviços inicializados")
    except Exception as e:
        print(f"❌ Erro ao inicializar serviços: {e}")
        return False
    
    # 2. Extrair dados do PostgreSQL
    print("\n2️⃣ EXTRAINDO DADOS DO POSTGRESQL:")
    
    try:
        # Forçar conexão PostgreSQL
        produtos_df = data_loader.load_produtos_from_db(force_postgresql=True)
        
        if produtos_df.empty:
            print("❌ Nenhum produto encontrado no PostgreSQL")
            return False
        
        print(f"✅ {len(produtos_df)} produtos extraídos do PostgreSQL")
        
        # Limitar para teste (remover se quiser processar todos)
        limite_teste = 20
        produtos_df = produtos_df.head(limite_teste)
        produtos = produtos_df.to_dict('records')
        
        print(f"📊 Processando {len(produtos)} produtos para teste")
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados: {e}")
        return False
    
    # 3. Classificar e salvar no SQLite
    print("\n3️⃣ CLASSIFICANDO E SALVANDO NO SQLITE:")
    
    resultados = []
    start_total = time.time()
    
    for i, produto in enumerate(produtos, 1):
        try:
            print(f"\n   📝 [{i}/{len(produtos)}] Processando produto ID {produto.get('produto_id')}:")
            desc_safe = sanitize_text_for_windows(produto.get('descricao_produto', '')[:60])
            print(f"      {desc_safe}...")
            
            start_time = time.time()
            
            # Classificar usando sistema unificado
            classificacao_data = _classify_produto_unified(produto, unified_service)
            
            # Preparar dados completos para SQLite
            dados_completos = {
                'produto_id': produto.get('produto_id'),
                'descricao_produto': produto.get('descricao_produto'),
                'codigo_produto': produto.get('codigo_produto'),
                'codigo_barra': produto.get('codigo_barra'),
                'ncm_original': produto.get('ncm'),
                'cest_original': produto.get('cest'),
                'marca_original': produto.get('marca', ''),
                'categoria_original': produto.get('categoria', ''),
                'ncm_sugerido': classificacao_data['ncm_sugerido'],
                'cest_sugerido': classificacao_data.get('cest_sugerido'),
                'confianca_sugerida': classificacao_data.get('confianca_sugerida', 0.0),
                'justificativa_sistema': classificacao_data.get('justificativa_sistema'),
                'fonte_dados': 'postgresql_extraction_script',
                'sistema_classificacao': classificacao_data.get('sistema_origem', 'unified_sqlite'),
                'observacoes_sistema': f"Extraído via script. Consultas realizadas: {len(classificacao_data.get('consultas_realizadas', []))}"
            }
            
            # Salvar classificação no SQLite
            classificacao_id = unified_service.criar_classificacao(dados_completos)
            
            # Salvar consultas dos agentes
            consultas_salvas = 0
            for consulta in classificacao_data.get('consultas_realizadas', []):
                try:
                    from main import _salvar_consulta_agente
                    consulta_id = _salvar_consulta_agente(unified_service, classificacao_id, produto.get('produto_id'), consulta)
                    if consulta_id:
                        consultas_salvas += 1
                except Exception as e:
                    print(f"      ⚠️ Erro ao salvar consulta: {e}")
            
            tempo_ms = int((time.time() - start_time) * 1000)
            
            # Resultado para relatório
            resultado = {
                'produto_id': produto.get('produto_id'),
                'descricao_produto': produto.get('descricao_produto'),
                'ncm_original': produto.get('ncm'),
                'ncm_classificado': classificacao_data['ncm_sugerido'],
                'cest_original': produto.get('cest'),
                'cest_classificado': classificacao_data.get('cest_sugerido'),
                'confianca': classificacao_data.get('confianca_sugerida', 0.0),
                'classificacao_id': classificacao_id,
                'consultas_salvas': consultas_salvas,
                'tempo_ms': tempo_ms
            }
            
            resultados.append(resultado)
            
            print(f"      ✅ NCM: {classificacao_data['ncm_sugerido']} | CEST: {classificacao_data.get('cest_sugerido', 'N/A')} | ID: {classificacao_id}")
            print(f"      📊 Confiança: {classificacao_data.get('confianca_sugerida', 0):.3f} | Consultas: {consultas_salvas} | Tempo: {tempo_ms}ms")
            
        except Exception as e:
            print(f"      ❌ Erro: {e}")
            continue
    
    tempo_total = time.time() - start_total
    
    # 4. Relatório final
    print("\n4️⃣ RELATÓRIO FINAL:")
    print("=" * 60)
    
    total_processados = len(resultados)
    ncms_validos = sum(1 for r in resultados if r['ncm_classificado'] not in ['99999999', None, ''])
    cests_atribuidos = sum(1 for r in resultados if r['cest_classificado'])
    confianca_media = sum(r['confianca'] for r in resultados) / total_processados if total_processados > 0 else 0
    consultas_totais = sum(r['consultas_salvas'] for r in resultados)
    
    print(f"📊 Produtos processados: {total_processados}")
    print(f"✅ NCMs válidos: {ncms_validos} ({ncms_validos/total_processados*100:.1f}%)")
    print(f"🎯 CESTs atribuídos: {cests_atribuidos} ({cests_atribuidos/total_processados*100:.1f}%)")
    print(f"📈 Confiança média: {confianca_media:.3f}")
    print(f"🔍 Consultas salvas: {consultas_totais}")
    print(f"⏱️ Tempo total: {tempo_total:.1f}s")
    print(f"⚡ Média por produto: {tempo_total/total_processados:.2f}s")
    
    # 5. Salvar relatório JSON
    relatorio = {
        'timestamp': datetime.now().isoformat(),
        'origem': 'postgresql_extraction',
        'total_processados': total_processados,
        'estatisticas': {
            'ncms_validos': ncms_validos,
            'cests_atribuidos': cests_atribuidos,
            'confianca_media': confianca_media,
            'consultas_totais': consultas_totais,
            'tempo_total_s': tempo_total
        },
        'resultados': resultados
    }
    
    relatorio_file = f"relatorio_extracao_postgresql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"📁 Relatório salvo: {relatorio_file}")
    
    # 6. Verificar dados no SQLite
    print("\n5️⃣ VERIFICAÇÃO NO SQLITE:")
    
    try:
        stats = unified_service.get_dashboard_stats()
        print(f"📊 Classificações totais no SQLite: {stats.get('total_classificacoes', 0)}")
        
        # Buscar últimas classificações
        with unified_service.get_session() as session:
            from database.unified_sqlite_models import ClassificacaoRevisao
            from sqlalchemy import desc
            
            ultimas = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.fonte_dados == 'postgresql_extraction_script'
            ).order_by(desc(ClassificacaoRevisao.data_criacao)).limit(5).all()
            
            print(f"📋 Últimas {len(ultimas)} classificações salvas:")
            for clf in ultimas:
                desc_safe = sanitize_text_for_windows(clf.descricao_produto[:50])
                print(f"   ID {clf.id}: {desc_safe} → NCM {clf.ncm_sugerido}")
        
    except Exception as e:
        print(f"⚠️ Erro na verificação: {e}")
    
    print(f"\n🎉 EXTRAÇÃO E CLASSIFICAÇÃO CONCLUÍDA COM SUCESSO!")
    return True

def main():
    """Função principal"""
    try:
        sucesso = extrair_e_classificar_postgresql()
        return 0 if sucesso else 1
    except KeyboardInterrupt:
        print("\n\n⏸️ Operação interrompida pelo usuário")
        return 1
    except Exception as e:
        print(f"\n\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
