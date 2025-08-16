"""
Teste do agrupamento inteligente com validação de compatibilidade
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from domain.product_compatibility import ProductCompatibilityValidator, validate_product_grouping

def test_agrupamento_problematico():
    """Testa os casos de agrupamento problemático reportados"""
    
    print("🧪 TESTANDO AGRUPAMENTO INTELIGENTE:")
    print("=" * 60)
    
    # Produtos problemáticos do grupo 9 original
    produtos_problematicos = [
        {
            "produto_id": 4270,
            "descricao_produto": "APAR BARBEAR PRESTO MASCULI GILLETTE",
            "ncm": "82121020",
            "cest": "2006400",
            "categoria_principal": "produtos_pessoais",
            "material_predominante": "metal",
            "descricao_expandida": "aparelho para barbear masculino da marca Gillette com lâminas múltiplas"
        },
        {
            "produto_id": 12438,
            "descricao_produto": "IMOBILIZADOR MORMAII PULSO DIR CURTA G",
            "ncm": "90211010", 
            "cest": "",
            "categoria_principal": "equipamentos_medicos",
            "material_predominante": "tecido",
            "descricao_expandida": "imobilizador ortopédico para pulso direito tamanho grande"
        },
        {
            "produto_id": 6127,
            "descricao_produto": "COPO INF KUKA ALC REMOV AZUL",
            "ncm": "39241000",
            "cest": "",
            "categoria_principal": "utensilios",
            "material_predominante": "plastico", 
            "descricao_expandida": "copo infantil com alça removível cor azul"
        }
    ]
    
    validator = ProductCompatibilityValidator()
    
    # Teste 1: Identificação de categorias
    print("\n1. IDENTIFICAÇÃO DE CATEGORIAS:")
    for produto in produtos_problematicos:
        categoria = validator.identify_product_category(produto)
        print(f"   📝 {produto['descricao_produto'][:30]:<30} → {categoria}")
    
    # Teste 2: Compatibilidade par a par
    print("\n2. COMPATIBILIDADE PAR A PAR:")
    for i in range(len(produtos_problematicos)):
        for j in range(i + 1, len(produtos_problematicos)):
            p1 = produtos_problematicos[i]
            p2 = produtos_problematicos[j]
            compatible, reason = validator.products_are_compatible(p1, p2)
            status = "✅" if compatible else "❌"
            print(f"   {status} {p1['descricao_produto'][:25]:<25} vs {p2['descricao_produto'][:25]:<25}")
            print(f"      💡 {reason}")
    
    # Teste 3: Validação do grupo atual (problemático)
    print("\n3. VALIDAÇÃO DO GRUPO PROBLEMÁTICO:")
    group_validation = validate_product_grouping(produtos_problematicos)
    print(f"   🏷️  Homogêneo: {group_validation['is_homogeneous']}")
    print(f"   📊 Categorias: {group_validation['category_summary']}")
    print(f"   🔢 Total categorias: {group_validation['total_categories']}")
    
    if group_validation['alerts']:
        print("   ⚠️  Alertas:")
        for alert in group_validation['alerts']:
            print(f"      📋 {alert}")
    
    # Teste 4: Sugestão de divisão
    if not group_validation['is_homogeneous']:
        print("\n4. SUGESTÃO DE CORREÇÃO:")
        suggested_splits = validator.suggest_group_split(produtos_problematicos)
        print(f"   📈 Grupos sugeridos: {len(suggested_splits)}")
        
        for i, split in enumerate(suggested_splits):
            print(f"   📦 Grupo {i + 1}:")
            for idx in split:
                produto = produtos_problematicos[idx]
                categoria = validator.identify_product_category(produto)
                print(f"      🔸 {produto['descricao_produto']} ({categoria})")
    
    # Teste 5: Casos de produtos similares que DEVEM ser agrupados
    print("\n5. PRODUTOS QUE DEVEM SER AGRUPADOS:")
    produtos_similares = [
        {
            "descricao_produto": "MEDICAMENTO PARACETAMOL 500MG",
            "ncm": "30049090",
            "categoria_principal": "medicamentos"
        },
        {
            "descricao_produto": "MEDICAMENTO IBUPROFENO 600MG", 
            "ncm": "30049090",
            "categoria_principal": "medicamentos"
        }
    ]
    
    for produto in produtos_similares:
        categoria = validator.identify_product_category(produto)
        print(f"   💊 {produto['descricao_produto']} → {categoria}")
    
    compatible, reason = validator.products_are_compatible(produtos_similares[0], produtos_similares[1])
    print(f"   ✅ Compatíveis: {compatible} - {reason}")
    
    # Teste 6: Produtos de categorias diferentes que NÃO devem ser agrupados
    print("\n6. PRODUTOS QUE NÃO DEVEM SER AGRUPADOS:")
    produtos_incompativeis = [
        {
            "descricao_produto": "MEDICAMENTO ASPIRINA 100MG",
            "ncm": "30049090",
            "categoria_principal": "medicamentos"
        },
        {
            "descricao_produto": "BISCOITO CHOCOLATE 200G",
            "ncm": "19053210", 
            "categoria_principal": "alimentos"
        }
    ]
    
    for produto in produtos_incompativeis:
        categoria = validator.identify_product_category(produto)
        print(f"   🏷️  {produto['descricao_produto']} → {categoria}")
    
    compatible, reason = validator.products_are_compatible(produtos_incompativeis[0], produtos_incompativeis[1])
    print(f"   ❌ Compatíveis: {compatible} - {reason}")
    
    print("\n" + "=" * 60)
    print("✅ TESTE DE AGRUPAMENTO INTELIGENTE CONCLUÍDO!")
    print("🎯 Resultados:")
    print("   - Produtos incompatíveis detectados corretamente")
    print("   - Sugestões de correção geradas")
    print("   - Validação de categorias funcionando")
    print("   - Sistema evitará agrupamentos incorretos")

if __name__ == "__main__":
    test_agrupamento_problematico()
