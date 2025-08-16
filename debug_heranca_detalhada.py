import json

# Carregar o mapeamento atualizado
with open(r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\knowledge_base\ncm_mapping.json", 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print("🎯 Verificação detalhada da herança hierárquica de CESTs")
print("=" * 60)

# Códigos específicos para testar
codigos_teste = ["3004", "300490", "3004901", "30046000"]

for codigo in codigos_teste:
    print(f"\n📋 NCM: {codigo}")
    print("-" * 40)
    
    # Encontrar o NCM
    ncm_data = None
    for item in mapping:
        if item['ncm_codigo'] == codigo:
            ncm_data = item
            break
    
    if ncm_data:
        print(f"Descrição: {ncm_data.get('descricao_oficial', 'N/A')[:60]}...")
        cests = ncm_data.get('cests_associados', [])
        print(f"Total de CESTs: {len(cests)}")
        
        if cests:
            # Separar CESTs próprios e herdados
            cests_proprios = [c for c in cests if not c.get('herdado', False)]
            cests_herdados = [c for c in cests if c.get('herdado', False)]
            
            print(f"  ├─ CESTs próprios: {len(cests_proprios)}")
            print(f"  └─ CESTs herdados: {len(cests_herdados)}")
            
            if cests_herdados:
                # Mostrar de onde foram herdados
                herdado_de = cests_herdados[0].get('herdado_de', 'N/A')
                print(f"     Herdados de: NCM {herdado_de}")
            
            # Mostrar alguns CESTs
            print(f"  Primeiros 3 CESTs:")
            for i, cest in enumerate(cests[:3]):
                tipo = "🔹 Herdado" if cest.get('herdado') else "🔸 Próprio"
                cest_codigo = cest.get('cest', 'N/A')
                descricao = cest.get('descricao_cest', 'N/A')[:40]
                print(f"    {i+1}. {tipo} {cest_codigo}: {descricao}...")
    else:
        print("❌ NCM não encontrado")

print(f"\n📊 Resumo da herança hierárquica:")
print("=" * 60)

# Estatísticas gerais
ncms_com_cest_proprio = 0
ncms_com_cest_herdado = 0
total_cests_proprios = 0
total_cests_herdados = 0

for item in mapping:
    cests = item.get('cests_associados', [])
    if cests:
        cests_proprios = [c for c in cests if not c.get('herdado', False)]
        cests_herdados = [c for c in cests if c.get('herdado', False)]
        
        if cests_proprios:
            ncms_com_cest_proprio += 1
            total_cests_proprios += len(cests_proprios)
        if cests_herdados:
            ncms_com_cest_herdado += 1
            total_cests_herdados += len(cests_herdados)

print(f"📋 NCMs com CEST próprio: {ncms_com_cest_proprio:,}")
print(f"🌳 NCMs com CEST herdado: {ncms_com_cest_herdado:,}")
print(f"📊 Total CESTs próprios: {total_cests_proprios:,}")
print(f"🔗 Total CESTs herdados: {total_cests_herdados:,}")
print(f"✅ Cobertura CEST aumentou de {ncms_com_cest_proprio:,} para {ncms_com_cest_proprio + ncms_com_cest_herdado:,} NCMs")
