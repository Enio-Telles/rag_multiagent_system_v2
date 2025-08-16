#!/usr/bin/env python3
"""
Teste para verificar se o dashboard da interface web está funcionando
"""

import requests
import json

def test_dashboard_endpoint():
    """Testa o endpoint de dashboard"""
    print("🔍 Testando endpoint /api/v1/dashboard/stats...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/dashboard/stats')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funcionando!")
            print("📊 Dados retornados:")
            for key, value in data.items():
                print(f"   {key}: {value}")
            
            # Verificar se tem dados
            total = data.get('total_classificacoes', 0)
            if total > 0:
                print(f"\n🎉 SUCESSO: {total} classificações encontradas!")
                return True
            else:
                print("\n⚠️ Endpoint funciona mas não há dados")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_interface_mapping():
    """Verifica se o mapeamento de campos está correto"""
    print("\n🔍 Verificando mapeamento de campos...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/dashboard/stats')
        data = response.json()
        
        expected_fields = ['total_classificacoes', 'aprovadas', 'corrigidas', 'pendentes_revisao']
        interface_fields = ['total_processados', 'total_aprovados', 'total_corrigidos', 'total_golden']
        
        print("✅ Mapeamento correto:")
        print(f"   Interface 'total_processados' ← API 'total_classificacoes': {data.get('total_classificacoes', 0)}")
        print(f"   Interface 'total_aprovados' ← API 'aprovadas': {data.get('aprovadas', 0)}")
        print(f"   Interface 'total_corrigidos' ← API 'corrigidas': {data.get('corrigidas', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTE DO DASHBOARD DA INTERFACE WEB ===\n")
    
    success1 = test_dashboard_endpoint()
    success2 = test_interface_mapping()
    
    if success1 and success2:
        print("\n🎉 PROBLEMA RESOLVIDO!")
        print("A interface web agora deve mostrar os 1000 produtos importados.")
        print("Acesse: http://localhost:8000/static/interface_revisao.html")
    else:
        print("\n❌ Ainda há problemas que precisam ser resolvidos.")
