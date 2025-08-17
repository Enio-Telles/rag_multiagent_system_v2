#!/usr/bin/env python3
"""
Teste específico da integração ABC Farma com main.py
"""

import os
import sys
import json

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_main_abc_farma_integration():
    """Testar classificação de produtos farmacêuticos via main.py"""
    
    print("=" * 70)
    print("🧪 TESTE INTEGRAÇÃO ABC FARMA COM MAIN.PY")
    print("=" * 70)
    
    # Produtos de teste farmacêuticos
    test_products = [
        {
            "produto_id": 1,
            "descricao_produto": "Dipirona Sódica 500mg comprimidos caixa com 20",
            "codigo_produto": "DIPIRONA_500"
        },
        {
            "produto_id": 2, 
            "descricao_produto": "Paracetamol 750mg comprimidos caixa com 10",
            "codigo_produto": "PARACETAMOL_750"
        },
        {
            "produto_id": 3,
            "descricao_produto": "Amoxicilina 500mg cápsulas frasco com 21",
            "codigo_produto": "AMOXICILINA_500"
        },
        {
            "produto_id": 4,
            "descricao_produto": "Notebook Dell Inspiron 15 Intel i5",
            "codigo_produto": "NOTEBOOK_DELL"
        },
        {
            "produto_id": 5,
            "descricao_produto": "Simvastatina 20mg comprimidos revestidos",
            "codigo_produto": "SIMVASTATINA_20"
        }
    ]
    
    # Salvar produtos em arquivo temporário
    temp_file = "test_products_abc_farma.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(test_products, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Produtos de teste salvos em: {temp_file}")
    print(f"📦 Total de produtos: {len(test_products)}")
    print("\nProdutos de teste:")
    for product in test_products:
        print(f"  {product['produto_id']}. {product['descricao_produto']}")
    
    print(f"\n🔄 Executando classificação via main.py...")
    print("Command: python src/main.py classify --from-file test_products_abc_farma.json")
    
    # Executar main.py
    import subprocess
    try:
        result = subprocess.run([
            'python', 
            'src/main.py', 
            'classify', 
            '--from-file', 
            temp_file
        ], capture_output=True, text=True, cwd='.')
        
        print("\n📊 RESULTADO DA EXECUÇÃO:")
        print("-" * 50)
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
            
        print(f"\nCódigo de retorno: {result.returncode}")
        
        # Verificar se arquivo de resultado foi criado
        import glob
        result_files = glob.glob("resultados_classificacao_unified_*.json")
        if result_files:
            latest_file = max(result_files)
            print(f"\n📋 Arquivo de resultado: {latest_file}")
            
            # Ler e exibir resultados
            with open(latest_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                
            print(f"\n✅ Resultados da classificação ({len(results)} produtos):")
            for result in results:
                produto_id = result.get('produto_id')
                descricao = result.get('descricao_produto', '')[:50]
                ncm = result.get('ncm_classificado')
                confianca = result.get('confianca_consolidada', 0)
                sistema = result.get('sistema', 'N/A')
                
                print(f"  {produto_id}. {descricao}...")
                print(f"     NCM: {ncm} | Confiança: {confianca:.2f} | Sistema: {sistema}")
                
                # Verificar se produtos farmacêuticos foram classificados corretamente
                if 'dipirona' in descricao.lower() or 'paracetamol' in descricao.lower() or 'amoxicilina' in descricao.lower() or 'simvastatina' in descricao.lower():
                    if ncm == '30049099':
                        print(f"     ✅ Produto farmacêutico classificado corretamente!")
                    else:
                        print(f"     ❌ ERRO: Produto farmacêutico com NCM incorreto!")
                print()
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
    
    finally:
        # Limpar arquivo temporário
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"🗑️  Arquivo temporário removido: {temp_file}")

if __name__ == "__main__":
    test_main_abc_farma_integration()
