import requests
import time

def test_api():
    print("🧪 Testando API com novas funcionalidades...")
    
    try:
        # Testar health check
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        print(f'✅ Health check: {response.status_code}')
        if response.status_code == 200:
            print(f'   Response: {response.json()}')
        
        # Testar validação de GTIN
        gtin_response = requests.post('http://localhost:8000/api/v1/gtin/validar?gtin=7894900011517', timeout=5)
        print(f'✅ GTIN validation: {gtin_response.status_code}')
        if gtin_response.status_code == 200:
            result = gtin_response.json()
            valido = result.get('valido', False)
            tipo = result.get('tipo', 'N/A')
            print(f'   GTIN válido: {valido}, Tipo: {tipo}')
        
        # Testar extração de GTIN
        extract_response = requests.get('http://localhost:8000/api/v1/gtin/extrair-da-descricao?descricao=Produto com EAN 7894900011517', timeout=5)
        print(f'✅ GTIN extraction: {extract_response.status_code}')
        if extract_response.status_code == 200:
            result = extract_response.json()
            total = result.get('total', 0)
            print(f'   GTINs encontrados: {total}')
            for gtin in result.get('gtins_encontrados', []):
                print(f'     - {gtin["gtin"]} ({gtin["tipo"]}) - Válido: {gtin["valido"]}')

    except Exception as e:
        print(f'❌ Erro: {e}')

if __name__ == "__main__":
    test_api()
