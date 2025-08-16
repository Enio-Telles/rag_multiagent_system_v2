#!/usr/bin/env python3
"""
scripts/build_knowledge_base.py
Fase 1: Construção da Base de Conhecimento Estruturada

Este script unifica todas as fontes de dados em um banco de mapeamento eficiente.
"""

import json
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, Any

# Adicionar o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from config import Config
from ingestion.data_loader import DataLoader

class KnowledgeBaseBuilder:
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        
        # Garantir que os diretórios existam
        self.config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Dicionário para mapear NCMs por nível hierárquico
        self.ncm_hierarchy = {}
    
    def _normalize_ncm(self, ncm_code: str) -> str:
        """Normaliza código NCM removendo pontos e espaços."""
        return str(ncm_code).replace(".", "").replace(" ", "").strip()
    
    def _build_ncm_hierarchy(self, ncm_data: list):
        """Constrói hierarquia de NCMs para permitir busca por códigos parciais."""
        print("🏗️ Construindo hierarquia de NCMs...")
        
        for item in ncm_data:
            code = self._normalize_ncm(item.get("Código", ""))
            if code:
                # Armazenar o código completo
                self.ncm_hierarchy[code] = {
                    "codigo_original": item.get("Código", ""),
                    "descricao_completa": item.get("Descricao_Completa", "").strip(),
                    "nivel": len(code)
                }
        
        print(f"✅ Hierarquia construída com {len(self.ncm_hierarchy)} códigos NCM.")
    
    def _find_best_ncm_match(self, input_ncm: str) -> str:
        """
        Encontra o melhor match de NCM considerando a hierarquia.
        Busca do mais específico para o mais geral.
        """
        normalized_input = self._normalize_ncm(input_ncm)
        
        # Primeiro, tenta match exato
        if normalized_input in self.ncm_hierarchy:
            return normalized_input
        
        # Se não encontrar exato, busca códigos que começam com o input (mais específicos)
        for code in self.ncm_hierarchy:
            if code.startswith(normalized_input) and len(code) >= len(normalized_input):
                return code
        
        # Se não encontrar mais específicos, busca códigos que o input começa (mais gerais)
        for length in range(len(normalized_input) - 1, 0, -1):
            partial_code = normalized_input[:length]
            if partial_code in self.ncm_hierarchy:
                return partial_code
        
        return None
    
    def build_mapping_database(self) -> Dict[str, Any]:
        """
        Constrói o banco de mapeamento unificado a partir de 4 arquivos JSON:
        
        1. descricoes_ncm.json - Base hierárquica NCM (15.141 códigos)
        2. CEST_RO.json - Dados oficiais CEST de Rondônia (vigentes)
        3. Anexos_conv_92_15_corrigido.json - Dados CEST complementares
        4. produtos_selecionados.json - Exemplos de produtos com GTIN
        
        UNIÃO DOS ARQUIVOS:
        - descricoes_ncm.json → estrutura base hierárquica (Código = NCM)
        - CEST_RO.json + Anexos_conv_92_15_corrigido.json → combinados via pd.concat 
          (NCM/SH = NCM_SH como chave de ligação)
        - produtos_selecionados.json → exemplos mapeados por campo 'ncm'
        
        Estrutura final por NCM:
        {
            'ncm_codigo': '22021000',
            'descricao_oficial': 'Águas, incluindo as águas minerais...',
            'cests_associados': [
                {'cest': '03.002.00', 'descricao_cest': 'Refrigerantes...'}
            ],
            'gtins_exemplos': [
                {
                    'gtin': '7891000100100', 
                    'descricao_produto': 'Coca-Cola 350ml',
                    'ncm_original': '22021000'
                }
            ]
        }
        """
        print("🔨 Iniciando construção do banco de mapeamento...")
        
        mapping_db = {}
        
        # ========================================================================
        # 1. CARREGAR BASE NCM COM HIERARQUIA
        # ========================================================================
        print("📋 Carregando descrições NCM...")
        ncm_data = self.data_loader.load_ncm_descriptions()
        if ncm_data:
            # Construir hierarquia de NCMs
            self._build_ncm_hierarchy(ncm_data)
            
            # Criar entradas na base de mapeamento para todos os códigos
            for code, data in self.ncm_hierarchy.items():
                mapping_db[code] = {
                    "ncm_codigo": code,
                    "codigo_original": data["codigo_original"],
                    "descricao_oficial": data["descricao_completa"],
                    "nivel_hierarquico": data["nivel"],
                    "cests_associados": [],
                    "gtins_exemplos": []
                }
        print(f"✅ {len(mapping_db)} NCMs carregados com hierarquia.")

        # ========================================================================
        # 2. MAPEAMENTO CEST COM HIERARQUIA
        # ========================================================================
        print("🔗 Mapeando dados CEST...")
        cest_data = self.data_loader.load_cest_mapping()
        if cest_data is not None and not cest_data.empty:
            print(f"📊 {len(cest_data)} registros CEST encontrados.")
            cest_count = 0
            cest_matched = 0
            
            for _, item in cest_data.iterrows():
                # Primeiro tenta NCM_SH, depois NCM/SH (para CEST_RO.json)
                ncm_input = str(item.get("NCM_SH", "") or item.get("NCM/SH", "")).strip()
                # Encontrar o melhor match considerando hierarquia
                best_match = self._find_best_ncm_match(ncm_input)
                
                if best_match and best_match in mapping_db:
                    cest_info = {
                        "cest": item.get("CEST", "").strip(),
                        "descricao_cest": (item.get("DESCRICAO", "") or item.get("DESCRIÇÃO", "")).strip(),
                        "ncm_original": ncm_input,
                        # Informações adicionais do CEST_RO.json (se disponíveis)
                        "tabela": item.get("TABELA", "").strip() if pd.notna(item.get("TABELA", "")) else None,
                        "anexo": item.get("ANEXO", "").strip() if pd.notna(item.get("ANEXO", "")) else None,
                        "situacao": item.get("Situação", "").strip() if pd.notna(item.get("Situação", "")) else None,
                        "inicio_vigencia": item.get("Início vig.", "").strip() if pd.notna(item.get("Início vig.", "")) else None
                    }
                    
                    # Remover campos None para manter estrutura limpa
                    cest_info = {k: v for k, v in cest_info.items() if v is not None}
                    
                    if cest_info not in mapping_db[best_match]["cests_associados"]:
                        mapping_db[best_match]["cests_associados"].append(cest_info)
                        cest_count += 1
                    cest_matched += 1
                    
            print(f"✅ {cest_matched}/{len(cest_data)} registros CEST mapeados.")
            print(f"✅ {cest_count} associações CEST adicionadas.")
        else:
            print("⚠️ Nenhum dado CEST carregado.")
        print("✅ Mapeamento CEST concluído.")
        
        # ========================================================================
        # 2.5. HERANÇA HIERÁRQUICA DE CESTs
        # ========================================================================
        print("🌳 Aplicando herança hierárquica de CESTs...")
        inherited_count = self._apply_cest_inheritance(mapping_db)
        print(f"✅ {inherited_count} NCMs receberam CESTs por herança hierárquica.")
        
        # ========================================================================
        # 3. MAPEAMENTO DE PRODUTOS SELECIONADOS (JSON) COM HIERARQUIA
        # ========================================================================
        print("🛍️  Mapeando produtos selecionados...")
        product_data = self.data_loader.load_produtos_selecionados()
        if product_data is not None and not product_data.empty:
            products_matched = 0
            products_added = 0
            
            for _, item in product_data.iterrows():
                # Usar 'ncm' do produtos_selecionados.json (equivale a NCM/SH = NCM_SH)
                ncm_input = str(item.get("ncm", "")).strip()
                # Encontrar o melhor match considerando hierarquia
                best_match = self._find_best_ncm_match(ncm_input)
                
                if best_match and best_match in mapping_db:
                    gtin_info = {
                        "gtin": str(item.get("gtin", "")).strip(),
                        "descricao_produto": item.get("descricao", "").strip(),
                        "ncm_original": ncm_input,
                        "cest_original": str(item.get("cest", "")).strip() if item.get("cest") else None
                    }
                    
                    # Remover campos None para manter estrutura limpa
                    gtin_info = {k: v for k, v in gtin_info.items() if v is not None and v != ""}
                    
                    # Limitar o número de exemplos para não sobrecarregar
                    if len(mapping_db[best_match]["gtins_exemplos"]) < self.config.MAX_GTIN_EXAMPLES:
                        mapping_db[best_match]["gtins_exemplos"].append(gtin_info)
                        products_added += 1
                    products_matched += 1
            
            print(f"✅ {products_matched}/{len(product_data)} produtos selecionados mapeados.")
            print(f"✅ {products_added} exemplos de produtos adicionados.")
        else:
            print("⚠️ Nenhum produto selecionado carregado.")
        print("✅ Mapeamento de produtos selecionados concluído.")
        
        # ========================================================================
        # 4. SALVAR A BASE DE CONHECIMENTO
        # ========================================================================
        print(f"💾 Salvando base de conhecimento em {self.config.NCM_MAPPING_FILE}...")
        try:
            with open(self.config.NCM_MAPPING_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(mapping_db.values()), f, ensure_ascii=False, indent=4)
            
            # ========================================================================
            # 5. ESTATÍSTICAS FINAIS
            # ========================================================================
            self._print_final_statistics(mapping_db)
            
            print("🎉 Base de conhecimento construída com sucesso!")
        except IOError as e:
            print(f"❌ Erro ao salvar o arquivo: {e}")
            return {}
        
        return mapping_db
    
    def _apply_cest_inheritance(self, mapping_db):
        """
        Aplica herança hierárquica de CESTs.
        NCMs filhos sem CEST próprio herdam os CESTs do NCM pai mais específico.
        """
        inherited_count = 0
        
        # Criar um dicionário para acesso rápido por código NCM
        ncm_dict = {data['ncm_codigo']: data for data in mapping_db.values()}
        
        # Processar todos os NCMs em ordem de comprimento (mais específicos primeiro)
        ncm_codes = sorted(ncm_dict.keys(), key=len, reverse=True)
        
        for ncm_code in ncm_codes:
            ncm_data = ncm_dict[ncm_code]
            
            # Se já tem CESTs próprios, pular
            if ncm_data.get('cests_associados'):
                continue
            
            # Buscar CEST do NCM pai mais específico
            parent_cests = self._find_parent_cests(ncm_code, ncm_dict)
            
            if parent_cests:
                # Herdar CESTs do pai, marcando como herdados
                inherited_cests = []
                for cest in parent_cests:
                    inherited_cest = cest.copy()
                    inherited_cest['herdado'] = True
                    inherited_cest['herdado_de'] = self._find_parent_with_cests(ncm_code, ncm_dict)
                    inherited_cests.append(inherited_cest)
                
                ncm_data['cests_associados'] = inherited_cests
                inherited_count += 1
        
        return inherited_count
    
    def _find_parent_cests(self, ncm_code, ncm_dict):
        """Encontra CESTs do NCM pai mais específico."""
        # Tentar códigos pais de tamanho decrescente
        for length in range(len(ncm_code) - 1, 0, -1):
            parent_code = ncm_code[:length]
            if parent_code in ncm_dict:
                parent_cests = ncm_dict[parent_code].get('cests_associados', [])
                # Só considerar CESTs próprios (não herdados) para evitar cadeia infinita
                own_cests = [c for c in parent_cests if not c.get('herdado', False)]
                if own_cests:
                    return own_cests
        return []
    
    def _find_parent_with_cests(self, ncm_code, ncm_dict):
        """Encontra o código do NCM pai que forneceu os CESTs."""
        for length in range(len(ncm_code) - 1, 0, -1):
            parent_code = ncm_code[:length]
            if parent_code in ncm_dict:
                parent_cests = ncm_dict[parent_code].get('cests_associados', [])
                own_cests = [c for c in parent_cests if not c.get('herdado', False)]
                if own_cests:
                    return parent_code
        return None
    
    def _print_final_statistics(self, mapping_db):
        """Imprime estatísticas finais da base construída."""
        print("\n📊 ESTATÍSTICAS FINAIS DA BASE DE CONHECIMENTO:")
        print("=" * 60)
        
        total_ncms = len(mapping_db)
        ncms_with_description = sum(1 for data in mapping_db.values() if data.get('descricao_oficial'))
        ncms_with_cest = sum(1 for data in mapping_db.values() if data.get('cests_associados'))
        ncms_with_examples = sum(1 for data in mapping_db.values() if data.get('gtins_exemplos'))
        
        # Separar CESTs próprios e herdados
        ncms_with_own_cest = 0
        ncms_with_inherited_cest = 0
        total_own_cests = 0
        total_inherited_cests = 0
        
        for data in mapping_db.values():
            cests = data.get('cests_associados', [])
            if cests:
                own_cests = [c for c in cests if not c.get('herdado', False)]
                inherited_cests = [c for c in cests if c.get('herdado', False)]
                
                if own_cests:
                    ncms_with_own_cest += 1
                    total_own_cests += len(own_cests)
                if inherited_cests:
                    ncms_with_inherited_cest += 1
                    total_inherited_cests += len(inherited_cests)
        
        total_cests = total_own_cests + total_inherited_cests
        total_examples = sum(len(data.get('gtins_exemplos', [])) for data in mapping_db.values())
        
        print(f"📋 Total de NCMs: {total_ncms:,}")
        print(f"📝 NCMs com descrição oficial: {ncms_with_description:,} ({ncms_with_description/total_ncms*100:.1f}%)")
        print(f"🎯 NCMs com CEST (total): {ncms_with_cest:,} ({ncms_with_cest/total_ncms*100:.1f}%)")
        print(f"   ├─ NCMs com CEST próprio: {ncms_with_own_cest:,}")
        print(f"   └─ NCMs com CEST herdado: {ncms_with_inherited_cest:,}")
        print(f"🛍️ NCMs com exemplos de produtos: {ncms_with_examples:,} ({ncms_with_examples/total_ncms*100:.1f}%)")
        print(f"📊 Total de associações CEST: {total_cests:,}")
        print(f"   ├─ CESTs próprios: {total_own_cests:,}")
        print(f"   └─ CESTs herdados: {total_inherited_cests:,}")
        print(f"📦 Total de exemplos de produtos: {total_examples:,}")
        print("=" * 60)
            
        return mapping_db


if __name__ == "__main__":
    builder = KnowledgeBaseBuilder()
    builder.build_mapping_database()