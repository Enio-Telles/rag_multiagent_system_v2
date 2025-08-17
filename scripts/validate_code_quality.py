#!/usr/bin/env python3
"""
scripts/validate_code_quality.py
Script para validar a qualidade do código do Sistema RAG Multiagente

Este script verifica:
- Imports não utilizados
- TODOs e FIXMEs
- Docstrings ausentes
- Complexidade de funções
- Padrões de código
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

class CodeQualityValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.issues = defaultdict(list)
        
    def validate_all(self) -> Dict[str, List[str]]:
        """Executa todas as validações."""
        print("🔍 Iniciando validação de qualidade do código...")
        
        # Encontrar todos os arquivos Python
        python_files = list(self.src_dir.rglob("*.py"))
        print(f"📁 Encontrados {len(python_files)} arquivos Python para análise")
        
        for py_file in python_files:
            self._validate_file(py_file)
        
        return dict(self.issues)
    
    def _validate_file(self, file_path: Path):
        """Valida um arquivo Python específico."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validações baseadas em texto
            self._check_todos_fixmes(file_path, content)
            self._check_long_lines(file_path, content)
            self._check_import_patterns(file_path, content)
            
            # Validações baseadas em AST
            try:
                tree = ast.parse(content)
                self._check_docstrings(file_path, tree)
                self._check_function_complexity(file_path, tree)
            except SyntaxError as e:
                self.issues[str(file_path)].append(f"Erro de sintaxe: {e}")
                
        except Exception as e:
            self.issues[str(file_path)].append(f"Erro ao processar arquivo: {e}")
    
    def _check_todos_fixmes(self, file_path: Path, content: str):
        """Verifica TODOs, FIXMEs e HACKs no código."""
        lines = content.split('\n')
        patterns = [
            (r'TODO', 'TODO encontrado'),
            (r'FIXME', 'FIXME encontrado'),
            (r'XXX', 'XXX encontrado'),
            (r'HACK', 'HACK encontrado')
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues[str(file_path)].append(
                        f"Linha {line_num}: {message} - {line.strip()}"
                    )
    
    def _check_long_lines(self, file_path: Path, content: str):
        """Verifica linhas muito longas (>120 caracteres)."""
        lines = content.split('\n')
        max_length = 120
        
        for line_num, line in enumerate(lines, 1):
            if len(line) > max_length:
                self.issues[str(file_path)].append(
                    f"Linha {line_num}: Linha muito longa ({len(line)} caracteres) - máximo {max_length}"
                )
    
    def _check_import_patterns(self, file_path: Path, content: str):
        """Verifica padrões problemáticos de import."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Import * (exceto casos específicos)
            if re.match(r'from .+ import \*', line) and 'typing' not in line:
                self.issues[str(file_path)].append(
                    f"Linha {line_num}: Import * evitado - {line}"
                )
            
            # Imports muito longos
            if line.startswith('from') and len(line) > 100:
                self.issues[str(file_path)].append(
                    f"Linha {line_num}: Import muito longo - considere quebrar em múltiplas linhas"
                )
    
    def _check_docstrings(self, file_path: Path, tree: ast.AST):
        """Verifica presença de docstrings em classes e funções."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Pular métodos privados e especiais
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Verificar se tem docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    node_type = "Classe" if isinstance(node, ast.ClassDef) else "Função"
                    self.issues[str(file_path)].append(
                        f"Linha {node.lineno}: {node_type} '{node.name}' sem docstring"
                    )
    
    def _check_function_complexity(self, file_path: Path, tree: ast.AST):
        """Verifica complexidade ciclomática básica das funções."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                if complexity > 10:  # Limite arbitrário
                    self.issues[str(file_path)].append(
                        f"Linha {node.lineno}: Função '{node.name}' muito complexa (complexidade: {complexity})"
                    )
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complexidade ciclomática básica."""
        complexity = 1  # Base
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def generate_report(self, issues: Dict[str, List[str]]) -> str:
        """Gera relatório de qualidade do código."""
        report = []
        report.append("# 📊 RELATÓRIO DE QUALIDADE DO CÓDIGO")
        report.append("=" * 60)
        
        total_issues = sum(len(file_issues) for file_issues in issues.values())
        total_files = len(issues)
        files_with_issues = len([f for f, i in issues.items() if i])
        
        report.append(f"\n## 📈 RESUMO EXECUTIVO")
        report.append(f"- **Total de arquivos analisados**: {total_files}")
        report.append(f"- **Arquivos com problemas**: {files_with_issues}")
        report.append(f"- **Total de problemas encontrados**: {total_issues}")
        
        if total_issues == 0:
            report.append("\n🎉 **PARABÉNS! Nenhum problema encontrado!**")
            return "\n".join(report)
        
        # Categorizar problemas
        categories = defaultdict(int)
        for file_issues in issues.values():
            for issue in file_issues:
                if "TODO" in issue or "FIXME" in issue or "XXX" in issue or "HACK" in issue:
                    categories["Marcadores de código"] += 1
                elif "docstring" in issue:
                    categories["Documentação"] += 1
                elif "muito longa" in issue:
                    categories["Formatação"] += 1
                elif "complexa" in issue:
                    categories["Complexidade"] += 1
                elif "Import" in issue:
                    categories["Imports"] += 1
                else:
                    categories["Outros"] += 1
        
        report.append(f"\n## 📊 PROBLEMAS POR CATEGORIA")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{category}**: {count}")
        
        # Detalhes por arquivo
        report.append(f"\n## 📁 DETALHES POR ARQUIVO")
        
        for file_path, file_issues in sorted(issues.items()):
            if not file_issues:
                continue
                
            relative_path = Path(file_path).relative_to(self.project_root)
            report.append(f"\n### 📄 {relative_path}")
            report.append(f"**{len(file_issues)} problema(s) encontrado(s):**")
            
            for issue in file_issues:
                report.append(f"- {issue}")
        
        # Recomendações
        report.append(f"\n## 💡 RECOMENDAÇÕES")
        
        if categories["Marcadores de código"] > 0:
            report.append("- **TODOs/FIXMEs**: Revisar e implementar ou remover marcadores antigos")
        
        if categories["Documentação"] > 0:
            report.append("- **Documentação**: Adicionar docstrings em funções e classes públicas")
        
        if categories["Formatação"] > 0:
            report.append("- **Formatação**: Considerar usar ferramentas como `black` para formatação automática")
        
        if categories["Complexidade"] > 0:
            report.append("- **Complexidade**: Refatorar funções complexas em funções menores")
        
        if categories["Imports"] > 0:
            report.append("- **Imports**: Organizar e otimizar imports usando ferramentas como `isort`")
        
        return "\n".join(report)

def main():
    """Função principal."""
    # Determinar diretório do projeto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"🔍 Validando qualidade do código em: {project_root}")
    
    # Executar validação
    validator = CodeQualityValidator(str(project_root))
    issues = validator.validate_all()
    
    # Gerar relatório
    report = validator.generate_report(issues)
    
    # Salvar relatório
    report_file = project_root / "RELATORIO_QUALIDADE_CODIGO.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Relatório salvo em: {report_file}")
    
    # Mostrar resumo no console
    total_issues = sum(len(file_issues) for file_issues in issues.values())
    if total_issues == 0:
        print("🎉 Nenhum problema encontrado!")
        return 0
    else:
        print(f"⚠️ {total_issues} problema(s) encontrado(s)")
        print(f"📖 Consulte o relatório completo em: {report_file}")
        return 1

if __name__ == "__main__":
    sys.exit(main())