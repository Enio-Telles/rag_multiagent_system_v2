import json
import pandas as pd

# Carregar CEST_RO.json diretamente para verificar os dados originais
print("🔍 DEBUG: Verificação direta dos dados CEST_RO.json")
print("=" * 60)

with open(r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\raw\CEST_RO.json", 'r', encoding='utf-8') as f:
    cest_data = json.load(f)

print(f"Total de registros em CEST_RO.json: {len(cest_data)}")

# Buscar registros com NCM "3004"
ncm_3004_records = [item for item in cest_data if item.get('NCM/SH') == '3004']
print(f"Registros com NCM/SH = '3004': {len(ncm_3004_records)}")

if ncm_3004_records:
    print("\\nPrimeiro registro encontrado:")
    record = ncm_3004_records[0]
    for key, value in record.items():
        print(f"  {key}: {value}")

# Agora testar o carregamento via DataLoader
print("\\n" + "=" * 60)
print("🔍 DEBUG: Verificação do carregamento via DataLoader")

import sys
from pathlib import Path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from ingestion.data_loader import DataLoader

data_loader = DataLoader()

# Simular apenas o carregamento do CEST_RO.json
cest_ro_path = r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos\rag_multiagent_system\data\raw\CEST_RO.json"

print(f"\\nCarregando {cest_ro_path}...")
with open(cest_ro_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Converter para DataFrame
df = pd.DataFrame(data)
print(f"DataFrame shape: {df.shape}")
print(f"Colunas: {list(df.columns)}")

# Filtrar por situação 'vigente'
if 'Situação' in df.columns:
    vigente_mask = df['Situação'].str.lower() == 'vigente'
    df_vigente = df[vigente_mask]
    print(f"Registros vigentes: {len(df_vigente)}")
    
    # Verificar NCM 3004 nos vigentes
    if 'NCM/SH' in df_vigente.columns:
        ncm_3004_vigente = df_vigente[df_vigente['NCM/SH'] == '3004']
        print(f"NCM 3004 nos vigentes: {len(ncm_3004_vigente)}")
        
        if len(ncm_3004_vigente) > 0:
            print("\\nPrimeiro registro vigente com NCM 3004:")
            record = ncm_3004_vigente.iloc[0]
            print(f"  NCM/SH: {record['NCM/SH']}")
            print(f"  CEST: {record.get('CEST', 'N/A')}")
            print(f"  Situação: {record.get('Situação', 'N/A')}")
            print(f"  DESCRIÇÃO: {record.get('DESCRIÇÃO', 'N/A')[:50]}...")

# Verificar o que acontece na normalização NCM_SH
print("\\n" + "=" * 60)
print("🔍 DEBUG: Teste da normalização NCM_SH")

if len(df_vigente) > 0:
    # Adicionar coluna NCM_SH normalizada
    df_vigente = df_vigente.copy()
    df_vigente['NCM_SH'] = df_vigente['NCM/SH'].astype(str).str.strip()
    
    print(f"Após normalização NCM_SH:")
    ncm_3004_normalized = df_vigente[df_vigente['NCM_SH'] == '3004']
    print(f"NCM 3004 após normalização: {len(ncm_3004_normalized)}")
    
    # Verificar tipos únicos de NCM/SH
    unique_ncm_types = df_vigente['NCM/SH'].apply(type).value_counts()
    print(f"\\nTipos de dados em NCM/SH: {unique_ncm_types}")
    
    # Verificar alguns valores de NCM/SH
    print(f"\\nPrimeiros 10 valores de NCM/SH: {df_vigente['NCM/SH'].head(10).tolist()}")
