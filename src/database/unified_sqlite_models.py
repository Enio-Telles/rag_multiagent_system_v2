"""
Modelos SQLite Unificados para todo o sistema RAG Multiagente
Integra: Knowledge Base + Classificações + Golden Set + Explicações + Métricas
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Index, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
import json

# Base unificada para todos os modelos
UnifiedBase = declarative_base()

# Tipo JSON para SQLite
class JsonType(JSON):
    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(Text())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'sqlite':
            return json.dumps(value) if value is not None else None
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'sqlite' and value is not None:
            return json.loads(value)
        return value

# =======================
# KNOWLEDGE BASE MODELS
# =======================

class NCMHierarchy(UnifiedBase):
    """Hierarquia NCM completa com estrutura otimizada"""
    __tablename__ = "ncm_hierarchy"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_ncm = Column(String(8), nullable=False, unique=True, index=True)
    descricao_oficial = Column(Text, nullable=False)
    descricao_curta = Column(String(200))
    nivel_hierarquico = Column(Integer, nullable=False)
    codigo_pai = Column(String(8), index=True)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    cests = relationship("NCMCestMapping", back_populates="ncm")
    exemplos = relationship("ProdutoExemplo", back_populates="ncm")
    
    __table_args__ = (
        Index('idx_ncm_hierarquia', 'codigo_ncm', 'nivel_hierarquico'),
        Index('idx_ncm_pai', 'codigo_pai', 'nivel_hierarquico'),
    )

class CestCategory(UnifiedBase):
    """Categorias CEST com relacionamentos completos"""
    __tablename__ = "cest_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_cest = Column(String(10), nullable=False, unique=True, index=True)
    descricao_cest = Column(Text, nullable=False)
    descricao_resumida = Column(String(200))
    categoria_produto = Column(String(100))
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamentos
    ncm_mappings = relationship("NCMCestMapping", back_populates="cest")

class NCMCestMapping(UnifiedBase):
    """Mapeamento NCM-CEST otimizado"""
    __tablename__ = "ncm_cest_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    ncm_codigo = Column(String(8), ForeignKey('ncm_hierarchy.codigo_ncm'), nullable=False, index=True)
    cest_codigo = Column(String(10), ForeignKey('cest_categories.codigo_cest'), nullable=False, index=True)
    tipo_relacao = Column(String(20), default='DIRETO')
    confianca_mapeamento = Column(Float, default=1.0)
    fonte_dados = Column(String(50))
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamentos
    ncm = relationship("NCMHierarchy", back_populates="cests")
    cest = relationship("CestCategory", back_populates="ncm_mappings")
    
    __table_args__ = (
        Index('idx_ncm_cest', 'ncm_codigo', 'cest_codigo'),
        Index('idx_ncm_ativo', 'ncm_codigo', 'ativo'),
    )

class ProdutoExemplo(UnifiedBase):
    """Produtos exemplo para cada NCM"""
    __tablename__ = "produtos_exemplos"
    
    id = Column(Integer, primary_key=True, index=True)
    ncm_codigo = Column(String(8), ForeignKey('ncm_hierarchy.codigo_ncm'), nullable=False, index=True)
    gtin = Column(String(14), index=True)
    descricao_produto = Column(Text, nullable=False)
    marca = Column(String(100))
    modelo = Column(String(100))
    categoria_produto = Column(String(100))
    material_predominante = Column(String(100))
    aplicacao_uso = Column(Text)
    fonte_dados = Column(String(50))
    qualidade_classificacao = Column(Float, default=0.0)
    verificado_humano = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamento
    ncm = relationship("NCMHierarchy", back_populates="exemplos")
    
    __table_args__ = (
        Index('idx_produto_ncm', 'ncm_codigo', 'ativo'),
        Index('idx_produto_gtin', 'gtin'),
        Index('idx_produto_categoria', 'categoria_produto'),
        Index('idx_exemplo_classificacao', 'qualidade_classificacao'),
    )

# =======================
# ABC FARMA DATABASE  
# =======================

class ABCFarmaProduct(UnifiedBase):
    """Base de dados ABC Farma para produtos farmacêuticos"""
    __tablename__ = "abc_farma_products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação do produto
    codigo_barra = Column(String(20), nullable=False, unique=True, index=True)
    gtin = Column(String(20), index=True)  # GTIN pode ser diferente do código de barras
    
    # Descrições do produto
    descricao_completa = Column(Text, nullable=False)
    descricao1 = Column(String(500))  # Descrição principal
    descricao2 = Column(String(500))  # Descrição secundária
    descricao_comercial = Column(String(500))
    
    # Informações farmacêuticas
    marca = Column(String(200), index=True)
    laboratorio = Column(String(200), index=True)
    categoria = Column(String(100), index=True)
    categoria_terapeutica = Column(String(200))
    principio_ativo = Column(String(500))
    concentracao = Column(String(200))
    forma_farmaceutica = Column(String(100))
    via_administracao = Column(String(100))
    
    # Embalagem e apresentação
    apresentacao = Column(String(300))
    unidade_medida = Column(String(50))
    quantidade_embalagem = Column(Integer)
    tipo_embalagem = Column(String(100))
    
    # Classificação fiscal
    ncm_farmaceutico = Column(String(15), default="30049099", index=True)
    cest_farmaceutico = Column(String(15), default="13.001.00", index=True)
    
    # Informações regulatórias
    registro_anvisa = Column(String(50))
    codigo_ean = Column(String(20))
    codigo_dci = Column(String(50))
    
    # Embedding para busca semântica
    embedding_descricao = Column(LargeBinary)  # Vetor de embeddings
    embedding_principio_ativo = Column(LargeBinary)
    
    # Metadados do sistema
    fonte_dados = Column(String(50), default="ABC_FARMA")
    confiabilidade_dados = Column(Float, default=1.0)
    data_cadastro = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, default=True)
    
    # Controle de qualidade
    validado_farmaceutico = Column(Boolean, default=False)
    observacoes = Column(Text)
    tags_busca = Column(JsonType)  # Tags adicionais para busca
    
    # Métricas de uso
    vezes_consultado = Column(Integer, default=0)
    ultima_consulta = Column(DateTime)
    usado_como_referencia = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_abc_farma_marca', 'marca'),
        Index('idx_abc_farma_categoria', 'categoria'),
        Index('idx_abc_farma_principio', 'principio_ativo'),
        Index('idx_abc_farma_lab', 'laboratorio'),
        Index('idx_abc_farma_ncm_cest', 'ncm_farmaceutico', 'cest_farmaceutico'),
        Index('idx_abc_farma_descricao', 'descricao1', 'descricao2'),
        Index('idx_abc_farma_busca', 'ativo', 'validado_farmaceutico'),
    )

# =======================
# CLASSIFICAÇÃO E REVISÃO
# =======================

class ClassificacaoRevisao(UnifiedBase):
    """Classificações de produtos com sistema de revisão humana"""
    __tablename__ = "classificacoes_revisao"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, nullable=False, index=True)
    descricao_produto = Column(Text, nullable=False)
    descricao_completa = Column(Text)
    codigo_produto = Column(String(100))
    
    # Código de barras
    codigo_barra = Column(String(50))
    codigo_barra_status = Column(String(20), default="PENDENTE_VERIFICACAO")
    codigo_barra_corrigido = Column(String(50))
    codigo_barra_observacoes = Column(Text)
    
    # GTIN (compatibilidade)
    gtin_original = Column(String(50))
    gtin_status = Column(String(20), default="NAO_VERIFICADO")
    gtin_corrigido = Column(String(50))
    gtin_observacoes = Column(Text)
    
    # Classificações
    ncm_original = Column(String(15))
    cest_original = Column(String(15))
    ncm_sugerido = Column(String(15))
    cest_sugerido = Column(String(15))
    confianca_sugerida = Column(Float)
    justificativa_sistema = Column(Text)
    
    # Revisão humana
    status_revisao = Column(String(20), default="PENDENTE_REVISAO", index=True)
    ncm_corrigido = Column(String(15))
    cest_corrigido = Column(String(15))
    justificativa_correcao = Column(Text)
    revisado_por = Column(String(100))
    data_revisao = Column(DateTime)
    
    # Metadados
    data_classificacao = Column(DateTime, default=func.now())
    data_criacao = Column(DateTime, default=func.now())
    dados_trace_json = Column(JsonType)
    
    # Explicações dos agentes
    explicacao_agente_expansao = Column(Text)
    explicacao_agente_ncm = Column(Text)
    explicacao_agente_cest = Column(Text)
    explicacao_agente_reconciliador = Column(Text)
    
    # Análise de qualidade
    tempo_revisao_segundos = Column(Integer)
    complexidade_produto = Column(String(20))
    
    # Relacionamentos
    explicacoes = relationship("ExplicacaoAgente", back_populates="classificacao")
    
    __table_args__ = (
        Index('idx_classificacao_status', 'status_revisao', 'data_criacao'),
        Index('idx_classificacao_produto', 'produto_id'),
        Index('idx_classificacao_ncm', 'ncm_original', 'ncm_sugerido'),
    )

# =======================
# GOLDEN SET
# =======================

class GoldenSetEntry(UnifiedBase):
    """Golden Set - Classificações validadas por humanos"""
    __tablename__ = "golden_set"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, nullable=False, index=True)
    descricao_produto = Column(Text, nullable=False)
    descricao_completa = Column(Text)
    codigo_produto = Column(String(100))
    gtin_validado = Column(String(50))
    
    # Classificação final validada
    ncm_final = Column(String(15), nullable=False)
    cest_final = Column(String(15))
    confianca_original = Column(Float)
    
    # Metadados da validação
    fonte_validacao = Column(String(20), default="HUMANA")
    justificativa_inclusao = Column(Text)
    revisado_por = Column(String(100))
    data_adicao = Column(DateTime, default=func.now())
    
    # Status e controle
    ativo = Column(Boolean, default=True)
    qualidade_score = Column(Float)
    vezes_usado = Column(Integer, default=0)
    embedding_atualizado = Column(Boolean, default=False)
    ultima_utilizacao = Column(DateTime)
    
    # Explicações para aprendizagem
    explicacao_expansao = Column(Text)
    explicacao_agregacao = Column(Text)
    explicacao_ncm = Column(Text)
    explicacao_cest = Column(Text)
    explicacao_reconciliacao = Column(Text)
    
    # Dados enriquecidos
    palavras_chave_fiscais = Column(Text)
    categoria_produto = Column(String(100))
    material_predominante = Column(String(100))
    aplicacoes_uso = Column(Text)
    caracteristicas_tecnicas = Column(Text)
    contexto_uso = Column(Text)
    similaridade_produtos = Column(Text)
    
    __table_args__ = (
        Index('idx_golden_set_ncm', 'ncm_final', 'ativo'),
        Index('idx_golden_set_qualidade', 'qualidade_score', 'ativo'),
        Index('idx_golden_set_uso', 'vezes_usado', 'ultima_utilizacao'),
    )

# =======================
# EXPLICAÇÕES DOS AGENTES
# =======================

class ExplicacaoAgente(UnifiedBase):
    """Explicações detalhadas de cada agente"""
    __tablename__ = "explicacoes_agentes"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, nullable=False, index=True)
    classificacao_id = Column(Integer, ForeignKey('classificacoes_revisao.id'), index=True)
    
    # Identificação do agente
    agente_nome = Column(String(50), nullable=False)
    agente_versao = Column(String(20), default="1.0")
    
    # Dados de entrada
    input_original = Column(Text)
    contexto_utilizado = Column(JsonType)
    
    # Processamento
    etapas_processamento = Column(JsonType)
    palavras_chave_identificadas = Column(Text)
    produtos_similares_encontrados = Column(JsonType)
    
    # Resultado
    resultado_agente = Column(JsonType)
    explicacao_detalhada = Column(Text)
    justificativa_tecnica = Column(Text)
    nivel_confianca = Column(Float)
    
    # Uso de conhecimento
    rag_consultado = Column(Boolean, default=False)
    golden_set_utilizado = Column(Boolean, default=False)
    base_ncm_consultada = Column(Boolean, default=False)
    exemplos_utilizados = Column(JsonType)
    
    # Metadados de execução
    tempo_processamento_ms = Column(Integer)
    memoria_utilizada_mb = Column(Float)
    tokens_llm_utilizados = Column(Integer)
    data_execucao = Column(DateTime, default=func.now())
    sessao_classificacao = Column(String(100))
    
    # Qualidade e feedback
    qualidade_explicacao = Column(Float)
    feedback_humano = Column(Text)
    marcado_para_melhoria = Column(Boolean, default=False)
    
    # Relacionamento
    classificacao = relationship("ClassificacaoRevisao", back_populates="explicacoes")
    
    __table_args__ = (
        Index('idx_explicacao_agente', 'agente_nome', 'data_execucao'),
        Index('idx_explicacao_produto', 'produto_id', 'agente_nome'),
        Index('idx_explicacao_sessao', 'sessao_classificacao'),
    )

# =======================
# CONSULTAS DOS AGENTES
# =======================

class ConsultaAgente(UnifiedBase):
    """Registro de todas as consultas realizadas pelos agentes"""
    __tablename__ = "consultas_agentes"
    
    id = Column(Integer, primary_key=True, index=True)
    agente_nome = Column(String(50), nullable=False, index=True)
    produto_id = Column(Integer, nullable=False, index=True)
    sessao_classificacao = Column(String(100), index=True)
    
    # Tipo de consulta
    tipo_consulta = Column(String(50), nullable=False)  # RAG, GOLDEN_SET, NCM_HIERARCHY, etc.
    query_original = Column(Text)
    query_processada = Column(Text)
    
    # Parâmetros da consulta
    parametros_busca = Column(JsonType)
    filtros_aplicados = Column(JsonType)
    limite_resultados = Column(Integer)
    
    # Resultados
    total_resultados_encontrados = Column(Integer)
    resultados_utilizados = Column(JsonType)
    score_relevancia_medio = Column(Float)
    
    # Metadados
    tempo_consulta_ms = Column(Integer)
    fonte_dados = Column(String(50))  # knowledge_base, golden_set, rag_vectorstore, etc.
    data_consulta = Column(DateTime, default=func.now())
    
    # Sucesso e qualidade
    consulta_bem_sucedida = Column(Boolean, default=True)
    qualidade_resultados = Column(Float)
    feedback_agente = Column(Text)
    
    __table_args__ = (
        Index('idx_consulta_agente_tempo', 'agente_nome', 'data_consulta'),
        Index('idx_consulta_produto', 'produto_id', 'tipo_consulta'),
        Index('idx_consulta_sessao', 'sessao_classificacao', 'agente_nome'),
    )

# =======================
# MÉTRICAS E MONITORAMENTO
# =======================

class MetricasQualidade(UnifiedBase):
    """Métricas históricas de qualidade do sistema"""
    __tablename__ = "metricas_qualidade"
    
    id = Column(Integer, primary_key=True, index=True)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    
    # Métricas de volume
    total_classificacoes = Column(Integer, default=0)
    total_revisadas = Column(Integer, default=0)
    total_aprovadas = Column(Integer, default=0)
    total_corrigidas = Column(Integer, default=0)
    
    # Métricas de qualidade
    taxa_aprovacao = Column(Float)
    confianca_media = Column(Float)
    confianca_mediana = Column(Float)
    
    # Métricas de performance
    tempo_medio_revisao = Column(Float)
    produtos_por_hora = Column(Float)
    
    # Detecção de drift
    variacao_taxa_aprovacao = Column(Float)
    variacao_confianca_media = Column(Float)
    
    # Metadados
    calculado_em = Column(DateTime, default=func.now())
    periodo_tipo = Column(String(20))
    
    __table_args__ = (
        Index('idx_metricas_periodo', 'data_inicio', 'data_fim'),
        Index('idx_metricas_tipo', 'periodo_tipo', 'calculado_em'),
    )

class EstadoOrdenacao(UnifiedBase):
    """Controle do estado da ordenação alfabética"""
    __tablename__ = "estado_ordenacao"
    
    id = Column(Integer, primary_key=True, index=True)
    ultima_letra_usada = Column(String(1), default="")
    ultimo_produto_id = Column(Integer)
    data_atualizacao = Column(DateTime, default=func.now())

# =======================
# INTERFACE WEB E INTERAÇÕES
# =======================

class InteracaoWeb(UnifiedBase):
    """Registro de todas as interações com a interface web"""
    __tablename__ = "interacoes_web"
    
    id = Column(Integer, primary_key=True, index=True)
    sessao_usuario = Column(String(100), nullable=False, index=True)
    usuario_id = Column(String(50))
    
    # Tipo de interação
    tipo_interacao = Column(String(50), nullable=False)  # CLASSIFICACAO, REVISAO, CORRECAO, CONSULTA
    endpoint_acessado = Column(String(100))
    metodo_http = Column(String(10))
    
    # Dados da interação
    dados_entrada = Column(JsonType)
    dados_saida = Column(JsonType)
    tempo_processamento_ms = Column(Integer)
    
    # Resultado
    sucesso = Column(Boolean, default=True)
    codigo_resposta = Column(Integer)
    mensagem_erro = Column(Text)
    
    # Metadados
    ip_usuario = Column(String(45))
    user_agent = Column(Text)
    data_interacao = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_interacao_sessao', 'sessao_usuario', 'data_interacao'),
        Index('idx_interacao_tipo', 'tipo_interacao', 'data_interacao'),
        Index('idx_interacao_usuario', 'usuario_id', 'tipo_interacao'),
    )

class CorrecaoIdentificada(UnifiedBase):
    """Registro de correções identificadas e aplicadas"""
    __tablename__ = "correcoes_identificadas"
    
    id = Column(Integer, primary_key=True, index=True)
    classificacao_id = Column(Integer, ForeignKey('classificacoes_revisao.id'), nullable=False)
    
    # Tipo de correção
    tipo_correcao = Column(String(50), nullable=False)  # NCM, CEST, GTIN, DESCRICAO
    campo_original = Column(String(50))
    valor_original = Column(Text)
    valor_corrigido = Column(Text)
    
    # Justificativa
    motivo_correcao = Column(Text)
    explicacao_detalhada = Column(Text)
    confianca_correcao = Column(Float)
    
    # Metadados
    corrigido_por = Column(String(100))  # HUMANO, AGENTE_IA, AUTOMATICO
    data_correcao = Column(DateTime, default=func.now())
    validado = Column(Boolean, default=False)
    data_validacao = Column(DateTime)
    
    # Impacto
    impacto_classificacao = Column(String(20))  # ALTO, MEDIO, BAIXO
    produtos_similares_afetados = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_correcao_tipo', 'tipo_correcao', 'data_correcao'),
        Index('idx_correcao_classificacao', 'classificacao_id'),
        Index('idx_correcao_impacto', 'impacto_classificacao', 'validado'),
    )

# =======================
# EMBEDDINGS E VETORES
# =======================

class EmbeddingProduto(UnifiedBase):
    """Embeddings vetoriais dos produtos para busca semântica"""
    __tablename__ = "embeddings_produtos"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, nullable=False, index=True)
    classificacao_id = Column(Integer, ForeignKey('classificacoes_revisao.id'))
    golden_set_id = Column(Integer, ForeignKey('golden_set.id'))
    
    # Embedding
    embedding_vector = Column(LargeBinary)  # Serialized numpy array
    embedding_model = Column(String(50), default="sentence-transformers")
    embedding_dimensoes = Column(Integer)
    
    # Texto usado para gerar embedding
    texto_original = Column(Text, nullable=False)
    texto_processado = Column(Text)
    
    # Metadados
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now())
    versao_modelo = Column(String(20))
    qualidade_embedding = Column(Float)
    
    __table_args__ = (
        Index('idx_embedding_produto', 'produto_id'),
        Index('idx_embedding_modelo', 'embedding_model', 'versao_modelo'),
        Index('idx_embedding_data', 'data_criacao'),
    )

# =======================
# METADADOS DO SISTEMA
# =======================

class KnowledgeBaseMetadata(UnifiedBase):
    """Metadados da base de conhecimento unificada"""
    __tablename__ = "knowledge_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    versao_base = Column(String(20), nullable=False)
    data_criacao = Column(DateTime, default=func.now())
    data_ultima_atualizacao = Column(DateTime, default=func.now())
    
    # Estatísticas da base
    total_ncms = Column(Integer, default=0)
    total_cests = Column(Integer, default=0)
    total_mapeamentos = Column(Integer, default=0)
    total_exemplos = Column(Integer, default=0)
    total_classificacoes = Column(Integer, default=0)
    total_golden_set = Column(Integer, default=0)
    total_explicacoes = Column(Integer, default=0)
    
    # Fontes de dados
    fontes_utilizadas = Column(JsonType)
    ativo = Column(Boolean, default=True)

# =======================
# ÍNDICES DE PERFORMANCE
# =======================

def create_unified_indexes(engine):
    """Cria índices avançados para performance ótima"""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Índices para busca hierárquica NCM
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ncm_busca_hierarquica 
            ON ncm_hierarchy(codigo_ncm, codigo_pai, nivel_hierarquico, ativo)
        """))
        
        # Índices para CEST por NCM
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cest_por_ncm 
            ON ncm_cest_mapping(ncm_codigo, ativo, tipo_relacao, confianca_mapeamento)
        """))
        
        # Índices para exemplos de qualidade
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exemplos_qualidade 
            ON produtos_exemplos(ncm_codigo, qualidade_classificacao DESC, verificado_humano DESC, ativo)
        """))
        
        # Índices para classificações por status e data
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_classificacao_dashboard 
            ON classificacoes_revisao(status_revisao, data_criacao DESC, confianca_sugerida)
        """))
        
        # Índices para golden set por uso
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_golden_set_uso_otimizado 
            ON golden_set(ativo, qualidade_score DESC, vezes_usado DESC, ncm_final)
        """))
        
        # Índices para explicações por agente e tempo
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_explicacao_agente_tempo 
            ON explicacoes_agentes(agente_nome, data_execucao DESC, nivel_confianca)
        """))
        
        # Índices para consultas por performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_consulta_performance 
            ON consultas_agentes(agente_nome, data_consulta DESC, tempo_consulta_ms)
        """))
        
        # Índices para métricas temporais
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_metricas_temporal 
            ON metricas_qualidade(data_inicio DESC, data_fim DESC, periodo_tipo)
        """))
        
        # Índices para interações web
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_interacao_performance 
            ON interacoes_web(tipo_interacao, data_interacao DESC, sucesso)
        """))
        
        conn.commit()
