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
        filhos_3004.append(item)

# Mostrar NCM pai
if ncm_3004:
    print(f"📋 NCM PAI: 3004")
    print(f"   Descrição: {ncm_3004.get('descricao_oficial', 'N/A')[:80]}...")
    cests = ncm_3004.get('cests_associados', [])
    print(f"   CESTs: {len(cests)}")
    if cests:
        for cest in cests[:3]:
            print(f"     - {cest.get('cest_codigo', 'N/A')}: {cest.get('descricao', 'N/A')[:40]}...")
    print()

# Mostrar alguns filhos
print(f"🌳 FILHOS DO NCM 3004 (primeiros 10 de {len(filhos_3004)}):")
for item in sorted(filhos_3004, key=lambda x: x['ncm_codigo'])[:10]:
    ncm_code = item['ncm_codigo']
    cests_count = len(item.get('cests_associados', []))
    descricao = item.get('descricao_oficial', 'N/A')
    print(f"   {ncm_code}: {cests_count} CESTs - {descricao[:50]}...")

print(f"\n📊 Estatísticas:")
print(f"   Total de filhos de 3004: {len(filhos_3004)}")
filhos_com_cest = [f for f in filhos_3004 if f.get('cests_associados')]
print(f"   Filhos com CEST próprio: {len(filhos_com_cest)}")
filhos_sem_cest = [f for f in filhos_3004 if not f.get('cests_associados')]
print(f"   Filhos SEM CEST: {len(filhos_sem_cest)}")

print(f"\n🔍 Exemplos de filhos SEM CEST:")
for item in sorted(filhos_sem_cest, key=lambda x: x['ncm_codigo'])[:5]:
    ncm_code = item['ncm_codigo']
    descricao = item.get('descricao_oficial', 'N/A')
    print(f"   {ncm_code}: {descricao[:60]}...")

# Verificar códigos específicos mencionados pelo usuário
codigos_especificos = ["300490", "3004901", "30046000"]
print(f"\n🎯 Verificação dos códigos específicos:")
for codigo in codigos_especificos:
    encontrado = False
    for item in mapping:
        if item['ncm_codigo'] == codigo:
            cests_count = len(item.get('cests_associados', []))
            descricao = item.get('descricao_oficial', 'N/A')
            print(f"   {codigo}: {cests_count} CESTs - {descricao[:60]}...")
            encontrado = True
            break
    if not encontrado:
        print(f"   {codigo}: ❌ NÃO ENCONTRADO")
