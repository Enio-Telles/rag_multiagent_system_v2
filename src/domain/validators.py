"""
Módulo de validação de códigos fiscais NCM e CEST
Implementa regras oficiais brasileiras com validação rigorosa
"""
from typing import Optional, Tuple, Set, List, Dict, Any
from pathlib import Path
import json
import re
from dataclasses import dataclass
from enum import Enum

class ValidationResult(Enum):
    """Resultado de validação"""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_BINDING = "invalid_binding"
    NOT_FOUND = "not_found"

@dataclass
class CestValidationDetails:
    """Detalhes da validação CEST"""
    result: ValidationResult
    normalized_cest: Optional[str] = None
    error_message: Optional[str] = None
    suggested_alternatives: List[str] = None
    
    @property
    def is_valid(self) -> bool:
        return self.result == ValidationResult.VALID

@dataclass 
class NcmValidationDetails:
    """Detalhes da validação NCM"""
    result: ValidationResult
    normalized_ncm: Optional[str] = None
    hierarchy_level: Optional[int] = None
    chapter: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        return self.result == ValidationResult.VALID

class CestFormatValidator:
    """Validador de formato CEST - 7 dígitos no padrão SS.III.DD"""
    
    @classmethod
    def normalize_cest(cls, cest: str | None) -> Optional[str]:
        """
        Normaliza CEST para formato padrão SS.III.DD
        
        Args:
            cest: Código CEST em qualquer formato
            
        Returns:
            CEST normalizado ou None se inválido
            
        Examples:
            >>> CestFormatValidator.normalize_cest("2106400")
            "21.064.00"
            >>> CestFormatValidator.normalize_cest("21.064.00")
            "21.064.00"
            >>> CestFormatValidator.normalize_cest("13001000")
            "13.001.00"
        """
        if not cest:
            return None
            
        # Remove espaços, pontos, hífens e outros separadores
        cest_clean = str(cest).strip()
        cest_digits = ''.join(c for c in cest_clean if c.isdigit())
        
        # CEST deve ter exatamente 7 ou 8 dígitos
        if len(cest_digits) == 7:
            # Formato correto: SS III DD
            return f"{cest_digits[:2]}.{cest_digits[2:5]}.{cest_digits[5:7]}"
        elif len(cest_digits) == 8:
            # Assume que o último dígito foi duplicado, pega apenas os 7 primeiros
            return f"{cest_digits[:2]}.{cest_digits[2:5]}.{cest_digits[5:7]}"
        else:
            # Número incorreto de dígitos
            return None
    
    @classmethod
    def validate_format(cls, cest: str | None) -> CestValidationDetails:
        """Valida formato CEST"""
        if not cest:
            return CestValidationDetails(
                result=ValidationResult.INVALID_FORMAT,
                error_message="CEST não fornecido"
            )
        
        normalized = cls.normalize_cest(cest)
        if normalized:
            return CestValidationDetails(
                result=ValidationResult.VALID,
                normalized_cest=normalized
            )
        else:
            return CestValidationDetails(
                result=ValidationResult.INVALID_FORMAT,
                error_message=f"CEST '{cest}' não está no formato SS.III.DD com 7 dígitos",
                suggested_alternatives=[]
            )

class NcmFormatValidator:
    """Validador de formato NCM - 8 dígitos"""
    
    NCM_PATTERN = re.compile(r'^(\d{2})(\d{2})(\d{2})(\d{2})$')
    
    @classmethod
    def normalize_ncm(cls, ncm: str | None) -> Optional[str]:
        """
        Normaliza NCM para 8 dígitos
        
        Args:
            ncm: Código NCM
            
        Returns:
            NCM normalizado ou None se inválido
        """
        if not ncm:
            return None
            
        # Remove pontos, espaços e garante apenas dígitos
        ncm_digits = ''.join(c for c in str(ncm) if c.isdigit())
        
        # Deve ter exatamente 8 dígitos
        if len(ncm_digits) != 8:
            return None
            
        return ncm_digits
    
    @classmethod
    def get_hierarchy_info(cls, ncm: str) -> Dict[str, str]:
        """
        Extrai informações hierárquicas do NCM
        
        Returns:
            Dict com chapter (4 dígitos), position (6 dígitos), etc.
        """
        ncm_normalized = cls.normalize_ncm(ncm)
        if not ncm_normalized:
            return {}
            
        return {
            "chapter": ncm_normalized[:4],      # 4 primeiros dígitos
            "position": ncm_normalized[:6],     # 6 primeiros dígitos  
            "subposition": ncm_normalized[:7],  # 7 primeiros dígitos
            "full": ncm_normalized             # 8 dígitos completos
        }
    
    @classmethod
    def validate_format(cls, ncm: str | None) -> NcmValidationDetails:
        """Valida formato NCM"""
        if not ncm:
            return NcmValidationDetails(
                result=ValidationResult.INVALID_FORMAT,
                error_message="NCM não fornecido"
            )
        
        normalized = cls.normalize_ncm(ncm)
        if normalized:
            hierarchy = cls.get_hierarchy_info(normalized)
            return NcmValidationDetails(
                result=ValidationResult.VALID,
                normalized_ncm=normalized,
                hierarchy_level=8,
                chapter=hierarchy.get("chapter")
            )
        else:
            return NcmValidationDetails(
                result=ValidationResult.INVALID_FORMAT,
                error_message=f"NCM '{ncm}' deve ter exatamente 8 dígitos"
            )

class FiscalCatalog:
    """Catálogo de regras fiscais NCM-CEST oficiais"""
    
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self._catalog_data: Dict[str, Any] = {}
        self._load_catalog()
    
    def _load_catalog(self):
        """Carrega catálogo de regras fiscais"""
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    self._catalog_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erro ao carregar catálogo fiscal: {e}")
                self._catalog_data = {}
        else:
            print(f"Catálogo fiscal não encontrado: {self.catalog_path}")
            self._catalog_data = {}
    
    def get_allowed_cests_for_ncm(self, ncm: str) -> Set[str]:
        """Retorna CESTs permitidos para um NCM específico"""
        ncm_normalized = NcmFormatValidator.normalize_ncm(ncm)
        if not ncm_normalized:
            return set()
        
        # Busca exata por NCM
        ncm_mapping = self._catalog_data.get("ncm_to_cests", {})
        if ncm_normalized in ncm_mapping:
            return set(ncm_mapping[ncm_normalized])
        
        return set()
    
    def get_allowed_cests_for_chapter(self, chapter: str) -> Set[str]:
        """Retorna CESTs permitidos para um capítulo NCM (4 dígitos)"""
        chapter_mapping = self._catalog_data.get("chapter_to_cests", {})
        return set(chapter_mapping.get(chapter, []))
    
    def get_cest_description(self, cest: str) -> Optional[str]:
        """Retorna descrição oficial do CEST"""
        cest_normalized = CestFormatValidator.normalize_cest(cest)
        if not cest_normalized:
            return None
        
        cest_descriptions = self._catalog_data.get("cest_descriptions", {})
        return cest_descriptions.get(cest_normalized)
    
    def suggest_alternative_cests(self, ncm: str, invalid_cest: str) -> List[str]:
        """Sugere CESTs alternativos válidos para um NCM"""
        hierarchy = NcmFormatValidator.get_hierarchy_info(ncm)
        
        # Primeiro tenta por NCM exato
        exact_cests = self.get_allowed_cests_for_ncm(ncm)
        if exact_cests:
            return list(exact_cests)[:3]  # Máximo 3 sugestões
        
        # Depois tenta por capítulo
        if "chapter" in hierarchy:
            chapter_cests = self.get_allowed_cests_for_chapter(hierarchy["chapter"])
            return list(chapter_cests)[:3]
        
        return []

class FiscalValidator:
    """Validador fiscal principal que combina validações de formato e regras de negócio"""
    
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog = FiscalCatalog(catalog_path) if catalog_path else None
    
    def validate_cest_format(self, cest: str | None) -> CestValidationDetails:
        """Valida apenas o formato do CEST"""
        return CestFormatValidator.validate_format(cest)
    
    def validate_ncm_format(self, ncm: str | None) -> NcmValidationDetails:
        """Valida apenas o formato do NCM"""
        return NcmFormatValidator.validate_format(ncm)
    
    def validate_cest_binding(self, cest: str | None, ncm: str | None) -> CestValidationDetails:
        """
        Valida se o CEST é válido para o NCM fornecido
        
        Args:
            cest: Código CEST
            ncm: Código NCM
            
        Returns:
            Detalhes da validação incluindo sugestões
        """
        # Primeiro valida formatos
        cest_format = self.validate_cest_format(cest)
        if not cest_format.is_valid:
            return cest_format
        
        ncm_format = self.validate_ncm_format(ncm)
        if not ncm_format.is_valid:
            return CestValidationDetails(
                result=ValidationResult.INVALID_BINDING,
                error_message="NCM inválido para validação de binding CEST"
            )
        
        # Se não há catálogo, aceita formato válido
        if not self.catalog:
            return cest_format
        
        # Valida binding usando catálogo
        allowed_cests = self.catalog.get_allowed_cests_for_ncm(ncm_format.normalized_ncm)
        
        if cest_format.normalized_cest in allowed_cests:
            return CestValidationDetails(
                result=ValidationResult.VALID,
                normalized_cest=cest_format.normalized_cest
            )
        
        # CEST não é válido para este NCM - sugere alternativas
        hierarchy = NcmFormatValidator.get_hierarchy_info(ncm_format.normalized_ncm)
        chapter_cests = self.catalog.get_allowed_cests_for_chapter(hierarchy.get("chapter", ""))
        
        if cest_format.normalized_cest in chapter_cests:
            return CestValidationDetails(
                result=ValidationResult.VALID,
                normalized_cest=cest_format.normalized_cest
            )
        
        # CEST inválido - fornecer sugestões
        suggestions = self.catalog.suggest_alternative_cests(ncm_format.normalized_ncm, cest)
        
        return CestValidationDetails(
            result=ValidationResult.INVALID_BINDING,
            error_message=f"CEST {cest_format.normalized_cest} não é válido para NCM {ncm_format.normalized_ncm}",
            suggested_alternatives=suggestions
        )
    
    def validate_classification(self, ncm: str | None, cest: str | None) -> Tuple[NcmValidationDetails, CestValidationDetails]:
        """
        Valida uma classificação completa NCM + CEST
        
        Returns:
            Tupla com validações de NCM e CEST
        """
        ncm_validation = self.validate_ncm_format(ncm)
        
        if cest:
            cest_validation = self.validate_cest_binding(cest, ncm)
        else:
            # CEST pode ser None (produtos sem CEST)
            cest_validation = CestValidationDetails(
                result=ValidationResult.VALID,
                normalized_cest=None
            )
        
        return ncm_validation, cest_validation

# Funções de conveniência para backward compatibility
def normalize_cest(cest: str | None) -> Optional[str]:
    """Função de conveniência para normalização CEST"""
    return CestFormatValidator.normalize_cest(cest)

def normalize_ncm(ncm: str | None) -> Optional[str]:
    """Função de conveniência para normalização NCM"""
    return NcmFormatValidator.normalize_ncm(ncm)

def validate_cest_format(cest: str | None) -> bool:
    """Função de conveniência para validação de formato CEST"""
    return CestFormatValidator.validate_format(cest).is_valid

def ensure_cest_matches_ncm(cest: str | None, ncm: str | None, catalog_path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """
    Função de conveniência para validação de binding CEST-NCM
    
    Returns:
        Tupla (is_valid, normalized_cest)
    """
    validator = FiscalValidator(catalog_path)
    result = validator.validate_cest_binding(cest, ncm)
    return result.is_valid, result.normalized_cest
