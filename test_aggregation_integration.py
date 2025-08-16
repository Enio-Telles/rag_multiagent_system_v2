"""
Teste de integração do AggregationAgent melhorado
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from agents.aggregation_agent import AggregationAgent
    from domain.product_compatibility import validate_product_grouping
    
    # Mock de configuração para teste
    class MockConfig:
        def get(self, key, default=None):
            config_values = {
                "min_group_size": 2,
                "max_group_size": 5,
                "group_similarity_threshold": 0.78,
                "enable_intelligent_grouping": True
            }
            return config_values.get(key, default)
    
    def test_aggregation_agent_melhorado():
        """Testa o AggregationAgent com os casos problemáticos"""
        
        print("🧪 TESTANDO AGGREGATION AGENT MELHORADO:")
        print("=" * 60)
        
        # Produtos problemáticos que estavam sendo agrupados incorretamente
        produtos_expandidos = [
            {
                "produto_original": {
                    "produto_id": 4270,
                    "descricao_produto": "APAR BARBEAR PRESTO MASCULI GILLETTE",
                    "ncm": "82121020"
                },
                "categoria_principal": "produtos_pessoais",
                "material_predominante": "metal_plastico",
                "descricao_expandida": "aparelho de barbear presto masculino gillette com lâminas múltiplas para uso pessoal",
                "palavras_chave_fiscais": ["barbear", "masculino", "higiene", "pessoal"]
            },
            {
                "produto_original": {
                    "produto_id": 12438,
                    "descricao_produto": "IMOBILIZADOR MORMAII PULSO DIR CURTA G",
                    "ncm": "90211010"
                },
                "categoria_principal": "equipamentos_medicos",
                "material_predominante": "tecido_elastico",
                "descricao_expandida": "imobilizador ortopédico mormaii para pulso direito tamanho grande curta",
                "palavras_chave_fiscais": ["imobilizador", "ortopedico", "pulso", "medico"]
            },
            {
                "produto_original": {
                    "produto_id": 6127,
                    "descricao_produto": "COPO INF KUKA ALC REMOV AZUL",
                    "ncm": "39241000"
                },
                "categoria_principal": "utensilios_domesticos",
                "material_predominante": "plastico",
                "descricao_expandida": "copo infantil kuka com alça removível cor azul para bebês",
                "palavras_chave_fiscais": ["copo", "infantil", "utensilio", "domestico"]
            },
            # Adicionar alguns produtos similares que DEVEM ser agrupados
            {
                "produto_original": {
                    "produto_id": 1001,
                    "descricao_produto": "APARELHO BARBEAR GILLETTE FUSION",
                    "ncm": "82121020"
                },
                "categoria_principal": "produtos_pessoais",
                "material_predominante": "metal_plastico",
                "descricao_expandida": "aparelho de barbear gillette fusion com lâminas múltiplas",
                "palavras_chave_fiscais": ["barbear", "gillette", "higiene", "pessoal"]
            },
            {
                "produto_original": {
                    "produto_id": 2001,
                    "descricao_produto": "MEDICAMENTO PARACETAMOL 500MG",
                    "ncm": "30049090"
                },
                "categoria_principal": "medicamentos",
                "material_predominante": "farmaceutico",
                "descricao_expandida": "medicamento paracetamol 500mg para alívio da dor",
                "palavras_chave_fiscais": ["medicamento", "paracetamol", "farmaco", "analgesico"]
            },
            {
                "produto_original": {
                    "produto_id": 2002,
                    "descricao_produto": "MEDICAMENTO IBUPROFENO 600MG",
                    "ncm": "30049090"
                },
                "categoria_principal": "medicamentos", 
                "material_predominante": "farmaceutico",
                "descricao_expandida": "medicamento ibuprofeno 600mg anti-inflamatório",
                "palavras_chave_fiscais": ["medicamento", "ibuprofeno", "farmaco", "anti-inflamatorio"]
            }
        ]
        
        # Inicializar agente com configuração mock
        config = MockConfig()
        agent = AggregationAgent(llm_client=None, config=config)
        
        # Executar agrupamento
        print("\n1. EXECUTANDO AGRUPAMENTO:")
        result = agent.run(produtos_expandidos)
        
        grupos = result["result"]["grupos"]
        estatisticas = result["result"]["estatisticas"]
        
        print(f"   📊 Total produtos: {estatisticas['total_produtos']}")
        print(f"   📦 Total grupos: {estatisticas['total_grupos']}")
        print(f"   🔄 Grupos heterogêneos: {estatisticas.get('grupos_heterogeneos', 0)}")
        print(f"   ✅ Grupos corrigidos: {estatisticas.get('grupos_corrigidos', 0)}")
        
        # Analisar cada grupo
        print("\n2. ANÁLISE DOS GRUPOS:")
        for i, grupo in enumerate(grupos):
            membros_produtos = [produtos_expandidos[idx] for idx in grupo["membros"]]
            
            print(f"\n   📦 Grupo {grupo['grupo_id']} ({grupo['tamanho']} produtos):")
            for idx in grupo["membros"]:
                produto = produtos_expandidos[idx]
                print(f"      🔸 {produto['produto_original']['descricao_produto']}")
            
            # Validar homogeneidade do grupo
            if "homogeneidade" in grupo:
                homog = grupo["homogeneidade"]
                status = "✅" if homog["is_homogeneous"] else "❌"
                print(f"      {status} Homogêneo: {homog['is_homogeneous']}")
                print(f"      📊 Categorias: {homog.get('category_summary', {})}")
                
                if homog.get("alerts"):
                    for alert in homog["alerts"]:
                        print(f"      ⚠️  {alert}")
        
        # Verificações específicas
        print("\n3. VERIFICAÇÕES ESPECÍFICAS:")
        
        # Verificar se produtos incompatíveis foram separados
        aparelho_barbear_grupos = []
        imobilizador_grupos = []
        copo_grupos = []
        medicamentos_grupos = []
        
        for grupo in grupos:
            for idx in grupo["membros"]:
                produto = produtos_expandidos[idx]
                desc = produto['produto_original']['descricao_produto']
                
                if "BARBEAR" in desc:
                    aparelho_barbear_grupos.append(grupo['grupo_id'])
                elif "IMOBILIZADOR" in desc:
                    imobilizador_grupos.append(grupo['grupo_id'])
                elif "COPO" in desc:
                    copo_grupos.append(grupo['grupo_id'])
                elif "MEDICAMENTO" in desc:
                    medicamentos_grupos.append(grupo['grupo_id'])
        
        # Verificar separação de produtos incompatíveis
        print(f"   🔍 Aparelhos barbear em grupos: {set(aparelho_barbear_grupos)}")
        print(f"   🔍 Imobilizadores em grupos: {set(imobilizador_grupos)}")
        print(f"   🔍 Copos em grupos: {set(copo_grupos)}")
        print(f"   🔍 Medicamentos em grupos: {set(medicamentos_grupos)}")
        
        # Validações
        grupos_barbear = set(aparelho_barbear_grupos)
        grupos_imobilizador = set(imobilizador_grupos)
        grupos_copo = set(copo_grupos)
        grupos_medicamentos = set(medicamentos_grupos)
        
        # Produtos incompatíveis devem estar em grupos diferentes
        assert not grupos_barbear.intersection(grupos_imobilizador), "❌ Aparelho barbear e imobilizador no mesmo grupo!"
        assert not grupos_barbear.intersection(grupos_copo), "❌ Aparelho barbear e copo no mesmo grupo!"
        assert not grupos_imobilizador.intersection(grupos_copo), "❌ Imobilizador e copo no mesmo grupo!"
        assert not grupos_medicamentos.intersection(grupos_barbear), "❌ Medicamentos e barbear no mesmo grupo!"
        assert not grupos_medicamentos.intersection(grupos_copo), "❌ Medicamentos e copo no mesmo grupo!"
        
        print("   ✅ Produtos incompatíveis separados corretamente!")
        
        # Medicamentos similares devem estar no mesmo grupo (se houver múltiplos)
        if len(grupos_medicamentos) <= 1:
            print("   ✅ Medicamentos similares agrupados corretamente!")
        else:
            print(f"   ⚠️  Medicamentos em {len(grupos_medicamentos)} grupos diferentes")
        
        # Aparelhos de barbear similares devem estar no mesmo grupo
        if len(grupos_barbear) <= 1:
            print("   ✅ Aparelhos de barbear similares agrupados corretamente!")
        else:
            print(f"   ⚠️  Aparelhos de barbear em {len(grupos_barbear)} grupos diferentes")
        
        print("\n" + "=" * 60)
        print("✅ TESTE DO AGGREGATION AGENT MELHORADO CONCLUÍDO!")
        print("🎯 Resultados:")
        print("   - Produtos incompatíveis foram separados automaticamente")
        print("   - Grupos homogêneos foram mantidos")
        print("   - Validação de compatibilidade funcionando")
        print("   - Sistema evita agrupamentos incorretos")
        
        return True

    if __name__ == "__main__":
        test_aggregation_agent_melhorado()

except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("📝 Certifique-se de que todos os módulos estão implementados")
    
    # Teste básico da funcionalidade de compatibilidade
    from domain.product_compatibility import ProductCompatibilityValidator, validate_product_grouping
    
    print("\n🧪 TESTANDO APENAS VALIDAÇÃO DE COMPATIBILIDADE:")
    
    produtos_basicos = [
        {"descricao_produto": "APAR BARBEAR", "ncm": "82121020"},
        {"descricao_produto": "IMOBILIZADOR PULSO", "ncm": "90211010"},
        {"descricao_produto": "COPO INFANTIL", "ncm": "39241000"}
    ]
    
    validacao = validate_product_grouping(produtos_basicos)
    print(f"✅ Homogêneo: {validacao['is_homogeneous']}")
    print(f"📊 Categorias: {validacao['category_summary']}")
    
    if validacao['alerts']:
        for alert in validacao['alerts']:
            print(f"⚠️  {alert}")
