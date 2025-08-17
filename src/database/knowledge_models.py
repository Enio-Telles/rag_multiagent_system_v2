"""
Modelos SQLAlchemy para a Base de Conhecimento Unificada
Substitui os arquivos JSON/CSV por um banco SQLite eficiente
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Base para os modelos da base de conhecimento
KnowledgeBase = declarative_base()

class NCMHierarchy(KnowledgeBase):
    """
    Tabela principal dos códigos NCM com estrutura hierárquica
    """
    __tablename__ = "ncm_hierarchy"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Código NCM (2, 4, 6 ou 8 dígitos)
    codigo_ncm = Column(String(8), nullable=False, unique=True, index=True)
    
    # Descrições
    descricao_oficial = Column(Text, nullable=False)
    descricao_curta = Column(String(200))
    
    # Hierarquia
    nivel_hierarquico = Column(Integer, nullable=False)  # 2, 4, 6, 8
    codigo_pai = Column(String(8), index=True)  # NCM pai na hierarquia
    
    # Metadados
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    cests = relationship("NCMCestMapping", back_populates="ncm")
    exemplos = relationship("ProdutoExemplo", back_populates="ncm")
    
    # Índices compostos
    __table_args__ = (
        Index('idx_ncm_hierarquia', 'codigo_ncm', 'nivel_hierarquico'),
        Index('idx_ncm_pai', 'codigo_pai', 'nivel_hierarquico'),
    )
    
    def __repr__(self):
        return f"<NCMHierarchy(codigo='{self.codigo_ncm}', nivel={self.nivel_hierarquico})>"


class CestCategory(KnowledgeBase):
    """
    Tabela de categorias CEST
    """
    __tablename__ = "cest_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Código CEST
    codigo_cest = Column(String(10), nullable=False, unique=True, index=True)
    
    # Descrições
    descricao_cest = Column(Text, nullable=False)
    descricao_resumida = Column(String(200))
    
    # Categoria do produto
    categoria_produto = Column(String(100))
    
    # Status
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamentos
    ncm_mappings = relationship("NCMCestMapping", back_populates="cest")
    
    def __repr__(self):
        return f"<CestCategory(codigo='{self.codigo_cest}')>"


class NCMCestMapping(KnowledgeBase):
    """
    Tabela de relacionamento NCM -> CEST
    """
    __tablename__ = "ncm_cest_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chaves estrangeiras
    ncm_codigo = Column(String(8), ForeignKey('ncm_hierarchy.codigo_ncm'), nullable=False, index=True)
    cest_codigo = Column(String(10), ForeignKey('cest_categories.codigo_cest'), nullable=False, index=True)
    
    # Metadados do mapeamento
    tipo_relacao = Column(String(20), default='DIRETO')  # DIRETO, HERDADO, OPCIONAL
    confianca_mapeamento = Column(Float, default=1.0)
    fonte_dados = Column(String(50))  # CEST_RO, MANUAL, etc.
    
    # Status
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamentos
    ncm = relationship("NCMHierarchy", back_populates="cests")
    cest = relationship("CestCategory", back_populates="ncm_mappings")
    
    # Índices compostos
    __table_args__ = (
        Index('idx_ncm_cest', 'ncm_codigo', 'cest_codigo'),
        Index('idx_ncm_ativo', 'ncm_codigo', 'ativo'),
    )
    
    def __repr__(self):
        return f"<NCMCestMapping(ncm='{self.ncm_codigo}', cest='{self.cest_codigo}')>"


class ProdutoExemplo(KnowledgeBase):
    """
    Tabela de produtos exemplo para cada NCM
    """
    __tablename__ = "produtos_exemplos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referência ao NCM
    ncm_codigo = Column(String(8), ForeignKey('ncm_hierarchy.codigo_ncm'), nullable=False, index=True)
    
    # Dados do produto
    gtin = Column(String(14), index=True)
    descricao_produto = Column(Text, nullable=False)
    marca = Column(String(100))
    modelo = Column(String(100))
    
    # Atributos adicionais
    categoria_produto = Column(String(100))
    material_predominante = Column(String(100))
    aplicacao_uso = Column(Text)
    
    # Metadados
    fonte_dados = Column(String(50))  # ABC_FARMA, MANUAL, etc.
    qualidade_classificacao = Column(Float, default=0.0)
    verificado_humano = Column(Boolean, default=False)
    
    # Status
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    
    # Relacionamento
    ncm = relationship("NCMHierarchy", back_populates="exemplos")
    
    # Índices
    __table_args__ = (
        Index('idx_produto_ncm', 'ncm_codigo', 'ativo'),
        Index('idx_produto_gtin', 'gtin'),
        Index('idx_produto_categoria', 'categoria_produto'),
    )
    
    def __repr__(self):
        return f"<ProdutoExemplo(gtin='{self.gtin}', ncm='{self.ncm_codigo}')>"


class KnowledgeBaseMetadata(KnowledgeBase):
    """
    Tabela de metadados da base de conhecimento
    """
    __tablename__ = "knowledge_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informações da versão
    versao_base = Column(String(20), nullable=False)
    data_criacao = Column(DateTime, default=func.now())
    data_ultima_atualizacao = Column(DateTime, default=func.now())
    
    # Estatísticas
    total_ncms = Column(Integer, default=0)
    total_cests = Column(Integer, default=0)
    total_mapeamentos = Column(Integer, default=0)
    total_exemplos = Column(Integer, default=0)
    
    # Fontes de dados utilizadas
    fontes_utilizadas = Column(Text)  # JSON com lista de arquivos fonte
    
    # Status
    ativo = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<KnowledgeBaseMetadata(versao='{self.versao_base}')>"


# Índices adicionais para performance
def create_performance_indexes(engine):
    """
    Cria índices adicionais para otimizar consultas específicas
    """
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Índices para busca hierárquica
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ncm_busca_hierarquica 
            ON ncm_hierarchy(codigo_ncm, codigo_pai, nivel_hierarquico, ativo)
        """))
        
        # Índices para busca de CEST por NCM
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cest_por_ncm 
            ON ncm_cest_mapping(ncm_codigo, ativo, tipo_relacao, confianca_mapeamento)
        """))
        
        # Índices para busca de exemplos
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exemplos_qualidade 
            ON produtos_exemplos(ncm_codigo, qualidade_classificacao DESC, verificado_humano DESC, ativo)
        """))
        
        conn.commit()
