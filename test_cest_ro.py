import json

with open('data/knowledge_base/ncm_mapping.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar NCMs que tenham CESTs com informações do CEST_RO
ncms_with_cest_ro = []
for ncm, info in data.items():
    for cest in info.get('cests_associados', []):
        if 'tabela' in cest or 'anexo' in cest:
            ncms_with_cest_ro.append((ncm, cest))
            if len(ncms_with_cest_ro) >= 3:
                break
    if len(ncms_with_cest_ro) >= 3:
        break

print('📊 VERIFICAÇÃO DO CEST_RO.json NO MAPEAMENTO:')
print('=' * 60)
for ncm, cest in ncms_with_cest_ro:
    print(f'NCM: {ncm}')
    print(f'CEST: {cest.get("cest", "N/A")}')
    desc = cest.get('descricao_cest', 'N/A')
    print(f'Descrição: {desc[:80]}...' if len(desc) > 80 else f'Descrição: {desc}')
    print(f'Tabela: {cest.get("tabela", "N/A")}')
    print(f'Anexo: {cest.get("anexo", "N/A")}')
    print(f'Situação: {cest.get("situacao", "N/A")}')
    print('-' * 40)

# Estatísticas gerais
total_cests_with_extra_info = 0
for ncm, info in data.items():
    for cest in info.get('cests_associados', []):
        if 'tabela' in cest or 'anexo' in cest:
            total_cests_with_extra_info += 1

print(f'\n📈 ESTATÍSTICAS:')
print(f'Total de CESTs com informações extras (tabela/anexo): {total_cests_with_extra_info}')
