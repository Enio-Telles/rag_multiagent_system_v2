"""
Teste específico para validação de agrupamento por código de produto
"""
import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from domain.product_deduplication import ProductDeduplicationValidator

def test_agrupamento_por_codigo_produto():
    """Testa agrupamento de produtos com mesmo código de produto"""
    
    print("="*80)
    print("TESTE: AGRUPAMENTO POR CÓDIGO DE PRODUTO")
    print("="*80)
    
    # Simular produtos iguais do arquivo JSON (mesmo codigo_produto)
    produtos_teste = [
        {
            "produto_id": 20117,
            "descricao_produto": "CHIP TIM PRÉ PLANO NAKED 4G",
            "codigo_produto": "000000000000192861",
            "codigo_barra": "7899403635857",
            "ncm": "85235290",
            "cest": "",
        },
        {
            "produto_id": 19880,
            "descricao_produto": "CHIP TIM PRÉ PLANO NAKED 4G",
            "codigo_produto": "000000000000192861",
            "codigo_barra": "7899403635857",
            "ncm": "85235290",
            "cest": "",
        },
        {
            "produto_id": 19879,
            "descricao_produto": "CHIP TIM PRÉ PLANO NAKED 4G",
            "codigo_produto": "000000000000192861",
            "codigo_barra": "7899403635857",
            "ncm": "85235290",
            "cest": "",
        },
        # Produto diferente para controle
        {
            "produto_id": 12345,
            "descricao_produto": "APARELHO BARBEAR GILLETTE",
            "codigo_produto": "000000000000999999",
            "codigo_barra": "1234567890123",
            "ncm": "82121000",
            "cest": "21.064.00",
        }
    ]
    
    print(f"Produtos de teste: {len(produtos_teste)}")
    for i, produto in enumerate(produtos_teste):
        print(f"  {i+1:2d}. {produto['descricao_produto']} (codigo: {produto['codigo_produto']})")
    
    # Testar validator diretamente
    validator = ProductDeduplicationValidator()
    
    print(f"\n🔍 TESTANDO COMPARAÇÕES PAREADAS:")
    print("-" * 60)
    
    # Testar produtos com mesmo código
    for i in range(3):  # Primeiros 3 produtos são iguais
        for j in range(i+1, 3):
            produto1 = produtos_teste[i]
            produto2 = produtos_teste[j]
            
            identical, reason, confidence = validator.products_are_identical(produto1, produto2)
            
            status = "✅ CORRETO" if identical else "❌ ERRO"
            print(f"\n{status} - Produto {i+1} vs Produto {j+1}")
            print(f"   Produto {i+1}: {produto1['descricao_produto']}")
            print(f"   Produto {j+1}: {produto2['descricao_produto']}")
            print(f"   Código: {produto1['codigo_produto']} vs {produto2['codigo_produto']}")
            print(f"   Resultado: {'IDÊNTICOS' if identical else 'DIFERENTES'} (confiança: {confidence:.2f})")
            print(f"   Razão: {reason}")
    
    # Testar produto diferente
    produto1 = produtos_teste[0]  # CHIP TIM
    produto2 = produtos_teste[3]  # APARELHO BARBEAR
    
    identical, reason, confidence = validator.products_are_identical(produto1, produto2)
    
    status = "✅ CORRETO" if not identical else "❌ ERRO"
    print(f"\n{status} - Produto diferente (controle)")
    print(f"   Produto 1: {produto1['descricao_produto']}")
    print(f"   Produto 2: {produto2['descricao_produto']}")
    print(f"   Código: {produto1['codigo_produto']} vs {produto2['codigo_produto']}")
    print(f"   Resultado: {'IDÊNTICOS' if identical else 'DIFERENTES'} (confiança: {confidence:.2f})")
    print(f"   Razão: {reason}")
    
    # Testar agrupamento completo
    print(f"\n🎲 TESTANDO AGRUPAMENTO COMPLETO:")
    print("-" * 60)
    
    grupos = validator.group_identical_products(produtos_teste)
    
    print(f"Total de grupos formados: {len(grupos)}")
    print(f"Grupos esperados: 2 (3 CHIPs + 1 Aparelho)")
    
    for i, grupo in enumerate(grupos):
        produtos_grupo = [produtos_teste[idx] for idx in grupo]
        print(f"\nGrupo {i+1}: {len(grupo)} produtos")
        for idx in grupo:
            produto = produtos_teste[idx]
            print(f"   - {produto['descricao_produto']} (ID: {produto['produto_id']})")
    
    # Validação final
    print(f"\n✅ VALIDAÇÃO FINAL:")
    print("-" * 50)
    
    success = True
    
    # Deve ter exatamente 2 grupos
    if len(grupos) != 2:
        print(f"❌ Erro: Esperado 2 grupos, encontrado {len(grupos)}")
        success = False
    else:
        print(f"✅ Número correto de grupos: {len(grupos)}")
    
    # Um grupo deve ter 3 produtos (CHIPs)
    grupo_chips = [g for g in grupos if len(g) == 3]
    if len(grupo_chips) != 1:
        print(f"❌ Erro: Esperado 1 grupo com 3 CHIPs, encontrado {len(grupo_chips)}")
        success = False
    else:
        print(f"✅ Grupo de CHIPs identificado corretamente: 3 produtos")
    
    # Um grupo deve ter 1 produto (Aparelho)
    grupo_aparelho = [g for g in grupos if len(g) == 1]
    if len(grupo_aparelho) != 1:
        print(f"❌ Erro: Esperado 1 grupo com 1 Aparelho, encontrado {len(grupo_aparelho)}")
        success = False
    else:
        print(f"✅ Produto único identificado corretamente: 1 produto")
    
    if success:
        print(f"\n🎉 TESTE PASSOU: Agrupamento por código de produto funcionando!")
    else:
        print(f"\n❌ TESTE FALHOU: Agrupamento por código de produto com problemas")
    
    return success


if __name__ == "__main__":
    try:
        success = test_agrupamento_por_codigo_produto()
        
        if success:
            print(f"\n🚀 SISTEMA PRONTO: Duplicatas por código de produto detectadas corretamente")
        else:
            print(f"\n⚠️  NECESSÁRIO AJUSTE: Sistema precisa de mais calibração")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
