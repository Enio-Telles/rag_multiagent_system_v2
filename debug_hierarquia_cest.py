import json

# Carregar o mapeamento atual
with open(r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\knowledge_base\ncm_mapping.json", 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print("🔍 Análise da hierarquia NCM 3004")
print("=" * 50)

# Buscar NCM 3004 e seus filhos
ncm_3004 = None
filhos_3004 = []

for item in mapping:
    ncm_code = item['ncm_codigo']
    if ncm_code == "3004":
        ncm_3004 = item
    elif ncm_code.startswith("3004") and len(ncm_code) > 4:
        filhos_3004.append((ncm_code, item))

# Mostrar NCM pai
if ncm_3004:
    print(f"📋 NCM PAI: 3004")
    print(f"   Descrição: {ncm_3004['descricao'][:80]}...")
    print(f"   CESTs: {len(ncm_3004.get('cests_associados', []))}")
    if ncm_3004.get('cests_associados'):
        for cest in ncm_3004['cests_associados'][:3]:
            print(f"     - {cest['cest_codigo']}")
    print()

# Mostrar alguns filhos
print(f"🌳 FILHOS DO NCM 3004 (primeiros 10 de {len(filhos_3004)}):")
for ncm_code, item in sorted(filhos_3004)[:10]:
    cests_count = len(item.get('cests_associados', []))
    print(f"   {ncm_code}: {cests_count} CESTs - {item['descricao'][:50]}...")

print(f"\n📊 Estatísticas:")
print(f"   Total de filhos de 3004: {len(filhos_3004)}")
filhos_com_cest = [f for f in filhos_3004 if f[1].get('cests_associados')]
print(f"   Filhos com CEST próprio: {len(filhos_com_cest)}")
filhos_sem_cest = [f for f in filhos_3004 if not f[1].get('cests_associados')]
print(f"   Filhos SEM CEST: {len(filhos_sem_cest)}")

print(f"\n🔍 Exemplos de filhos SEM CEST:")
for ncm_code, item in sorted(filhos_sem_cest)[:5]:
    print(f"   {ncm_code}: {item['descricao'][:60]}...")
