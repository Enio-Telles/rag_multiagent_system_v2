"""
Serviço de Explicações dos Agentes - Versão Simplificada
Gerencia explicações detalhadas dos agentes para rastreabilidade
"""

from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database.models import ExplicacaoAgente, ClassificacaoRevisao, GoldenSetEntry
from database.connection import get_db

logger = logging.getLogger(__name__)

def clean_circular_references(obj, max_depth=5, current_depth=0):
    """
    Remove referências circulares de objetos Python para serialização JSON
    """
    if current_depth > max_depth:
        return f"<MAX_DEPTH_REACHED_{max_depth}>"
    
    if obj is None:
        return None
    
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            try:
                if isinstance(v, (dict, list)):
                    cleaned[k] = clean_circular_references(v, max_depth, current_depth + 1)
                else:
                    cleaned[k] = v
            except:
                cleaned[k] = f"<SERIALIZATION_ERROR>"
        return cleaned
    
    if isinstance(obj, list):
        cleaned = []
        for item in obj:
            try:
                cleaned.append(clean_circular_references(item, max_depth, current_depth + 1))
            except:
                cleaned.append(f"<SERIALIZATION_ERROR>")
        return cleaned
    
    # Para outros tipos, tentar converter para string
    try:
        return str(obj)
    except:
        return f"<OBJECT_TYPE_{type(obj).__name__}>"

class ExplicacaoService:
    """Serviço para gerenciar explicações dos agentes"""
    
    def salvar_explicacao_agente(self, produto_id: int, explicacao_data: Dict[str, Any], 
                                 classificacao_id: Optional[int] = None, 
                                 sessao_classificacao: Optional[str] = None) -> bool:
        """
        Método alternativo para compatibilidade com HybridRouter
        """
        if sessao_classificacao:
            explicacao_data = explicacao_data.copy()
            explicacao_data['sessao_classificacao'] = sessao_classificacao
        return self.salvar_explicacao(produto_id, classificacao_id, explicacao_data)
    
    def salvar_explicacao(self, produto_id: int, classificacao_id: Optional[int], explicacao_data: Dict[str, Any]) -> bool:
        """
        Salva explicação detalhada de um agente
        
        Args:
            produto_id: ID do produto
            classificacao_id: ID da classificação (opcional)
            explicacao_data: Dados da explicação do agente
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            db = next(get_db())
            
            # Limpar referências circulares dos campos JSON
            contexto_utilizado = clean_circular_references(explicacao_data.get("contexto_utilizado"))
            etapas_processamento = clean_circular_references(explicacao_data.get("etapas_processamento"))
            resultado_agente = clean_circular_references(explicacao_data.get("resultado_agente"))
            
            explicacao = ExplicacaoAgente(
                produto_id=produto_id,
                classificacao_id=classificacao_id,
                agente_nome=explicacao_data.get("agente_nome"),
                agente_versao=explicacao_data.get("agente_versao", "1.0"),
                input_original=str(explicacao_data.get("input_original", ""))[:1000],  # Limitar tamanho
                contexto_utilizado=contexto_utilizado,
                etapas_processamento=etapas_processamento,
                resultado_agente=resultado_agente,
                explicacao_detalhada=str(explicacao_data.get("explicacao_detalhada", ""))[:5000],  # Limitar tamanho
                justificativa_tecnica=str(explicacao_data.get("justificativa_tecnica", ""))[:2000],
                nivel_confianca=explicacao_data.get("nivel_confianca"),
                tempo_processamento_ms=explicacao_data.get("tempo_processamento_ms"),
                tokens_llm_utilizados=explicacao_data.get("tokens_utilizados"),
                memoria_utilizada_mb=explicacao_data.get("memoria_utilizada_mb"),
                rag_consultado=explicacao_data.get("rag_consultado", False),
                golden_set_utilizado=explicacao_data.get("golden_set_utilizado", False),
                base_ncm_consultada=explicacao_data.get("base_ncm_consultada", False)
            )
            
            db.add(explicacao)
            db.commit()
            
            logger.info(f"✅ Explicação salva para produto {produto_id}, agente {explicacao_data.get('agente_nome')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar explicação: {e}")
            if 'db' in locals():
                db.rollback()
            return False
    
    def obter_explicacoes_produto(self, produto_id: int) -> Dict[str, Any]:
        """
        Obtém todas as explicações de um produto
        
        Args:
            produto_id: ID do produto
            
        Returns:
            Dict com explicações organizadas por agente
        """
        try:
            db = next(get_db())
            
            explicacoes = db.query(ExplicacaoAgente).filter(
                ExplicacaoAgente.produto_id == produto_id
            ).order_by(ExplicacaoAgente.data_execucao.desc()).all()
            
            resultado = {
                "produto_id": produto_id,
                "total_explicacoes": len(explicacoes),
                "explicacoes_por_agente": {}
            }
            
            for exp in explicacoes:
                agente = exp.agente_nome
                if agente not in resultado["explicacoes_por_agente"]:
                    resultado["explicacoes_por_agente"][agente] = []
                
                resultado["explicacoes_por_agente"][agente].append({
                    "id": exp.id,
                    "versao": exp.agente_versao,
                    "input": exp.input_original,
                    "output": exp.resultado_agente,
                    "explicacao": exp.explicacao_detalhada,
                    "confianca": exp.nivel_confianca,
                    "tempo_ms": exp.tempo_processamento_ms,
                    "tokens": exp.tokens_llm_utilizados,
                    "memoria_mb": exp.memoria_utilizada_mb,
                    "timestamp": exp.data_execucao.isoformat() if exp.data_execucao else None,
                    "justificativa": exp.justificativa_tecnica
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter explicações: {e}")
            return {"erro": str(e)}
    
    def gerar_relatorio_agente(self, agente_nome: str, periodo_dias: int = 30) -> Dict[str, Any]:
        """
        Gera relatório de performance de um agente
        
        Args:
            agente_nome: Nome do agente
            periodo_dias: Período em dias para análise
            
        Returns:
            Dict com estatísticas do agente
        """
        try:
            db = next(get_db())
            
            data_inicio = datetime.now() - timedelta(days=periodo_dias)
            
            # Buscar explicações do período
            explicacoes = db.query(ExplicacaoAgente).filter(
                and_(
                    ExplicacaoAgente.agente_nome == agente_nome,
                    ExplicacaoAgente.data_execucao >= data_inicio
                )
            ).all()
            
            if not explicacoes:
                return {
                    "agente": agente_nome,
                    "periodo_dias": periodo_dias,
                    "total_execucoes": 0,
                    "message": "Nenhuma execução encontrada no período"
                }
            
            # Calcular estatísticas
            total_execucoes = len(explicacoes)
            tempo_total = sum(exp.tempo_processamento_ms or 0 for exp in explicacoes)
            tempo_medio = tempo_total / total_execucoes if total_execucoes > 0 else 0
            
            memoria_total = sum(exp.memoria_utilizada_mb or 0 for exp in explicacoes)
            memoria_media = memoria_total / total_execucoes if total_execucoes > 0 else 0
            
            tokens_total = sum(exp.tokens_llm_utilizados or 0 for exp in explicacoes)
            
            confiancas = [exp.nivel_confianca for exp in explicacoes if exp.nivel_confianca is not None]
            confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0
            
            return {
                "agente": agente_nome,
                "periodo_dias": periodo_dias,
                "total_execucoes": total_execucoes,
                "tempo_medio_ms": round(tempo_medio, 2),
                "memoria_media_mb": round(memoria_media, 2),
                "tokens_total": tokens_total,
                "confianca_media": round(confianca_media, 2),
                "uso_rag_percent": 0,  # Simplificado por enquanto
                "uso_golden_set_percent": 0,  # Simplificado por enquanto
                "data_relatorio": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return {"erro": str(e)}
    
    def atualizar_golden_set_com_explicacoes(self, golden_set_id: int, explicacoes: Dict[str, str]) -> bool:
        """
        Atualiza entrada do Golden Set com explicações dos agentes
        
        Args:
            golden_set_id: ID da entrada no Golden Set
            explicacoes: Dict com explicações por agente
            
        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            db = next(get_db())
            
            entrada = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.id == golden_set_id
            ).first()
            
            if not entrada:
                logger.warning(f"⚠️ Entrada {golden_set_id} não encontrada no Golden Set")
                return False
            
            # Atualizar explicações
            if "expansion" in explicacoes:
                entrada.explicacao_expansao = explicacoes["expansion"]
            if "aggregation" in explicacoes:
                entrada.explicacao_agregacao = explicacoes["aggregation"]
            if "ncm" in explicacoes:
                entrada.explicacao_ncm = explicacoes["ncm"]
            if "cest" in explicacoes:
                entrada.explicacao_cest = explicacoes["cest"]
            if "reconciler" in explicacoes:
                entrada.explicacao_reconciliacao = explicacoes["reconciler"]
            
            db.commit()
            
            logger.info(f"✅ Golden Set {golden_set_id} atualizado com explicações")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar Golden Set: {e}")
            if 'db' in locals():
                db.rollback()
            return False
