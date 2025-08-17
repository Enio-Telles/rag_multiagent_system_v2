"""
Script para integrar os novos endpoints de banco por empresa na API principal
"""

import sys
import os

# Verificar se o arquivo da API principal existe
api_file = "src/api/api_unified.py"

if not os.path.exists(api_file):
    print(f"❌ Arquivo {api_file} não encontrado")
    sys.exit(1)

# Ler conteúdo atual
with open(api_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar se já foi integrado
if "empresa_database_api" in content:
    print("✅ Endpoints de banco por empresa já estão integrados")
    sys.exit(0)

# Encontrar linha de imports
import_line = "from src.api.empresa_api import router as empresa_router"

if import_line not in content:
    print("❌ Linha de import da empresa API não encontrada")
    sys.exit(1)

# Adicionar novo import
new_import = "from src.api.empresa_database_api import router as empresa_db_router"
content = content.replace(import_line, f"{import_line}\n{new_import}")

# Encontrar linha de inclusão do router
include_line = "app.include_router(empresa_router)"

if include_line not in content:
    print("❌ Linha de inclusão do empresa router não encontrada")
    sys.exit(1)

# Adicionar novo router
new_include = "app.include_router(empresa_db_router)"
content = content.replace(include_line, f"{include_line}\n{new_include}")

# Salvar arquivo modificado
with open(api_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Endpoints de banco por empresa integrados com sucesso!")
print("🌐 Novos endpoints disponíveis:")
print("  - POST   /api/v1/empresa-db/inicializar")
print("  - GET    /api/v1/empresa-db/empresas")
print("  - GET    /api/v1/empresa-db/empresas/{id}/stats")
print("  - GET    /api/v1/empresa-db/empresas/{id}/relatorio")
print("  - POST   /api/v1/empresa-db/empresas/{id}/produtos")
print("  - GET    /api/v1/empresa-db/empresas/{id}/produtos/{produto_id}")
print("  - POST   /api/v1/empresa-db/empresas/{id}/classificacoes/{class_id}/aprovar")
print("  - POST   /api/v1/empresa-db/empresas/{id}/classificacoes/{class_id}/rejeitar")
print("  - POST   /api/v1/empresa-db/empresas/{id}/produtos/{produto_id}/golden-set")
print("  - GET    /api/v1/empresa-db/golden-set")
print("  - GET    /api/v1/empresa-db/golden-set/{id}/validacoes")
print("  - GET    /api/v1/empresa-db/empresas/{id}/produtos")
print("  - GET    /api/v1/empresa-db/empresas/{id}/agentes/performance")
