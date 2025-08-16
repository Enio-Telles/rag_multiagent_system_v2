import json

# Carregar o mapeamento
with open(r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\knowledge_base\ncm_mapping.json", 'r', encoding='utf-8') as f:
    mapping = json.load(f)

# Encontrar NCM 3004 para ver a estrutura real dos CESTs
for item in mapping:
    if item['ncm_codigo'] == '3004':
        print("🔍 Estrutura dos CESTs do NCM 3004:")
        print("=" * 50)
        cests = item.get('cests_associados', [])
        print(f"Total de CESTs: {len(cests)}")
        
        if cests:
            print("\\nPrimeiro CEST (estrutura completa):")
            first_cest = cests[0]
            for key, value in first_cest.items():
                print(f"  {key}: {value}")
            
            print("\\nTodos os códigos CEST:")
            for i, cest in enumerate(cests):
                # Tentar diferentes chaves possíveis
                codigo = (cest.get('CEST') or 
                         cest.get('cest_codigo') or 
                         cest.get('cest') or 
                         'N/A')
                
                descricao = (cest.get('DESCRIÇÃO') or 
                           cest.get('DESCRICAO') or 
                           cest.get('descricao') or 
                           'N/A')[:40]
                
                print(f"  {i+1:2d}. {codigo}: {descricao}...")
        break
