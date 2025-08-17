# ============================================================================
# src/agents/base_agent.py - Classe Base para Agentes
# ============================================================================

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import time
import tracemalloc
from datetime import datetime

class BaseAgent(ABC):
    """Classe base para todos os agentes do sistema."""
    
    def __init__(self, name: str, llm_client, config):
        self.name = name
        self.llm_client = llm_client
        self.config = config
        
        # Sistema de explicações
        self.explicacao_ativa = True
        self.contexto_execucao = {}
        self.etapas_processamento = []
        self.palavras_chave_identificadas = []
        self.produtos_similares = []
        self.exemplos_utilizados = []
        
        # Sistema de rastreamento de consultas
        self.consultas_realizadas = []
        self.consulta_metadados_service = None
        self.produto_id_atual = None
        
        # Métricas de performance
        self.tempo_inicio = None
        self.memoria_inicial = None
        self.tokens_utilizados = 0
    
    def configurar_rastreamento_consultas(self, consulta_service, produto_id: str):
        """Configura o serviço de rastreamento de consultas para este agente."""
        self.consulta_metadados_service = consulta_service
        self.produto_id_atual = produto_id
        self.consultas_realizadas = []
    
    def registrar_consulta_database(self, tipo_consulta: str, fonte_dados: str, 
                                  query: str = "", contexto: Dict[str, Any] = None) -> str:
        """Registra uma consulta ao banco de dados e retorna o ID da consulta."""
        if not self.consulta_metadados_service or not self.produto_id_atual:
            return None
            
        try:
            consulta_id = self.consulta_metadados_service.registrar_consulta(
                produto_id=self.produto_id_atual,
                agente_nome=self.name.lower().replace('agent', ''),
                tipo_consulta=tipo_consulta,
                query_original=query[:1000],  # Limitar tamanho
                banco_origem=fonte_dados,
                metadados=contexto or {}
            )
            
            # Armazenar para referência local
            consulta_info = {
                "consulta_id": consulta_id,
                "tipo": tipo_consulta,
                "fonte": fonte_dados,
                "timestamp": datetime.now().isoformat()
            }
            self.consultas_realizadas.append(consulta_info)
            
            return consulta_id
            
        except Exception as e:
            print(f"Erro ao registrar consulta: {e}")
            return None
    
    def finalizar_consulta_database(self, consulta_id: str, tempo_execucao_ms: int,
                                  resultados_encontrados: int, qualidade_score: float = 0.0,
                                  metadata_resultados: Dict[str, Any] = None):
        """Finaliza o registro de uma consulta com os resultados obtidos."""
        if not self.consulta_metadados_service or not consulta_id:
            return
            
        try:
            # Criar lista de resultados simulados para compatibilidade
            resultados_simulados = []
            if resultados_encontrados > 0:
                for i in range(min(resultados_encontrados, 5)):  # Máximo 5 itens simulados
                    resultados_simulados.append({
                        "indice": i,
                        "score": qualidade_score,
                        "metadata": metadata_resultados or {}
                    })
            
            self.consulta_metadados_service.registrar_resultado(
                consulta_id=consulta_id,
                resultados=resultados_simulados,
                tempo_execucao_ms=tempo_execucao_ms
            )
        except Exception as e:
            print(f"Erro ao finalizar consulta: {e}")

    @abstractmethod
    def run(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Método principal que cada agente deve implementar."""
        pass
    
    def iniciar_explicacao(self, input_data: Any, context: Dict[str, Any] = None):
        """Inicia o sistema de rastreamento e explicação."""
        if not self.explicacao_ativa:
            return
            
        self.tempo_inicio = time.time()
        tracemalloc.start()
        self.memoria_inicial = tracemalloc.get_traced_memory()[0]
        
        self.contexto_execucao = {
            "input_original": str(input_data)[:1000],  # Limitar tamanho
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.etapas_processamento = []
        self.palavras_chave_identificadas = []
        self.produtos_similares = []
        self.exemplos_utilizados = []
        self.tokens_utilizados = 0
    
    def adicionar_etapa(self, nome_etapa: str, descricao: str, resultado: Any = None):
        """Adiciona uma etapa de processamento ao rastreamento."""
        if not self.explicacao_ativa:
            return
            
        etapa = {
            "nome": nome_etapa,
            "descricao": descricao,
            "timestamp": datetime.now().isoformat(),
            "resultado": str(resultado)[:500] if resultado else None
        }
        self.etapas_processamento.append(etapa)
    
    def adicionar_palavras_chave(self, palavras: List[str]):
        """Adiciona palavras-chave identificadas durante o processamento."""
        if not self.explicacao_ativa:
            return
        self.palavras_chave_identificadas.extend(palavras)
    
    def adicionar_produto_similar(self, produto: Dict[str, Any]):
        """Adiciona produto similar encontrado durante a análise."""
        if not self.explicacao_ativa:
            return
        self.produtos_similares.append(produto)
    
    def adicionar_exemplo_utilizado(self, exemplo: Dict[str, Any]):
        """Adiciona exemplo do Golden Set ou base de conhecimento utilizado."""
        if not self.explicacao_ativa:
            return
        self.exemplos_utilizados.append(exemplo)
    
    def contar_tokens_llm(self, prompt: str, resposta: str):
        """Conta tokens aproximados utilizados em chamadas LLM."""
        if not self.explicacao_ativa:
            return
        # Aproximação simples: 1 token ≈ 4 caracteres
        tokens_prompt = len(prompt) // 4
        tokens_resposta = len(resposta) // 4
        self.tokens_utilizados += tokens_prompt + tokens_resposta
    
    def finalizar_explicacao(self, resultado: Dict[str, Any], 
                           explicacao_detalhada: str = "", 
                           justificativa_tecnica: str = "",
                           nivel_confianca: float = 0.0) -> Dict[str, Any]:
        """Finaliza o rastreamento e retorna dados completos da explicação."""
        if not self.explicacao_ativa:
            return resultado
            
        tempo_final = time.time()
        tempo_processamento = int((tempo_final - self.tempo_inicio) * 1000) if self.tempo_inicio else 0
        
        memoria_final = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0
        memoria_utilizada = max(0, (memoria_final - self.memoria_inicial) / 1024 / 1024) if self.memoria_inicial else 0
        
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        # Dados completos da explicação
        explicacao_completa = {
            "agente_nome": self.name,
            "agente_versao": "1.0",
            "input_original": self.contexto_execucao.get("input_original", ""),
            "contexto_utilizado": self.contexto_execucao.get("context", {}),
            "etapas_processamento": self.etapas_processamento,
            "palavras_chave_identificadas": ", ".join(set(self.palavras_chave_identificadas)),
            "produtos_similares_encontrados": self.produtos_similares,
            "resultado_agente": resultado,
            "explicacao_detalhada": explicacao_detalhada,
            "justificativa_tecnica": justificativa_tecnica,
            "nivel_confianca": nivel_confianca,
            "rag_consultado": any("rag" in etapa.get("nome", "").lower() for etapa in self.etapas_processamento),
            "golden_set_utilizado": any("golden" in etapa.get("nome", "").lower() for etapa in self.etapas_processamento),
            "base_ncm_consultada": any("ncm" in etapa.get("nome", "").lower() for etapa in self.etapas_processamento),
            "exemplos_utilizados": self.exemplos_utilizados,
            "tempo_processamento_ms": tempo_processamento,
            "memoria_utilizada_mb": round(memoria_utilizada, 2),
            "tokens_llm_utilizados": self.tokens_utilizados,
            "data_execucao": datetime.now().isoformat()
        }
        
        # Adicionar explicação ao resultado principal
        resultado["explicacao_agente"] = explicacao_completa
        
        return resultado
    
    def _create_trace(self, action: str, input_data: Any, output: Any, reasoning: str = "") -> Dict[str, Any]:
        """Cria um trace de auditoria para rastreabilidade."""
        trace = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "input": str(input_data)[:500] + "..." if len(str(input_data)) > 500 else str(input_data),
            "output": str(output)[:500] + "..." if len(str(output)) > 500 else str(output),
            "reasoning": reasoning
        }
        
        # Adicionar como etapa se explicação estiver ativa
        if self.explicacao_ativa:
            self.adicionar_etapa(action, reasoning, output)
        
        return trace