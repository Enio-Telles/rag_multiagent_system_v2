"""
Modelos de banco de dados para o sistema de revisão humana
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# Tipo JSON compatível com SQLite e PostgreSQL
JsonType = JSON().with_variant(JSONB(), 'postgresql').with_variant(Text(), 'sqlite')

class ClassificacaoRevisao(Base):
    """
    Tabela para armazenar classificações e seu status de revisão
    """
    __tablename__ = "classificacoes_revisao"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Dados do produto
    produto_id = Column(Integer, nullable=False, index=True)
    descricao_produto = Column(Text, nullable=False)
    descricao_completa = Column(Text)  # Descrição mais detalhada informada pelo revisor
    codigo_produto = Column(String(100))
    
    # Código de barras - validação apenas por humanos no sistema de revisão
    codigo_barra = Column(String(50))  # Código de barras extraído do PostgreSQL
    codigo_barra_status = Column(String(20), default="PENDENTE_VERIFICACAO")  # PENDENTE_VERIFICACAO, CORRETO, INCORRETO, NAO_APLICAVEL
    codigo_barra_corrigido = Column(String(50))  # Código corrigido pelo revisor humano
    codigo_barra_observacoes = Column(Text)  # Observações sobre correções no código
    
    # GTIN (campos legados - manter para compatibilidade)
    gtin_original = Column(String(50))  # GTIN extraído originalmente
    gtin_status = Column(String(20), default="NAO_VERIFICADO")  # NAO_VERIFICADO, CORRETO, INCORRETO, NAO_APLICAVEL
    gtin_corrigido = Column(String(50))  # GTIN corrigido pelo especialista
    gtin_observacoes = Column(Text)  # Observações sobre o GTIN
    
    # Classificação original (do banco de dados)
    ncm_original = Column(String(15))
    cest_original = Column(String(15))
    
    # Classificação sugerida pelo sistema
    ncm_sugerido = Column(String(15))
    cest_sugerido = Column(String(15))
    confianca_sugerida = Column(Float)
    justificativa_sistema = Column(Text)
    
    # Status da revisão
    status_revisao = Column(String(20), default="PENDENTE_REVISAO", index=True)
    # Valores possíveis: PENDENTE_REVISAO, APROVADO, CORRIGIDO
    
    # Classificação corrigida pelo especialista
    ncm_corrigido = Column(String(15))
    cest_corrigido = Column(String(15))
    justificativa_correcao = Column(Text)
    
    # Dados da revisão
    revisado_por = Column(String(100))
    data_revisao = Column(DateTime)
    
    # Metadados
    data_classificacao = Column(DateTime, default=func.now())
    data_criacao = Column(DateTime, default=func.now())
    dados_trace_json = Column(JsonType)  # Armazena traces completos dos agentes
    
    # Explicações detalhadas dos agentes
    explicacao_agente_expansao = Column(Text)  # Explicação do agente de expansão
    explicacao_agente_ncm = Column(Text)       # Explicação do agente NCM
    explicacao_agente_cest = Column(Text)      # Explicação do agente CEST
    explicacao_agente_reconciliador = Column(Text)  # Explicação do agente reconciliador
    
    # Campos para análise de qualidade
    tempo_revisao_segundos = Column(Integer)  # Tempo gasto na revisão
    complexidade_produto = Column(String(20))  # SIMPLES, MEDIO, COMPLEXO
    
    def __repr__(self):
        return f"<ClassificacaoRevisao(produto_id={self.produto_id}, status={self.status_revisao})>"


class EstadoOrdenacao(Base):
    """
    Tabela para controlar o estado da ordenação alfabética
    """
    __tablename__ = "estado_ordenacao"
    
    id = Column(Integer, primary_key=True, index=True)
    ultima_letra_usada = Column(String(1), default="")
    ultimo_produto_id = Column(Integer)
    data_atualizacao = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<EstadoOrdenacao(ultima_letra={self.ultima_letra_usada}, produto_id={self.ultimo_produto_id})>"


class MetricasQualidade(Base):
    """
    Tabela para armazenar métricas históricas de qualidade
    Usado para análise de drift e monitoramento
    """
    __tablename__ = "metricas_qualidade"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Período da métrica
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    
    # Métricas de volume
    total_classificacoes = Column(Integer, default=0)
    total_revisadas = Column(Integer, default=0)
    total_aprovadas = Column(Integer, default=0)
    total_corrigidas = Column(Integer, default=0)
    
    # Métricas de qualidade
    taxa_aprovacao = Column(Float)  # % aprovadas / total revisadas
    confianca_media = Column(Float)
    confianca_mediana = Column(Float)
    
    # Métricas de performance
    tempo_medio_revisao = Column(Float)  # em segundos
    produtos_por_hora = Column(Float)
    
    # Detecção de drift
    variacao_taxa_aprovacao = Column(Float)  # em relação ao período anterior
    variacao_confianca_media = Column(Float)
    
    # Metadados
    calculado_em = Column(DateTime, default=func.now())
    periodo_tipo = Column(String(20))  # DIARIO, SEMANAL, MENSAL
    
    def __repr__(self):
        return f"<MetricasQualidade(periodo={self.data_inicio} - {self.data_fim}, taxa={self.taxa_aprovacao})>"


class GoldenSetEntry(Base):
    """
    Tabela para armazenar classificações validadas por humanos (Golden Set)
    Usado para aprendizagem contínua e melhoria do sistema
    """
    __tablename__ = "golden_set"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Dados do produto validado
    produto_id = Column(Integer, nullable=False, index=True)
    descricao_produto = Column(Text, nullable=False)  # Descrição original
    descricao_completa = Column(Text)  # Descrição completa inserida pelo usuário
    codigo_produto = Column(String(100))
    gtin_validado = Column(String(50))  # GTIN final validado e revisado por humanos
    
    # Classificação final validada
    ncm_final = Column(String(15), nullable=False)  # NCM revisado por humanos
    cest_final = Column(String(15))  # CEST revisado por humanos
    confianca_original = Column(Float)  # Confiança que o sistema tinha originalmente
    
    # Metadados da validação
    fonte_validacao = Column(String(20), default="HUMANA")  # HUMANA, AUTOMATICA, IMPORTADA
    justificativa_inclusao = Column(Text)
    revisado_por = Column(String(100))
    data_adicao = Column(DateTime, default=func.now())
    
    # Status e controle
    ativo = Column(Boolean, default=True)
    qualidade_score = Column(Float)  # Score de qualidade da entrada (opcional)
    vezes_usado = Column(Integer, default=0)  # Quantas vezes foi usado em classificações
    
    # Dados para retreinamento e uso pelos agentes
    embedding_atualizado = Column(Boolean, default=False)
    ultima_utilizacao = Column(DateTime)
    
    # Explicações detalhadas dos agentes para uso em aprendizagem
    explicacao_expansao = Column(Text)  # Como o produto foi expandido/analisado
    explicacao_agregacao = Column(Text) # Análise de agregação de informações
    explicacao_ncm = Column(Text)       # Justificativa da classificação NCM
    explicacao_cest = Column(Text)      # Justificativa da classificação CEST
    explicacao_reconciliacao = Column(Text)  # Análise final e reconciliação
    
    # Dados enriquecidos para uso pelos agentes
    palavras_chave_fiscais = Column(Text)  # Palavras-chave separadas por vírgula
    categoria_produto = Column(String(100))  # Categoria identificada
    material_predominante = Column(String(100))  # Material principal
    aplicacoes_uso = Column(Text)  # Aplicações e usos do produto
    caracteristicas_tecnicas = Column(Text)  # Características técnicas identificadas
    contexto_uso = Column(Text)  # Contexto de uso do produto
    similaridade_produtos = Column(Text)  # Produtos similares do Golden Set
    
    def __repr__(self):
        return f"<GoldenSetEntry(id={self.id}, produto_id={self.produto_id}, ncm='{self.ncm_final}')>"


class ExplicacaoAgente(Base):
    """
    Tabela para armazenar explicações detalhadas de cada agente para cada produto
    Permite rastreabilidade e melhoria contínua do sistema
    """
    __tablename__ = "explicacoes_agentes"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Referência ao produto/classificação
    produto_id = Column(Integer, nullable=False, index=True)
    classificacao_id = Column(Integer, index=True)  # FK para ClassificacaoRevisao
    
    # Identificação do agente
    agente_nome = Column(String(50), nullable=False)  # expansion, aggregation, ncm, cest, reconciler
    agente_versao = Column(String(20), default="1.0")
    
    # Dados de entrada do agente
    input_original = Column(Text)  # Dados originais recebidos pelo agente
    contexto_utilizado = Column(JsonType)  # Contexto e informações auxiliares
    
    # Processamento e análise
    etapas_processamento = Column(JsonType)  # Etapas seguidas pelo agente
    palavras_chave_identificadas = Column(Text)  # Palavras-chave encontradas
    produtos_similares_encontrados = Column(JsonType)  # Produtos similares do RAG/Golden Set
    
    # Resultado e explicação
    resultado_agente = Column(JsonType)  # Resultado produzido pelo agente
    explicacao_detalhada = Column(Text)  # Explicação em linguagem natural
    justificativa_tecnica = Column(Text)  # Justificativa técnica da classificação
    nivel_confianca = Column(Float)  # Confiança do agente (0.0 a 1.0)
    
    # Uso de conhecimento
    rag_consultado = Column(Boolean, default=False)  # Se consultou base RAG
    golden_set_utilizado = Column(Boolean, default=False)  # Se usou Golden Set
    base_ncm_consultada = Column(Boolean, default=False)  # Se consultou base hierárquica NCM
    exemplos_utilizados = Column(JsonType)  # Exemplos específicos utilizados
    
    # Metadados de execução
    tempo_processamento_ms = Column(Integer)  # Tempo de processamento em millisegundos
    memoria_utilizada_mb = Column(Float)  # Memória utilizada aproximada
    tokens_llm_utilizados = Column(Integer)  # Tokens utilizados do LLM
    
    # Auditoria
    data_execucao = Column(DateTime, default=func.now())
    sessao_classificacao = Column(String(100))  # ID da sessão de classificação
    
    # Qualidade e feedback
    qualidade_explicacao = Column(Float)  # Score de qualidade da explicação
    feedback_humano = Column(Text)  # Feedback de revisores humanos
    marcado_para_melhoria = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<ExplicacaoAgente(agente='{self.agente_nome}', produto_id={self.produto_id})>"
