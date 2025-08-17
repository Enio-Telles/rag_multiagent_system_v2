"""
Serviço para rastreamento de consultas dos agentes aos bancos de dados
Captura metadados das consultas (origem, tipo, resultados)
"""

from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database.models import ExplicacaoAgente
from database.connection import get_db

logger = logging.getLogger(__name__)

class ConsultaMetadadosService:
    """Serviço para rastrear consultas dos agentes com metadados"""
    
    def __init__(self):
        self.consultas_ativas = {}  # Armazena consultas da sessão atual
    
    def registrar_consulta(self, 
                          produto_id: int,
                          agente_nome: str,
                          tipo_consulta: str,
                          query_original: str,
                          banco_origem: str,
                          metadados: Dict[str, Any]) -> str:
        """
        Registra uma consulta realizada por um agente
        
        Args:
            produto_id: ID do produto sendo processado
            agente_nome: Nome do agente (expansion, ncm, cest, etc)
            tipo_consulta: Tipo da consulta (rag, ncm_hierarchy, cest_mapping, golden_set)
            query_original: Query/texto original usado na consulta
            banco_origem: Origem dos dados (faiss_vector, ncm_base, cest_base, golden_set)
            metadados: Metadados adicionais da consulta
            
        Returns:
            str: ID único da consulta
        """
        consulta_id = f"{produto_id}_{agente_nome}_{tipo_consulta}_{datetime.now().timestamp()}"
        
        consulta_data = {
            "id": consulta_id,
            "produto_id": produto_id,
            "agente_nome": agente_nome,
            "tipo_consulta": tipo_consulta,
            "query_original": query_original,
            "banco_origem": banco_origem,
            "timestamp": datetime.now().isoformat(),
            "metadados": metadados
        }
        
        # Armazenar na sessão
        if produto_id not in self.consultas_ativas:
            self.consultas_ativas[produto_id] = []
        
        self.consultas_ativas[produto_id].append(consulta_data)
        
        logger.info(f"📊 Consulta registrada: {agente_nome} -> {tipo_consulta} em {banco_origem}")
        return consulta_id
    
    def registrar_resultados(self,
                           consulta_id: str,
                           resultados: List[Dict[str, Any]],
                           tempo_execucao_ms: int,
                           total_encontrados: int) -> bool:
        """
        Registra os resultados de uma consulta
        
        Args:
            consulta_id: ID da consulta
            resultados: Lista de resultados encontrados
            tempo_execucao_ms: Tempo de execução em milissegundos
            total_encontrados: Total de resultados encontrados
            
        Returns:
            bool: True se registrou com sucesso
        """
        try:
            # Encontrar consulta na sessão
            for produto_id, consultas in self.consultas_ativas.items():
                for consulta in consultas:
                    if consulta["id"] == consulta_id:
                        consulta["resultados"] = {
                            "items": resultados[:10],  # Limitar a 10 itens para não sobrecarregar
                            "total_encontrados": total_encontrados,
                            "tempo_execucao_ms": tempo_execucao_ms,
                            "timestamp_resultado": datetime.now().isoformat()
                        }
                        
                        # Adicionar métricas de qualidade
                        consulta["metricas"] = self._calcular_metricas_consulta(resultados, tempo_execucao_ms)
                        
                        logger.info(f"📈 Resultados registrados para {consulta_id}: {total_encontrados} itens em {tempo_execucao_ms}ms")
                        return True
            
            logger.warning(f"⚠️ Consulta {consulta_id} não encontrada para registrar resultados")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar resultados: {e}")
            return False
    
    def registrar_resultado(self, consulta_id: str, resultados: List[Dict[str, Any]], tempo_execucao_ms: int) -> bool:
        """
        Alias para registrar_resultados - para compatibilidade
        
        Args:
            consulta_id: ID da consulta
            resultados: Lista de resultados encontrados
            tempo_execucao_ms: Tempo de execução em millisegundos
            
        Returns:
            bool: True se registrou com sucesso
        """
        return self.registrar_resultados(consulta_id, resultados, tempo_execucao_ms, len(resultados))
    
    def finalizar_consulta(self, consulta_id: str, resultados: List[Dict[str, Any]], tempo_execucao_ms: int) -> bool:
        """
        Finaliza uma consulta registrando os resultados obtidos
        
        Args:
            consulta_id: ID da consulta retornado por registrar_consulta
            resultados: Lista de resultados encontrados
            tempo_execucao_ms: Tempo de execução em millisegundos
            
        Returns:
            bool: True se finalizou com sucesso
        """
        return self.registrar_resultados(consulta_id, resultados, tempo_execucao_ms, len(resultados))
    
    def obter_consultas_produto(self, produto_id: int) -> List[Dict[str, Any]]:
        """
        Obtém todas as consultas realizadas para um produto
        
        Args:
            produto_id: ID do produto
            
        Returns:
            List[Dict]: Lista de consultas com metadados
        """
        return self.consultas_ativas.get(produto_id, [])
    
    def obter_consultas_por_agente(self, produto_id: int, agente_nome: str) -> List[Dict[str, Any]]:
        """
        Obtém consultas de um agente específico para um produto
        
        Args:
            produto_id: ID do produto
            agente_nome: Nome do agente
            
        Returns:
            List[Dict]: Lista de consultas do agente
        """
        consultas_produto = self.obter_consultas_produto(produto_id)
        return [c for c in consultas_produto if c["agente_nome"] == agente_nome]
    
    def salvar_consultas_permanente(self, produto_id: int, classificacao_id: Optional[int] = None) -> bool:
        """
        Salva as consultas da sessão no banco permanente via ExplicacaoAgente
        
        Args:
            produto_id: ID do produto
            classificacao_id: ID da classificação (opcional)
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            if produto_id not in self.consultas_ativas:
                return True  # Nada para salvar
            
            db = next(get_db())
            consultas = self.consultas_ativas[produto_id]
            
            # Agrupar consultas por agente
            consultas_por_agente = {}
            for consulta in consultas:
                agente = consulta["agente_nome"]
                if agente not in consultas_por_agente:
                    consultas_por_agente[agente] = []
                consultas_por_agente[agente].append(consulta)
            
            # Salvar no ExplicacaoAgente
            for agente_nome, consultas_agente in consultas_por_agente.items():
                explicacao = ExplicacaoAgente(
                    produto_id=produto_id,
                    classificacao_id=classificacao_id,
                    agente_nome=agente_nome,
                    agente_versao="1.0",
                    contexto_utilizado={
                        "consultas_realizadas": len(consultas_agente),
                        "bancos_consultados": list(set(c["banco_origem"] for c in consultas_agente)),
                        "tipos_consulta": list(set(c["tipo_consulta"] for c in consultas_agente))
                    },
                    etapas_processamento={
                        "consultas_detalhadas": consultas_agente,
                        "resumo_execucao": self._gerar_resumo_consultas(consultas_agente)
                    },
                    observacoes=f"Registro automático de {len(consultas_agente)} consultas realizadas pelo agente"
                )
                
                db.add(explicacao)
            
            db.commit()
            
            # Limpar consultas da sessão após salvar
            del self.consultas_ativas[produto_id]
            
            logger.info(f"💾 Consultas salvas permanentemente para produto {produto_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar consultas permanente: {e}")
            if 'db' in locals():
                db.rollback()
            return False
    
    def _calcular_metricas_consulta(self, resultados: List[Dict[str, Any]], tempo_ms: int) -> Dict[str, Any]:
        """Calcula métricas de qualidade da consulta"""
        if not resultados:
            return {
                "relevancia_media": 0.0,
                "performance": "lenta" if tempo_ms > 1000 else "normal",
                "qualidade_resultados": "baixa"
            }
        
        # Calcular relevância média (baseado em scores se disponíveis)
        scores = []
        for resultado in resultados:
            if "score" in resultado:
                scores.append(resultado["score"])
            elif "similarity" in resultado:
                scores.append(resultado["similarity"])
        
        relevancia_media = sum(scores) / len(scores) if scores else 0.5
        
        # Avaliar performance
        if tempo_ms < 100:
            performance = "excelente"
        elif tempo_ms < 500:
            performance = "boa"
        elif tempo_ms < 1000:
            performance = "normal"
        else:
            performance = "lenta"
        
        # Qualidade dos resultados
        if relevancia_media > 0.8:
            qualidade = "alta"
        elif relevancia_media > 0.6:
            qualidade = "media"
        else:
            qualidade = "baixa"
        
        return {
            "relevancia_media": round(relevancia_media, 3),
            "performance": performance,
            "qualidade_resultados": qualidade,
            "tempo_categoria": performance,
            "total_resultados": len(resultados)
        }
    
    def _gerar_resumo_consultas(self, consultas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera resumo das consultas de um agente"""
        total_consultas = len(consultas)
        tipos_consulta = list(set(c["tipo_consulta"] for c in consultas))
        bancos_origem = list(set(c["banco_origem"] for c in consultas))
        
        # Tempo total e médio
        tempos = [c.get("resultados", {}).get("tempo_execucao_ms", 0) for c in consultas]
        tempo_total = sum(tempos)
        tempo_medio = tempo_total / len(tempos) if tempos else 0
        
        # Total de resultados encontrados
        total_resultados = sum(c.get("resultados", {}).get("total_encontrados", 0) for c in consultas)
        
        return {
            "total_consultas": total_consultas,
            "tipos_consulta": tipos_consulta,
            "bancos_origem": bancos_origem,
            "tempo_total_ms": tempo_total,
            "tempo_medio_ms": round(tempo_medio, 2),
            "total_resultados_encontrados": total_resultados,
            "consultas_com_resultados": len([c for c in consultas if c.get("resultados", {}).get("total_encontrados", 0) > 0])
        }

# Instância global para uso pelos agentes
consulta_tracker = ConsultaMetadadosService()
