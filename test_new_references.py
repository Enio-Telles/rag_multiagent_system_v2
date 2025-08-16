#!/usr/bin/env python3
# ============================================================================
# test_new_references.py - Teste dos Novos Arquivos de Referência
# ============================================================================

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion.data_loader import DataLoader
from orchestrator.hybrid_router import HybridRouter

def test_data_loader():
    """Testa o carregamento dos novos arquivos de referência."""
    print("🧪 TESTANDO CARREGAMENTO DOS NOVOS ARQUIVOS DE REFERÊNCIA...")
    
    data_loader = DataLoader()
    
    # Teste 1: Carregar mapeamento CEST (incluindo conv_142_formatado)
    print("\n📁 Teste 1: Carregando mapeamento CEST...")
    cest_df = data_loader.load_cest_mapping()
    if cest_df is not None and not cest_df.empty:
        print(f"✅ CEST mapping carregado: {len(cest_df)} registros")
        
        # Verificar se dados do conv_142_formatado estão presentes
        if 'segmento' in cest_df.columns or 'SEGMENTO' in cest_df.columns:
            print("✅ Dados do conv_142_formatado detectados (coluna segmento presente)")
            
            # Mostrar alguns exemplos de medicamentos (segmento 13)
            segmento_col = 'SEGMENTO' if 'SEGMENTO' in cest_df.columns else 'segmento'
            medicamentos = cest_df[cest_df[segmento_col] == 13]
            if not medicamentos.empty:
                print(f"✅ Encontrados {len(medicamentos)} registros de medicamentos (segmento 13)")
                print("📋 Exemplos de medicamentos:")
                for i, (_, row) in enumerate(medicamentos.head(3).iterrows()):
                    ncm = row.get('NCM_SH', row.get('ncm', 'N/A'))
                    cest = row.get('CEST', row.get('cest', 'N/A'))
                    desc = row.get('DESCRICAO', row.get('descricao_oficial_cest', 'N/A'))
                    print(f"   {i+1}. NCM {ncm} -> CEST {cest}: {desc[:80]}...")
            else:
                print("⚠️ Nenhum medicamento (segmento 13) encontrado")
        else:
            print("⚠️ Dados do conv_142_formatado não detectados")
    else:
        print("❌ Falha ao carregar mapeamento CEST")
    
    # Teste 2: Carregar ABC Farma
    print("\n📁 Teste 2: Carregando ABC Farma...")
    abc_farma_df = data_loader.load_abc_farma_gtin()
    if abc_farma_df is not None and not abc_farma_df.empty:
        print(f"✅ ABC Farma carregado: {len(abc_farma_df)} medicamentos")
        
        # Mostrar alguns exemplos
        print("📋 Exemplos de medicamentos ABC Farma:")
        for i, (_, row) in enumerate(abc_farma_df.head(3).iterrows()):
            codigo_barra = row.get('codigo_barra', 'N/A')
            desc = row.get('descricao_completa', 'N/A')
            marca = row.get('marca', 'N/A')
            print(f"   {i+1}. GTIN {codigo_barra}: {desc[:60]}... (Marca: {marca})")
    else:
        print("❌ Falha ao carregar ABC Farma")

def test_hybrid_router():
    """Testa o HybridRouter com os novos dados de referência."""
    print("\n🤖 TESTANDO HYBRID ROUTER COM NOVOS DADOS...")
    
    try:
        router = HybridRouter()
        
        # Verificar se os bancos de dados foram carregados
        print(f"✅ Banco CEST de referência: {len(router.cest_reference_db)} NCMs")
        print(f"✅ Banco ABC Farma: {len(router.abc_farma_db)} GTINs")
        
        # Teste com produto medicamento simulado
        produto_teste = {
            'id': 1,
            'descricao_produto': 'Paracetamol 500mg 20 comprimidos',
            'codigo_barra': '7896789012345'
        }
        
        print(f"\n🧪 Testando contexto estruturado para produto medicamento...")
        context = router._get_structured_context('30049099', produto_teste)
        print("📋 Contexto gerado:")
        print(context[:500] + "..." if len(context) > 500 else context)
        
    except Exception as e:
        print(f"❌ Erro ao testar HybridRouter: {e}")

def test_medicamento_detection():
    """Testa a detecção específica de medicamentos."""
    print("\n💊 TESTANDO DETECÇÃO DE MEDICAMENTOS...")
    
    try:
        router = HybridRouter()
        
        # Produtos de teste
        produtos_teste = [
            {
                'id': 1,
                'descricao_produto': 'Dipirona 500mg 10 comprimidos',
                'codigo_barra': '1234567890123'
            },
            {
                'id': 2,
                'descricao_produto': 'Xarope para tosse infantil 120ml',
                'codigo_barra': '9876543210987'
            },
            {
                'id': 3,
                'descricao_produto': 'Smartphone Samsung Galaxy',
                'codigo_barra': '5555555555555'
            }
        ]
        
        for produto in produtos_teste:
            print(f"\n🔍 Testando: {produto['descricao_produto']}")
            
            # Simular produto expandido
            produto_expandido = produto.copy()
            produto_expandido['expansion_data'] = {
                'categoria_principal': 'medicamento' if 'dipirona' in produto['descricao_produto'].lower() or 'xarope' in produto['descricao_produto'].lower() else 'eletrônico',
                'palavras_chave_fiscais': ['medicamento', 'farmaco'] if 'dipirona' in produto['descricao_produto'].lower() or 'xarope' in produto['descricao_produto'].lower() else ['eletrônico']
            }
            
            context = router._get_structured_context('30049099', produto_expandido)
            
            if 'MEDICAMENTO' in context:
                print("✅ Medicamento detectado corretamente")
            else:
                print("⚠️ Medicamento não detectado")
                
    except Exception as e:
        print(f"❌ Erro ao testar detecção de medicamentos: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DOS NOVOS ARQUIVOS DE REFERÊNCIA")
    print("=" * 60)
    
    test_data_loader()
    test_hybrid_router()
    test_medicamento_detection()
    
    print("\n" + "=" * 60)
    print("✅ TESTES CONCLUÍDOS!")