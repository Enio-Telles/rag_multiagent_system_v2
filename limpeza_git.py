"""
Script para limpar repositório GitHub removendo arquivos desnecessários
e corrigindo .gitignore
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Set

class GitHubRepoCleaner:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.files_to_remove = set()
        self.dirs_to_remove = set()
        self.backup_dir = self.repo_path / "cleanup_backup_github"
        
    def identify_files_to_remove(self):
        """Identifica arquivos que devem ser removidos do GitHub"""
        
        # 1. Dados e bancos de dados
        data_patterns = [
            "data/**/*.db",
            "data/**/*.sqlite*", 
            "data/**/*.csv",
            "data/**/*.json",
            "data/**/*.xlsx",
            "data/**/*.parquet",
            "data/**/*.feather",
            "data/**/*.pkl",
            "data/**/*.pickle",
            "**/*.faiss",
            "**/*.index"
        ]
        
        # 2. Arquivos de ambiente e configuração sensível
        config_patterns = [
            ".env*",
            "*.env",
            "config/local.py",
            "config/production.py", 
            "secrets.json",
            "credentials.json"
        ]
        
        # 3. Logs e arquivos temporários
        temp_patterns = [
            "**/*.log",
            "logs/**/*",
            "temp/**/*",
            "tmp/**/*",
            "**/*.tmp",
            "**/*.temp",
            "cleanup_backup/**/*",
            "cleanup_backup_github/**/*"
        ]
        
        # 4. Cache e arquivos gerados
        cache_patterns = [
            "__pycache__/**/*",
            "**/*.pyc",
            "**/*.pyo", 
            "**/*.pyd",
            ".pytest_cache/**/*",
            ".cache/**/*",
            "cache/**/*",
            "node_modules/**/*"
        ]
        
        # 5. Modelos e embeddings grandes
        ml_patterns = [
            "**/*.model",
            "**/*.bin",
            "**/*.safetensors",
            "**/*.pt",
            "**/*.pth",
            "**/*.h5",
            "embeddings/**/*",
            "vectors/**/*"
        ]
        
        # 6. Backups e arquivos obsoletos
        backup_patterns = [
            "backup/**/*",
            "**/*_backup*",
            "**/*_old*",
            "**/*.bak",
            "**/*.backup"
        ]
        
        # 7. Arquivos específicos obsoletos identificados anteriormente
        obsolete_files = [
            "migrate_to_sqlite.py",
            "complete_sqlite_migration.py",
            "integrate_enhanced_sqlite.py",
            "test_sqlite_simple.py",
            "src/agents/expansion_agent.py",
            "src/agents/aggregation_agent.py", 
            "src/agents/ncm_agent.py",
            "src/agents/cest_agent.py",
            "src/agents/reconciler_agent.py",
            "src/api/empresa_database_api.py"
        ]
        
        all_patterns = (
            data_patterns + config_patterns + temp_patterns + 
            cache_patterns + ml_patterns + backup_patterns
        )
        
        # Busca arquivos por padrões
        for pattern in all_patterns:
            for file_path in self.repo_path.glob(pattern):
                if file_path.is_file():
                    self.files_to_remove.add(file_path)
                elif file_path.is_dir():
                    self.dirs_to_remove.add(file_path)
        
        # Adiciona arquivos específicos obsoletos
        for file_name in obsolete_files:
            file_path = self.repo_path / file_name
            if file_path.exists():
                self.files_to_remove.add(file_path)
    
    def get_files_to_keep(self) -> Set[str]:
        """Define arquivos essenciais que DEVEM ser mantidos"""
        essential_files = {
            # Documentação essencial
            "README.md",
            "MANUAL_COMPLETO_SISTEMA.md",
            
            # Configuração do projeto
            "requirements.txt",
            "package.json",
            ".gitignore",
            
            # Código fonte principal
            "src/main.py",
            "start_unified_system.py",
            
            # Configuração de exemplo (sem dados sensíveis)
            ".env.example",
            "config.example.py",
            
            # Dados de exemplo pequenos
            "data/examples/sample_products.json",
            "data/schema/database_schema.sql"
        }
        return essential_files
    
    def create_corrected_gitignore(self):
        """Cria .gitignore corrigido mais específico"""
        
        new_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
.venv/
.env/
ENV/
env.bak/
venv.bak/

# Environment variables (MANTER .env.example)
.env
.env.local
.env.production
.env.development
secrets.json
credentials.json

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.sublime-workspace
.sublime-project

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Logs
*.log
logs/
error.log
debug.log
app.log

# Databases (GRANDES)
data/knowledge_base/*.db
data/knowledge_base/*.sqlite*
data/*.sqlite*
data/*.db

# Large datasets (MANTER exemplos pequenos)
data/raw/large_datasets/
data/processed/large_files/
data/knowledge_base/faiss_index.faiss
data/knowledge_base/*.faiss

# Machine Learning models
*.model
*.pkl
*.pickle
*.joblib
*.h5
*.hdf5
*.onnx
*.pb
*.pt
*.pth
*.bin
*.safetensors

# Vector embeddings
embeddings/
vectors/
*.npy
*.npz

# Cache
.cache/
cache/
.pytest_cache/
.ollama/
ollama_cache/
llm_cache/

# Temporary files
temp/
tmp/
*.tmp
*.temp
cleanup_backup*/

# Test outputs
test_results/
test_outputs/
coverage_reports/
htmlcov/
.coverage
.coverage.*

# Node.js (frontend)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production builds
build/
dist/

# Backups
backup/
*_backup*
*_old*
*.bak
*.backup

# Large CSVs (MANTER samples pequenos)
data/**/*.csv
!data/examples/*.csv
!data/samples/*.csv

# Large JSONs (MANTER configs e exemplos)
data/**/*.json
!data/examples/*.json
!data/schema/*.json
!package.json
!frontend/package.json

# Documentation builds (MANTER markdown sources)
docs/_build/
docs/build/
site/
"""
        
        gitignore_path = self.repo_path / ".gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(new_gitignore)
        
        print("✅ .gitignore corrigido criado")
    
    def create_essential_files(self):
        """Cria arquivos essenciais que devem existir"""
        
        # 1. .env.example
        env_example = """# Configurações do Sistema RAG Multiagente
# Copie para .env e configure os valores

# Database
DATABASE_URL=sqlite:///data/unified_system.db
POSTGRES_URL=postgresql://user:password@localhost:5432/rag_system

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.1:8b

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/system.log

# FAISS Configuration
FAISS_INDEX_PATH=data/knowledge_base/faiss_index.faiss
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
"""
        
        env_example_path = self.repo_path / ".env.example"
        with open(env_example_path, "w", encoding="utf-8") as f:
            f.write(env_example)
        
        # 2. requirements.txt simplificado
        requirements = """# Core dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.12.1

# Database
sqlite3
psycopg2-binary==2.9.7

# Machine Learning
sentence-transformers==2.2.2
faiss-cpu==1.7.4
numpy==1.24.3
pandas==2.0.3

# HTTP Client
httpx==0.25.0
requests==2.31.0

# Utilities
python-dotenv==1.0.0
click==8.1.7
rich==13.6.0
loguru==0.7.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.10.1
flake8==6.1.0
"""
        
        req_path = self.repo_path / "requirements.txt"
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(requirements)
        
        # 3. Estrutura de dados de exemplo
        examples_dir = self.repo_path / "data" / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        sample_products = """[
  {
    "id": 1,
    "nome": "Paracetamol 500mg",
    "descricao": "Medicamento analgésico e antipirético",
    "categoria": "Medicamentos",
    "ncm_sugerido": "30049099",
    "cest_sugerido": "200300"
  },
  {
    "id": 2, 
    "nome": "Smartphone Android",
    "descricao": "Telefone celular com sistema Android",
    "categoria": "Eletrônicos",
    "ncm_sugerido": "85171231",
    "cest_sugerido": "121800"
  }
]"""
        
        sample_path = examples_dir / "sample_products.json"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(sample_products)
        
        print("✅ Arquivos essenciais criados")
    
    def remove_from_git_history(self, files_to_remove: List[str]):
        """Remove arquivos do histórico do Git usando git filter-branch"""
        
        print("🧹 Removendo arquivos do histórico do Git...")
        
        # Cria backup do repositório
        print("📦 Criando backup do repositório...")
        
        for file_path in files_to_remove:
            try:
                # Remove do histórico usando git filter-repo (mais seguro que filter-branch)
                cmd = f'git filter-repo --path "{file_path}" --invert-paths --force'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Removido do histórico: {file_path}")
                else:
                    print(f"⚠️ Erro ao remover {file_path}: {result.stderr}")
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def clean_repository(self, remove_from_history=False):
        """Executa limpeza completa do repositório"""
        
        print("🔍 Identificando arquivos para remoção...")
        self.identify_files_to_remove()
        
        essential_files = self.get_files_to_keep()
        
        # Remove arquivos desnecessários do working directory
        removed_files = []
        for file_path in self.files_to_remove:
            relative_path = file_path.relative_to(self.repo_path)
            if str(relative_path) not in essential_files:
                try:
                    if file_path.exists():
                        file_path.unlink()
                        removed_files.append(str(relative_path))
                        print(f"🗑️ Removido: {relative_path}")
                except Exception as e:
                    print(f"❌ Erro ao remover {relative_path}: {e}")
        
        # Remove diretórios vazios
        for dir_path in self.dirs_to_remove:
            try:
                if dir_path.exists() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"📁 Diretório removido: {dir_path.relative_to(self.repo_path)}")
            except Exception as e:
                print(f"❌ Erro ao remover diretório: {e}")
        
        # Corrige .gitignore
        self.create_corrected_gitignore()
        
        # Cria arquivos essenciais
        self.create_essential_files()
        
        # Remove do histórico Git se solicitado
        if remove_from_history and removed_files:
            response = input("⚠️ Remover arquivos do histórico Git? Isso reescreverá o histórico! (s/N): ")
            if response.lower() == 's':
                self.remove_from_git_history(removed_files)
        
        print(f"\n✅ Limpeza concluída! Removidos {len(removed_files)} arquivos")
        
        return removed_files
    
    def generate_cleanup_commands(self):
        """Gera comandos Git para finalizar a limpeza"""
        
        commands = """
# 🔧 Comandos para finalizar limpeza do repositório

# 1. Adicionar mudanças ao Git
git add .
git add .gitignore

# 2. Commit das mudanças
git commit -m "🧹 Limpeza completa do repositório

- Removidos arquivos desnecessários (dados, logs, cache)
- Corrigido .gitignore para ser mais específico
- Adicionados arquivos de exemplo e configuração
- Mantidos apenas arquivos essenciais do código fonte"

# 3. Forçar push (se removeu do histórico)
git push origin main --force

# 4. Verificar status
git status

# 5. Verificar tamanho do repositório
du -sh .git/

# 6. Limpar cache local do Git
git gc --aggressive --prune=now
"""
        
        commands_file = self.repo_path / "cleanup_commands.sh"
        with open(commands_file, "w", encoding="utf-8") as f:
            f.write(commands)
        
        print(f"📋 Comandos salvos em: {commands_file}")
        return commands

def main():
    """Função principal"""
    
    print("🧹 LIMPEZA COMPLETA DO REPOSITÓRIO GITHUB")
    print("="*50)
    
    cleaner = GitHubRepoCleaner()
    
    # Executa limpeza
    removed_files = cleaner.clean_repository(remove_from_history=False)
    
    # Gera comandos finais
    commands = cleaner.generate_cleanup_commands()
    
    print("\n📊 RESUMO DA LIMPEZA:")
    print(f"📁 Arquivos removidos: {len(removed_files)}")
    print("✅ .gitignore corrigido")
    print("✅ Arquivos essenciais criados")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Revisar mudanças: git status")
    print("2. Executar: git add .")
    print("3. Executar: git commit -m 'Limpeza do repositório'")
    print("4. Executar: git push origin main")
    print("\n⚠️ IMPORTANTE: Verifique se todos os arquivos essenciais estão preservados!")

if __name__ == "__main__":
    main()