"""
Script para identificar e remover arquivos obsoletos do sistema
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

class ObsoleteFileCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.obsolete_files = []
        self.backup_dir = self.project_root / "cleanup_backup"
        
    def identify_obsolete_files(self):
        """Identifica arquivos obsoletos baseado em padrões"""
        
        # 1. Scripts de migração antigos
        migration_scripts = [
            "migrate_to_sqlite.py",
            "complete_sqlite_migration.py", 
            "integrate_enhanced_sqlite.py"
        ]
        
        # 2. Agentes antigos (sem _new)
        old_agents = [
            "src/agents/expansion_agent.py",
            "src/agents/aggregation_agent.py",
            "src/agents/ncm_agent.py", 
            "src/agents/cest_agent.py",
            "src/agents/reconciler_agent.py"
        ]
        
        # 3. Scripts de teste/debug antigos
        test_debug_patterns = [
            "test_sqlite_simple.py",
            "debug_*.py",
            "check_*.py", 
            "validate_*.py"
        ]
        
        # 4. APIs legacy
        legacy_apis = [
            "src/api/empresa_database_api.py",
            "src/api/multiempresa_api.py"
        ]
        
        # 5. Documentação obsoleta
        old_docs = [
            "documentacao/README_old*.md",
            "documentacao/RELATORIO_old*.md"
        ]
        
        all_patterns = (
            migration_scripts + old_agents + 
            test_debug_patterns + legacy_apis + old_docs
        )
        
        for pattern in all_patterns:
            if "*" in pattern:
                # Padrão com wildcard
                parent_dir = self.project_root / Path(pattern).parent
                if parent_dir.exists():
                    for file in parent_dir.glob(Path(pattern).name):
                        if file.is_file():
                            self.obsolete_files.append(file)
            else:
                # Arquivo específico
                file_path = self.project_root / pattern
                if file_path.exists():
                    self.obsolete_files.append(file_path)
    
    def check_file_usage(self, file_path: Path):
        """Verifica se arquivo é referenciado em outros arquivos"""
        file_name = file_path.name
        
        # Busca referências no código
        for py_file in self.project_root.rglob("*.py"):
            if py_file == file_path:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if file_name in content:
                        return True, f"Referenciado em {py_file}"
            except:
                continue
        
        return False, "Nenhuma referência encontrada"
    
    def analyze_impact(self):
        """Analisa impacto da remoção de cada arquivo"""
        analysis = {
            "safe_to_remove": [],
            "check_manually": [],
            "keep": []
        }
        
        for file_path in self.obsolete_files:
            is_used, reason = self.check_file_usage(file_path)
            
            if not is_used:
                analysis["safe_to_remove"].append({
                    "file": str(file_path),
                    "reason": reason,
                    "size_mb": file_path.stat().st_size / (1024*1024)
                })
            else:
                analysis["check_manually"].append({
                    "file": str(file_path), 
                    "reason": reason
                })
        
        return analysis
    
    def create_backup(self, files_to_remove):
        """Cria backup dos arquivos antes da remoção"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"cleanup_{timestamp}"
        backup_subdir.mkdir()
        
        for file_info in files_to_remove:
            file_path = Path(file_info["file"])
            if file_path.exists():
                # Mantém estrutura de diretórios no backup
                relative_path = file_path.relative_to(self.project_root)
                backup_file = backup_subdir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_file)
        
        return backup_subdir
    
    def remove_obsolete_files(self, analysis, create_backup=True):
        """Remove arquivos obsoletos com opção de backup"""
        files_to_remove = analysis["safe_to_remove"]
        
        if not files_to_remove:
            print("✅ Nenhum arquivo obsoleto encontrado para remoção segura")
            return
        
        if create_backup:
            backup_dir = self.create_backup(files_to_remove)
            print(f"📦 Backup criado em: {backup_dir}")
        
        total_size = 0
        removed_count = 0
        
        for file_info in files_to_remove:
            file_path = Path(file_info["file"])
            if file_path.exists():
                total_size += file_info["size_mb"]
                file_path.unlink()
                removed_count += 1
                print(f"🗑️  Removido: {file_path}")
        
        print(f"\n✅ Limpeza concluída:")
        print(f"   📁 Arquivos removidos: {removed_count}")
        print(f"   💾 Espaço liberado: {total_size:.2f} MB")
    
    def generate_report(self, analysis):
        """Gera relatório detalhado da análise"""
        report = f"""
# 📊 Relatório de Limpeza de Arquivos Obsoletos

## Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

### ✅ Arquivos Seguros para Remoção ({len(analysis['safe_to_remove'])})
"""
        
        total_size = 0
        for file_info in analysis["safe_to_remove"]:
            total_size += file_info["size_mb"]
            report += f"- `{file_info['file']}` ({file_info['size_mb']:.2f} MB)\n"
        
        report += f"\n**Total de espaço a ser liberado: {total_size:.2f} MB**\n"
        
        if analysis["check_manually"]:
            report += f"\n### ⚠️ Verificar Manualmente ({len(analysis['check_manually'])})\n"
            for file_info in analysis["check_manually"]:
                report += f"- `{file_info['file']}` - {file_info['reason']}\n"
        
        report += """
### 🛡️ Arquivos Preservados por Segurança
- `src/agents/base_agent.py` - Classe base dos agentes
- `start_unified_system.py` - Inicializador principal
- `src/main.py` - Ponto de entrada principal
- `requirements.txt` - Dependências do projeto

### 📋 Recomendações
1. **Backup**: Sempre criar backup antes da remoção
2. **Teste**: Executar testes após limpeza
3. **Documentação**: Atualizar documentação se necessário
4. **Revisão**: Revisar arquivos marcados para verificação manual
"""
        
        return report

def main():
    """Função principal para execução do script"""
    project_root = "."  # Diretório atual
    
    cleaner = ObsoleteFileCleaner(project_root)
    
    print("🔍 Identificando arquivos obsoletos...")
    cleaner.identify_obsolete_files()
    
    print("📊 Analisando impacto da remoção...")
    analysis = cleaner.analyze_impact()
    
    # Gera relatório
    report = cleaner.generate_report(analysis)
    
    # Salva relatório
    with open("cleanup_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📄 Relatório salvo em: cleanup_report.md")
    print("\n" + "="*50)
    print(report)
    
    # Pergunta se deve remover arquivos
    if analysis["safe_to_remove"]:
        response = input(f"\n❓ Remover {len(analysis['safe_to_remove'])} arquivos obsoletos? (s/N): ")
        if response.lower() == 's':
            cleaner.remove_obsolete_files(analysis, create_backup=True)
        else:
            print("❌ Operação cancelada. Arquivos preservados.")
    
    if analysis["check_manually"]:
        print(f"\n⚠️  ATENÇÃO: {len(analysis['check_manually'])} arquivos precisam de verificação manual")
        print("   Consulte o relatório para detalhes.")

if __name__ == "__main__":
    main()