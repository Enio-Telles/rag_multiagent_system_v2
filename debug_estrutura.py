import json

# Carregar o mapeamento atual
with open(r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\knowledge_base\ncm_mapping.json", 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print("🔍 Estrutura do arquivo ncm_mapping.json")
print("=" * 50)

print(f"Tipo: {type(mapping)}")
print(f"Tamanho: {len(mapping)}")

# Mostrar um exemplo de item
if mapping:
    item_exemplo = mapping[0]
    print(f"\nEstrutura do primeiro item:")
    for key, value in item_exemplo.items():
        if isinstance(value, list) and len(value) > 0:
            print(f"  {key}: lista com {len(value)} itens")
            if key == 'cests_associados' and len(value) > 0:
                print(f"    Exemplo: {value[0]}")
        else:
            print(f"  {key}: {str(value)[:50]}...")

# Buscar especificamente o NCM 3004
print(f"\n🔍 Procurando NCM 3004...")
for item in mapping:
    if item.get('ncm_codigo') == '3004':
        print(f"✅ Encontrado NCM 3004:")
        print(f"   NCM: {item.get('ncm_codigo')}")
        print(f"   Descrição: {item.get('descricao', 'N/A')[:80]}...")
        cests = item.get('cests_associados', [])
        print(f"   CESTs: {len(cests)}")
        for cest in cests[:3]:
            print(f"     - {cest.get('cest_codigo', 'N/A')}")
        break
