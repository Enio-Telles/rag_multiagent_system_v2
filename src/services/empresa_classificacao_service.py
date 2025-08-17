"""
Serviço de Integração para Bancos de Dados por Empresa
Integra o EmpresaDatabaseManager com o sistema de classificação existente
"""

import time
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.database.empresa_database_manager import EmpresaDatabaseManager
from src.services.empresa_contexto_service import EmpresaContextoService

class EmpresaClassificacaoService:
    """Serviço que integra classificação com bancos segregados por empresa"""
    
    def __init__(self):
        self.db_manager = EmpresaDatabaseManager()
        self.contexto_service = EmpresaContextoService()
        
    def inicializar_empresa(self, empresa_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inicializa uma nova empresa no sistema"""
        try:
            # Gerar ID único para empresa (usar CNPJ ou número sequencial)
            import time
            empresa_id = int(time.time() * 1000) % 1000000  # ID baseado em timestamp
            
            # Criar banco de dados específico da empresa
            db_path = self.db_manager.create_empresa_database(empresa_id, empresa_data)
            
            # Criar Golden Set compartilhado se não existir
            self.db_manager.create_golden_set_shared()
            
            return {
                "sucesso": True,
                "empresa_id": empresa_id,
                "database_path": db_path,
                "empresa_info": empresa_data,
                "mensagem": f"Empresa {empresa_id} inicializada com sucesso"
            }
            
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "mensagem": "Erro ao inicializar empresa"
            }
    
    def classificar_produto_empresa(self, empresa_id: int, produto_data: Dict[str, Any],
                                  hybrid_router) -> Dict[str, Any]:
        """Classifica um produto específico de uma empresa"""
        start_time = time.time()
        
        try:
            # 1. Inserir produto no banco da empresa
            produto_id = self.db_manager.insert_produto(empresa_id, produto_data)
            
            # 2. Obter contexto da empresa do banco
            db_path = self.db_manager.get_empresa_db_path(empresa_id)
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM empresa_info WHERE id = ?", (empresa_id,))
                empresa_info = dict(cursor.fetchone() or {})
            
            contexto_empresa = {
                "empresa_id": empresa_id,
                "tipo_atividade": empresa_info.get('tipo_atividade', ''),
                "canal_venda": empresa_info.get('canal_venda', ''),
                "segmento_cest_preferencial": 28 if empresa_info.get('canal_venda') == 'porta_a_porta' else None
            }
            
            # 3. Preparar dados para classificação
            nome_produto = produto_data.get('nome_produto', '')
            
            # 4. Executar classificação com rastreamento de agentes
            resultado_classificacao = self._classificar_com_rastreamento(
                empresa_id, produto_id, nome_produto, hybrid_router, contexto_empresa
            )
            
            # 5. Salvar classificação final
            classificacao_id = self.db_manager.insert_classificacao(
                empresa_id, produto_id, resultado_classificacao
            )
            
            tempo_total = time.time() - start_time
            
            return {
                "sucesso": True,
                "empresa_id": empresa_id,
                "produto_id": produto_id,
                "classificacao_id": classificacao_id,
                "resultado": resultado_classificacao,
                "tempo_execucao": tempo_total,
                "contexto_aplicado": contexto_empresa
            }
            
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "empresa_id": empresa_id,
                "produto_data": produto_data
            }
    
    def _classificar_com_rastreamento(self, empresa_id: int, produto_id: int, 
                                    nome_produto: str, hybrid_router, 
                                    contexto_empresa: Dict[str, Any]) -> Dict[str, Any]:
        """Executa classificação com rastreamento completo de agentes"""
        
        # Wrapper para rastrear ações dos agentes
        original_methods = {}
        
        def create_tracked_method(agent_name: str, method_name: str, original_method):
            def tracked_method(*args, **kwargs):
                start_time = time.time()
                
                try:
                    # Registrar entrada
                    input_data = {
                        "args": str(args),
                        "kwargs": {k: str(v) for k, v in kwargs.items()},
                        "contexto_empresa": contexto_empresa
                    }
                    
                    # Executar método original
                    resultado = original_method(*args, **kwargs)
                    
                    # Calcular tempo
                    tempo_execucao = time.time() - start_time
                    
                    # Registrar ação
                    self.db_manager.insert_agente_acao(empresa_id, {
                        "produto_id": produto_id,
                        "classificacao_id": None,  # Será atualizado depois
                        "agente_nome": agent_name,
                        "acao_tipo": method_name,
                        "input_dados": input_data,
                        "output_resultado": resultado if isinstance(resultado, dict) else {"resultado": str(resultado)},
                        "justificativa": f"Execução de {method_name} pelo agente {agent_name}",
                        "confianca": getattr(resultado, 'confidence', None) if hasattr(resultado, 'confidence') else None,
                        "tempo_execucao": tempo_execucao,
                        "sucesso": True
                    })
                    
                    return resultado
                    
                except Exception as e:
                    # Registrar erro
                    tempo_execucao = time.time() - start_time
                    
                    self.db_manager.insert_agente_acao(empresa_id, {
                        "produto_id": produto_id,
                        "classificacao_id": None,
                        "agente_nome": agent_name,
                        "acao_tipo": method_name,
                        "input_dados": {"args": str(args), "kwargs": str(kwargs)},
                        "output_resultado": {},
                        "justificativa": f"Erro em {method_name}",
                        "confianca": 0.0,
                        "tempo_execucao": tempo_execucao,
                        "sucesso": False,
                        "erro_detalhes": str(e)
                    })
                    
                    raise e
            
            return tracked_method
        
        # Rastrear consultas de busca semântica
        def track_semantic_search(agent_name: str, query: str, results: List[Any]) -> None:
            self.db_manager.insert_agente_consulta(empresa_id, {
                "produto_id": produto_id,
                "agente_nome": agent_name,
                "tipo_consulta": "semantic_search",
                "query_original": query,
                "query_processada": query,
                "resultados_encontrados": len(results),
                "resultado_detalhes": {"results": results[:5]},  # Primeiros 5 resultados
                "relevancia_score": results[0].get('score', 0) if results else 0,
                "tempo_resposta": 0.1,  # Estimativa
                "sucesso": True
            })
        
        # Instrumentar agentes se disponíveis
        try:
            agents_to_track = [
                ("expansion", hybrid_router.expansion_agent),
                ("ncm", hybrid_router.ncm_agent),
                ("cest", hybrid_router.cest_agent),
                ("aggregation", hybrid_router.aggregation_agent),
                ("reconciler", hybrid_router.reconciler_agent)
            ]
            
            for agent_name, agent in agents_to_track:
                if hasattr(agent, 'classify'):
                    original_methods[f"{agent_name}_classify"] = agent.classify
                    agent.classify = create_tracked_method(agent_name, "classify", agent.classify)
                    
                if hasattr(agent, 'process'):
                    original_methods[f"{agent_name}_process"] = agent.process
                    agent.process = create_tracked_method(agent_name, "process", agent.process)
        except Exception as e:
            print(f"Aviso: Não foi possível instrumentar todos os agentes: {e}")
        
        try:
            # Executar classificação
            resultado = hybrid_router.classify_product_with_explanations(
                nome_produto, contexto_empresa
            )
            
            return resultado
            
        finally:
            # Restaurar métodos originais
            for agent_name, agent in agents_to_track:
                if hasattr(agent, 'classify') and f"{agent_name}_classify" in original_methods:
                    agent.classify = original_methods[f"{agent_name}_classify"]
                if hasattr(agent, 'process') and f"{agent_name}_process" in original_methods:
                    agent.process = original_methods[f"{agent_name}_process"]
    
    def aprovar_classificacao(self, empresa_id: int, classificacao_id: int, 
                            usuario: str, observacoes: str = "") -> Dict[str, Any]:
        """Aprova uma classificação"""
        try:
            db_path = self.db_manager.get_empresa_db_path(empresa_id)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Atualizar status
                cursor.execute("""
                    UPDATE classificacoes 
                    SET status = 'aprovado', aprovado_por = ?, data_aprovacao = ?, 
                        observacoes = ? 
                    WHERE id = ?
                """, (usuario, datetime.now(), observacoes, classificacao_id))
                
                # Obter dados da classificação
                cursor.execute("SELECT produto_id FROM classificacoes WHERE id = ?", (classificacao_id,))
                produto_id = cursor.fetchone()[0]
                
                # Registrar histórico
                cursor.execute("""
                    INSERT INTO historico_mudancas 
                    (produto_id, classificacao_id, tipo_mudanca, usuario, motivo)
                    VALUES (?, ?, 'aprovacao', ?, ?)
                """, (produto_id, classificacao_id, usuario, observacoes or "Classificação aprovada"))
                
                conn.commit()
            
            return {"sucesso": True, "mensagem": "Classificação aprovada"}
            
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
    
    def rejeitar_classificacao(self, empresa_id: int, classificacao_id: int,
                             usuario: str, motivo: str) -> Dict[str, Any]:
        """Rejeita uma classificação"""
        try:
            db_path = self.db_manager.get_empresa_db_path(empresa_id)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Atualizar status
                cursor.execute("""
                    UPDATE classificacoes 
                    SET status = 'rejeitado', observacoes = ? 
                    WHERE id = ?
                """, (motivo, classificacao_id))
                
                # Obter dados da classificação
                cursor.execute("SELECT produto_id FROM classificacoes WHERE id = ?", (classificacao_id,))
                produto_id = cursor.fetchone()[0]
                
                # Registrar histórico
                cursor.execute("""
                    INSERT INTO historico_mudancas 
                    (produto_id, classificacao_id, tipo_mudanca, usuario, motivo)
                    VALUES (?, ?, 'rejeicao', ?, ?)
                """, (produto_id, classificacao_id, usuario, motivo))
                
                conn.commit()
            
            return {"sucesso": True, "mensagem": "Classificação rejeitada"}
            
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
    
    def adicionar_ao_golden_set(self, empresa_id: int, produto_id: int, 
                              usuario: str = "sistema") -> Dict[str, Any]:
        """Adiciona um produto aprovado ao Golden Set compartilhado"""
        try:
            # Obter dados do produto da empresa
            produto_detalhado = self.db_manager.get_produto_detalhado(empresa_id, produto_id)
            
            if not produto_detalhado or "erro" in produto_detalhado:
                return {"sucesso": False, "erro": "Produto não encontrado"}
            
            produto = produto_detalhado["produto"]
            classificacoes = produto_detalhado["classificacoes"]
            
            # Encontrar classificação aprovada
            classificacao_aprovada = None
            for c in classificacoes:
                if c["status"] == "aprovado":
                    classificacao_aprovada = c
                    break
            
            if not classificacao_aprovada:
                return {"sucesso": False, "erro": "Nenhuma classificação aprovada encontrada"}
            
            # Inserir no Golden Set
            with sqlite3.connect(self.db_manager.golden_set_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO golden_set_produtos 
                    (gtin, nome_produto, descricao_padronizada, ncm_codigo, ncm_descricao,
                     cest_codigo, cest_descricao, categoria_padrao, confianca_validacao,
                     origem_validacao, numero_validacoes, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    produto["gtin"],
                    produto["nome_produto"],
                    produto["descricao_enriquecida"],
                    classificacao_aprovada["ncm_codigo"],
                    classificacao_aprovada["ncm_descricao"],
                    classificacao_aprovada["cest_codigo"],
                    classificacao_aprovada["cest_descricao"],
                    produto["categoria"],
                    classificacao_aprovada["confianca_ncm"],
                    "manual",
                    1,
                    f"Adicionado pela empresa {empresa_id}"
                ))
                
                golden_id = cursor.lastrowid
                
                # Registrar validação
                cursor.execute("""
                    INSERT INTO golden_set_validacoes 
                    (produto_golden_id, empresa_origem_id, validador, tipo_validacao, 
                     confianca, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    golden_id, empresa_id, usuario, "manual",
                    classificacao_aprovada["confianca_ncm"],
                    f"Produto validado da empresa {empresa_id}"
                ))
                
                conn.commit()
            
            return {
                "sucesso": True,
                "golden_set_id": golden_id,
                "mensagem": "Produto adicionado ao Golden Set"
            }
            
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
    
    def get_relatorio_empresa(self, empresa_id: int) -> Dict[str, Any]:
        """Gera relatório completo da empresa"""
        try:
            # Estatísticas gerais
            stats = self.db_manager.get_empresa_stats(empresa_id)
            
            # Informações da empresa (simulado)
            contexto = {
                "empresa_id": empresa_id,
                "nome": f"Empresa {empresa_id}",
                "ativo": True
            }
            
            # Últimas classificações
            db_path = self.db_manager.get_empresa_db_path(empresa_id)
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Últimas 10 classificações
                cursor.execute("""
                    SELECT c.*, p.nome_produto, p.gtin
                    FROM classificacoes c
                    JOIN produtos_empresa p ON c.produto_id = p.id
                    ORDER BY c.data_classificacao DESC
                    LIMIT 10
                """)
                ultimas_classificacoes = [dict(row) for row in cursor.fetchall()]
                
                # Performance por agente
                cursor.execute("""
                    SELECT agente_nome, 
                           COUNT(*) as total_acoes,
                           AVG(tempo_execucao) as tempo_medio,
                           SUM(CASE WHEN sucesso = 1 THEN 1 ELSE 0 END) as sucessos,
                           AVG(confianca) as confianca_media
                    FROM agente_acoes
                    GROUP BY agente_nome
                """)
                performance_agentes = [dict(row) for row in cursor.fetchall()]
            
            return {
                "empresa_id": empresa_id,
                "informacoes_empresa": contexto,
                "estatisticas": stats,
                "ultimas_classificacoes": ultimas_classificacoes,
                "performance_agentes": performance_agentes,
                "data_relatorio": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"erro": str(e)}
    
    def listar_empresas(self) -> List[Dict[str, Any]]:
        """Lista todas as empresas com seus bancos"""
        return self.db_manager.list_empresas_databases()
