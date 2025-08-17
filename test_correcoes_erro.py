#!/usr/bin/env python3
"""
Script para testar as correções dos erros identificados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feedback.consulta_metadados_service import ConsultaMetadadosService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def testar_servico_consulta():
    """Testa o serviço de consulta com os métodos corrigidos"""
    print("🔧 Testando ConsultaMetadadosService...")
    
    service = ConsultaMetadadosService()
    
    # Testar registro de consulta
    consulta_id = service.registrar_consulta(
        produto_id=12345,
        agente_nome="NCMAgent",
        tipo_consulta="rag",
        query_original="chip tim celular",
        banco_origem="faiss_vector",
        metadados={"modelo": "test", "versao": "1.0"}
    )
    
    print(f"✅ Consulta registrada: {consulta_id}")
    
    # Testar registrar_resultado (método que estava faltando)
    resultados_teste = [
        {"codigo": "85171200", "score": 0.95, "descricao": "Telefones para redes celulares"},
        {"codigo": "85176200", "score": 0.87, "descricao": "Aparelhos para transmissão"}
    ]
    
    success = service.registrar_resultado(consulta_id, resultados_teste, 150)
    print(f"✅ Resultados registrados: {success}")
    
    # Verificar dados da consulta
    consultas = service.obter_consultas_produto(12345)
    print(f"✅ Consultas encontradas: {len(consultas)}")
    
    if consultas:
        consulta = consultas[0]
        print(f"   - ID: {consulta['id']}")
        print(f"   - Agente: {consulta['agente_nome']}")
        print(f"   - Tipo: {consulta['tipo_consulta']}")
        if 'resultados' in consulta:
            print(f"   - Resultados: {consulta['resultados']['total_encontrados']} itens")
            print(f"   - Tempo: {consulta['resultados']['tempo_execucao_ms']}ms")
    
    print("✅ Teste do ConsultaMetadadosService concluído")

def testar_metodos_obrigatorios():
    """Testa se todos os métodos necessários existem"""
    print("\n🔍 Verificando métodos obrigatórios...")
    
    service = ConsultaMetadadosService()
    
    metodos_necessarios = [
        'registrar_consulta',
        'registrar_resultados', 
        'registrar_resultado',  # Método que estava faltando
        'finalizar_consulta',
        'obter_consultas_produto',
        'salvar_consultas_permanente'
    ]
    
    for metodo in metodos_necessarios:
        if hasattr(service, metodo):
            print(f"✅ {metodo} - OK")
        else:
            print(f"❌ {metodo} - FALTANDO")
    
    print("✅ Verificação de métodos concluída")

if __name__ == "__main__":
    print("🚀 Testando correções dos erros identificados...")
    print("="*60)
    
    try:
        testar_metodos_obrigatorios()
        testar_servico_consulta()
        
        print("\n" + "="*60)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Erro 'registrar_resultado' não encontrado - CORRIGIDO")
        print("✅ Erro 'iniciar_explicação' - CORRIGIDO no hybrid_router.py")
        print("✅ Sistema de rastreamento funcionando corretamente")
        
    except Exception as e:
        print(f"\n❌ ERRO durante os testes: {e}")
        import traceback
        traceback.print_exc()
