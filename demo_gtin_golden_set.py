#!/usr/bin/env python3
"""
Script de demonstração da gestão de GTIN e Golden Set
Mostra como usar as novas funcionalidades de revisão
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuração da API
API_BASE = "http://localhost:8000/api/v1"

def testar_validacao_gtin():
    """Testa a validação de códigos GTIN"""
    print("🧪 Testando validação de GTIN...")
    
    gtins_teste = [
        "7894900011517",  # Exemplo válido EAN13
        "12345678901",    # Exemplo inválido
        "789490001151",   # Exemplo incompleto
        "0123456789012",  # Exemplo UPC
    ]
    
    for gtin in gtins_teste:
        try:
            response = requests.post(f"{API_BASE}/gtin/validar", params={"gtin": gtin})
            if response.status_code == 200:
                resultado = response.json()
                status = "✅ VÁLIDO" if resultado["valido"] else "❌ INVÁLIDO"
                print(f"  GTIN {gtin}: {status} ({resultado.get('tipo', 'N/A')}) - {resultado.get('detalhes', '')}")
            else:
                print(f"  GTIN {gtin}: Erro HTTP {response.status_code}")
        except Exception as e:
            print(f"  GTIN {gtin}: Erro - {e}")

def testar_extracao_gtin():
    """Testa extração de GTIN de descrições"""
    print("\n🔍 Testando extração de GTIN de descrições...")
    
    descricoes_teste = [
        "Refrigerante Coca-Cola 350ml - EAN: 7894900011517",
        "Smartphone Samsung Galaxy A54 128GB GTIN 1234567890123 Azul",
        "Parafuso de aço inoxidável M6 x 20mm sem código",
        "Produto com código incorreto: 123456789",
    ]
    
    for descricao in descricoes_teste:
        try:
            response = requests.get(f"{API_BASE}/gtin/extrair-da-descricao", 
                                  params={"descricao": descricao})
            if response.status_code == 200:
                resultado = response.json()
                print(f"  Descrição: {descricao[:50]}...")
                for gtin in resultado["gtins_encontrados"]:
                    status = "✅" if gtin["valido"] else "❌"
                    print(f"    {status} {gtin['gtin']} ({gtin['tipo']}) - {gtin['detalhes']}")
            else:
                print(f"  Erro HTTP {response.status_code}")
        except Exception as e:
            print(f"  Erro - {e}")

def simular_revisao_com_gtin():
    """Simula processo de revisão incluindo gestão de GTIN"""
    print("\n🎯 Simulando processo de revisão com GTIN...")
    
    # Primeiro, vamos buscar classificações pendentes
    try:
        response = requests.get(f"{API_BASE}/classificacoes", 
                              params={"status": "PENDENTE_REVISAO", "limit": 1})
        if response.status_code == 200:
            classificacoes = response.json()
            if not classificacoes:
                print("  ℹ️  Nenhuma classificação pendente encontrada")
                return
            
            produto = classificacoes[0]
            print(f"  📦 Produto ID: {produto['produto_id']}")
            print(f"  📝 Descrição: {produto['descricao_produto']}")
            print(f"  🎯 NCM Sugerido: {produto.get('ncm_sugerido', 'N/A')}")
            print(f"  📊 CEST Sugerido: {produto.get('cest_sugerido', 'N/A')}")
            print(f"  🎲 Confiança: {produto.get('confianca_sugerida', 0):.2f}")
            
            # Buscar detalhes completos
            detalhes_response = requests.get(f"{API_BASE}/classificacoes/{produto['produto_id']}")
            if detalhes_response.status_code == 200:
                detalhes = detalhes_response.json()
                print(f"  🏷️  GTIN Atual: {detalhes.get('gtin_atual', 'N/A')}")
                print(f"  📍 Status GTIN: {detalhes.get('gtin_status', 'N/A')}")
                
                # Simular diferentes ações de revisão
                print("\n  🔄 Simulando ações possíveis:")
                print("     1. ✅ Aprovar classificação e GTIN")
                print("     2. ✏️  Corrigir NCM e manter GTIN")  
                print("     3. 🏷️  Corrigir GTIN e aprovar classificação")
                print("     4. 🏆 Adicionar ao Golden Set")
            
        else:
            print(f"  Erro ao buscar classificações: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  Erro na simulação: {e}")

def demonstrar_golden_set():
    """Demonstra funcionalidades do Golden Set"""
    print("\n🏆 Demonstrando Golden Set...")
    
    try:
        # Obter estatísticas do Golden Set
        response = requests.get(f"{API_BASE}/golden-set/estatisticas")
        if response.status_code == 200:
            stats = response.json()
            print(f"  📊 Total de entradas: {stats.get('total_entradas', 0)}")
            print(f"  📈 Entradas recentes (30 dias): {stats.get('entradas_recentes_30_dias', 0)}")
            
            confianca = stats.get('estatisticas_confianca', {})
            print(f"  🎯 Confiança média: {confianca.get('media', 0):.3f}")
            print(f"  📊 Range de confiança: {confianca.get('minima', 0):.3f} - {confianca.get('maxima', 0):.3f}")
            
            top_revisores = stats.get('top_revisores', [])
            if top_revisores:
                print("  👥 Top revisores:")
                for revisor in top_revisores[:3]:
                    print(f"     • {revisor['revisor']}: {revisor['total']} entradas")
        else:
            print(f"  Erro ao obter estatísticas: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  Erro ao acessar Golden Set: {e}")

def demonstrar_dashboard():
    """Mostra estatísticas do dashboard"""
    print("\n📊 Dashboard de Estatísticas...")
    
    try:
        response = requests.get(f"{API_BASE}/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"  📋 Total de classificações: {stats.get('total_classificacoes', 0)}")
            print(f"  ⏳ Pendentes de revisão: {stats.get('pendentes_revisao', 0)}")
            print(f"  ✅ Aprovadas: {stats.get('aprovadas', 0)}")
            print(f"  ✏️  Corrigidas: {stats.get('corrigidas', 0)}")
            print(f"  📈 Taxa de aprovação: {stats.get('taxa_aprovacao', 0):.1%}")
            print(f"  🎯 Confiança média: {stats.get('confianca_media', 0):.3f}")
        else:
            print(f"  Erro ao obter estatísticas: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  Erro ao acessar dashboard: {e}")

def verificar_api_disponivel():
    """Verifica se a API está disponível"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão com a API: {e}")
        return False

def main():
    """Função principal da demonstração"""
    print("🚀 DEMONSTRAÇÃO: Sistema de Revisão com GTIN e Golden Set")
    print("=" * 60)
    
    # Verificar se API está disponível
    print("🔌 Verificando conexão com a API...")
    if not verificar_api_disponivel():
        print("\n❌ ERRO: API não está disponível!")
        print("💡 Certifique-se de que a API está rodando:")
        print("   python src/main.py setup-review --start-api")
        print("   OU")
        print("   .\\start_api.ps1")
        return
    
    print("✅ API está disponível!\n")
    
    # Executar demonstrações
    demonstrar_dashboard()
    time.sleep(1)
    
    testar_validacao_gtin()
    time.sleep(1)
    
    testar_extracao_gtin()
    time.sleep(1)
    
    simular_revisao_com_gtin()
    time.sleep(1)
    
    demonstrar_golden_set()
    
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print(f"🌐 Interface web: http://localhost:8000")
    print(f"📚 Documentação: http://localhost:8000/api/docs")
    print("=" * 60)

if __name__ == "__main__":
    main()
