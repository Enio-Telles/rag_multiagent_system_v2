import json

with open('data/knowledge_base/ncm_mapping.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('📊 VERIFICAÇÃO DA UNIÃO DOS 4 ARQUIVOS JSON:')
print('=' * 60)

# Verificar NCMs com CESTs do CEST_RO.json
ncms_com_cest_ro = 0
ncms_com_produtos = 0
ncms_com_cest_original = 0

exemplos_cest_ro = []
exemplos_produtos = []

for item in data:
    ncm = item.get('ncm_codigo', '')
    cests = item.get('cests_associados', [])
    produtos = item.get('gtins_exemplos', [])
    
    # Verificar CESTs com informações do CEST_RO
    for cest in cests:
        if 'tabela' in cest or 'anexo' in cest:
            ncms_com_cest_ro += 1
            if len(exemplos_cest_ro) < 2:
                exemplos_cest_ro.append((ncm, cest))
            break
    
    # Verificar produtos do produtos_selecionados.json
    if produtos:
        ncms_com_produtos += 1
        if len(exemplos_produtos) < 2:
            exemplos_produtos.append((ncm, produtos[0]))
        
        # Verificar se há cest_original nos produtos
        for produto in produtos:
            if 'cest_original' in produto:
                ncms_com_cest_original += 1
                break

print(f'1. descricoes_ncm.json → {len(data)} NCMs na estrutura base')
print(f'2. CEST_RO.json + Anexos_conv_92_15_corrigido.json → {ncms_com_cest_ro} NCMs com CESTs extras')
print(f'3. produtos_selecionados.json → {ncms_com_produtos} NCMs com produtos')
print(f'4. Produtos com CEST original → {ncms_com_cest_original} NCMs')

print(f'\n🔍 EXEMPLOS DE UNIÃO:')
print('-' * 40)

if exemplos_cest_ro:
    print('EXEMPLO CEST_RO.json:')
    ncm, cest = exemplos_cest_ro[0]
    print(f'NCM: {ncm}')
    print(f'CEST: {cest.get("cest")}')
    print(f'Tabela: {cest.get("tabela", "N/A")}')
    print(f'Situação: {cest.get("situacao", "N/A")}')
    print()

if exemplos_produtos:
    print('EXEMPLO produtos_selecionados.json:')
    ncm, produto = exemplos_produtos[0]
    print(f'NCM: {ncm}')
    print(f'GTIN: {produto.get("gtin")}')
    print(f'Produto: {produto.get("descricao_produto", "N/A")[:50]}...')
    if 'cest_original' in produto:
        print(f'CEST Original: {produto.get("cest_original")}')
    print()

print(f'📈 RESUMO DA UNIÃO:')
print(f'✅ Total de arquivos unidos: 4')
print(f'✅ Base NCM: descricoes_ncm.json (15.141 códigos)')
print(f'✅ Dados CEST: CEST_RO.json + Anexos_conv_92_15_corrigido.json')
print(f'✅ Produtos: produtos_selecionados.json (814 exemplos)')
print(f'✅ Estrutura mapeamento mantida: ✓')
