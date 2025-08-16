import json
import pandas as pd

# Verificar CEST_RO.json
with open('data/raw/CEST_RO.json', 'r', encoding='utf-8') as f:
    cest_data = json.load(f)

# Buscar NCM 3004
ncm_3004_entries = [item for item in cest_data if item.get('NCM/SH') == '3004']
print('🔍 NCM 3004 no CEST_RO.json:')
for entry in ncm_3004_entries[:3]:
    print(f'CEST: {entry.get("CEST")}')
    print(f'NCM/SH: {entry.get("NCM/SH")}')
    print(f'Situação: {entry.get("Situação")}')
    desc = entry.get("DESCRIÇÃO", "")
    print(f'Descrição: {desc[:80]}...')
    print('-' * 40)

print(f'Total de registros com NCM/SH = 3004: {len(ncm_3004_entries)}')

# Verificar ncm_mapping.json
with open('data/knowledge_base/ncm_mapping.json', 'r', encoding='utf-8') as f:
    mapping_data = json.load(f)

# Buscar NCM 3004 no mapeamento
ncm_3004_mapping = None
for item in mapping_data:
    if item.get('ncm_codigo') == '3004':
        ncm_3004_mapping = item
        break

print(f'\n🔍 NCM 3004 no mapeamento:')
if ncm_3004_mapping:
    print(f'NCM: {ncm_3004_mapping.get("ncm_codigo")}')
    print(f'Descrição: {ncm_3004_mapping.get("descricao_oficial", "")[:80]}...')
    print(f'CESTs associados: {len(ncm_3004_mapping.get("cests_associados", []))}')
    if ncm_3004_mapping.get("cests_associados"):
        for cest in ncm_3004_mapping["cests_associados"]:
            print(f'  - CEST: {cest.get("cest")}')
else:
    print('❌ NCM 3004 não encontrado no mapeamento')
