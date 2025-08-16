import json

with open('data/knowledge_base/ncm_mapping.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar NCMs que tenham CESTs com informações do CEST_RO
ncms_with_cest_ro = []
total_cests_with_extra_info = 0

for item in data:
    ncm = item.get('ncm_codigo', '')
    cests = item.get('cests_associados', [])
    
    for cest in cests:
        if 'tabela' in cest or 'anexo' in cest:
            total_cests_with_extra_info += 1
            if len(ncms_with_cest_ro) < 5:
                ncms_with_cest_ro.append((ncm, cest))

print('📊 VERIFICAÇÃO DO CEST_RO.json NO MAPEAMENTO:')
print('=' * 60)

if ncms_with_cest_ro:
    for ncm, cest in ncms_with_cest_ro:
        print(f'NCM: {ncm}')
        print(f'CEST: {cest.get("cest", "N/A")}')
        desc = cest.get('descricao_cest', 'N/A')
        print(f'Descrição: {desc[:80]}...' if len(desc) > 80 else f'Descrição: {desc}')
        print(f'Tabela: {cest.get("tabela", "N/A")}')
        print(f'Anexo: {cest.get("anexo", "N/A")}')
        print(f'Situação: {cest.get("situacao", "N/A")}')
        print(f'Início Vigência: {cest.get("inicio_vigencia", "N/A")}')
        print('-' * 40)
else:
    print('❌ Nenhum CEST com informações extras encontrado')

print(f'\n📈 ESTATÍSTICAS:')
print(f'Total de CESTs com informações extras (tabela/anexo): {total_cests_with_extra_info}')
print(f'Total de itens no mapeamento: {len(data)}')

# Verificar quantos têm CESTs no total
total_with_cests = sum(1 for item in data if item.get('cests_associados', []))
print(f'Total de NCMs com CESTs: {total_with_cests}')
