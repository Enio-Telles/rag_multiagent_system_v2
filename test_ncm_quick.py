#!/usr/bin/env python3
import sys
sys.path.append('src')
from services.unified_sqlite_service import get_unified_service

service = get_unified_service()
ncms = service.buscar_ncms_por_nivel(8, 5)
print('Primeiros 5 NCMs:')
for ncm in ncms:
    print(f'{ncm["codigo_ncm"]}: {ncm["descricao_oficial"][:50]}...')
