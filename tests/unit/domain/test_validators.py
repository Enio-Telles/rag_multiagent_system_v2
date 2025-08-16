"""
Testes unitários para os validadores do domínio fiscal
"""
import pytest
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys

# Adicionar src ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from domain.validators import (
    FiscalValidator,
    CestFormatValidator, 
    NcmFormatValidator,
    ValidationResult,
    CestValidationDetails,
    NcmValidationDetails
)

class TestCestFormatValidator:
    """Testes para validação de formato CEST"""
    
    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.validator = CestFormatValidator()
    
    def test_formato_cest_valido(self):
        """Testa formato CEST válido SS.III.DD"""
        valid_cests = [
            "13.001.00",
            "21.064.00", 
            "01.002.10",
            "99.999.99"
        ]
        
        for cest in valid_cests:
            result = self.validator.validate_format(cest)
            assert result.is_valid, f"CEST {cest} deveria ser válido"
            assert result.details.formatted_code == cest
            assert result.details.sector == cest[:2]
            assert result.details.item == cest[3:6]
            assert result.details.digit == cest[7:9]
    
    def test_formato_cest_invalido(self):
        """Testa formatos CEST inválidos"""
        invalid_cests = [
            "13001000",      # Sem pontos
            "13.001",        # Incompleto
            "13.001.0",      # Dígito incompleto
            "1.001.00",      # Setor com 1 dígito
            "13.01.00",      # Item com 2 dígitos
            "13.0001.00",    # Item com 4 dígitos
            "13.001.000",    # Dígito com 3 dígitos
            "AB.001.00",     # Letras no setor
            "13.ABC.00",     # Letras no item
            "13.001.AB",     # Letras no dígito
            "",              # Vazio
            "13-001-00",     # Hífens em vez de pontos
            "13.001.00.01"   # Muito longo
        ]
        
        for cest in invalid_cests:
            result = self.validator.validate_format(cest)
            assert not result.is_valid, f"CEST {cest} deveria ser inválido"
            assert len(result.details.errors) > 0
    
    def test_normalizacao_cest(self):
        """Testa normalização automática de CEST"""
        test_cases = [
            ("13001000", "13.001.00"),
            ("1300100", "13.001.00"),
            (" 13.001.00 ", "13.001.00"),
            ("13-001-00", "13.001.00"),
            ("13/001/00", "13.001.00")
        ]
        
        for input_cest, expected in test_cases:
            result = self.validator.normalize(input_cest)
            assert result == expected, f"Normalização de {input_cest} falhou"


class TestNcmFormatValidator:
    """Testes para validação de formato NCM"""
    
    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.validator = NcmFormatValidator()
    
    def test_formato_ncm_valido(self):
        """Testa formato NCM válido de 8 dígitos"""
        valid_ncms = [
            "30049090",
            "21050000",
            "12345678",
            "00000001"
        ]
        
        for ncm in valid_ncms:
            result = self.validator.validate_format(ncm)
            assert result.is_valid, f"NCM {ncm} deveria ser válido"
            assert result.details.formatted_code == ncm
            assert result.details.chapter == ncm[:2]
            assert result.details.heading == ncm[:4]
            assert result.details.subheading == ncm[:6]
    
    def test_formato_ncm_invalido(self):
        """Testa formatos NCM inválidos"""
        invalid_ncms = [
            "3004909",       # 7 dígitos
            "300490901",     # 9 dígitos
            "3004.90.90",    # Com pontos
            "ABCD1234",      # Com letras
            "",              # Vazio
            "30-04-90-90",   # Com hífens
            " 30049090 ",    # Com espaços (deve normalizar)
            "3004909A"       # Letra no final
        ]
        
        for ncm in invalid_ncms:
            result = self.validator.validate_format(ncm)
            if ncm.strip() == "30049090":  # Caso especial de normalização
                assert result.is_valid
            else:
                assert not result.is_valid, f"NCM {ncm} deveria ser inválido"
    
    def test_normalizacao_ncm(self):
        """Testa normalização automática de NCM"""
        test_cases = [
            ("3004.90.90", "30049090"),
            (" 30049090 ", "30049090"),
            ("3004-90-90", "30049090"),
            ("30/04/90/90", "30049090")
        ]
        
        for input_ncm, expected in test_cases:
            result = self.validator.normalize(input_ncm)
            assert result == expected, f"Normalização de {input_ncm} falhou"


class TestFiscalValidator:
    """Testes para validador fiscal principal"""
    
    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.validator = FiscalValidator()
    
    def test_binding_medicamentos_valido(self):
        """Testa binding válido NCM medicamentos com CEST 13.xxx.xx"""
        valid_bindings = [
            ("30049090", "13.001.00"),
            ("30041000", "13.004.00"),
            ("30043900", "13.007.00")
        ]
        
        for ncm, cest in valid_bindings:
            result = self.validator.validate_binding(ncm, cest)
            assert result.is_valid, f"Binding {ncm}-{cest} deveria ser válido"
    
    def test_binding_medicamentos_invalido(self):
        """Testa binding inválido NCM medicamentos com CEST incorreto"""
        invalid_bindings = [
            ("30049090", "21.064.00"),  # Medicamento com CEST de sorvete
            ("30041000", "01.001.00"),  # Medicamento com CEST de autopeça
            ("30043900", "99.999.99")   # CEST inexistente
        ]
        
        for ncm, cest in invalid_bindings:
            result = self.validator.validate_binding(ncm, cest)
            assert not result.is_valid, f"Binding {ncm}-{cest} deveria ser inválido"
            assert "medicamento" in " ".join(result.details.errors).lower()
    
    def test_binding_sorvetes_valido(self):
        """Testa binding válido NCM sorvetes com CEST 21.064.00"""
        result = self.validator.validate_binding("21050000", "21.064.00")
        assert result.is_valid, "Binding sorvete deveria ser válido"
    
    def test_validacao_completa_produto_medicamento(self):
        """Testa validação completa de produto medicamento"""
        result = self.validator.validate_product_classification(
            ncm="30049090",
            cest="13.001.00",
            product_description="Medicamento para hipertensão"
        )
        
        assert result.is_valid, "Produto medicamento deveria ser válido"
        assert result.confidence_score > 0.8
    
    def test_validacao_completa_produto_erro_binding(self):
        """Testa validação completa com erro de binding"""
        result = self.validator.validate_product_classification(
            ncm="30049090",
            cest="21.064.00",  # CEST incorreto para medicamento
            product_description="Medicamento para diabetes"
        )
        
        assert not result.is_valid, "Produto com binding incorreto deveria ser inválido"
        assert result.confidence_score < 0.5
        assert any("binding" in error.lower() for error in result.details.errors)


class TestValidationIntegration:
    """Testes de integração dos validadores"""
    
    def test_casos_reais_medicamentos(self):
        """Testa casos reais de medicamentos reportados"""
        validator = FiscalValidator()
        
        # Caso real: NCM 30049090 estava sendo classificado como 21.064.00
        result = validator.validate_product_classification(
            ncm="30049090",
            cest="21.064.00",  # Erro real encontrado
            product_description="Medicamento genérico"
        )
        
        assert not result.is_valid, "Erro de binding deveria ser detectado"
        
        # Correção: NCM 30049090 deve usar CEST 13.xxx.xx
        result_corrected = validator.validate_product_classification(
            ncm="30049090", 
            cest="13.001.00",  # CEST correto
            product_description="Medicamento genérico"
        )
        
        assert result_corrected.is_valid, "Binding correto deveria ser válido"
    
    def test_normalizacao_formato_cest_7_digitos(self):
        """Testa que CEST sempre tem 7 dígitos conforme reportado"""
        validator = FiscalValidator()
        
        test_cases = [
            "13001000",  # Sem pontos
            "1300100",   # 7 dígitos sem pontos
            "13.001.0",  # Incompleto
        ]
        
        for cest_input in test_cases:
            if len(cest_input.replace(".", "")) == 7:
                normalized = validator.cest_validator.normalize(cest_input)
                assert len(normalized.replace(".", "")) == 7, f"CEST {cest_input} não tem 7 dígitos após normalização"
                assert "." in normalized, f"CEST {cest_input} não foi formatado com pontos"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
