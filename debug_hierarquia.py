import json
import pandas as pd
import sys
from pathlib import Path

# Adicionar o diretório src ao path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import Config
from ingestion.data_loader import DataLoader

class DebugKnowledgeBaseBuilder:
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        self.ncm_hierarchy = {}
    
    def _normalize_ncm(self, ncm_code: str) -> str:
        """Normaliza código NCM removendo pontos e espaços."""
        return str(ncm_code).replace(".", "").replace(" ", "").strip()
    
    def _build_ncm_hierarchy(self, ncm_data: list):
        """Constrói hierarquia de NCMs para permitir busca por códigos parciais."""
        for item in ncm_data:
            code = self._normalize_ncm(item.get("Código", ""))
            if code:
                self.ncm_hierarchy[code] = {
                    "codigo_original": item.get("Código", ""),
                    "descricao_completa": item.get("Descricao_Completa", "").strip(),
                    "nivel": len(code)
                }
    
    def _find_best_ncm_match(self, ncm_input: str) -> str:
        """Encontra o melhor match NCM considerando hierarquia."""
        normalized_input = self._normalize_ncm(ncm_input)
        
        print(f"🔍 Buscando match para: '{ncm_input}' → normalizado: '{normalized_input}'")
        
        # Primeiro, tenta match exato
        if normalized_input in self.ncm_hierarchy:
            print(f"✅ Match exato encontrado: {normalized_input}")
            return normalized_input
        
        # Se não encontrar exato, busca códigos que começam com o input (mais específicos)
        matches_especificos = []
        for code in self.ncm_hierarchy:
            if code.startswith(normalized_input) and len(code) >= len(normalized_input):
                matches_especificos.append(code)
        
        if matches_especificos:
            print(f"🎯 Matches específicos encontrados: {matches_especificos[:5]}...")
            return matches_especificos[0]
        
        # Se não encontrar mais específicos, busca códigos que o input começa (mais gerais)
        for length in range(len(normalized_input) - 1, 0, -1):
            partial_code = normalized_input[:length]
            if partial_code in self.ncm_hierarchy:
                print(f"📈 Match hierárquico encontrado: {partial_code}")
                return partial_code
        
        print(f"❌ Nenhum match encontrado para: {normalized_input}")
        return None

# Executar debug
debug = DebugKnowledgeBaseBuilder()

# Carregar hierarquia NCM
ncm_data = debug.data_loader.load_ncm_descriptions()
if ncm_data:
    debug._build_ncm_hierarchy(ncm_data)
    print(f"Hierarquia carregada: {len(debug.ncm_hierarchy)} códigos")
    
    # Testar busca para "3004"
    result = debug._find_best_ncm_match("3004")
    print(f"Resultado final: {result}")
    
    # Verificar se 3004 existe na hierarquia
    if "3004" in debug.ncm_hierarchy:
        print(f"✅ 3004 existe na hierarquia: {debug.ncm_hierarchy['3004']}")
    else:
        print("❌ 3004 NÃO existe na hierarquia")
        
        # Verificar códigos próximos
        proximos = [code for code in debug.ncm_hierarchy.keys() if code.startswith("300")]
        print(f"Códigos próximos (300*): {sorted(proximos)[:10]}")
