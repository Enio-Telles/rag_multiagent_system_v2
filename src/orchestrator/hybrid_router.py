# ============================================================================
# src/orchestrator/hybrid_router.py - Orquestrador Híbrido Principal
# ============================================================================

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager

# Fixed imports with proper module paths
from config import Config
from ingestion.data_loader import DataLoader
from ingestion.chunker import TextChunker
from vectorstore.faiss_store import FaissMetadataStore
from llm.ollama_client import OllamaClient
from agents.expansion_agent import ExpansionAgent
from agents.aggregation_agent import AggregationAgent
from agents.ncm_agent import NCMAgent
from agents.cest_agent import CESTAgent
from agents.reconciler_agent import ReconcilerAgent

# Importar novo serviço de base de conhecimento SQLite
from services.knowledge_base_service import KnowledgeBaseService

# Setup logging
logger = logging.getLogger(__name__)

# Importar sistema de aprendizagem contínua (Fase 5)
try:
    from feedback.continuous_learning import AugmentedRetrieval
    CONTINUOUS_LEARNING_AVAILABLE = True
except ImportError:
    CONTINUOUS_LEARNING_AVAILABLE = False
    logger.warning("Sistema de aprendizagem contínua não disponível")

# Importar sistema de explicações
try:
    from feedback.explicacao_service import ExplicacaoService
    EXPLICACAO_SERVICE_AVAILABLE = True
except ImportError:
    EXPLICACAO_SERVICE_AVAILABLE = False
    logger.warning("Serviço de explicações não disponível")

# Importar sistema de rastreamento de consultas
try:
    from feedback.consulta_metadados_service import ConsultaMetadadosService
    CONSULTA_METADADOS_SERVICE_AVAILABLE = True
except ImportError:
    CONSULTA_METADADOS_SERVICE_AVAILABLE = False
    logger.warning("Serviço de rastreamento de consultas não disponível")

# Importar sistema de contexto da empresa
try:
    from services.empresa_contexto_service import EmpresaContextoService
    EMPRESA_CONTEXTO_SERVICE_AVAILABLE = True
except ImportError:
    EMPRESA_CONTEXTO_SERVICE_AVAILABLE = False
    logger.warning("Serviço de contexto da empresa não disponível")
    logger.warning("Serviço de rastreamento de consultas não disponível")

class HybridRouter:
    """
    Orquestrador principal que coordena todo o fluxo de trabalho do sistema agêntico híbrido.
    Combina conhecimento estruturado (NCM mapping) com conhecimento semântico (RAG).
    """
    
    # Cache size limit to prevent memory issues
    MAX_CACHE_SIZE = 1000
    
    def __init__(self):
        self.config = Config()
        self._validate_configuration()
        
        self.data_loader = DataLoader()
        
        # Componentes principais
        self.llm_client = OllamaClient(self.config.OLLAMA_URL, self.config.OLLAMA_MODEL)
        self.vector_store = FaissMetadataStore(self.config.VECTOR_DIMENSION)
        
        # Sistema de aprendizagem contínua (Fase 5)
        self.augmented_retrieval = None
        if CONTINUOUS_LEARNING_AVAILABLE:
            try:
                self.augmented_retrieval = AugmentedRetrieval(self.config)
                logger.info("Sistema de aprendizagem contínua ativado")
            except Exception as e:
                logger.warning(f"Erro ao inicializar aprendizagem contínua: {e}")
        
        # Sistema de explicações
        self.explicacao_service = None
        if EXPLICACAO_SERVICE_AVAILABLE:
            try:
                self.explicacao_service = ExplicacaoService()
                logger.info("Serviço de explicações ativado")
            except Exception as e:
                logger.warning(f"Erro ao inicializar serviço de explicações: {e}")
        
        # Sistema de rastreamento de consultas
        self.consulta_metadados_service = None
        if CONSULTA_METADADOS_SERVICE_AVAILABLE:
            try:
                self.consulta_metadados_service = ConsultaMetadadosService()
                logger.info("Serviço de rastreamento de consultas ativado")
            except Exception as e:
                logger.warning(f"Erro ao inicializar serviço de consultas: {e}")
        
        # Sistema de contexto da empresa
        self.empresa_contexto_service = None
        if EMPRESA_CONTEXTO_SERVICE_AVAILABLE:
            try:
                self.empresa_contexto_service = EmpresaContextoService()
                logger.info("Serviço de contexto da empresa ativado")
            except Exception as e:
                logger.warning(f"Erro ao inicializar serviço de contexto: {e}")
        
        # Agentes especializados
        self.expansion_agent = ExpansionAgent(self.llm_client, self.config)
        self.aggregation_agent = AggregationAgent(self.llm_client, self.config)
        self.ncm_agent = NCMAgent(self.llm_client, self.config)
        self.cest_agent = CESTAgent(self.llm_client, self.config)
        self.reconciler_agent = ReconcilerAgent(self.llm_client, self.config)
        
        # Cache para otimização com limite de tamanho
        self.classification_cache = {}
        
        # Novo serviço de base de conhecimento SQLite (substitui JSON)
        self.knowledge_service = KnowledgeBaseService()
        
        # Carregar dados de referência adicionais
        self.abc_farma_db = self._load_abc_farma_db()
    
    def _validate_configuration(self) -> None:
        """Valida os parâmetros de configuração necessários."""
        required_attrs = [
            'OLLAMA_URL', 'OLLAMA_MODEL', 'VECTOR_DIMENSION',
            'FAISS_INDEX_FILE', 'METADATA_DB_FILE'
        ]
        
        for attr in required_attrs:
            if not hasattr(self.config, attr):
                raise ValueError(f"Configuração obrigatória ausente: {attr}")
            
            value = getattr(self.config, attr)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Configuração inválida para {attr}: {value}")
        
        logger.info("Configuração validada com sucesso")
    
    def _manage_cache_size(self) -> None:
        """Gerencia o tamanho do cache para evitar problemas de memória."""
        if len(self.classification_cache) > self.MAX_CACHE_SIZE:
            # Remove os itens mais antigos (FIFO)
            items_to_remove = len(self.classification_cache) - self.MAX_CACHE_SIZE + 100
            keys_to_remove = list(self.classification_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self.classification_cache[key]
            
            logger.info(f"Cache limpo: removidos {items_to_remove} itens")

    def get_ncm_info(self, codigo_ncm: str) -> Optional[Dict]:
        """
        Busca informações de NCM usando o serviço SQLite (substitui _load_mapping_db)
        """
        try:
            return self.knowledge_service.buscar_ncm_por_codigo(codigo_ncm)
        except Exception as e:
            logger.error(f"Erro ao buscar NCM {codigo_ncm}: {e}")
            return None
    
    def get_cests_for_ncm(self, codigo_ncm: str) -> List[Dict]:
        """
        Busca CESTs associados a um NCM usando o serviço SQLite
        """
        try:
            return self.knowledge_service.buscar_cests_hierarquia_ncm(codigo_ncm)
        except Exception as e:
            logger.error(f"Erro ao buscar CESTs para NCM {codigo_ncm}: {e}")
            return []
    
    def get_product_examples(self, codigo_ncm: str, limite: int = 5) -> List[Dict]:
        """
        Busca produtos exemplo para um NCM usando o serviço SQLite
        """
        try:
            return self.knowledge_service.buscar_exemplos_por_ncm(codigo_ncm, limite)
        except Exception as e:
            logger.error(f"Erro ao buscar exemplos para NCM {codigo_ncm}: {e}")
            return []
    
    def search_ncms_by_keywords(self, palavras: List[str], limite: int = 20) -> List[Dict]:
        """
        Busca NCMs por palavras-chave usando o serviço SQLite
        """
        try:
            return self.knowledge_service.buscar_ncms_por_palavras(palavras, limite)
        except Exception as e:
            logger.error(f"Erro ao buscar NCMs por palavras {palavras}: {e}")
            return []
    
    def _load_abc_farma_db(self) -> Dict:
        """Carrega dados da Tabela ABC Farma para identificação de medicamentos."""
        try:
            abc_farma_df = self.data_loader.load_abc_farma_gtin()
            if abc_farma_df is None or abc_farma_df.empty:
                logger.warning("Nenhum dado ABC Farma carregado")
                return {}
            
            # Criar índice por código de barras para busca rápida
            farma_by_gtin = {}
            
            for _, row in abc_farma_df.iterrows():
                codigo_barra = str(row.get('codigo_barra', '')).strip()
                descricao_completa = str(row.get('descricao_completa', '')).strip()
                marca = str(row.get('marca', '')).strip()
                categoria = str(row.get('categoria', '')).strip()
                
                if codigo_barra and codigo_barra != 'nan':
                    farma_by_gtin[codigo_barra] = {
                        'descricao_completa': descricao_completa,
                        'marca': marca,
                        'categoria': categoria,
                        'eh_medicamento': categoria.upper() == 'MEDICAMENTO'
                    }
            
            logger.info(f"Banco ABC Farma carregado: {len(farma_by_gtin)} produtos farmacêuticos")
            return farma_by_gtin
            
        except Exception as e:
            logger.error(f"Erro ao carregar banco ABC Farma: {e}")
            return {}
    
    def _initialize_vector_store(self):
        """Inicializa o banco vetorial se necessário."""
        try:
            faiss_index_path = Path(self.config.FAISS_INDEX_FILE)
            metadata_db_path = Path(self.config.METADATA_DB_FILE)
            
            if faiss_index_path.exists():
                logger.info("Carregando índice vetorial existente...")
                self.vector_store.load_index(str(faiss_index_path))
                self.vector_store.initialize_metadata_db(str(metadata_db_path))
                logger.info("Índice vetorial carregado com sucesso")
            else:
                logger.warning("Índice vetorial não encontrado. Execute o comando 'ingest' primeiro.")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar vector store: {e}")
            raise
    
    def ingest_knowledge(self) -> bool:
        """Executa o processo de ingestão e vetorização do conhecimento."""
        logger.info("Iniciando processo de ingestão...")
        
        try:
            # Inicializar banco de metadados
            metadata_db_path = Path(self.config.METADATA_DB_FILE)
            self.vector_store.initialize_metadata_db(str(metadata_db_path))
            
            # Carregar e processar produtos
            logger.info("Carregando produtos da base de dados...")
            produtos_df = self.data_loader.load_produtos_from_db()
            
            if produtos_df.empty:
                logger.warning("Nenhum produto encontrado na base de dados")
                return False
            
            chunker = TextChunker()
            chunks = chunker.chunk_produtos(produtos_df)
            
            if not chunks:
                logger.warning("Nenhum chunk foi criado dos produtos")
                return False
            
            logger.info(f"Criados {len(chunks)} chunks de produtos para vetorização")
            
            # Adicionar chunks ao banco vetorial
            self.vector_store.add_documents(chunks)
            
            # Salvar índice
            faiss_index_path = Path(self.config.FAISS_INDEX_FILE)
            self.vector_store.save_index(str(faiss_index_path))
            
            logger.info("Processo de ingestão concluído com sucesso!")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Arquivo não encontrado durante ingestão: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Erro de permissão durante ingestão: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado na ingestão: {e}")
            return False
    
    def _get_structured_context(self, ncm_candidate: str, produto_expandido: Dict = None) -> str:
        """Obtém contexto estruturado usando o serviço SQLite."""
        context_parts = []
        
        # Contexto NCM usando serviço SQLite
        if ncm_candidate:
            ncm_info = self.get_ncm_info(ncm_candidate)
            if ncm_info:
                context_parts.append(f"""
INFORMAÇÕES OFICIAIS NCM {ncm_candidate}:
- Descrição Oficial: {ncm_info.get('descricao_oficial', 'N/A')}
- Descrição Curta: {ncm_info.get('descricao_curta', 'N/A')}
- Nível Hierárquico: {ncm_info.get('nivel_hierarquico', 'N/A')}""")
                
                # Buscar CESTs associados
                cests = self.get_cests_for_ncm(ncm_candidate)
                if cests:
                    context_parts.append(f"\nCESTs Disponíveis para este NCM ({len(cests)} encontrados):")
                    for cest in cests[:5]:  # Limitar a 5 CESTs
                        tipo_relacao = cest.get('tipo_relacao', 'DIRETO')
                        confianca = cest.get('confianca', 1.0)
                        context_parts.append(f"- CEST {cest['codigo_cest']} ({tipo_relacao}, {confianca:.1f}): {cest['descricao_cest']}")
                
                # Buscar exemplos de produtos
                exemplos = self.get_product_examples(ncm_candidate, 3)
                if exemplos:
                    context_parts.append(f"\nExemplos de Produtos Classificados ({len(exemplos)} encontrados):")
                    for exemplo in exemplos:
                        qualidade = exemplo.get('qualidade_classificacao', 0.0)
                        context_parts.append(f"- {exemplo.get('descricao_produto', 'N/A')} (Qualidade: {qualidade:.1f})")
        
        # Contexto específico para medicamentos (ABC Farma)
        if produto_expandido:
            codigo_barra = produto_expandido.get('codigo_barra', '')
            if codigo_barra and codigo_barra in self.abc_farma_db:
                farma_info = self.abc_farma_db[codigo_barra]
                if farma_info['eh_medicamento']:
                    context_parts.append(f"""
IDENTIFICAÇÃO MEDICAMENTO (ABC Farma):
- Código de Barras: {codigo_barra}
- Descrição Completa: {farma_info['descricao_completa']}
- Marca: {farma_info['marca']}
- Categoria: {farma_info['categoria']}
- ATENÇÃO: Este produto é um MEDICAMENTO (Capítulo 30 NCM, Segmento 13 CEST)
- Para medicamentos, usar sempre CESTs da categoria 13.xxx.xx""")
            
            # Verificar se é medicamento por características expandidas
            expansion_data = produto_expandido.get('expansion_data', {})
            categoria = expansion_data.get('categoria_principal', '').lower()
            palavras_chave = ' '.join(expansion_data.get('palavras_chave_fiscais', [])).lower()
            
            if any(termo in categoria or termo in palavras_chave for termo in ['medicamento', 'farmaco', 'remedio', 'comprimido', 'capsula', 'xarope']):
                context_parts.append("""
INDICAÇÃO DE MEDICAMENTO DETECTADA:
- Este produto parece ser um medicamento baseado em suas características
- Medicamentos devem ser classificados no Capítulo 30 do NCM (30.xx.xx.xx)
- Para CEST, usar sempre o Segmento 13 (13.xxx.xx) para medicamentos""")
        
        if not context_parts:
            return "Nenhuma informação estruturada disponível para este NCM."
        
        return '\n'.join(context_parts)
    
    def _get_semantic_context(self, produto_text: str, ncm_filter: str = None, 
                             agente_nome: str = "sistema", produto_id: str = None) -> List[Dict]:
        """Obtém contexto semântico do banco vetorial com aprendizagem contínua e rastreamento."""
        import time
        
        # Registrar consulta RAG se o rastreamento estiver disponível
        consulta_id = None
        tempo_inicio = time.time()
        
        if self.consulta_metadados_service and produto_id:
            try:
                consulta_id = self.consulta_metadados_service.registrar_consulta(
                    produto_id=produto_id,
                    agente_nome=agente_nome,
                    tipo_consulta="rag",
                    query_original=produto_text[:1000],
                    banco_origem="faiss_vector",
                    metadados={"ncm_filter": ncm_filter} if ncm_filter else {}
                )
            except Exception as e:
                logger.warning(f"Erro ao registrar consulta RAG: {e}")
        
        try:
            # Usar aprendizagem contínua se disponível (Fase 5)
            if self.augmented_retrieval:
                results = self.augmented_retrieval.buscar_contexto_aumentado(
                    query=produto_text,
                    k_principal=3,
                    k_golden=2
                )
                
                # Adicionar marcadores para exemplos validados
                for result in results:
                    if result.get("fonte") == "golden_set":
                        result["text"] = f"[Exemplo Validado] {result['text']}"
                
                # Registrar resultado da consulta
                if consulta_id:
                    tempo_execucao = int((time.time() - tempo_inicio) * 1000)
                    
                    try:
                        self.consulta_metadados_service.registrar_resultados(
                            consulta_id=consulta_id,
                            resultados=results[:10],  # Limitar para não sobrecarregar
                            tempo_execucao_ms=tempo_execucao,
                            total_encontrados=len(results)
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao registrar resultado RAG: {e}")
                
                return results
            else:
                # Fallback para busca normal
                metadata_filter = {"ncm": ncm_filter} if ncm_filter else None
                results = self.vector_store.search(produto_text, k=5, metadata_filter=metadata_filter)
                
                # Registrar resultado da consulta normal
                if consulta_id:
                    tempo_execucao = int((time.time() - tempo_inicio) * 1000)
                    
                    try:
                        self.consulta_metadados_service.registrar_resultados(
                            consulta_id=consulta_id,
                            resultados=results[:10],  # Limitar para não sobrecarregar
                            tempo_execucao_ms=tempo_execucao,
                            total_encontrados=len(results)
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao registrar resultado RAG: {e}")
                
                return results
                
        except AttributeError as e:
            logger.error(f"Erro de atributo na busca semântica: {e}")
            return []
        except ValueError as e:
            logger.error(f"Erro de valor na busca semântica: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado na busca semântica: {e}")
            # Fallback para busca normal em caso de erro
            try:
                metadata_filter = {"ncm": ncm_filter} if ncm_filter else None
                results = self.vector_store.search(produto_text, k=5, metadata_filter=metadata_filter)
                return results
            except Exception:
                logger.error("Falha completa na busca semântica, retornando lista vazia")
                return []
    
    def _calcular_qualidade_rag(self, results: List[Dict], query: str) -> float:
        """Calcula score de qualidade baseado nos resultados RAG."""
        if not results:
            return 0.0
        
        try:
            # Fatores de qualidade:
            # 1. Score médio dos resultados (0.4)
            # 2. Número de resultados encontrados (0.3) 
            # 3. Diversidade de fontes (0.3)
            
            # Score médio dos resultados
            scores = [r.get("score", 0) for r in results]
            score_medio = sum(scores) / len(scores) if scores else 0
            
            # Normalizar para 0-1 (scores podem ser negativos ou > 1)
            score_normalizado = max(0, min(1, (score_medio + 1) / 2))
            
            # Quantidade de resultados (normalizado para 1-5 resultados)
            fator_quantidade = min(1.0, len(results) / 5.0)
            
            # Diversidade de fontes (diferentes NCMs, categorias)
            ncms_unicos = set()
            for result in results:
                ncm = result.get("metadata", {}).get("ncm", "")
                if ncm:
                    ncms_unicos.add(ncm)
            
            fator_diversidade = min(1.0, len(ncms_unicos) / 3.0) if ncms_unicos else 0.5
            
            # Score final ponderado
            qualidade_final = (
                score_normalizado * 0.4 +
                fator_quantidade * 0.3 +
                fator_diversidade * 0.3
            )
            
            return round(qualidade_final, 3)
            
        except Exception as e:
            logger.warning(f"Erro ao calcular qualidade RAG: {e}")
            return 0.5  # Score neutro em caso de erro
    
    @contextmanager
    def _safe_agent_execution(self, agent_name: str):
        """Context manager para execução segura de agentes."""
        try:
            logger.debug(f"Iniciando execução do {agent_name}")
            yield
            logger.debug(f"Execução do {agent_name} concluída com sucesso")
        except Exception as e:
            logger.error(f"Erro na execução do {agent_name}: {e}")
            raise
    
    def cleanup_resources(self) -> None:
        """Limpa recursos e conexões abertas."""
        try:
            # Limpar cache
            self.classification_cache.clear()
            logger.info("Cache limpo")
            
            # Fechar conexões do vector store se necessário
            if hasattr(self.vector_store, 'close'):
                self.vector_store.close()
                logger.info("Vector store fechado")
                
            # Fechar conexões do LLM client se necessário
            if hasattr(self.llm_client, 'close'):
                self.llm_client.close()
                logger.info("LLM client fechado")
                
        except Exception as e:
            logger.error(f"Erro durante limpeza de recursos: {e}")
    
    def classify_products(self, produtos: List[Dict]) -> List[Dict]:
        """
        Classifica uma lista de produtos usando a arquitetura agêntica híbrida.
        
        Args:
            produtos: Lista de produtos com pelo menos 'descricao_produto'
            
        Returns:
            Lista de produtos classificados com NCM/CEST e traces de auditoria
        """
        print(f"🎯 INICIANDO CLASSIFICAÇÃO DE {len(produtos)} PRODUTOS...")
        
        # Inicializar vector store
        self._initialize_vector_store()
        
        try:
            # ========================================================================
            # ETAPA 1: EXPANSÃO DE DESCRIÇÕES
            # ========================================================================
            print("🔍 Etapa 1: Expandindo descrições dos produtos...")
            produtos_expandidos = []
            
            for i, produto in enumerate(produtos):
                print(f"   Processando produto {i+1}/{len(produtos)}")
                descricao = produto.get('descricao_produto', '')
                expansion_result = self.expansion_agent.run(descricao)
                
                # Criar produto expandido mantendo todos os campos originais + dados de expansão
                produto_expandido = produto.copy()
                expansion_data = expansion_result['result']
                produto_expandido['descricao_expandida'] = expansion_data.get('descricao_expandida', descricao)
                produto_expandido['expansion_data'] = expansion_data  # Guardar dados completos da expansão
                produtos_expandidos.append(produto_expandido)
            
            print(f"✅ {len(produtos_expandidos)} produtos expandidos.")
            
            # ========================================================================
            # ETAPA 2: AGREGAÇÃO INTELIGENTE  
            # ========================================================================
            print("🎲 Etapa 2: Agrupando produtos similares...")
            aggregation_result = self.aggregation_agent.run(produtos_expandidos)
            grupos = aggregation_result['grupos']
            
            print(f"✅ {len(produtos)} produtos agrupados em {len(grupos)} grupos.")
            print(f"📊 Redução de processamento: {aggregation_result['estatisticas'].get('taxa_duplicacao', 0)*100:.1f}%")
            
            # ========================================================================
            # ETAPA 3: CLASSIFICAÇÃO DOS REPRESENTANTES
            # ========================================================================
            print("🧠 Etapa 3: Classificando representantes de cada grupo...")
            
            for i, grupo in enumerate(grupos):
                print(f"   Processando grupo {i+1}/{len(grupos)} (produtos: {len(grupo['produtos'])})")
                
                # Usar o representante do grupo
                produto_expandido = grupo['representante']
                if not produto_expandido:
                    continue
                
                # Obter contextos híbridos
                expansion_data = produto_expandido.get('expansion_data', {})
                palavras_chave = expansion_data.get('palavras_chave_fiscais', [])
                produto_text = f"{produto_expandido.get('descricao_expandida', '')} {' '.join(palavras_chave)}"
                
                # Contexto estruturado (tentar alguns NCMs candidatos comuns)
                structured_context = "Nenhum contexto estruturado específico disponível."
                
                # Contexto semântico com rastreamento
                representante_id = produto_expandido.get('id', produto_expandido.get('produto_id', 0))
                semantic_context = self._get_semantic_context(
                    produto_text, 
                    agente_nome="aggregation", 
                    produto_id=str(representante_id)
                )
                
                context = {
                    "structured_context": structured_context,
                    "semantic_context": semantic_context
                }
                
                # Classificar NCM
                try:
                    ncm_result = self.ncm_agent.run(produto_expandido, context)
                except Exception as e:
                    print(f"❌ ERRO no NCM Agent: {e}")
                    continue
                
                # Atualizar contexto estruturado com NCM determinado
                ncm_determinado = ncm_result['result'].get('ncm_recomendado', '')
                context['structured_context'] = self._get_structured_context(ncm_determinado, produto_expandido)
                
                # Classificar CEST
                try:
                    cest_result = self.cest_agent.run(produto_expandido, ncm_result['result'], context)
                except Exception as e:
                    print(f"❌ ERRO no CEST Agent: {e}")
                    continue
                
                # Reconciliar
                try:
                    reconciliation_result = self.reconciler_agent.run(
                        produto_expandido, 
                        ncm_result['result'], 
                        cest_result['result'], 
                        context
                    )
                except Exception as e:
                    print(f"❌ ERRO no Reconciler Agent: {e}")
                    continue
                
                # Armazenar no cache usando o ID do grupo
                cache_key = grupo['id']
                self.classification_cache[cache_key] = {
                    'expansion': None,  # Já foi processado na etapa 1
                    'ncm': ncm_result,
                    'cest': cest_result,
                    'reconciliation': reconciliation_result,
                    'context_used': context
                }
                
                # Gerenciar tamanho do cache
                self._manage_cache_size()
            
            # ========================================================================
            # ETAPA 4: PROPAGAÇÃO DOS RESULTADOS
            # ========================================================================
            print("📤 Etapa 4: Propagando resultados para todos os produtos...")
            
            resultados_finais = []
            
            for i, produto in enumerate(produtos):
                # Encontrar o grupo deste produto baseado nos índices originais
                grupo_do_produto = None
                for grupo in grupos:
                    if i in grupo['indices_originais']:
                        grupo_do_produto = grupo
                        break
                
                if grupo_do_produto and grupo_do_produto['id'] in self.classification_cache:
                    cached_result = self.classification_cache[grupo_do_produto['id']]
                    classificacao = cached_result['reconciliation']['result']['classificacao_final']
                    auditoria = cached_result['reconciliation']['result']['auditoria']
                    
                    # Verificar se este produto é o representante
                    representante_produto = grupo_do_produto['representante']
                    eh_representante = False
                    if representante_produto and 'id' in produto and 'id' in representante_produto:
                        eh_representante = produto['id'] == representante_produto['id']
                    
                    resultado_produto = {
                        **produto,  # Dados originais do produto
                        'ncm_classificado': classificacao['ncm'],
                        'cest_classificado': classificacao['cest'],
                        'confianca_consolidada': classificacao['confianca_consolidada'],
                        'grupo_id': grupo_do_produto['id'],
                        'eh_representante': eh_representante,
                        'auditoria': auditoria,
                        'justificativa': cached_result['reconciliation']['result']['justificativa_final']
                    }
                    
                    resultados_finais.append(resultado_produto)
                else:
                    # Fallback para produto não agrupado
                    resultados_finais.append({
                        **produto,
                        'ncm_classificado': '00000000',
                        'cest_classificado': None,
                        'confianca_consolidada': 0.0,
                        'grupo_id': -1,
                        'eh_representante': False,
                        'auditoria': {'consistente': False, 'alertas': ['Produto não foi agrupado corretamente']},
                        'justificativa': 'Produto não foi processado corretamente'
                    })
            
            print(f"✅ CLASSIFICAÇÃO CONCLUÍDA! {len(resultados_finais)} produtos processados.")
            
            return resultados_finais
            
        except Exception as e:
            print(f"❌ ERRO GRAVE na classificação: {e}")
            # Retornar produtos com erro
            return [{
                **produto,
                'ncm_classificado': '00000000',
                'cest_classificado': None,
                'confianca_consolidada': 0.0,
                'erro': str(e)
            } for produto in produtos]
    
    def classify_product_with_explanations(self, produto: Dict[str, Any], salvar_explicacoes: bool = True) -> Dict[str, Any]:
        """
        Classifica um único produto com explicações detalhadas de cada agente.
        
        Args:
            produto: Dados do produto a ser classificado
            salvar_explicacoes: Se deve salvar as explicações no banco de dados
            
        Returns:
            Dict com classificação e explicações detalhadas de cada agente
        """
        import uuid
        sessao_id = str(uuid.uuid4())
        produto_id = produto.get('id', produto.get('produto_id', 0))
        
        print(f"🎯 CLASSIFICANDO PRODUTO COM EXPLICAÇÕES: {produto.get('descricao_produto', 'N/A')}")
        
        # Obter contexto da empresa se disponível
        contexto_empresa = None
        if self.empresa_contexto_service:
            try:
                contexto_empresa = self.empresa_contexto_service.obter_contexto_empresa()
                if contexto_empresa:
                    print(f"🏢 CONTEXTO EMPRESA APLICADO: {contexto_empresa.get('tipo_atividade', 'N/A')}")
                    if contexto_empresa.get('cest_especifico_aplicavel'):
                        print(f"📋 CEST ESPECÍFICO PARA ATIVIDADE: {contexto_empresa.get('cest_especifico_aplicavel')}")
            except Exception as e:
                logger.warning(f"Erro ao obter contexto da empresa: {e}")
        
        # Inicializar vector store
        self._initialize_vector_store()
        
        # Configurar rastreamento de consultas em todos os agentes
        if self.consulta_metadados_service:
            try:
                self.expansion_agent.configurar_rastreamento_consultas(
                    self.consulta_metadados_service, str(produto_id)
                )
                self.aggregation_agent.configurar_rastreamento_consultas(
                    self.consulta_metadados_service, str(produto_id)
                )
                self.ncm_agent.configurar_rastreamento_consultas(
                    self.consulta_metadados_service, str(produto_id)
                )
                self.cest_agent.configurar_rastreamento_consultas(
                    self.consulta_metadados_service, str(produto_id)
                )
                self.reconciler_agent.configurar_rastreamento_consultas(
                    self.consulta_metadados_service, str(produto_id)
                )
                logger.info(f"Rastreamento de consultas configurado para produto {produto_id}")
            except Exception as e:
                logger.warning(f"Erro ao configurar rastreamento: {e}")
        
        try:
            # ========================================================================
            # ETAPA 1: EXPANSÃO COM EXPLICAÇÃO
            # ========================================================================
            print("🔍 Etapa 1: Expandindo descrição com explicação...")
            descricao = produto.get('descricao_produto', '')
            
            # Preparar contexto inicial com empresa se disponível
            contexto_inicial = {"produto_id": produto_id}
            if contexto_empresa:
                contexto_inicial["empresa_contexto"] = contexto_empresa
                if self.empresa_contexto_service:
                    contexto_inicial = self.empresa_contexto_service.aplicar_contexto_agente(
                        contexto_inicial, "expansion", produto
                    )
            
            # Ativar explicações no agente
            self.expansion_agent.iniciar_explicacao(descricao, contexto_inicial)
            expansion_result = self.expansion_agent.run(descricao)
            
            # Finalizar explicação com detalhes específicos
            explicacao_expansao = f"""
            ANÁLISE DE EXPANSÃO:
            - Descrição original: {descricao}
            - Características identificadas: {expansion_result.get('result', {}).get('caracteristicas_tecnicas', 'N/A')}
            - Palavras-chave fiscais extraídas: {expansion_result.get('result', {}).get('palavras_chave_fiscais', 'N/A')}
            - Material predominante: {expansion_result.get('result', {}).get('material_predominante', 'N/A')}
            - Categoria do produto: {expansion_result.get('result', {}).get('categoria_produto', 'N/A')}
            {f"- Contexto empresa considerado: {contexto_empresa.get('tipo_atividade', 'N/A')}" if contexto_empresa else ""}
            """
            
            expansion_result = self.expansion_agent.finalizar_explicacao(
                expansion_result,
                explicacao_expansao,
                "Expansão semântica baseada em análise de características e contexto do produto",
                expansion_result.get('result', {}).get('confianca', 0.0)
            )
            
            # Salvar explicação se solicitado
            if salvar_explicacoes and self.explicacao_service:
                self.explicacao_service.salvar_explicacao_agente(
                    produto_id, 
                    expansion_result.get('explicacao_agente', {}),
                    sessao_classificacao=sessao_id
                )
            
            # ========================================================================
            # ETAPA 2: AGREGAÇÃO (SIMPLIFICADA PARA UM PRODUTO)
            # ========================================================================
            print("🎲 Etapa 2: Análise de agregação...")
            
            # Preparar contexto para agregação
            contexto_agregacao = {"produto_id": produto_id}
            if contexto_empresa:
                contexto_agregacao["empresa_contexto"] = contexto_empresa
                if self.empresa_contexto_service:
                    contexto_agregacao = self.empresa_contexto_service.aplicar_contexto_agente(
                        contexto_agregacao, "aggregation", produto
                    )
            
            self.aggregation_agent.iniciar_explicacao([produto], contexto_agregacao)
            aggregation_result = self.aggregation_agent.run([produto])
            
            explicacao_agregacao = f"""
            ANÁLISE DE AGREGAÇÃO:
            - Produto processado individualmente
            - Verificação de similaridade com base de conhecimento
            - Contexto enriquecido com dados expandidos
            """
            
            aggregation_result = self.aggregation_agent.finalizar_explicacao(
                aggregation_result,
                explicacao_agregacao,
                "Análise de similaridade e contexto para classificação individualizada",
                0.8  # Alta confiança para processamento individual
            )
            
            if salvar_explicacoes and self.explicacao_service:
                self.explicacao_service.salvar_explicacao_agente(
                    produto_id,
                    aggregation_result.get('explicacao_agente', {}),
                    sessao_classificacao=sessao_id
                )
            
            # ========================================================================
            # ETAPA 3: CLASSIFICAÇÃO NCM COM EXPLICAÇÃO
            # ========================================================================
            print("🧠 Etapa 3: Classificação NCM com explicação...")
            
            # Preparar contexto enriquecido
            expansion_data = expansion_result.get('result', {})
            palavras_chave = expansion_data.get('palavras_chave_fiscais', [])
            produto_text = f"{expansion_data.get('descricao_expandida', descricao)} {' '.join(palavras_chave)}"
            
            # Contexto semântico com rastreamento
            semantic_context = self._get_semantic_context(
                produto_text, 
                agente_nome="ncm", 
                produto_id=str(produto_id)
            )
            
            context = {
                "structured_context": "Classificação individual - contexto específico será determinado",
                "semantic_context": semantic_context,
                "expansion_data": expansion_data
            }
            
            # Aplicar contexto da empresa ao NCM se disponível
            if contexto_empresa:
                context["empresa_contexto"] = contexto_empresa
                if self.empresa_contexto_service:
                    context = self.empresa_contexto_service.aplicar_contexto_agente(
                        context, "ncm", produto
                    )
            
            # Classificar NCM com explicação
            self.ncm_agent.iniciar_explicacao(produto, context)
            ncm_result = self.ncm_agent.run(produto, context)
            
            ncm_data = ncm_result.get('result', {})
            explicacao_ncm = f"""
            CLASSIFICAÇÃO NCM:
            - NCM recomendado: {ncm_data.get('ncm_recomendado', 'N/A')}
            - Confiança: {ncm_data.get('confianca', 0.0)}
            - Justificativa: {ncm_data.get('justificativa', 'N/A')}
            - Capítulo NCM: {ncm_data.get('capitulo_ncm', 'N/A')}
            - Palavras-chave utilizadas: {', '.join(palavras_chave)}
            - Produtos similares consultados: {len(semantic_context) if isinstance(semantic_context, list) else 0} encontrados
            """
            
            ncm_result = self.ncm_agent.finalizar_explicacao(
                ncm_result,
                explicacao_ncm,
                f"Classificação fiscal NCM baseada em análise técnica e semântica do produto",
                ncm_data.get('confianca', 0.0)
            )
            
            if salvar_explicacoes and self.explicacao_service:
                self.explicacao_service.salvar_explicacao_agente(
                    produto_id,
                    ncm_result.get('explicacao_agente', {}),
                    sessao_classificacao=sessao_id
                )
            
            # ========================================================================
            # ETAPA 4: CLASSIFICAÇÃO CEST COM EXPLICAÇÃO
            # ========================================================================
            print("📋 Etapa 4: Classificação CEST com explicação...")
            
            # Atualizar contexto com NCM determinado
            ncm_determinado = ncm_data.get('ncm_recomendado', '')
            context['structured_context'] = self._get_structured_context(ncm_determinado, produto)
            
            # Aplicar contexto da empresa ao CEST (mais importante aqui)
            if contexto_empresa:
                context["empresa_contexto"] = contexto_empresa
                if self.empresa_contexto_service:
                    context = self.empresa_contexto_service.aplicar_contexto_agente(
                        context, "cest", produto
                    )
                    # Log especial para CEST específico de atividade
                    if contexto_empresa.get('cest_especifico_aplicavel'):
                        print(f"🎯 APLICANDO CEST ESPECÍFICO POR ATIVIDADE: {contexto_empresa.get('cest_especifico_aplicavel')}")
            
            self.cest_agent.iniciar_explicacao(produto, context)
            cest_result = self.cest_agent.run(produto, ncm_data, context)
            
            cest_data = cest_result.get('result', {})
            explicacao_cest = f"""
            CLASSIFICAÇÃO CEST:
            - CEST recomendado: {cest_data.get('cest_recomendado', 'N/A')}
            - Confiança: {cest_data.get('confianca', 0.0)}
            - Justificativa: {cest_data.get('justificativa', 'N/A')}
            - NCM base utilizado: {ncm_determinado}
            - Aplicável à substituição tributária: {cest_data.get('aplicavel_st', 'N/A')}
            {f"- Contexto empresa aplicado: {contexto_empresa.get('tipo_atividade', 'N/A')}" if contexto_empresa else ""}
            {f"- CEST específico por atividade: {contexto_empresa.get('cest_especifico_aplicavel', 'N/A')}" if contexto_empresa and contexto_empresa.get('cest_especifico_aplicavel') else ""}
            """
            
            cest_result = self.cest_agent.finalizar_explicacao(
                cest_result,
                explicacao_cest,
                f"Classificação CEST baseada no NCM {ncm_determinado} e características do produto",
                cest_data.get('confianca', 0.0)
            )
            
            if salvar_explicacoes and self.explicacao_service:
                self.explicacao_service.salvar_explicacao_agente(
                    produto_id,
                    cest_result.get('explicacao_agente', {}),
                    sessao_classificacao=sessao_id
                )
            
            # ========================================================================
            # ETAPA 5: RECONCILIAÇÃO COM EXPLICAÇÃO
            # ========================================================================
            print("🔄 Etapa 5: Reconciliação final com explicação...")
            
            # Aplicar contexto da empresa na reconciliação
            if contexto_empresa:
                context["empresa_contexto"] = contexto_empresa
                if self.empresa_contexto_service:
                    context = self.empresa_contexto_service.aplicar_contexto_agente(
                        context, "reconciler", produto
                    )
            
            self.reconciler_agent.iniciar_explicacao(produto, context)
            reconciliation_result = self.reconciler_agent.run(produto, ncm_data, cest_data, context)
            
            reconciliation_data = reconciliation_result.get('result', {})
            classificacao_final = reconciliation_data.get('classificacao_final', {})
            
            explicacao_reconciliacao = f"""
            RECONCILIAÇÃO FINAL:
            - NCM final: {classificacao_final.get('ncm', 'N/A')}
            - CEST final: {classificacao_final.get('cest', 'N/A')}
            - Confiança consolidada: {classificacao_final.get('confianca_consolidada', 0.0)}
            - Consistência dos agentes: {reconciliation_data.get('auditoria', {}).get('consistente', False)}
            - Conflitos detectados: {len(reconciliation_data.get('auditoria', {}).get('conflitos_identificados', []))}
            - Ajustes realizados: {len(reconciliation_data.get('auditoria', {}).get('ajustes_realizados', []))}
            {f"- Contexto empresa considerado: {contexto_empresa.get('tipo_atividade', 'N/A')}" if contexto_empresa else ""}
            {f"- CEST aplicado por atividade específica: {contexto_empresa.get('cest_especifico_aplicavel', 'N/A')}" if contexto_empresa and contexto_empresa.get('cest_especifico_aplicavel') else ""}
            """
            
            reconciliation_result = self.reconciler_agent.finalizar_explicacao(
                reconciliation_result,
                explicacao_reconciliacao,
                f"Análise final de consistência e consolidação das classificações dos agentes especializados",
                classificacao_final.get('confianca_consolidada', 0.0)
            )
            
            if salvar_explicacoes and self.explicacao_service:
                self.explicacao_service.salvar_explicacao_agente(
                    produto_id,
                    reconciliation_result.get('explicacao_agente', {}),
                    sessao_classificacao=sessao_id
                )
            
            # ========================================================================
            # RESULTADO FINAL COM TODAS AS EXPLICAÇÕES
            # ========================================================================
            resultado_final = {
                **produto,  # Dados originais do produto
                'ncm_classificado': classificacao_final.get('ncm', '00000000'),
                'cest_classificado': classificacao_final.get('cest'),
                'confianca_consolidada': classificacao_final.get('confianca_consolidada', 0.0),
                'justificativa_final': reconciliation_data.get('justificativa_final', ''),
                'auditoria': reconciliation_data.get('auditoria', {}),
                'sessao_classificacao': sessao_id,
                
                # Contexto da empresa aplicado
                'contexto_empresa_aplicado': contexto_empresa if contexto_empresa else None,
                
                # Explicações detalhadas de cada agente
                'explicacoes_agentes': {
                    'expansao': expansion_result.get('explicacao_agente', {}),
                    'agregacao': aggregation_result.get('explicacao_agente', {}),
                    'ncm': ncm_result.get('explicacao_agente', {}),
                    'cest': cest_result.get('explicacao_agente', {}),
                    'reconciliacao': reconciliation_result.get('explicacao_agente', {})
                }
            }
            
            print(f"✅ CLASSIFICAÇÃO COM EXPLICAÇÕES CONCLUÍDA!")
            print(f"📊 NCM: {resultado_final['ncm_classificado']}")
            print(f"📊 CEST: {resultado_final['cest_classificado']}")
            print(f"📊 Confiança: {resultado_final['confianca_consolidada']:.3f}")
            
            return resultado_final
            
        except Exception as e:
            print(f"❌ ERRO na classificação com explicações: {e}")
            return {
                **produto,
                'ncm_classificado': '00000000',
                'cest_classificado': None,
                'confianca_consolidada': 0.0,
                'erro': str(e),
                'explicacoes_agentes': {}
            }