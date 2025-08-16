#!/usr/bin/env python3
"""
Teste Básico do Sistema de Explicações
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from config import Config
from orchestrator.hybrid_router import HybridRouter

def teste_basico():
    """Teste básico de classificação com explicações"""
    print("🧪 TESTE BÁSICO DE EXPLICAÇÕES")
    print("=" * 50)
    
    try:
        # Inicializar sistema
        router = HybridRouter()
        
        # Produto de teste
        produto = "Notebook Dell Inspiron 15 Intel i5 8GB RAM"
        
        print(f"📱 Produto: {produto}")
        print("🔄 Executando classificação...")
        
        # Classificar produto
        produto_dict = {"descricao_produto": produto}
        resultado = router.classify_products([produto_dict])[0]
        
        print(f"✅ RESULTADO:")
        print(f"  📋 NCM: {resultado.get('ncm', 'N/A')}")
        print(f"  🏷️ CEST: {resultado.get('cest', 'N/A')}")
        print(f"  📊 Confiança: {resultado.get('confidence', 0.0):.3f}")
        
        # Testar serviço de explicações diretamente
        print("\n🔍 TESTANDO SERVIÇO DE EXPLICAÇÕES...")
        
        from feedback.explicacao_service import ExplicacaoService
        
        explicacao_service = ExplicacaoService()
        
        # Salvar uma explicação de teste
        explicacao_data = {
            "agente_nome": "test",
            "input_original": produto,
            "explicacao_detalhada": "Teste de explicação",
            "nivel_confianca": 0.85,
            "tempo_processamento_ms": 150
        }
        
        sucesso = explicacao_service.salvar_explicacao(9999, None, explicacao_data)
        print(f"  💾 Salvar explicação: {'✅' if sucesso else '❌'}")
        
        # Recuperar explicações
        explicacoes = explicacao_service.obter_explicacoes_produto(9999)
        print(f"  📋 Explicações encontradas: {explicacoes.get('total_explicacoes', 0)}")
        
        # Relatório básico
        relatorio = explicacao_service.gerar_relatorio_agente("test")
        if "erro" not in relatorio:
            print(f"  📊 Relatório gerado: ✅")
            print(f"    - Execuções: {relatorio.get('total_execucoes', 0)}")
        else:
            print(f"  📊 Relatório: ❌ {relatorio.get('erro', 'Erro desconhecido')}")
        
        print("\n🎉 TESTE BÁSICO CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    teste_basico()
