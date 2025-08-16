# Script simples para testar conexão com banco
import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import Config
    from ingestion.data_loader import DataLoader
    
    dl = DataLoader()
    result = dl.load_produtos_from_db()
    if result is not None:
        print(f"✅ Conexão OK - {len(result)} produtos carregados")
    else:
        print("❌ Erro na conexão")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
