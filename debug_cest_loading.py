import json
import pandas as pd
import sys
from pathlib import Path

# Adicionar o diretório src ao path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import Config
from ingestion.data_loader import DataLoader

# Simular o processo de carregamento CEST
config = Config()
data_loader = DataLoader()

print("🔍 DEBUG: Processamento dos dados CEST")
print("=" * 50)

# Carregar dados CEST
cest_data = data_loader.load_cest_mapping()
print(f"Total de registros CEST carregados: {len(cest_data)}")

# Filtrar apenas registros com NCM/SH = "3004"
ncm_3004_records = cest_data[
    (cest_data['NCM_SH'] == '3004') | 
    (cest_data['NCM/SH'] == '3004') if 'NCM/SH' in cest_data.columns else False
]

print(f"\\nRegistros com NCM 3004: {len(ncm_3004_records)}")

if len(ncm_3004_records) > 0:
    print("\\nPrimeiros registros:")
    for idx, row in ncm_3004_records.head(3).iterrows():
        print(f"Registro {idx}:")
        print(f"  NCM_SH: {row.get('NCM_SH', 'N/A')}")
        print(f"  NCM/SH: {row.get('NCM/SH', 'N/A')}")
        print(f"  CEST: {row.get('CEST', 'N/A')}")
        print(f"  Situação: {row.get('Situação', 'N/A')}")
        print(f"  DESCRICAO: {row.get('DESCRICAO', 'N/A')[:50]}...")
        print()

# Verificar colunas disponíveis
print(f"\\nColunas no DataFrame CEST: {list(cest_data.columns)}")

# Verificar como o código está processando o NCM_SH
print("\\nTeste do processamento NCM_SH:")
for _, item in ncm_3004_records.head(2).iterrows():
    ncm_input = str(item.get("NCM_SH", "") or item.get("NCM/SH", "")).strip()
    print(f"  Processamento: NCM_SH='{item.get('NCM_SH', 'N/A')}' | NCM/SH='{item.get('NCM/SH', 'N/A')}' → resultado: '{ncm_input}'")
