"""
Teste do sistema de detecção de duplicatas - AggregationAgent v2.0
Foco em identificar produtos idênticos com descrições diferentes
"""
import sys
import os
from pathlib import Path

# Adicionar src    print(f"🎯 CONCLUSÃO:")
    print(f"   Sistema detectou {resumo['total_duplicatas_eliminadas']} duplicatas em {resumo['total_produtos_processados']} produtos")
    if resumo['total_produtos_processados'] > 0:
        print(f"   Eficiência: {(resumo['total_duplicatas_eliminadas']/resumo['total_produtos_processados']*100):.1f}% de redução")
    else:
        print(f"   Eficiência: N/A (produtos processados = 0)") path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from agents.aggregation_agent import AggregationAgent
from domain.product_deduplication import ProductDeduplicationValidator

def test_deteccao_duplicatas():
    """Teste principal do sistema de detecção de duplicatas"""
    
    print("="*80)
    print("TESTE: DETECÇÃO DE PRODUTOS IDÊNTICOS COM DESCRIÇÕES DIFERENTES")
    print("="*80)
    
    # Dados de teste que simulam produtos reais com variações de descrição
    produtos_teste = [
        # Grupo 1: Aparelhos de barbear Presto (MESMO PRODUTO)
        {
            "descricao_produto": "APAR BARBEAR PRESTO MASCULI GILLETTE",
            "ncm": "82121000",
            "cest": "21.064.00",
            "gtin": "7891024567890"
        },
        {
            "descricao_produto": "APARELHO BARBEAR PRESTOB MASCULINO GILETE", 
            "ncm": "82121000",
            "cest": "21.064.00",
            "gtin": "7891024567891"  # GTIN diferente mesmo produto
        },
        {
            "descricao_produto": "BARBEAD PRESTOB MASCULINO GILLETTE",
            "ncm": "82121000", 
            "cest": "21.064.00",
            "gtin": "7891024567892"
        },
        
        # Grupo 2: Barbeadores Presto 2 unidades (MESMO PRODUTO)
        {
            "descricao_produto": "BARBEAD PRESTOB 2 UNID",
            "ncm": "82121000",
            "cest": "21.064.00",
            "gtin": "7891024567893"
        },
        {
            "descricao_produto": "BARBEADOR PRESTOBARBA 2 UNIDADES",
            "ncm": "82121000",
            "cest": "21.064.00", 
            "gtin": "7891024567894"
        },
        {
            "descricao_produto": "APAR BARBEAR PRESTO 2 UN MASCULINO",
            "ncm": "82121000",
            "cest": "21.064.00",
            "gtin": "7891024567895"
        },
        
        # Produto 3: Diferente - 3 unidades (PRODUTO DIFERENTE)
        {
            "descricao_produto": "BARBEADOR PRESTOBARBA 3 UNIDADES",
            "ncm": "82121000",
            "cest": "21.064.00",
            "gtin": "7891024567896"
        },
        
        # Produto 4: Marca diferente (PRODUTO DIFERENTE)
        {
            "descricao_produto": "APARELHO BARBEAR MORMAII MASCULINO",
            "ncm": "82121000", 
            "cest": "21.064.00",
            "gtin": "7891024567897"
        },
        
        # Produto 5: Categoria totalmente diferente (PRODUTO DIFERENTE)
        {
            "descricao_produto": "COPO PLASTICO 200ML AZUL",
            "ncm": "39241000",
            "cest": "21.065.00",
            "gtin": "7891024567898"
        },
        
        # Produto 6: Biscoito Lacta (PRODUTO ÚNICO)
        {
            "descricao_produto": "BISCOITO LACTA RECHEADO CHOCOLATE 100G",
            "ncm": "19059090",
            "cest": "17.023.00",
            "gtin": "7891024567899"
        }
    ]
    
    print(f"Produtos de teste: {len(produtos_teste)}")
    for i, produto in enumerate(produtos_teste):
        print(f"  {i+1:2d}. {produto['descricao_produto']}")
    
    # Configuração do agente focada em detecção de duplicatas
    config = {
        "enable_product_deduplication": True,
        "min_deduplication_confidence": 0.7,
        "strict_duplicate_matching": True
    }
    
    # Executar detecção de duplicatas
    print("\n" + "="*50)
    print("EXECUTANDO DETECÇÃO DE DUPLICATAS...")
    print("="*50)
    
    agent = AggregationAgent(llm_client=None, config=config)
    resultado = agent.run(produtos_teste)
    
    # Analisar resultados
    print(f"\n📊 ESTATÍSTICAS:")
    estatisticas = resultado.get('estatisticas', {})
    print(f"   Total de produtos processados: {estatisticas.get('total_products', len(produtos_teste))}")
    print(f"   Grupos formados: {len(resultado.get('grupos', []))}")
    print(f"   Grupos com duplicatas: {estatisticas.get('grupos_com_duplicatas', 0)}")
    print(f"   Produtos únicos: {estatisticas.get('produtos_unicos', 0)}")
    
    # Mostrar grupos detalhadamente
    print(f"\n🔍 GRUPOS IDENTIFICADOS:")
    print("-" * 80)
    
    for grupo in resultado["grupos"]:
        print(f"\n🔸 GRUPO {grupo['id']} - {grupo['tipo'].upper()}")
        print(f"   Confiança: {grupo['confidence']:.2f}")
        print(f"   Produtos no grupo: {len(grupo['produtos'])}")
        
        if grupo['tipo'] == 'duplicatas_detectadas':
            print(f"   ✅ DUPLICATAS IDENTIFICADAS:")
            for produto in grupo["produtos"]:
                print(f"      • {produto['descricao_produto']}")
            
            # Mostrar análise de duplicação
            if 'duplicate_analysis' in grupo:
                analysis = grupo['duplicate_analysis']
                print(f"   📝 Descrição canônica sugerida:")
                print(f"      → {analysis.get('canonical_description', 'N/A')}")
                print(f"   🎯 Duplicatas eliminadas: {analysis.get('duplicate_count', 0)}")
        
        elif grupo['tipo'] == 'produto_unico':
            produto = grupo['produtos'][0]
            print(f"   ✨ PRODUTO ÚNICO: {produto['descricao_produto']}")
        
        elif grupo['tipo'] == 'produto_unico_baixa_confianca':
            produto = grupo['produtos'][0]
            print(f"   ⚠️  SEPARADO (baixa confiança): {produto['descricao_produto']}")
            print(f"      Motivo: {grupo.get('motivo_separacao', 'N/A')}")
    
    # Resumo final de duplicatas
    print(f"\n📈 RESUMO DE DUPLICATAS:")
    print("-" * 50)
    resumo = agent.get_duplicate_summary(resultado)
    
    print(f"   Duplicatas eliminadas: {resumo['total_duplicatas_eliminadas']}")
    print(f"   Economia obtida: {resumo['economia_percentual']:.1f}%")
    print(f"   Taxa de duplicação: {resumo['taxa_duplicacao']:.2f}")
    
    if resumo['detalhes_duplicatas']:
        print(f"\n   Detalhes por grupo:")
        for detalhe in resumo['detalhes_duplicatas']:
            print(f"      Grupo {detalhe['grupo_id']}: {detalhe['duplicatas_eliminadas']} duplicatas")
            print(f"        Representante: {detalhe['produto_representante']}")
    
    # Validação dos resultados esperados
    print(f"\n✅ VALIDAÇÃO DOS RESULTADOS:")
    print("-" * 50)
    
    # Verificar se duplicatas foram corretamente identificadas
    grupos_duplicatas = [g for g in resultado['grupos'] if g['tipo'] == 'duplicatas_detectadas']
    
    # Deve haver pelo menos 2 grupos de duplicatas
    if len(grupos_duplicatas) >= 2:
        print("   ✓ Grupos de duplicatas identificados corretamente")
    else:
        print("   ✗ Erro: Grupos de duplicatas não identificados adequadamente")
    
    # Verificar se produtos diferentes não foram agrupados incorretamente
    produtos_diferentes_separados = True
    for grupo in grupos_duplicatas:
        descriptions = [p['descricao_produto'] for p in grupo['produtos']]
        
        # Verificar se não misturou quantidades diferentes
        has_2_units = any('2' in desc for desc in descriptions)
        has_3_units = any('3' in desc for desc in descriptions) 
        if has_2_units and has_3_units:
            produtos_diferentes_separados = False
            print("   ✗ Erro: Produtos com quantidades diferentes foram agrupados")
        
        # Verificar se não misturou marcas diferentes
        has_gillette = any('gilet' in desc.lower() for desc in descriptions)
        has_mormaii = any('mormai' in desc.lower() for desc in descriptions)
        if has_gillette and has_mormaii:
            produtos_diferentes_separados = False
            print("   ✗ Erro: Produtos com marcas diferentes foram agrupados")
    
    if produtos_diferentes_separados:
        print("   ✓ Produtos diferentes mantidos separados corretamente")
    
    # Verificar economia
    if resumo['economia_percentual'] > 0:
        print(f"   ✓ Economia de duplicatas: {resumo['economia_percentual']:.1f}%")
    else:
        print("   ⚠️  Nenhuma economia de duplicatas obtida")
    
    print(f"\n🎯 CONCLUSÃO:")
    print(f"   Sistema detectou {resumo['total_duplicatas_eliminadas']} duplicatas em {resumo['total_produtos_processados']} produtos")
    print(f"   Eficiência: {(resumo['total_duplicatas_eliminadas']/resumo['total_produtos_processados']*100):.1f}% de redução")
    
    return resultado, resumo


def test_validator_direto():
    """Teste direto do ProductDeduplicationValidator"""
    
    print("\n" + "="*80)
    print("TESTE DIRETO: PRODUCT DEDUPLICATION VALIDATOR")
    print("="*80)
    
    validator = ProductDeduplicationValidator()
    
    # Pares de teste para validação de identidade
    test_pairs = [
        # DEVEM SER IDÊNTICOS
        {
            "produto1": {"descricao_produto": "APAR BARBEAR PRESTO MASCULI GILLETTE"},
            "produto2": {"descricao_produto": "APARELHO BARBEAR PRESTOB MASCULINO GILETE"},
            "expected": True,
            "case": "Mesmo produto, abreviações diferentes"
        },
        {
            "produto1": {"descricao_produto": "BARBEAD PRESTOB 2 UNID"},
            "produto2": {"descricao_produto": "BARBEADOR PRESTOBARBA 2 UNIDADES"},
            "expected": True,
            "case": "Mesmo produto com quantidade, unidades abreviadas"
        },
        
        # NÃO DEVEM SER IDÊNTICOS
        {
            "produto1": {"descricao_produto": "BARBEADOR PRESTOBARBA 2 UNIDADES"},
            "produto2": {"descricao_produto": "BARBEADOR PRESTOBARBA 3 UNIDADES"},
            "expected": False,
            "case": "Quantidades diferentes"
        },
        {
            "produto1": {"descricao_produto": "APARELHO BARBEAR PRESTO GILLETTE"},
            "produto2": {"descricao_produto": "APARELHO BARBEAR PRESTO MORMAII"},
            "expected": False,
            "case": "Marcas diferentes"
        },
        {
            "produto1": {"descricao_produto": "APARELHO BARBEAR GILLETTE"},
            "produto2": {"descricao_produto": "COPO PLASTICO 200ML"},
            "expected": False,
            "case": "Produtos completamente diferentes"
        }
    ]
    
    print("Testando pares de produtos:")
    
    correct_predictions = 0
    total_tests = len(test_pairs)
    
    for i, test_case in enumerate(test_pairs, 1):
        produto1 = test_case["produto1"]
        produto2 = test_case["produto2"]
        expected = test_case["expected"]
        case_name = test_case["case"]
        
        identical, reason, confidence = validator.products_are_identical(produto1, produto2)
        
        # Verificar se predição está correta
        is_correct = identical == expected
        correct_predictions += is_correct
        
        # Mostrar resultado
        status = "✅ CORRETO" if is_correct else "❌ ERRO"
        print(f"\n{i:2d}. {status} - {case_name}")
        print(f"    Produto 1: {produto1['descricao_produto']}")
        print(f"    Produto 2: {produto2['descricao_produto']}")
        print(f"    Esperado: {'Idênticos' if expected else 'Diferentes'}")
        print(f"    Resultado: {'Idênticos' if identical else 'Diferentes'} (confiança: {confidence:.2f})")
        print(f"    Razão: {reason}")
    
    # Estatísticas finais
    accuracy = correct_predictions / total_tests * 100
    print(f"\n📊 PERFORMANCE DO VALIDATOR:")
    print(f"   Acertos: {correct_predictions}/{total_tests}")
    print(f"   Precisão: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print(f"   ✅ Validator funcionando adequadamente")
    else:
        print(f"   ❌ Validator precisa de ajustes")
    
    return accuracy


if __name__ == "__main__":
    # Executar testes
    print("Iniciando testes do sistema de detecção de duplicatas...")
    
    try:
        # Teste 1: Sistema completo 
        resultado_aggregation, resumo = test_deteccao_duplicatas()
        
        # Teste 2: Validator direto
        accuracy = test_validator_direto()
        
        print(f"\n" + "="*80)
        print("SUMMARY FINAL DOS TESTES")
        print("="*80)
        print(f"✅ AggregationAgent: {resumo['total_duplicatas_eliminadas']} duplicatas detectadas")
        print(f"✅ DeduplicationValidator: {accuracy:.1f}% de precisão")
        print(f"🎯 Sistema otimizado para identificar produtos idênticos com descrições diferentes")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
