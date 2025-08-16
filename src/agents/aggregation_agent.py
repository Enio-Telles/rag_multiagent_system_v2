# ============================================================================
# src/agents/aggregation_agent.py - Agente de Detecção de Duplicatas  
# ============================================================================

from typing import List, Dict, Any
from .base_agent import BaseAgent
import sys
import logging
from pathlib import Path

# Adicionar domain ao path para importar validators
sys.path.append(str(Path(__file__).parent.parent))

try:
    from domain.product_deduplication import ProductDeduplicationValidator, validate_product_deduplication
except ImportError:
    # Fallback se deduplication validator não estiver disponível
    class ProductDeduplicationValidator:
        def group_identical_products(self, produtos):
            return [[i] for i in range(len(produtos))]
        def products_are_identical(self, p1, p2):
            return False, "Fallback: não disponível", 0.0
        def suggest_canonical_description(self, descriptions):
            return descriptions[0] if descriptions else ""
    
    def validate_product_deduplication(produtos):
        return {"total_products": len(produtos), "unique_products": len(produtos), "duplicates_found": 0}

class AggregationAgent(BaseAgent):
    """
    Agente responsável por identificar produtos idênticos com descrições diferentes.
    
    OBJETIVO PRINCIPAL:
    - Detectar duplicatas: produtos IGUAIS com descrições variadas
    - Exemplo: "barbeador prestobarba 2 unidades" = "barbead prestob 2 unid"
    - NÃO agrupa: aparelhos de marcas diferentes, quantidades diferentes
    
    CRITÉRIOS DE IDENTIDADE:
    - Mesmo tipo de produto (ex: aparelho barbear)
    - Mesma marca (ex: Gillette = Gilete = Gil)  
    - Mesma variante (ex: Presto = Prestob = Presto Barba)
    - Mesma quantidade (ex: 2 unidades = 2 unid = 2x)
    - Mesmo tamanho/especificação
    """
    
    def __init__(self, llm_client, config):
        super().__init__("AggregationAgent", llm_client, config)
        self.deduplication_validator = ProductDeduplicationValidator()
        
        # Configurações de detecção de duplicatas - usar getattr para Config object
        self.min_confidence = getattr(config, "min_deduplication_confidence", 0.7)
        self.enable_deduplication = getattr(config, "enable_product_deduplication", True)
        self.strict_matching = getattr(config, "strict_duplicate_matching", True)
        
        # Configurar logger se não existir
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.setLevel(logging.INFO)
    
    def run(self, produtos_expandidos: List[Dict], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Identifica produtos idênticos com descrições diferentes (detecção de duplicatas)
        
        Args:
            produtos_expandidos: Lista de produtos para análise de duplicatas
            context: Contexto adicional
            
        Returns:
            Dict com grupos de produtos, sendo cada grupo produtos idênticos
        """
        if not produtos_expandidos:
            return {"grupos": [], "estatisticas": {"total_produtos": 0}}
        
        self.logger.info(f"Iniciando detecção de duplicatas para {len(produtos_expandidos)} produtos")
        
        try:
            if self.enable_deduplication:
                # Usar validator dedicado para detecção de duplicatas
                grupos_indices = self.deduplication_validator.group_identical_products(produtos_expandidos)
                
                # Converter para formato esperado com análise detalhada
                grupos_finais = []
                for i, grupo_indices in enumerate(grupos_indices):
                    produtos_grupo = [produtos_expandidos[idx] for idx in grupo_indices]
                    
                    if len(produtos_grupo) > 1:
                        # Grupo com duplicatas detectadas
                        analysis = self._analyze_duplicate_group(produtos_grupo, grupo_indices)
                        
                        # Aplicar filtro de confiança
                        if analysis["confidence"] >= self.min_confidence:
                            grupos_finais.append({
                                "id": i,
                                "produtos": produtos_grupo,
                                "indices_originais": grupo_indices,
                                "tipo": "duplicatas_detectadas",
                                "representante": self._select_representative(produtos_grupo),
                                "confidence": analysis["confidence"],
                                "duplicate_analysis": analysis
                            })
                        else:
                            # Confiança baixa - separar em produtos únicos
                            for j, produto in enumerate(produtos_grupo):
                                grupos_finais.append({
                                    "id": f"{i}_{j}",
                                    "produtos": [produto],
                                    "indices_originais": [grupo_indices[j]],
                                    "tipo": "produto_unico_baixa_confianca",
                                    "representante": produto,
                                    "confidence": 1.0,
                                    "motivo_separacao": f"Confiança {analysis['confidence']:.2f} < {self.min_confidence}"
                                })
                    else:
                        # Produto único
                        grupos_finais.append({
                            "id": i,
                            "produtos": produtos_grupo,
                            "indices_originais": grupo_indices,
                            "tipo": "produto_unico",
                            "representante": produtos_grupo[0] if produtos_grupo else None,
                            "confidence": 1.0
                        })
                
                # Estatísticas de duplicação
                estatisticas = validate_product_deduplication(produtos_expandidos)
                grupos_com_duplicatas = len([g for g in grupos_finais if g["tipo"] == "duplicatas_detectadas"])
                produtos_unicos = len([g for g in grupos_finais if g["tipo"] in ["produto_unico", "produto_unico_baixa_confianca"]])
                
                estatisticas.update({
                    "total_grupos": len(grupos_finais),
                    "grupos_com_duplicatas": grupos_com_duplicatas,
                    "produtos_unicos": produtos_unicos,
                    "taxa_duplicacao": grupos_com_duplicatas / len(grupos_finais) if grupos_finais else 0
                })
                
            else:
                # Fallback: cada produto é um grupo único
                grupos_finais = []
                for i, produto in enumerate(produtos_expandidos):
                    grupos_finais.append({
                        "id": i,
                        "produtos": [produto],
                        "indices_originais": [i],
                        "tipo": "produto_unico",
                        "representante": produto,
                        "confidence": 1.0
                    })
                
                estatisticas = {
                    "total_produtos": len(produtos_expandidos),
                    "total_grupos": len(grupos_finais),
                    "duplicates_found": 0,
                    "unique_products": len(produtos_expandidos)
                }
            
            self.logger.info(f"Detecção concluída: {estatisticas.get('duplicates_found', 0)} grupos com duplicatas encontrados")
            
            return {
                "grupos": grupos_finais,
                "estatisticas": estatisticas,
                "metodos_utilizados": ["product_deduplication_validator"] if self.enable_deduplication else ["fallback"],
                "configuracao": {
                    "min_confidence": self.min_confidence,
                    "strict_matching": self.strict_matching,
                    "enable_deduplication": self.enable_deduplication
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de duplicatas: {e}")
            # Fallback em caso de erro  
            grupos_fallback = []
            for i, produto in enumerate(produtos_expandidos):
                grupos_fallback.append({
                    "id": i,
                    "produtos": [produto],
                    "indices_originais": [i],
                    "tipo": "fallback_erro",
                    "representante": produto,
                    "confidence": 0.5,
                    "erro": str(e)
                })
            
            return {
                "grupos": grupos_fallback,
                "estatisticas": {"total_produtos": len(produtos_expandidos), "erro": str(e)},
                "metodos_utilizados": ["fallback_erro"]
            }
    
    def _analyze_duplicate_group(self, produtos: List[Dict], indices: List[int]) -> Dict[str, Any]:
        """Analisa um grupo de produtos idênticos para validar duplicação"""
        descriptions = [p.get("descricao_produto", "") for p in produtos]
        
        # Calcular confiança média entre todos os pares
        confidences = []
        reasons = []
        
        for i in range(len(produtos)):
            for j in range(i + 1, len(produtos)):
                identical, reason, confidence = self.deduplication_validator.products_are_identical(
                    produtos[i], produtos[j]
                )
                confidences.append(confidence)
                reasons.append(reason)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Sugerir descrição canônica
        canonical = self.deduplication_validator.suggest_canonical_description(descriptions)
        
        return {
            "confidence": avg_confidence,
            "descriptions": descriptions,
            "canonical_description": canonical,
            "similarity_reasons": reasons,
            "duplicate_count": len(produtos) - 1,
            "indices": indices
        }
    
    def _select_representative(self, produtos: List[Dict]) -> Dict[str, Any]:
        """Seleciona produto representante de um grupo de duplicatas"""
        if not produtos:
            return None
        
        if len(produtos) == 1:
            return produtos[0]
        
        # Priorizar descrição mais completa (mais palavras)
        best_product = max(produtos, key=lambda p: len(p.get("descricao_produto", "").split()))
        
        # Adicionar metadados de representação
        best_product = best_product.copy()
        best_product["_is_representative"] = True
        best_product["_represents_products"] = len(produtos)
        best_product["_duplicate_descriptions"] = [p.get("descricao_produto", "") for p in produtos]
        
        return best_product
    
    def get_duplicate_summary(self, resultado_agrupamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resumo dos grupos de duplicatas encontrados
        
        Args:
            resultado_agrupamento: Resultado do método run()
            
        Returns:
            Resumo das duplicatas encontradas
        """
        grupos = resultado_agrupamento.get("grupos", [])
        estatisticas = resultado_agrupamento.get("estatisticas", {})
        
        # Extrair grupos com duplicatas
        grupos_duplicatas = [g for g in grupos if g.get("tipo") == "duplicatas_detectadas"]
        
        # Análise detalhada
        duplicate_details = []
        total_duplicates_eliminated = 0
        
        for grupo in grupos_duplicatas:
            analysis = grupo.get("duplicate_analysis", {})
            duplicate_count = analysis.get("duplicate_count", 0)
            total_duplicates_eliminated += duplicate_count
            
            duplicate_details.append({
                "grupo_id": grupo["id"],
                "produto_representante": grupo["representante"].get("descricao_produto", ""),
                "descricoes_duplicatas": analysis.get("descriptions", []),
                "descricao_canonica": analysis.get("canonical_description", ""),
                "confianca": analysis.get("confidence", 0.0),
                "duplicatas_eliminadas": duplicate_count
            })
        
        return {
            "total_produtos_processados": estatisticas.get("total_produtos", 0),
            "grupos_formados": len(grupos),
            "grupos_com_duplicatas": len(grupos_duplicatas),
            "total_duplicatas_eliminadas": total_duplicates_eliminated,
            "taxa_duplicacao": len(grupos_duplicatas) / len(grupos) if grupos else 0,
            "economia_percentual": (total_duplicates_eliminated / estatisticas.get("total_produtos", 1)) * 100,
            "detalhes_duplicatas": duplicate_details,
            "produtos_unicos": len([g for g in grupos if g.get("tipo") in ["produto_unico", "produto_unico_baixa_confianca"]])
        }


# Exemplo de uso e teste
if __name__ == "__main__":
    import json
    
    # Dados de teste com produtos duplicados
    produtos_teste = [
        {
            "descricao_produto": "APAR BARBEAR PRESTO MASCULI GILLETTE",
            "ncm": "82121000",
            "cest": "21.064.00"
        },
        {
            "descricao_produto": "APARELHO BARBEAR PRESTOB MASCULINO GILETE", 
            "ncm": "82121000",
            "cest": "21.064.00"
        },
        {
            "descricao_produto": "BARBEAD PRESTOB 2 UNID",
            "ncm": "82121000", 
            "cest": "21.064.00"
        },
        {
            "descricao_produto": "BARBEADOR PRESTOBARBA 2 UNIDADES",
            "ncm": "82121000",
            "cest": "21.064.00"
        },
        {
            "descricao_produto": "COPO PLASTICO 200ML",
            "ncm": "39241000",
            "cest": "21.065.00"
        }
    ]
    
    print("=== TESTE DO AGGREGATION AGENT (DETECÇÃO DE DUPLICATAS) ===")
    
    # Simular config e llm_client
    config = {
        "enable_product_deduplication": True,
        "min_deduplication_confidence": 0.7,
        "strict_duplicate_matching": True
    }
    
    agent = AggregationAgent(llm_client=None, config=config)
    
    # Executar detecção
    resultado = agent.run(produtos_teste)
    
    # Mostrar resultado
    print(f"\nTotal de produtos: {len(produtos_teste)}")
    print(f"Grupos formados: {len(resultado['grupos'])}")
    print(f"Duplicatas encontradas: {resultado['estatisticas'].get('duplicates_found', 0)}")
    
    print("\n--- GRUPOS IDENTIFICADOS ---")
    for grupo in resultado["grupos"]:
        print(f"\nGrupo {grupo['id']} ({grupo['tipo']}):")
        print(f"  Confiança: {grupo['confidence']:.2f}")
        for produto in grupo["produtos"]:
            print(f"  - {produto['descricao_produto']}")
        
        if grupo.get("duplicate_analysis"):
            canonical = grupo["duplicate_analysis"].get("canonical_description", "")
            print(f"  → Descrição canônica sugerida: {canonical}")
    
    # Resumo de duplicatas
    resumo = agent.get_duplicate_summary(resultado)
    print(f"\n--- RESUMO DE DUPLICATAS ---")
    print(f"Duplicatas eliminadas: {resumo['total_duplicatas_eliminadas']}")
    print(f"Economia: {resumo['economia_percentual']:.1f}%")
    print(f"Taxa de duplicação: {resumo['taxa_duplicacao']:.2f}")
