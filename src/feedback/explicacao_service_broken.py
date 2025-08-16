# ============================================================================
# src/feedback/explicacao_service.py - Serviço de Gerenciamento de Explicações
# ============================================================================

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import ExplicacaoAgente, ClassificacaoRevisao, GoldenSetEntry
from database.connection import get_db

logger = logging.getLogger(__name__)

class ExplicacaoService:
    """
    Serviço responsável por gerenciar e armazenar explicações detalhadas dos agentes.
    Facilita a análise de performance e melhoria contínua do sistema.
    """
    
    def __init__(self):
        self.db_session = None
    
    def salvar_explicacao_agente(self, produto_id: int, explicacao_data: Dict[str, Any], 
                               classificacao_id: Optional[int] = None, 
                               sessao_classificacao: Optional[str] = None) -> bool:
        """
        Salva a explicação detalhada de um agente no banco de dados.
        
        Args:
            produto_id: ID do produto classificado
            explicacao_data: Dados da explicação do agente
            classificacao_id: ID da classificação (opcional)
            sessao_classificacao: ID da sessão de classificação
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            db = next(get_db())
            explicacao = ExplicacaoAgente(
                produto_id=produto_id,
                classificacao_id=classificacao_id,
                agente_nome=explicacao_data.get("agente_nome"),
                agente_versao=explicacao_data.get("agente_versao", "1.0"),
                input_original=explicacao_data.get("input_original"),
                contexto_utilizado=explicacao_data.get("contexto_utilizado"),
                etapas_processamento=explicacao_data.get("etapas_processamento"),
                palavras_chave_identificadas=explicacao_data.get("palavras_chave_identificadas"),
                produtos_similares_encontrados=explicacao_data.get("produtos_similares_encontrados"),
                resultado_agente=explicacao_data.get("resultado_agente"),
                explicacao_detalhada=explicacao_data.get("explicacao_detalhada"),
                justificativa_tecnica=explicacao_data.get("justificativa_tecnica"),
                nivel_confianca=explicacao_data.get("nivel_confianca", 0.0),
                rag_consultado=explicacao_data.get("rag_consultado", False),
                golden_set_utilizado=explicacao_data.get("golden_set_utilizado", False),
                base_ncm_consultada=explicacao_data.get("base_ncm_consultada", False),
                exemplos_utilizados=explicacao_data.get("exemplos_utilizados"),
                tempo_processamento_ms=explicacao_data.get("tempo_processamento_ms"),
                    memoria_utilizada_mb=explicacao_data.get("memoria_utilizada_mb"),
                    tokens_llm_utilizados=explicacao_data.get("tokens_llm_utilizados"),
                    sessao_classificacao=sessao_classificacao
                )
                
                db.add(explicacao)
                db.commit()
                
                logger.info(f"Explicação do agente {explicacao_data.get('agente_nome')} salva para produto {produto_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar explicação do agente: {str(e)}")
            return False
    
    def obter_explicacoes_produto(self, produto_id: int) -> List[Dict[str, Any]]:
        """
        Obtém todas as explicações de agentes para um produto específico.
        
        Args:
            produto_id: ID do produto
            
        Returns:
            List[Dict]: Lista de explicações dos agentes
        """
        try:
            db = next(get_db())
        try:
                explicacoes = db.query(ExplicacaoAgente).filter(
                    ExplicacaoAgente.produto_id == produto_id
                ).order_by(ExplicacaoAgente.data_execucao.desc()).all()
                
                resultado = []
                for exp in explicacoes:
                    resultado.append({
                        "id": exp.id,
                        "agente_nome": exp.agente_nome,
                        "agente_versao": exp.agente_versao,
                        "explicacao_detalhada": exp.explicacao_detalhada,
                        "justificativa_tecnica": exp.justificativa_tecnica,
                        "nivel_confianca": exp.nivel_confianca,
                        "palavras_chave": exp.palavras_chave_identificadas,
                        "etapas_processamento": exp.etapas_processamento,
                        "produtos_similares": exp.produtos_similares_encontrados,
                        "exemplos_utilizados": exp.exemplos_utilizados,
                        "tempo_processamento_ms": exp.tempo_processamento_ms,
                        "memoria_utilizada_mb": exp.memoria_utilizada_mb,
                        "tokens_utilizados": exp.tokens_llm_utilizados,
                        "rag_consultado": exp.rag_consultado,
                        "golden_set_utilizado": exp.golden_set_utilizado,
                        "base_ncm_consultada": exp.base_ncm_consultada,
                        "data_execucao": exp.data_execucao.isoformat() if exp.data_execucao else None
                    })
                
                return resultado
                
        except Exception as e:
            logger.error(f"Erro ao obter explicações do produto {produto_id}: {str(e)}")
            return []
    
    def obter_explicacao_por_agente(self, produto_id: int, agente_nome: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a explicação mais recente de um agente específico para um produto.
        
        Args:
            produto_id: ID do produto
            agente_nome: Nome do agente (expansion, ncm, cest, etc.)
            
        Returns:
            Dict ou None: Dados da explicação ou None se não encontrada
        """
        try:
            db = next(get_db())
        try:
                explicacao = db.query(ExplicacaoAgente).filter(
                    ExplicacaoAgente.produto_id == produto_id,
                    ExplicacaoAgente.agente_nome == agente_nome
                ).order_by(ExplicacaoAgente.data_execucao.desc()).first()
                
                if not explicacao:
                    return None
                
                return {
                    "agente_nome": explicacao.agente_nome,
                    "explicacao_detalhada": explicacao.explicacao_detalhada,
                    "justificativa_tecnica": explicacao.justificativa_tecnica,
                    "nivel_confianca": explicacao.nivel_confianca,
                    "palavras_chave": explicacao.palavras_chave_identificadas,
                    "etapas_processamento": explicacao.etapas_processamento,
                    "produtos_similares": explicacao.produtos_similares_encontrados,
                    "exemplos_utilizados": explicacao.exemplos_utilizados,
                    "tempo_processamento_ms": explicacao.tempo_processamento_ms,
                    "tokens_utilizados": explicacao.tokens_llm_utilizados,
                    "rag_consultado": explicacao.rag_consultado,
                    "golden_set_utilizado": explicacao.golden_set_utilizado,
                    "data_execucao": explicacao.data_execucao.isoformat() if explicacao.data_execucao else None
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter explicação do agente {agente_nome} para produto {produto_id}: {str(e)}")
            return None
    
    def atualizar_golden_set_com_explicacoes(self, produto_id: int, golden_set_id: int) -> bool:
        """
        Atualiza uma entrada do Golden Set com as explicações dos agentes.
        
        Args:
            produto_id: ID do produto
            golden_set_id: ID da entrada no Golden Set
            
        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            db = next(get_db())
        try:
                # Buscar entrada do Golden Set
                golden_entry = db.query(GoldenSetEntry).filter(
                    GoldenSetEntry.id == golden_set_id
                ).first()
                
                if not golden_entry:
                    logger.warning(f"Entrada do Golden Set {golden_set_id} não encontrada")
                    return False
                
                # Buscar explicações dos agentes
                explicacoes = self.obter_explicacoes_produto(produto_id)
                
                # Atualizar campos de explicação no Golden Set
                for exp in explicacoes:
                    agente = exp["agente_nome"]
                    explicacao = exp["explicacao_detalhada"]
                    
                    if agente == "expansion":
                        golden_entry.explicacao_expansao = explicacao
                    elif agente == "aggregation":
                        golden_entry.explicacao_agregacao = explicacao
                    elif agente == "ncm":
                        golden_entry.explicacao_ncm = explicacao
                    elif agente == "cest":
                        golden_entry.explicacao_cest = explicacao
                    elif agente == "reconciler":
                        golden_entry.explicacao_reconciliacao = explicacao
                    
                    # Extrair palavras-chave e características
                    if exp["palavras_chave"]:
                        if golden_entry.palavras_chave_fiscais:
                            golden_entry.palavras_chave_fiscais += f", {exp['palavras_chave']}"
                        else:
                            golden_entry.palavras_chave_fiscais = exp["palavras_chave"]
                
                db.commit()
                logger.info(f"Golden Set {golden_set_id} atualizado com explicações dos agentes")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar Golden Set com explicações: {str(e)}")
            return False
    
    def gerar_relatorio_agente(self, agente_nome: str, periodo_dias: int = 30) -> Dict[str, Any]:
        """
        Gera relatório de performance de um agente específico.
        
        Args:
            agente_nome: Nome do agente
            periodo_dias: Período em dias para análise
            
        Returns:
            Dict: Relatório de performance
        """
        try:
            db = next(get_db())
        try:
                # Buscar explicações do período
                from datetime import timedelta
                data_inicio = datetime.now() - timedelta(days=periodo_dias)
                
                explicacoes = db.query(ExplicacaoAgente).filter(
                    ExplicacaoAgente.agente_nome == agente_nome,
                    ExplicacaoAgente.data_execucao >= data_inicio
                ).all()
                
                if not explicacoes:
                    return {"erro": f"Nenhuma explicação encontrada para {agente_nome} nos últimos {periodo_dias} dias"}
                
                # Calcular métricas
                total_execucoes = len(explicacoes)
                tempo_medio = sum(exp.tempo_processamento_ms or 0 for exp in explicacoes) / total_execucoes
                memoria_media = sum(exp.memoria_utilizada_mb or 0 for exp in explicacoes) / total_execucoes
                tokens_total = sum(exp.tokens_llm_utilizados or 0 for exp in explicacoes)
                confianca_media = sum(exp.nivel_confianca or 0 for exp in explicacoes) / total_execucoes
                
                rag_usado = sum(1 for exp in explicacoes if exp.rag_consultado)
                golden_set_usado = sum(1 for exp in explicacoes if exp.golden_set_utilizado)
                
                return {
                    "agente_nome": agente_nome,
                    "periodo_dias": periodo_dias,
                    "total_execucoes": total_execucoes,
                    "tempo_medio_ms": round(tempo_medio, 2),
                    "memoria_media_mb": round(memoria_media, 2),
                    "tokens_total": tokens_total,
                    "confianca_media": round(confianca_media, 3),
                    "uso_rag_percent": round((rag_usado / total_execucoes) * 100, 1),
                    "uso_golden_set_percent": round((golden_set_usado / total_execucoes) * 100, 1),
                    "data_relatorio": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatório do agente {agente_nome}: {str(e)}")
            return {"erro": str(e)}
    
    def limpar_explicacoes_antigas(self, dias_manter: int = 90) -> int:
        """
        Remove explicações antigas para otimizar o banco de dados.
        
        Args:
            dias_manter: Número de dias de explicações para manter
            
        Returns:
            int: Número de registros removidos
        """
        try:
            db = next(get_db())
        try:
                from datetime import timedelta
                data_limite = datetime.now() - timedelta(days=dias_manter)
                
                explicacoes_antigas = db.query(ExplicacaoAgente).filter(
                    ExplicacaoAgente.data_execucao < data_limite,
                    ExplicacaoAgente.marcado_para_melhoria == False  # Manter marcadas para melhoria
                ).all()
                
                count = len(explicacoes_antigas)
                
                for exp in explicacoes_antigas:
                    db.delete(exp)
                
                db.commit()
                logger.info(f"Removidas {count} explicações antigas (anteriores a {data_limite})")
                return count
                
        except Exception as e:
            logger.error(f"Erro ao limpar explicações antigas: {str(e)}")
            return 0
