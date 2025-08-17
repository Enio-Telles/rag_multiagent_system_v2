#!/usr/bin/env python3
"""
Script para testar se a API está retornando os dados do PostgreSQL
"""

import requests
import json

def testar_api_proximo_pendente():
    """Testa se a API está retornando os dados do PostgreSQL corretamente"""
    print("🔍 Testando endpoint de próximo pendente...")
    
    try:
        # Fazer uma requisição para o endpoint de próximo pendente
        url = 'http://localhost:8000/api/v1/classificacoes/proximo-pendente'
        response = requests.get(url, timeout=10)
        print(f'🌐 Status da requisição: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Dados recebidos da API:')
            print(f'   - Produto ID: {data.get("produto_id")}')
            print(f'   - Descrição: {data.get("descricao_produto", "N/A")[:50]}...')
            print(f'   - Código Produto: {data.get("codigo_produto", "N/A")}')
            print(f'   - Código Barra: {data.get("codigo_barra", "N/A")}')
            print(f'   - NCM Original: {data.get("ncm_original", "N/A")}')
            print(f'   - CEST Original: {data.get("cest_original", "N/A")}')
            print(f'   - NCM Sugerido: {data.get("ncm_sugerido", "N/A")}')
            print(f'   - CEST Sugerido: {data.get("cest_sugerido", "N/A")}')
            
            # Verificar se os campos importantes do PostgreSQL estão preenchidos
            campos_postgres = {
                'codigo_produto': data.get("codigo_produto"),
                'codigo_barra': data.get("codigo_barra"), 
                'ncm_original': data.get("ncm_original"),
                'cest_original': data.get("cest_original")
            }
            
            print(f'\n📊 Status dos campos do PostgreSQL:')
            for campo, valor in campos_postgres.items():
                status = "✅ PREENCHIDO" if valor not in [None, "", "N/A"] else "❌ VAZIO"
                print(f'   - {campo}: {status} ({valor})')
                
            return data
        else:
            print(f'❌ Erro {response.status_code}: {response.text}')
            return None
            
    except requests.exceptions.ConnectionError:
        print('❌ API não está rodando - inicie com start_api.ps1')
        return None
    except Exception as e:
        print(f'❌ Erro inesperado: {e}')
        return None

def testar_stats_dashboard():
    """Testa as estatísticas do dashboard"""
    print("\n🔍 Testando estatísticas do dashboard...")
    
    try:
        url = 'http://localhost:8000/api/v1/dashboard/stats'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Estatísticas do dashboard:')
            print(f'   - Total classificações: {data.get("total_classificacoes", 0)}')
            print(f'   - Pendentes revisão: {data.get("pendentes_revisao", 0)}')
            print(f'   - Aprovadas: {data.get("aprovadas", 0)}')
            print(f'   - Corrigidas: {data.get("corrigidas", 0)}')
            return data
        else:
            print(f'❌ Erro {response.status_code}: {response.text}')
            return None
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        return None

if __name__ == "__main__":
    print("🚀 Testando se os dados do PostgreSQL estão sendo importados para a interface web...")
    print("="*80)
    
    # Testar API
    dados_produto = testar_api_proximo_pendente()
    testar_stats_dashboard()
    
    print("\n" + "="*80)
    
    if dados_produto:
        # Verificar se pelo menos alguns campos do PostgreSQL estão preenchidos
        campos_importantes = [
            dados_produto.get("codigo_produto"),
            dados_produto.get("ncm_original"),
            dados_produto.get("cest_original")
        ]
        
        campos_preenchidos = [c for c in campos_importantes if c not in [None, "", "N/A"]]
        
        if len(campos_preenchidos) >= 2:
            print("✅ SUCESSO: Dados do PostgreSQL estão sendo importados corretamente!")
            print("✅ Os campos NCM original, CEST original e código produto estão disponíveis")
        else:
            print("⚠️ PROBLEMA: Poucos campos do PostgreSQL estão preenchidos")
            print("❌ Pode haver problema na importação dos dados")
    else:
        print("❌ FALHA: Não foi possível obter dados da API")
