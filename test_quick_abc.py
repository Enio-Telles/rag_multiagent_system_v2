#!/usr/bin/env python3
import sys
sys.path.append('src')
from services.unified_sqlite_service import get_unified_service

service = get_unified_service()
results = service.search_abc_farma_by_text('DIPIRONA', 3)
print(f'Encontrados {len(results)} produtos:')
for r in results:
    print(f'- {r["descricao"][:80]}...')
    print(f'  NCM: {r["ncm"]}')
