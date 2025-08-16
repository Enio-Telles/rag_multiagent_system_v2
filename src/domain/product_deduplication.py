"""
Detector de produtos idênticos com descrições diferentes
Foco em identificar duplicatas e variações de descrição do mesmo produto exato
"""
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ProductIdentity:
    """Identidade normalizada de um produto"""
    brand: str = ""
    product_type: str = ""
    variant: str = ""
    quantity: str = ""
    unit: str = ""
    size: str = ""
    normalized_key: str = ""

class ProductDeduplicationValidator:
    """Validador para identificar produtos idênticos com descrições diferentes"""
    
    def __init__(self):
        self.brand_variations = self._load_brand_variations()
        self.common_abbreviations = self._load_abbreviations()
        self.unit_normalizations = self._load_unit_normalizations()
        
    def _load_brand_variations(self) -> Dict[str, List[str]]:
        """Mapeamento de variações de marcas conhecidas"""
        return {
            "gillette": ["gillette", "gilete", "gil", "gillet"],
            "mormaii": ["mormaii", "mormai", "morm"],
            "kuka": ["kuka", "kuca"],
            "presto": ["presto", "prest", "prs"],
            "lacta": ["lacta", "lact"],
            "toddy": ["toddy", "todd", "tody"],
            "prestobarba": ["prestobarba", "prestob", "presto barba", "presto-barba"]
        }
    
    def _load_abbreviations(self) -> Dict[str, List[str]]:
        """Abreviações comuns em descrições"""
        return {
            "aparelho": ["apar", "ap", "aparelho"],
            "barbear": ["barbear", "barb", "bb"],
            "masculino": ["masculi", "masc", "m", "masculino"],
            "unidades": ["unid", "un", "und", "unidades", "pcs", "peças"],
            "gramas": ["gr", "g", "gramas", "grs"],
            "mililitros": ["ml", "mli", "mililitros"],
            "imobilizador": ["imobilizador", "imob", "imobiliz"],
            "direito": ["dir", "d", "direito", "drt"],
            "esquerdo": ["esq", "e", "esquerdo", "esqd"],
            "curta": ["curta", "curt", "c"],
            "média": ["media", "med", "m"],
            "grande": ["grande", "g", "grd"],
            "pequeno": ["pequeno", "p", "peq"],
            "médio": ["medio", "med", "m"],
            "biscoito": ["bisc", "biscoito", "bolacha"],
            "recheado": ["rech", "recheado", "rechd"],
            "chocolate": ["choc", "chocolate", "cacau"],
            "infantil": ["inf", "infantil", "criança", "bebe"]
        }
    
    def _load_unit_normalizations(self) -> Dict[str, str]:
        """Normalização de unidades"""
        return {
            "gr": "g",
            "grs": "g", 
            "gramas": "g",
            "ml": "ml",
            "mli": "ml",
            "mililitros": "ml",
            "un": "unid",
            "und": "unid",
            "pcs": "unid",
            "peças": "unid",
            "unidades": "unid"
        }
    
    def normalize_description(self, description: str) -> ProductIdentity:
        """
        Normaliza descrição do produto para identificação de duplicatas
        
        Exemplos:
        - "APAR BARBEAR PRESTO MASCULI GILLETTE" 
        - "APARELHO BARBEAR PRESTOB MASCULINO GILETE"
        → Mesmo produto: aparelho_barbear_presto_masculino_gillette
        """
        if not description:
            return ProductIdentity()
        
        # Converter para minúsculas e remover caracteres especiais
        desc = description.lower().strip()
        desc = re.sub(r'[^\w\s]', ' ', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # Extrair informações estruturadas
        identity = ProductIdentity()
        
        # Identificar marca
        identity.brand = self._extract_brand(desc)
        
        # Identificar tipo de produto
        identity.product_type = self._extract_product_type(desc)
        
        # Identificar variante/modelo
        identity.variant = self._extract_variant(desc)
        
        # Identificar quantidade
        identity.quantity = self._extract_quantity(desc)
        
        # Identificar unidade
        identity.unit = self._extract_unit(desc)
        
        # Identificar tamanho
        identity.size = self._extract_size(desc)
        
        # Criar chave normalizada
        identity.normalized_key = self._create_normalized_key(identity)
        
        return identity
    
    def _extract_brand(self, desc: str) -> str:
        """Extrai e normaliza marca"""
        for canonical_brand, variations in self.brand_variations.items():
            for variation in variations:
                if variation in desc:
                    return canonical_brand
        return ""
    
    def _extract_product_type(self, desc: str) -> str:
        """Extrai tipo de produto"""
        product_types = {
            "aparelho_barbear": ["apar barbear", "aparelho barbear", "barbead", "barbeador"],
            "imobilizador": ["imobilizador", "imob"],
            "copo": ["copo"],
            "biscoito": ["bisc", "biscoito", "bolacha"],
            "medicamento": ["medicamento", "remedio", "farmaco"],
            "protetor": ["protetor", "protec"]
        }
        
        for product_type, keywords in product_types.items():
            for keyword in keywords:
                if keyword in desc:
                    return product_type
        return ""
    
    def _extract_variant(self, desc: str) -> str:
        """Extrai variante/modelo do produto"""
        variants = []
        
        # Variantes comuns - unificar presto com prestob/prestobarba
        variant_patterns = [
            r'\b(presto(?:b|barba)?)\b',
            r'\b(fusion)\b', 
            r'\b(mach3)\b',
            r'\b(sensor)\b',
            r'\b(lacta)\b',
            r'\b(toddy)\b',
            r'\b(original)\b',
            r'\b(premium)\b'
        ]
        
        for pattern in variant_patterns:
            match = re.search(pattern, desc)
            if match:
                variant = match.group(1)
                # Normalizar todas as variações de presto
                if variant in ["prestob", "presto", "prestobarba"]:
                    variant = "presto"
                variants.append(variant)
        
        return "_".join(sorted(set(variants)))
    
    def _extract_quantity(self, desc: str) -> str:
        """Extrai quantidade"""
        # Padrões de quantidade
        quantity_patterns = [
            r'(\d+)\s*(?:unid|un|und|pcs|peças)',
            r'(\d+)\s*x',
            r'pacote\s*(?:de|com)?\s*(\d+)',
            r'kit\s*(\d+)',
            r'(\d+)\s*(?:gramas?|gr?|g)\b',
            r'(\d+)\s*(?:ml|mililitros?)\b'
        ]
        
        for pattern in quantity_patterns:
            match = re.search(pattern, desc)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_unit(self, desc: str) -> str:
        """Extrai unidade"""
        unit_patterns = [
            r'\d+\s*(g|gr|gramas?)\b',
            r'\d+\s*(ml|mililitros?)\b',
            r'\d+\s*(unid|un|und|pcs|peças)\b'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, desc)
            if match:
                unit = match.group(1).lower()
                return self.unit_normalizations.get(unit, unit)
        
        return ""
    
    def _extract_size(self, desc: str) -> str:
        """Extrai tamanho (G, M, P, etc.)"""
        size_patterns = [
            r'\b(pequeno?|p)\b',
            r'\b(medio?|m)\b', 
            r'\b(grande?|g)\b',
            r'\b(curta?|curt)\b',
            r'\b(longa?|long)\b'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, desc)
            if match:
                size = match.group(1).lower()
                if size in ["pequeno", "p"]:
                    return "p"
                elif size in ["medio", "med", "m"]:
                    return "m"
                elif size in ["grande", "g"]:
                    return "g"
                elif size in ["curta", "curt"]:
                    return "curta"
                elif size in ["longa", "long"]:
                    return "longa"
        
        return ""
    
    def _create_normalized_key(self, identity: ProductIdentity) -> str:
        """Cria chave normalizada para comparação - mais flexível"""
        components = [
            identity.product_type,
            identity.brand,
            identity.variant,
            identity.quantity,
            identity.unit
            # Removendo size por enquanto para ser mais permissivo
        ]
        
        # Remover componentes vazios e criar chave
        key_parts = [part for part in components if part]
        return "_".join(key_parts)
    
    def products_are_identical(self, produto1: Dict, produto2: Dict) -> Tuple[bool, str, float]:
        """
        Verifica se dois produtos são idênticos (mesmo produto, descrições diferentes)
        
        Returns:
            Tuple[bool, str, float]: (são_idênticos, razão, confiança)
        """
        # Preferir descrição expandida se disponível, senão usar original
        desc1 = produto1.get("descricao_expandida", produto1.get("descricao_produto", ""))
        desc2 = produto2.get("descricao_expandida", produto2.get("descricao_produto", ""))
        
        if not desc1 or not desc2:
            return False, "Descrições vazias", 0.0
        
        # REGRA 1: Descrições idênticas = produtos idênticos
        if desc1.strip() == desc2.strip():
            return True, "Descrições idênticas", 1.0
        
        # REGRA 2: Mesmo código de produto = produtos idênticos (mesmo que descrições sejam ligeiramente diferentes)
        codigo1 = produto1.get("codigo_produto", "")
        codigo2 = produto2.get("codigo_produto", "")
        if codigo1 and codigo2 and codigo1 == codigo2:
            # Verificar se as descrições são similares o suficiente
            similarity = SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
            if similarity > 0.8:  # 80% de similaridade textual
                return True, f"Mesmo código de produto ({codigo1}) com descrições similares (sim={similarity:.2f})", 0.95
            elif similarity > 0.5:  # Ainda similar, mas menos confiança
                return True, f"Mesmo código de produto ({codigo1}) com descrições diferentes (sim={similarity:.2f})", 0.85
        
        # REGRA 3: Análise semântica baseada na normalização (para casos sem código de produto)
        # Normalizar ambas as descrições
        identity1 = self.normalize_description(desc1)
        identity2 = self.normalize_description(desc2)
        
        # Comparar chaves normalizadas
        if identity1.normalized_key == identity2.normalized_key and identity1.normalized_key:
            confidence = self._calculate_confidence(desc1, desc2, identity1, identity2)
            return True, f"Produto idêntico: {identity1.normalized_key}", confidence
        
        # Verificar similaridade alta mesmo com chaves diferentes - mais permissivo
        similarity = self._calculate_similarity_flexible(identity1, identity2)
        if similarity > 0.75:  # Reduzido de 0.8 para 0.75
            # Verificar se as diferenças são apenas de formatação
            if self._are_formatting_differences_only_flexible(identity1, identity2):
                confidence = similarity * 0.9
                return True, f"Mesmo produto com variações de formatação (sim={similarity:.2f})", confidence
        
        return False, f"Produtos diferentes: '{identity1.normalized_key}' vs '{identity2.normalized_key}'", similarity
    
    def _calculate_confidence(self, desc1: str, desc2: str, identity1: ProductIdentity, identity2: ProductIdentity) -> float:
        """Calcula confiança na identificação"""
        # Fatores que aumentam confiança
        confidence = 0.5  # Base
        
        # Similaridade textual das descrições originais
        text_similarity = SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
        confidence += text_similarity * 0.3
        
        # Presença de componentes estruturados
        if identity1.brand and identity1.brand == identity2.brand:
            confidence += 0.1
        if identity1.quantity and identity1.quantity == identity2.quantity:
            confidence += 0.1
        if identity1.unit and identity1.unit == identity2.unit:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_similarity_flexible(self, identity1: ProductIdentity, identity2: ProductIdentity) -> float:
        """Calcula similaridade entre identidades - versão mais flexível"""
        # Componentes essenciais para identidade
        essential_components = ["product_type", "brand", "quantity", "unit"]
        optional_components = ["variant", "size"]
        
        essential_matches = 0
        essential_total = 0
        optional_matches = 0
        optional_total = 0
        
        # Verificar componentes essenciais
        for component in essential_components:
            val1 = getattr(identity1, component, "")
            val2 = getattr(identity2, component, "")
            
            if val1 or val2:  # Se pelo menos um tem valor
                essential_total += 1
                if val1 == val2:
                    essential_matches += 1
                elif val1 and val2:  # Ambos têm valor mas são diferentes
                    # Verificar similaridade textual alta
                    sim = SequenceMatcher(None, val1, val2).ratio()
                    if sim > 0.8:  # Para componentes essenciais, exigir alta similaridade
                        essential_matches += sim
        
        # Verificar componentes opcionais
        for component in optional_components:
            val1 = getattr(identity1, component, "")
            val2 = getattr(identity2, component, "")
            
            if val1 or val2:
                optional_total += 1
                if val1 == val2:
                    optional_matches += 1
                elif val1 and val2:
                    sim = SequenceMatcher(None, val1, val2).ratio()
                    if sim > 0.6:  # Para opcionais, ser mais permissivo
                        optional_matches += sim
        
        # Calcular score final com peso maior para essenciais
        essential_score = essential_matches / essential_total if essential_total > 0 else 0.0
        optional_score = optional_matches / optional_total if optional_total > 0 else 1.0  # Default positivo se não há opcionais
        
        # Score final: 80% peso para essenciais, 20% para opcionais
        final_score = (essential_score * 0.8) + (optional_score * 0.2)
        
        return final_score
    
    def _are_formatting_differences_only_flexible(self, identity1: ProductIdentity, identity2: ProductIdentity) -> bool:
        """Verifica se as diferenças são apenas de formatação - versão mais flexível"""
        # Se tipo, marca e quantidade são iguais ou muito similares, é formatação
        type_same = identity1.product_type == identity2.product_type
        brand_same = identity1.brand == identity2.brand
        
        # Para quantidade, ser mais flexível
        quantity_same = (
            identity1.quantity == identity2.quantity or
            (not identity1.quantity and not identity2.quantity) or  # Ambos vazios
            (identity1.quantity and identity2.quantity and 
             SequenceMatcher(None, identity1.quantity, identity2.quantity).ratio() > 0.8)
        )
        
        return type_same and brand_same and quantity_same
    
    def suggest_canonical_description(self, descriptions: List[str]) -> str:
        """Sugere descrição canônica para um grupo de produtos idênticos"""
        if not descriptions:
            return ""
        
        if len(descriptions) == 1:
            return descriptions[0]
        
        # Escolher a descrição mais completa (mais palavras)
        longest = max(descriptions, key=lambda x: len(x.split()))
        
        # Ou escolher a mais comum (se houvesse histórico)
        return longest
    
    def group_identical_products(self, produtos: List[Dict]) -> List[List[int]]:
        """
        Agrupa produtos idênticos
        
        Returns:
            List[List[int]]: Lista de grupos de índices de produtos idênticos
        """
        if len(produtos) <= 1:
            return [[i] for i in range(len(produtos))]
        
        groups = []
        processed = set()
        
        for i, produto1 in enumerate(produtos):
            if i in processed:
                continue
                
            # Começar novo grupo com produto atual
            current_group = [i]
            processed.add(i)
            
            # Procurar produtos idênticos
            for j, produto2 in enumerate(produtos[i+1:], i+1):
                if j in processed:
                    continue
                    
                identical, reason, confidence = self.products_are_identical(produto1, produto2)
                
                if identical and confidence > 0.7:
                    current_group.append(j)
                    processed.add(j)
            
            groups.append(current_group)
        
        return groups


def validate_product_deduplication(produtos: List[Dict]) -> Dict[str, Any]:
    """
    Função de conveniência para validar duplicação de produtos
    
    Returns:
        Dict com análise de duplicação
    """
    validator = ProductDeduplicationValidator()
    
    groups = validator.group_identical_products(produtos)
    
    # Estatísticas
    duplicates_found = sum(1 for group in groups if len(group) > 1)
    total_duplicates = sum(len(group) - 1 for group in groups if len(group) > 1)
    
    # Análise detalhada dos grupos com duplicatas
    duplicate_analysis = []
    for group in groups:
        if len(group) > 1:
            group_products = [produtos[i] for i in group]
            descriptions = [p.get("descricao_expandida", p.get("descricao_produto", "")) for p in group_products]
            canonical = validator.suggest_canonical_description(descriptions)
            
            duplicate_analysis.append({
                "indices": group,
                "descriptions": descriptions,
                "canonical_description": canonical,
                "duplicate_count": len(group) - 1
            })
    
    return {
        "total_products": len(produtos),
        "total_groups": len(groups),
        "unique_products": len(groups),
        "duplicates_found": duplicates_found,
        "total_duplicates": total_duplicates,
        "deduplication_rate": total_duplicates / len(produtos) if produtos else 0,
        "duplicate_analysis": duplicate_analysis
    }
