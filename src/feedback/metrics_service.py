"""
Serviço para cálculo de métricas e análise de qualidade
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path

# Adicionar src ao path para imports absolutos
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from database.models import ClassificacaoRevisao, MetricasQualidade, GoldenSetEntry

logger = logging.getLogger(__name__)

class MetricsService:
    """
    Serviço responsável por calcular métricas de qualidade e detectar drift
    """
    
    def calcular_estatisticas(self, db: Session, periodo_dias: int = 30) -> Dict[str, Any]:
        """
        Calcula estatísticas gerais para o dashboard
        """
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        # Consultas base
        total_query = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.data_classificacao >= data_inicio
        )
        
        revisadas_query = total_query.filter(
            ClassificacaoRevisao.status_revisao.in_(["APROVADO", "CORRIGIDO"])
        )
        
        # Contadores
        total_classificacoes = total_query.count()
        pendentes_revisao = total_query.filter(
            ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
        ).count()
        
        aprovadas = total_query.filter(
            ClassificacaoRevisao.status_revisao == "APROVADO"
        ).count()
        
        corrigidas = total_query.filter(
            ClassificacaoRevisao.status_revisao == "CORRIGIDO"
        ).count()
        
        total_revisadas = aprovadas + corrigidas
        
        # Cálculos de métricas
        taxa_aprovacao = (aprovadas / total_revisadas * 100) if total_revisadas > 0 else 0
        
        # Confiança média
        confianca_result = total_query.with_entities(
            func.avg(ClassificacaoRevisao.confianca_sugerida)
        ).scalar()
        confianca_media = float(confianca_result) if confianca_result else 0.0
        
        # Tempo médio de revisão
        tempo_result = revisadas_query.filter(
            ClassificacaoRevisao.tempo_revisao_segundos.isnot(None)
        ).with_entities(
            func.avg(ClassificacaoRevisao.tempo_revisao_segundos)
        ).scalar()
        tempo_medio_revisao = float(tempo_result) if tempo_result else None
        
        # Distribuição de confiança
        distribuicao_confianca = self._calcular_distribuicao_confianca(db, data_inicio)
        
        # Contar entradas no Golden Set
        total_golden = db.query(GoldenSetEntry).filter(
            and_(
                GoldenSetEntry.ativo == True,
                GoldenSetEntry.data_adicao >= data_inicio
            )
        ).count()
        
        return {
            "total_classificacoes": total_classificacoes,
            "pendentes_revisao": pendentes_revisao,
            "aprovadas": aprovadas,
            "corrigidas": corrigidas,
            "total_golden": total_golden,
            "taxa_aprovacao": round(taxa_aprovacao, 2),
            "confianca_media": round(confianca_media, 3),
            "tempo_medio_revisao": round(tempo_medio_revisao / 60, 2) if tempo_medio_revisao else None,  # em minutos
            "distribuicao_confianca": distribuicao_confianca
        }
    
    def _calcular_distribuicao_confianca(self, db: Session, data_inicio: datetime) -> Dict[str, int]:
        """
        Calcula a distribuição de confiança em faixas
        """
        query = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.data_classificacao >= data_inicio
        )
        
        distribuicao = {
            "0.0-0.5": 0,
            "0.5-0.7": 0,
            "0.7-0.8": 0,
            "0.8-0.9": 0,
            "0.9-1.0": 0
        }
        
        for classificacao in query.all():
            confianca = classificacao.confianca_sugerida or 0.0
            
            if confianca < 0.5:
                distribuicao["0.0-0.5"] += 1
            elif confianca < 0.7:
                distribuicao["0.5-0.7"] += 1
            elif confianca < 0.8:
                distribuicao["0.7-0.8"] += 1
            elif confianca < 0.9:
                distribuicao["0.8-0.9"] += 1
            else:
                distribuicao["0.9-1.0"] += 1
        
        return distribuicao
    
    def calcular_acuracia_temporal(self, db: Session, periodo_dias: int = 90) -> List[Dict[str, Any]]:
        """
        Calcula a acurácia ao longo do tempo para análise de drift
        """
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        # Agrupar por semana
        dados = []
        for i in range(0, periodo_dias, 7):
            semana_inicio = data_inicio + timedelta(days=i)
            semana_fim = semana_inicio + timedelta(days=7)
            
            total_query = db.query(ClassificacaoRevisao).filter(
                and_(
                    ClassificacaoRevisao.data_classificacao >= semana_inicio,
                    ClassificacaoRevisao.data_classificacao < semana_fim
                )
            )
            
            revisadas_query = total_query.filter(
                ClassificacaoRevisao.status_revisao.in_(["APROVADO", "CORRIGIDO"])
            )
            
            total_semana = total_query.count()
            aprovadas_semana = total_query.filter(
                ClassificacaoRevisao.status_revisao == "APROVADO"
            ).count()
            
            revisadas_semana = revisadas_query.count()
            
            # Cálculos
            acuracia = (aprovadas_semana / revisadas_semana * 100) if revisadas_semana > 0 else 0
            
            confianca_result = total_query.with_entities(
                func.avg(ClassificacaoRevisao.confianca_sugerida)
            ).scalar()
            confianca_media = float(confianca_result) if confianca_result else 0.0
            
            dados.append({
                "semana": semana_inicio.strftime("%Y-%m-%d"),
                "total_classificacoes": total_semana,
                "total_revisadas": revisadas_semana,
                "acuracia": round(acuracia, 2),
                "confianca_media": round(confianca_media, 3)
            })
        
        return dados
    
    def detectar_drift_qualidade(self, db: Session, janela_semanas: int = 4) -> Dict[str, Any]:
        """
        Detecta drift na qualidade das classificações
        """
        data_limite = datetime.now() - timedelta(weeks=janela_semanas)
        
        # Período atual (últimas X semanas)
        stats_atual = self._calcular_stats_periodo(db, data_limite, datetime.now())
        
        # Período anterior (X semanas anteriores)
        data_anterior_inicio = data_limite - timedelta(weeks=janela_semanas)
        stats_anterior = self._calcular_stats_periodo(db, data_anterior_inicio, data_limite)
        
        # Calcular variações
        variacao_taxa = stats_atual["taxa_aprovacao"] - stats_anterior["taxa_aprovacao"]
        variacao_confianca = stats_atual["confianca_media"] - stats_anterior["confianca_media"]
        
        # Definir thresholds para alerta
        THRESHOLD_TAXA = -10.0  # Queda de 10% na taxa de aprovação
        THRESHOLD_CONFIANCA = -0.05  # Queda de 0.05 na confiança média
        
        alertas = []
        if variacao_taxa < THRESHOLD_TAXA:
            alertas.append(f"Queda significativa na taxa de aprovação: {variacao_taxa:.1f}%")
        
        if variacao_confianca < THRESHOLD_CONFIANCA:
            alertas.append(f"Queda significativa na confiança média: {variacao_confianca:.3f}")
        
        return {
            "periodo_atual": {
                "inicio": data_limite.strftime("%Y-%m-%d"),
                "fim": datetime.now().strftime("%Y-%m-%d"),
                "stats": stats_atual
            },
            "periodo_anterior": {
                "inicio": data_anterior_inicio.strftime("%Y-%m-%d"),
                "fim": data_limite.strftime("%Y-%m-%d"),
                "stats": stats_anterior
            },
            "variacoes": {
                "taxa_aprovacao": round(variacao_taxa, 2),
                "confianca_media": round(variacao_confianca, 3)
            },
            "drift_detectado": len(alertas) > 0,
            "alertas": alertas
        }
    
    def _calcular_stats_periodo(self, db: Session, data_inicio: datetime, data_fim: datetime) -> Dict[str, float]:
        """
        Calcula estatísticas para um período específico
        """
        query = db.query(ClassificacaoRevisao).filter(
            and_(
                ClassificacaoRevisao.data_classificacao >= data_inicio,
                ClassificacaoRevisao.data_classificacao < data_fim
            )
        )
        
        revisadas_query = query.filter(
            ClassificacaoRevisao.status_revisao.in_(["APROVADO", "CORRIGIDO"])
        )
        
        aprovadas = query.filter(
            ClassificacaoRevisao.status_revisao == "APROVADO"
        ).count()
        
        total_revisadas = revisadas_query.count()
        
        taxa_aprovacao = (aprovadas / total_revisadas * 100) if total_revisadas > 0 else 0
        
        confianca_result = query.with_entities(
            func.avg(ClassificacaoRevisao.confianca_sugerida)
        ).scalar()
        confianca_media = float(confianca_result) if confianca_result else 0.0
        
        return {
            "taxa_aprovacao": taxa_aprovacao,
            "confianca_media": confianca_media,
            "total_revisadas": total_revisadas
        }
    
    def salvar_metricas_historicas(self, db: Session, periodo_dias: int = 7):
        """
        Salva métricas históricas para análise de longo prazo
        """
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=periodo_dias)
            
            # Verificar se já existe métrica para este período
            existing = db.query(MetricasQualidade).filter(
                and_(
                    MetricasQualidade.data_inicio == data_inicio.date(),
                    MetricasQualidade.data_fim == data_fim.date()
                )
            ).first()
            
            if existing:
                logger.info(f"Métricas já existem para período {data_inicio.date()} - {data_fim.date()}")
                return
            
            # Calcular estatísticas
            stats = self.calcular_estatisticas(db, periodo_dias)
            
            # Criar registro
            metricas = MetricasQualidade(
                data_inicio=data_inicio,
                data_fim=data_fim,
                total_classificacoes=stats["total_classificacoes"],
                total_revisadas=stats["aprovadas"] + stats["corrigidas"],
                total_aprovadas=stats["aprovadas"],
                total_corrigidas=stats["corrigidas"],
                taxa_aprovacao=stats["taxa_aprovacao"],
                confianca_media=stats["confianca_media"],
                confianca_mediana=stats["confianca_media"],  # Simplificação
                tempo_medio_revisao=stats["tempo_medio_revisao"],
                periodo_tipo="SEMANAL" if periodo_dias == 7 else "PERSONALIZADO"
            )
            
            db.add(metricas)
            db.commit()
            
            logger.info(f"Métricas históricas salvas para período {data_inicio.date()} - {data_fim.date()}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar métricas históricas: {e}")
            raise
