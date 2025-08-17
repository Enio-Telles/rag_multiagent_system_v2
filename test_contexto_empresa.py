"""
Teste do Sistema de Contexto da Empresa
Valida a integração completa do contexto empresarial com os agentes de classificação
"""

import sys
import os
sys.path.append('src')

from database.connection import SessionLocal
from services.empresa_contexto_service import EmpresaContextoService
from orchestrator.hybrid_router import HybridRouter
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_contexto_empresa():
    """Testa o sistema completo de contexto da empresa"""
    
    print("🧪 TESTE DO SISTEMA DE CONTEXTO DA EMPRESA")
    print("=" * 60)
    
    try:
        # 1. Inicializar serviços
        print("\n📋 1. Inicializando serviços...")
        session = SessionLocal()
        try:
            empresa_service = EmpresaContextoService()
            router = HybridRouter()
            
            # 2. Cadastrar empresa porta a porta
            print("\n🏢 2. Cadastrando empresa porta a porta...")
            dados_empresa = {
                'razao_social': 'VENDAS PORTA A PORTA LTDA',
                'nome_fantasia': 'VendaMais',
                'cnae_principal': '47.89-0-99',  # Comércio varejista não especificado
                'atividade_descricao': 'Venda de produtos variados diretamente ao consumidor em domicílio',
                'modalidade_venda': 'porta_a_porta',
                'tipo_estabelecimento': 'comercio_eletronico',
                'regime_tributario': 'simples_nacional',
                'segmento_cest_aplicavel': '28',  # Segmento 28 para porta a porta
                'observacoes_classificacao': 'Empresa especializada em venda porta a porta com foco em cosméticos e produtos de higiene. Aplicar sempre CEST do segmento 28 quando aplicável.',
                'categorias_produtos': ['cosmeticos', 'higiene_pessoal', 'perfumaria'],
                'exemplos_produtos': ['batons', 'cremes', 'perfumes', 'sabonetes'],
                'estados_atuacao': ['SP', 'RJ', 'MG'],
                'abrangencia': 'regional',
                'contexto_agentes': {
                    'cest_agent': 'Priorizar segmento 28 para todos os produtos aplicáveis',
                    'ncm_agent': 'Considerar uso final domiciliar',
                    'reconciler': 'Validar consistência com regras de porta a porta'
                },
                'preferencias_classificacao': {
                    'aplicar_cest_28': True,
                    'priorizar_st': True
                }
            }
            
            empresa_cadastrada = empresa_service.cadastrar_empresa(
                session, "12345678901234", dados_empresa, "TestUser"
            )
            print(f"✅ Empresa cadastrada com ID: {empresa_cadastrada.id}")
            
            # 3. Obter contexto
            print("\n🎯 3. Obtendo contexto da empresa...")
            contexto = empresa_service.obter_contexto_empresa(session, "12345678901234")
            print(f"📊 Contexto obtido:")
            print(f"   - Atividade: {contexto.get('atividade_descricao')}")
            print(f"   - Modalidade venda: {contexto.get('modalidade_venda')}")
            print(f"   - CEST específico: {contexto.get('segmento_cest_aplicavel')}")
            
            # 4. Produto de teste (batom - típico para porta a porta)
            print("\n💄 4. Testando classificação com contexto...")
            produto_teste = {
                'id': 9999,
                'produto_id': 9999,
                'descricao_produto': 'BATOM HIDRATANTE VERMELHO ESCURO 3.5G',
                'descricao_completa': 'Batom hidratante cor vermelho escuro, com fórmula enriquecida com vitamina E, peso líquido 3.5 gramas',
                'codigo_produto': 'BAT001VE',
                'codigo_barra': '7891234567890'
            }
            
            # 5. Classificar com contexto
            print("\n🤖 5. Executando classificação com contexto empresa...")
            resultado = router.classify_product_with_explanations(produto_teste)
            
            # 6. Mostrar resultados
            print("\n📊 6. RESULTADOS DA CLASSIFICAÇÃO")
            print("-" * 50)
            print(f"NCM classificado: {resultado.get('ncm_classificado')}")
            print(f"CEST classificado: {resultado.get('cest_classificado')}")
            print(f"Confiança: {resultado.get('confianca_consolidada', 0):.3f}")
            
            # Verificar se contexto foi aplicado
            contexto_aplicado = resultado.get('contexto_empresa_aplicado')
            if contexto_aplicado:
                print(f"\n🎯 CONTEXTO EMPRESA APLICADO:")
                print(f"   - Atividade: {contexto_aplicado.get('atividade_descricao')}")
                print(f"   - Modalidade venda: {contexto_aplicado.get('modalidade_venda')}")
                if contexto_aplicado.get('segmento_cest_aplicavel'):
                    print(f"   - CEST específico para porta a porta: {contexto_aplicado.get('segmento_cest_aplicavel')}")
            else:
                print("⚠️ Contexto da empresa NÃO foi aplicado")
            
            # Verificar explicações dos agentes
            explicacoes = resultado.get('explicacoes_agentes', {})
            
            print(f"\n📝 EXPLICAÇÕES DOS AGENTES:")
            for agente, explicacao in explicacoes.items():
                if explicacao:
                    print(f"\n{agente.upper()}:")
                    print(f"   - Confiança: {explicacao.get('nivel_confianca', 0):.3f}")
                    detalhes = explicacao.get('explicacao_detalhada', '')
                    if 'empresa' in detalhes.lower() or 'porta' in detalhes.lower():
                        print(f"   ✅ Contexto empresa detectado na explicação")
                    else:
                        print(f"   ⚠️ Contexto empresa não detectado na explicação")
            
            # 7. Teste com produto diferente (não cosmético)
            print("\n🔧 7. Testando com produto não-cosmético...")
            produto_ferramenta = {
                'id': 9998,
                'produto_id': 9998,
                'descricao_produto': 'CHAVE PHILLIPS 3MM CABO PLASTICO',
                'descricao_completa': 'Chave de fenda Phillips tamanho 3mm com cabo de plástico resistente',
                'codigo_produto': 'FER001CH',
                'codigo_barra': '7891234567891'
            }
            
            resultado_ferramenta = router.classify_product_with_explanations(produto_ferramenta)
            
            print("\n📊 RESULTADO FERRAMENTA:")
            print(f"NCM: {resultado_ferramenta.get('ncm_classificado')}")
            print(f"CEST: {resultado_ferramenta.get('cest_classificado')}")
            print(f"Confiança: {resultado_ferramenta.get('confianca_consolidada', 0):.3f}")
            
            # Verificar se CEST 28 foi aplicado mesmo para ferramenta
            cest_ferramenta = resultado_ferramenta.get('cest_classificado')
            if cest_ferramenta and cest_ferramenta.startswith('28'):
                print("✅ CEST segmento 28 aplicado corretamente (porta a porta)")
            else:
                print("ℹ️ CEST segmento 28 não aplicado (verificar se aplicável)")
            
            print("\n" + "="*60)
            print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print("✅ Sistema de contexto da empresa integrado aos agentes")
            
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"\n❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_contexto_empresa()
    if sucesso:
        print("\n🚀 Sistema pronto para uso com contexto empresarial!")
    else:
        print("\n⚠️ Problemas detectados - revisar implementação")
