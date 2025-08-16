#!/usr/bin/env python3
"""
scripts/test_mapping.py
Teste Intermediário 1: Validação do Banco de Mapeamento Hierárquico

Este script testa se o ncm_mapping.json foi construído corretamente com suporte à hierarquia.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import Config

class MappingTester:
    def __init__(self):
        self.config = Config()
        self.mapping_db = None
        self.ncm_index = {}
    
    def load_mapping_db(self) -> bool:
        """Carrega o banco de mapeamento."""
        try:
            with open(self.config.NCM_MAPPING_FILE, 'r', encoding='utf-8') as f:
                mapping_list = json.load(f)
            
            # Converter lista para dicionário indexado por código NCM
            self.mapping_db = {}
            for item in mapping_list:
                self.mapping_db[item['ncm_codigo']] = item
                self.ncm_index[item['ncm_codigo']] = item
            
            print(f"✅ Banco de mapeamento carregado: {len(self.mapping_db)} NCMs")
            return True
            
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.config.NCM_MAPPING_FILE}")
            print("Execute primeiro: python scripts/build_knowledge_base.py")
            return False
        
        except Exception as e:
            print(f"❌ Erro ao carregar mapping: {e}")
            return False
    
    def test_specific_ncm(self, ncm_code: str):
        """Testa um NCM específico."""
        print(f"\n🔍 TESTANDO NCM: {ncm_code}")
        print("=" * 60)
        
        # Normalizar código NCM
        normalized_code = ncm_code.replace(".", "").strip()
        
        if normalized_code in self.mapping_db:
            data = self.mapping_db[normalized_code]
            
            print(f"📋 Código: {data['ncm_codigo']}")
            print(f"🏷️ Código Original: {data.get('codigo_original', 'N/A')}")
            print(f"📝 Descrição Oficial: {data['descricao_oficial']}")
            print(f"🏗️ Nível Hierárquico: {data.get('nivel_hierarquico', 'N/A')}")
            
            # CESTs associados
            if data['cests_associados']:
                print(f"\n🎯 CESTs Associados ({len(data['cests_associados'])}):")
                for i, cest in enumerate(data['cests_associados'], 1):
                    ncm_orig = cest.get('ncm_original', 'N/A')
                    print(f"   {i}. CEST {cest['cest']}: {cest['descricao_cest']}")
                    print(f"      NCM Original: {ncm_orig}")
            else:
                print("\n🎯 CESTs Associados: Nenhum")
            
            # Exemplos de produtos
            if data['gtins_exemplos']:
                print(f"\n🛍️ Exemplos de Produtos ({len(data['gtins_exemplos'])}):")
                for i, exemplo in enumerate(data['gtins_exemplos'][:5], 1):  # Mostrar apenas os primeiros 5
                    gtin = exemplo.get('gtin', 'N/A')
                    descricao = exemplo.get('descricao_produto', 'N/A')
                    ncm_orig = exemplo.get('ncm_original', 'N/A')
                    print(f"   {i}. GTIN: {gtin}")
                    print(f"      Descrição: {descricao}")
                    print(f"      NCM Original: {ncm_orig}")
                
                if len(data['gtins_exemplos']) > 5:
                    restantes = len(data['gtins_exemplos']) - 5
                    print(f"      ... e mais {restantes} produtos")
            else:
                print("\n🛍️ Exemplos de Produtos: Nenhum")
        else:
            print(f"❌ NCM {ncm_code} não encontrado no banco de mapeamento")
    
    def test_hierarchy_search(self, partial_code: str):
        """Testa busca hierárquica."""
        print(f"\n🌳 TESTE DE HIERARQUIA: {partial_code}")
        print("=" * 60)
        
        # Normalizar código
        normalized = partial_code.replace(".", "").strip()
        
        # Encontrar códigos que começam com o parcial
        matches = [code for code in self.mapping_db.keys() if code.startswith(normalized)]
        matches.sort()
        
        if matches:
            print(f"📊 Encontrados {len(matches)} códigos na hierarquia:")
            
            # Organizar por nível
            por_nivel = {}
            for code in matches:
                nivel = len(code)
                if nivel not in por_nivel:
                    por_nivel[nivel] = []
                por_nivel[nivel].append(code)
            
            for nivel in sorted(por_nivel.keys()):
                codes = por_nivel[nivel]
                print(f"\n  📋 Nível {nivel} ({len(codes)} códigos):")
                
                for code in codes[:3]:  # Mostrar apenas 3 exemplos por nível
                    data = self.mapping_db[code]
                    cests = len(data['cests_associados'])
                    produtos = len(data['gtins_exemplos'])
                    print(f"    • {data.get('codigo_original', code)}: {cests} CESTs, {produtos} produtos")
                
                if len(codes) > 3:
                    print(f"    ... e mais {len(codes) - 3} códigos")
        else:
            print(f"❌ Nenhum código encontrado para: {partial_code}")
    
    def run_comprehensive_test(self):
        """Executa teste abrangente do banco de mapeamento."""
        print("🧪 TESTE ABRANGENTE DO BANCO DE MAPEAMENTO")
        print("=" * 70)
        
        if not self.load_mapping_db():
            return False
        
        # Estatísticas gerais
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"   📋 Total de NCMs: {len(self.mapping_db):,}")
        
        # Contar por nível hierárquico
        por_nivel = {}
        for data in self.mapping_db.values():
            nivel = data.get('nivel_hierarquico', len(data['ncm_codigo']))
            por_nivel[nivel] = por_nivel.get(nivel, 0) + 1
        
        print(f"   🏗️ Distribuição por nível:")
        for nivel in sorted(por_nivel.keys()):
            print(f"      Nível {nivel}: {por_nivel[nivel]:,} códigos")
        
        # Estatísticas de dados associados
        ncms_com_cest = sum(1 for data in self.mapping_db.values() if data['cests_associados'])
        ncms_com_produtos = sum(1 for data in self.mapping_db.values() if data['gtins_exemplos'])
        total_cests = sum(len(data['cests_associados']) for data in self.mapping_db.values())
        total_produtos = sum(len(data['gtins_exemplos']) for data in self.mapping_db.values())
        
        print(f"\n   🎯 NCMs com CEST: {ncms_com_cest:,} ({ncms_com_cest/len(self.mapping_db)*100:.1f}%)")
        print(f"   🛍️ NCMs com produtos: {ncms_com_produtos:,} ({ncms_com_produtos/len(self.mapping_db)*100:.1f}%)")
        print(f"   📊 Total de CESTs: {total_cests:,}")
        print(f"   📦 Total de produtos: {total_produtos:,}")
        
        # Testes específicos
        test_cases = [
            "8407.31.10",  # NCM específico (8 dígitos)
            "8407.3",      # NCM parcial (5 dígitos)
            "84.07",       # NCM parcial (4 dígitos)
            "3815.12.10",  # Outro NCM específico
            "30049099",    # NCM farmacêutico (sem pontos)
        ]
        
        for test_case in test_cases:
            self.test_specific_ncm(test_case)
        
        # Testes de hierarquia
        hierarchy_tests = [
            "8407",
            "3815",
            "30049"
        ]
        
        for hierarchy_test in hierarchy_tests:
            self.test_hierarchy_search(hierarchy_test)
        
        print(f"\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        return True


def main():
    """Função principal."""
    tester = MappingTester()
    
    if len(sys.argv) > 1:
        # Teste de NCM específico
        ncm_code = sys.argv[1]
        if tester.load_mapping_db():
            tester.test_specific_ncm(ncm_code)
    else:
        # Teste abrangente
        tester.run_comprehensive_test()


if __name__ == "__main__":
    main()