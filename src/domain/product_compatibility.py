"""
Validador de compatibilidade de produtos para agrupamento
Evita agrupar produtos de categorias muito diferentes
"""
import sys
from pathlib import Path
import re
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass

# Adicionar src ao path se necessário
sys.path.append(str(Path(__file__).parent.parent))

try:
    from domain.validators import NcmFormatValidator
except ImportError:
    # Fallback se validators não estiverem disponíveis
    class NcmFormatValidator:
        @staticmethod
        def get_hierarchy_info(ncm: str) -> Dict[str, str]:
            if not ncm or len(ncm) != 8:
                return {}
            return {
                "chapter": ncm[:2],
                "heading": ncm[:4], 
                "subheading": ncm[:6],
                "full": ncm
            }

@dataclass
class ProductCategory:
    """Categoria de produto com critérios de compatibilidade"""
    name: str
    ncm_chapters: Set[str]  # Capítulos NCM permitidos
    keywords: Set[str]      # Palavras-chave da categoria
    incompatible_with: Set[str]  # Categorias incompatíveis

class ProductCompatibilityValidator:
    """Valida se produtos podem ser agrupados juntos"""
    
    def __init__(self):
        self.categories = self._define_product_categories()
        self.forbidden_combinations = self._define_forbidden_combinations()
    
    def _define_product_categories(self) -> Dict[str, ProductCategory]:
        """Define categorias de produtos com critérios de compatibilidade"""
        return {
            "medicamentos": ProductCategory(
                name="medicamentos",
                ncm_chapters={"30"},
                keywords={"medicamento", "farmac", "droga", "remedio", "antibiotico", "vitamina"},
                incompatible_with={"alimentos", "eletronicos", "texteis", "automoveis", "cosmeticos", "ortopedicos"}
            ),
            "alimentos": ProductCategory(
                name="alimentos",
                ncm_chapters={"19", "20", "21", "22", "04", "15", "16", "17", "18"},
                keywords={"biscoito", "cookie", "chocolate", "bebida", "leite", "queijo", "sorvete"},
                incompatible_with={"medicamentos", "eletronicos", "automoveis", "produtos_quimicos"}
            ),
            "cosmeticos": ProductCategory(
                name="cosmeticos",
                ncm_chapters={"33"},
                keywords={"perfume", "shampoo", "sabonete", "creme", "protetor", "maquiagem", "batom"},
                incompatible_with={"medicamentos", "alimentos", "eletronicos", "automoveis"}
            ),
            "eletronicos": ProductCategory(
                name="eletronicos",
                ncm_chapters={"85", "84", "90"},
                keywords={"eletronic", "aparelho", "celular", "telefone", "computador", "cabo", "fonte"},
                incompatible_with={"medicamentos", "alimentos", "texteis", "cosmeticos"}
            ),
            "texteis": ProductCategory(
                name="texteis",
                ncm_chapters={"61", "62", "63", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60"},
                keywords={"roupa", "camisa", "calca", "tecido", "algodao", "poliester", "fibra"},
                incompatible_with={"medicamentos", "alimentos", "eletronicos", "automoveis"}
            ),
            "automoveis": ProductCategory(
                name="automoveis",
                ncm_chapters={"87", "40"},
                keywords={"carro", "auto", "pneu", "motor", "oleo", "filtro", "peca"},
                incompatible_with={"medicamentos", "alimentos", "cosmeticos", "texteis"}
            ),
            "produtos_pessoais": ProductCategory(
                name="produtos_pessoais",
                ncm_chapters={"82", "96"},
                keywords={"barbear", "escova", "pente", "navalha", "barbeador", "higiene"},
                incompatible_with={"medicamentos", "alimentos", "eletronicos", "automoveis"}
            ),
            "ortopedicos": ProductCategory(
                name="ortopedicos", 
                ncm_chapters={"90"},
                keywords={"imobilizador", "ortopedico", "suporte", "munhequeira", "joelheira", "tala"},
                incompatible_with={"alimentos", "eletronicos", "automoveis", "texteis", "medicamentos"}
            ),
            "utensilios": ProductCategory(
                name="utensilios",
                ncm_chapters={"39", "70", "82"},
                keywords={"copo", "prato", "utensilio", "plastico", "vidro", "cozinha"},
                incompatible_with={"medicamentos", "eletronicos", "automoveis", "texteis"}
            )
        }
    
    def _define_forbidden_combinations(self) -> List[Tuple[str, str]]:
        """Define combinações explicitamente proibidas"""
        return [
            ("medicamentos", "alimentos"),
            ("medicamentos", "eletronicos"),
            ("medicamentos", "automoveis"),
            ("medicamentos", "texteis"),
            ("medicamentos", "cosmeticos"),
            ("medicamentos", "ortopedicos"),      # Medicamentos ≠ Equipamentos ortopédicos
            ("alimentos", "eletronicos"),
            ("alimentos", "automoveis"),
            ("alimentos", "produtos_quimicos"),
            ("eletronicos", "texteis"),
            ("eletronicos", "cosmeticos"),
            ("automoveis", "cosmeticos"),
            ("automoveis", "texteis"),
            ("produtos_pessoais", "ortopedicos"),  # Aparelho barbear ≠ imobilizador
            ("utensilios", "produtos_pessoais"),   # Copo ≠ aparelho barbear
            ("utensilios", "ortopedicos"),         # Copo ≠ imobilizador
            ("utensilios", "medicamentos")         # Copo ≠ medicamentos
        ]
    
    def identify_product_category(self, produto: Dict) -> str:
        """Identifica a categoria de um produto"""
        
        # Verificar por NCM primeiro
        ncm = produto.get("ncm") or produto.get("ncm_classificado", "")
        if ncm:
            hierarchy = NcmFormatValidator.get_hierarchy_info(str(ncm))
            chapter = hierarchy.get("chapter", "")
            
            for cat_name, category in self.categories.items():
                if chapter in category.ncm_chapters:
                    return cat_name
        
        # Verificar por palavras-chave na descrição
        descricao = (produto.get("descricao_produto", "") + " " + 
                    produto.get("descricao_expandida", "")).lower()
        
        # Ordenar por prioridade (categorias mais específicas primeiro)
        categories_ordered = ["medicamentos", "produtos_pessoais", "ortopedicos", "cosmeticos", 
                            "alimentos", "eletronicos", "texteis", "automoveis", "utensilios"]
        
        for cat_name in categories_ordered:
            if cat_name in self.categories:
                category = self.categories[cat_name]
                for keyword in category.keywords:
                    if keyword.lower() in descricao:
                        return cat_name
        
        # Categoria genérica se não identificada
        return "outros"
    
    def products_are_compatible(self, produto1: Dict, produto2: Dict) -> Tuple[bool, str]:
        """
        Verifica se dois produtos podem ser agrupados juntos
        
        Returns:
            Tuple[bool, str]: (compatível, razão)
        """
        
        cat1 = self.identify_product_category(produto1)
        cat2 = self.identify_product_category(produto2)
        
        # Produtos da mesma categoria são sempre compatíveis
        if cat1 == cat2:
            return True, f"Mesma categoria: {cat1}"
        
        # Verificar combinações proibidas
        if (cat1, cat2) in self.forbidden_combinations or (cat2, cat1) in self.forbidden_combinations:
            return False, f"Categorias incompatíveis: {cat1} vs {cat2}"
        
        # Verificar incompatibilidades definidas nas categorias
        if cat1 in self.categories and cat2 in self.categories[cat1].incompatible_with:
            return False, f"Categoria {cat1} incompatível com {cat2}"
        
        if cat2 in self.categories and cat1 in self.categories[cat2].incompatible_with:
            return False, f"Categoria {cat2} incompatível com {cat1}"
        
        # Se não há incompatibilidade explícita, permitir agrupamento
        return True, f"Categorias compatíveis: {cat1} e {cat2}"
    
    def validate_group_homogeneity(self, produtos: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Valida se um grupo de produtos é homogêneo
        
        Returns:
            Tuple[bool, List[str]]: (homogêneo, alertas)
        """
        if len(produtos) <= 1:
            return True, []
        
        alertas = []
        categories = [self.identify_product_category(p) for p in produtos]
        unique_categories = set(categories)
        
        # Se há mais de 2 categorias diferentes, é suspeito
        if len(unique_categories) > 2:
            alertas.append(f"Muitas categorias no grupo: {unique_categories}")
            return False, alertas
        
        # Verificar compatibilidade par a par
        for i in range(len(produtos)):
            for j in range(i + 1, len(produtos)):
                compatible, reason = self.products_are_compatible(produtos[i], produtos[j])
                if not compatible:
                    alertas.append(f"Produtos incompatíveis: {produtos[i].get('descricao_produto', '')} vs {produtos[j].get('descricao_produto', '')} - {reason}")
                    return False, alertas
        
        return True, alertas
    
    def suggest_group_split(self, produtos: List[Dict]) -> List[List[int]]:
        """
        Sugere como dividir um grupo heterogêneo
        
        Returns:
            List[List[int]]: Lista de subgrupos (índices dos produtos)
        """
        if len(produtos) <= 1:
            return [[0]] if produtos else []
        
        # Agrupar por categoria
        category_groups = {}
        for i, produto in enumerate(produtos):
            category = self.identify_product_category(produto)
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(i)
        
        # Retornar grupos separados por categoria
        return list(category_groups.values())
    
    def get_category_summary(self, produtos: List[Dict]) -> Dict[str, int]:
        """Retorna resumo das categorias presentes nos produtos"""
        categories = [self.identify_product_category(p) for p in produtos]
        summary = {}
        for cat in categories:
            summary[cat] = summary.get(cat, 0) + 1
        return summary


# Função de conveniência para usar o validator
def validate_product_grouping(produtos: List[Dict]) -> Dict[str, Any]:
    """
    Função de conveniência para validar agrupamento de produtos
    
    Returns:
        Dict com validação e sugestões
    """
    validator = ProductCompatibilityValidator()
    
    is_homogeneous, alerts = validator.validate_group_homogeneity(produtos)
    category_summary = validator.get_category_summary(produtos)
    
    result = {
        "is_homogeneous": is_homogeneous,
        "alerts": alerts,
        "category_summary": category_summary,
        "total_products": len(produtos),
        "total_categories": len(category_summary)
    }
    
    if not is_homogeneous:
        suggested_splits = validator.suggest_group_split(produtos)
        result["suggested_splits"] = suggested_splits
        result["suggested_split_count"] = len(suggested_splits)
    
    return result
