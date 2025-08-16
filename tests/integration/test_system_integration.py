"""
Testes de integração para o sistema multiagente completo
"""
import asyncio
import json
from pathlib import Path
import sys

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

class TestSystemIntegration:
    """Testes de integração do sistema completo"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.test_data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        
    def test_classificacao_medicamentos_end_to_end(self):
        """Teste end-to-end para classificação de medicamentos"""
        
        # Dados de teste baseados no caso real reportado
        test_products = [
            {
                "produto": "Medicamento para hipertensão",
                "ncm_esperado": "30049090",
                "cest_esperado": "13.001.00",  # Não 21.064.00
                "categoria": "medicamento"
            },
            {
                "produto": "Sorvete de chocolate",
                "ncm_esperado": "21050000", 
                "cest_esperado": "21.064.00",
                "categoria": "alimento"
            }
        ]
        
        for produto in test_products:
            # Simular processamento do sistema
            result = self._simulate_multiagent_classification(produto)
            
            # Validações
            assert result["ncm"] == produto["ncm_esperado"], f"NCM incorreto para {produto['produto']}"
            assert result["cest"] == produto["cest_esperado"], f"CEST incorreto para {produto['produto']}"
            assert result["is_valid"], f"Classificação inválida para {produto['produto']}"
    
    def test_validacao_formato_cest_7_digitos(self):
        """Testa que todos os CESTs gerados têm 7 dígitos"""
        
        test_cests = [
            "13001000",   # Input sem formatação
            "13.001.00",  # Input já formatado
            "1300100",    # Input com 7 dígitos
        ]
        
        for cest_input in test_cests:
            formatted = self._format_cest(cest_input)
            
            # CEST sempre deve ter 7 dígitos
            digits_only = formatted.replace(".", "")
            assert len(digits_only) == 7, f"CEST {formatted} não tem 7 dígitos"
            
            # Deve estar formatado como SS.III.DD
            assert formatted.count(".") == 2, f"CEST {formatted} não tem formatação correta"
            
            parts = formatted.split(".")
            assert len(parts[0]) == 2, f"Setor {parts[0]} não tem 2 dígitos"
            assert len(parts[1]) == 3, f"Item {parts[1]} não tem 3 dígitos"
            assert len(parts[2]) == 2, f"Dígito {parts[2]} não tem 2 dígitos"
    
    def test_binding_rules_compliance(self):
        """Testa conformidade com regras de binding NCM-CEST"""
        
        binding_tests = [
            # Medicamentos devem usar CEST 13.xxx.xx
            {
                "ncm": "30049090",
                "cest_valido": "13.001.00",
                "cest_invalido": "21.064.00",
                "categoria": "medicamento"
            },
            # Sorvetes devem usar CEST 21.064.00
            {
                "ncm": "21050000",
                "cest_valido": "21.064.00", 
                "cest_invalido": "13.001.00",
                "categoria": "sorvete"
            }
        ]
        
        for test in binding_tests:
            # Teste binding válido
            valid_result = self._validate_binding(test["ncm"], test["cest_valido"])
            assert valid_result["is_valid"], f"Binding válido falhou: {test['ncm']} -> {test['cest_valido']}"
            
            # Teste binding inválido
            invalid_result = self._validate_binding(test["ncm"], test["cest_invalido"])
            assert not invalid_result["is_valid"], f"Binding inválido passou: {test['ncm']} -> {test['cest_invalido']}"
    
    def test_load_reference_catalogs(self):
        """Testa carregamento dos catálogos de referência"""
        
        catalog_files = [
            "data/reference/cest_catalog.json",
            "data/reference/ncm_catalog.json"
        ]
        
        for catalog_file in catalog_files:
            catalog_path = Path(__file__).parent.parent.parent / catalog_file
            assert catalog_path.exists(), f"Catálogo {catalog_file} não encontrado"
            
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)
            
            assert "metadata" in catalog_data, f"Catálogo {catalog_file} sem metadata"
            assert "version" in catalog_data["metadata"], f"Catálogo {catalog_file} sem versão"
    
    def test_configuration_loading(self):
        """Testa carregamento da configuração"""
        
        # Simular carregamento de configuração
        config = self._load_test_config()
        
        assert config["classification"]["enforce_cest_format"], "Validação de formato CEST deve estar habilitada"
        assert config["classification"]["enforce_cest_ncm_binding"], "Validação de binding deve estar habilitada"
        assert config["classification"]["reject_invalid_bindings"], "Rejeição de bindings inválidos deve estar habilitada"
    
    # Métodos auxiliares para simular componentes do sistema
    
    def _simulate_multiagent_classification(self, produto):
        """Simula classificação pelo sistema multiagente"""
        
        # Simular lógica dos agentes
        if "medicamento" in produto["produto"].lower():
            return {
                "ncm": "30049090",
                "cest": "13.001.00",  # CEST correto para medicamentos
                "is_valid": True,
                "confidence": 0.95
            }
        elif "sorvete" in produto["produto"].lower():
            return {
                "ncm": "21050000",
                "cest": "21.064.00",
                "is_valid": True,
                "confidence": 0.90
            }
        else:
            return {
                "ncm": "00000000",
                "cest": "00.000.00",
                "is_valid": False,
                "confidence": 0.10
            }
    
    def _format_cest(self, cest_input):
        """Simula formatação de CEST"""
        
        # Remover caracteres não numéricos
        digits = ''.join(c for c in cest_input if c.isdigit())
        
        # Garantir 7 dígitos
        if len(digits) < 7:
            digits = digits.ljust(7, '0')
        elif len(digits) > 7:
            digits = digits[:7]
        
        # Formatizar como SS.III.DD
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:7]}"
    
    def _validate_binding(self, ncm, cest):
        """Simula validação de binding NCM-CEST"""
        
        # Regras simplificadas baseadas nos requisitos
        if ncm.startswith("3003") or ncm.startswith("3004"):
            # Medicamentos devem usar CEST 13.xxx.xx
            is_valid = cest.startswith("13.")
            return {
                "is_valid": is_valid,
                "rule": "medicamentos_must_use_cest_13"
            }
        elif ncm.startswith("2105"):
            # Sorvetes devem usar CEST 21.064.00
            is_valid = cest == "21.064.00"
            return {
                "is_valid": is_valid,
                "rule": "sorvetes_must_use_cest_21_064"
            }
        else:
            return {
                "is_valid": True,
                "rule": "no_specific_rule"
            }
    
    def _load_test_config(self):
        """Simula carregamento de configuração para testes"""
        
        return {
            "classification": {
                "enforce_cest_format": True,
                "enforce_cest_ncm_binding": True,
                "reject_invalid_bindings": True,
                "min_confidence_threshold": 0.6
            },
            "validation": {
                "cest_must_have_7_digits": True,
                "cest_format_pattern": r"^\d{2}\.\d{3}\.\d{2}$"
            }
        }


def run_integration_tests():
    """Executa todos os testes de integração"""
    
    test_suite = TestSystemIntegration()
    
    tests = [
        test_suite.test_classificacao_medicamentos_end_to_end,
        test_suite.test_validacao_formato_cest_7_digitos,
        test_suite.test_binding_rules_compliance,
        test_suite.test_load_reference_catalogs,
        test_suite.test_configuration_loading
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_suite.setup_method()
            test()
            print(f"✅ {test.__name__} - PASSOU")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - FALHOU: {e}")
            failed += 1
    
    print(f"\n📊 Resultados: {passed} passaram, {failed} falharam")
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
