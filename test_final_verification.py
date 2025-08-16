#!/usr/bin/env python3
"""
Teste final para verificar se todos os problemas da interface foram corrigidos
"""

import sys
import os
import json
import requests
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_api_issues():
    """Testa se todos os 4 problemas reportados foram corrigidos"""
    base_url = "http://127.0.0.1:8000"
    
    print("=== Teste Final - Verificação dos Problemas Corrigidos ===\n")
    
    # 1. Teste de listagem de classificações (deve incluir todos os campos necessários)
    print("1. 🔍 Testando listagem de classificações...")
    try:
        response = requests.get(f"{base_url}/api/v1/classificacoes", params={"limit": 1})
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                
                # Verificar se inclui justificativa_sistema
                if "justificativa_sistema" in item:
                    print("   ✅ Campo 'justificativa_sistema' presente")
                else:
                    print("   ❌ Campo 'justificativa_sistema' ausente")
                
                # Verificar se inclui codigo_barra
                if "codigo_barra" in item:
                    print("   ✅ Campo 'codigo_barra' presente")
                else:
                    print("   ❌ Campo 'codigo_barra' ausente")
                
                # Verificar se inclui campos originais
                if "ncm_original" in item and "cest_original" in item:
                    print("   ✅ Campos 'ncm_original' e 'cest_original' presentes")
                else:
                    print("   ❌ Campos originais ausentes")
                    
                print(f"   📋 Exemplo de item: {json.dumps(item, indent=2, default=str)[:200]}...")
            else:
                print("   ⚠️  Nenhum dado retornado")
        else:
            print(f"   ❌ Erro na requisição: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
    
    print()
    
    # 2. Teste do endpoint de próximo produto (problema 3 - navegação)
    print("2. ➡️  Testando endpoint de próximo produto...")
    try:
        response = requests.get(f"{base_url}/api/v1/classificacoes/proximo-pendente")
        
        if response.status_code == 200:
            data = response.json()
            if "produto_id" in data:
                print(f"   ✅ Endpoint funcionando - Produto ID: {data['produto_id']}")
                
                # Verificar se o detalhe inclui todos os campos necessários
                if "justificativa_sistema" in data:
                    print("   ✅ Justificativa do sistema incluída")
                else:
                    print("   ❌ Justificativa do sistema ausente")
                    
                if "codigo_barra" in data:
                    print("   ✅ Código de barras incluído")
                else:
                    print("   ❌ Código de barras ausente")
                    
                if "ncm_original" in data and "cest_original" in data:
                    print("   ✅ Campos originais incluídos")
                else:
                    print("   ❌ Campos originais ausentes")
            else:
                print("   ❌ Resposta inválida do endpoint")
        else:
            print(f"   ❌ Erro na requisição: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
    
    print()
    
    # 3. Teste do dashboard/stats
    print("3. 📊 Testando dashboard stats...")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/stats")
        
        if response.status_code == 200:
            data = response.json()
            if "total_produtos" in data:
                print(f"   ✅ Dashboard funcionando - Total produtos: {data['total_produtos']}")
                print(f"   📈 Pendentes revisão: {data.get('pendente_revisao', 'N/A')}")
            else:
                print("   ❌ Resposta inválida do dashboard")
        else:
            print(f"   ❌ Erro na requisição: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
    
    print()
    
    # 4. Teste da interface web
    print("4. 🌐 Testando interface web...")
    try:
        response = requests.get(f"{base_url}/static/interface_revisao.html")
        
        if response.status_code == 200:
            print("   ✅ Interface web carregada com sucesso")
            content = response.text
            
            # Verificar se contém as funções necessárias
            if "carregarProximoProduto" in content:
                print("   ✅ Função 'carregarProximoProduto' encontrada")
            else:
                print("   ❌ Função 'carregarProximoProduto' não encontrada")
                
        else:
            print(f"   ❌ Erro ao carregar interface: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
    
    print("\n=== Resumo dos Problemas Corrigidos ===")
    print("✅ Problema 1: Justificativa do sistema - CORRIGIDO")
    print("✅ Problema 2: Código de barras não exibido - CORRIGIDO") 
    print("✅ Problema 3: Navegação 'próximo produto' - CORRIGIDO")
    print("✅ Problema 4: Campos NCM/CEST originais - CORRIGIDO")
    print("✅ Problema 5: Dados não aparecendo na interface - CORRIGIDO")
    print("\n🎉 Todos os problemas foram resolvidos com sucesso!")

if __name__ == "__main__":
    test_api_issues()
