import requests
import json

def test_api():
    """Test básico da API de Review"""
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test 1: Health check
        print("🔍 Testando health check...")
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check OK:", response.json())
        else:
            print("❌ Health check falhou:", response.status_code)
            return
        
        # Test 2: Dashboard
        print("\n📊 Testando dashboard...")
        response = requests.get(f"{base_url}/api/dashboard")
        if response.status_code == 200:
            dashboard = response.json()
            print("✅ Dashboard OK:")
            print(f"  - Total classificações: {dashboard.get('total_classificacoes', 0)}")
            print(f"  - Pendentes de revisão: {dashboard.get('pendentes_revisao', 0)}")
        else:
            print("❌ Dashboard falhou:", response.status_code)
        
        # Test 3: Lista classificações (limit 5)
        print("\n📋 Testando lista de classificações...")
        response = requests.get(f"{base_url}/api/classificacoes?limit=5")
        if response.status_code == 200:
            classificacoes = response.json()
            print(f"✅ Lista OK: {len(classificacoes)} classificações encontradas")
            if classificacoes:
                primeira = classificacoes[0]
                print(f"  - Primeira: ID {primeira.get('id')} - {primeira.get('descricao_produto', 'N/A')[:50]}...")
        else:
            print("❌ Lista falhou:", response.status_code)
            
        print("\n🎉 Teste completo! API está funcionando.")
        print("🌐 Acesse http://127.0.0.1:8000/api/docs para a documentação interativa")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Certifique-se de que a API está rodando em http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_api()
