"""
Schema SQLite Padronizado para Bancos de Empresa
Definição completa das tabelas e índices otimizados
"""

import sqlite3
from typing import Dict, Any, List
from datetime import datetime
import json

class EmpresaSchemaManager:
    """Gerencia schema padronizado para bancos SQLite de empresa"""
    
    # Schema version para versionamento
    SCHEMA_VERSION = "2.0.0"
    
    @classmethod
    def get_table_definitions(cls) -> Dict[str, str]:
        """Retorna definições SQL de todas as tabelas"""
        
        return {
            # Tabela de informações da empresa
            "empresa_info": """
                CREATE TABLE IF NOT EXISTS empresa_info (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    cnpj TEXT UNIQUE NOT NULL,
                    razao_social TEXT,
                    nome_fantasia TEXT,
                    tipo_atividade TEXT NOT NULL,
                    descricao_atividade TEXT,
                    codigo_cnae_primario TEXT,
                    codigo_cnae_secundarios JSON,
                    canal_venda TEXT NOT NULL,
                    porte_empresa TEXT,
                    regime_tributario TEXT,
                    endereco_completo JSON,
                    contatos JSON,
                    segmento_cest_preferencial INTEGER,
                    configuracoes_classificacao JSON,
                    origem_db_config JSON,
                    ativo BOOLEAN DEFAULT 1,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_criacao TEXT,
                    versao_schema TEXT DEFAULT '2.0.0'
                )
            """,
            
            # Tabela de produtos da empresa
            "produtos_empresa": """
                CREATE TABLE IF NOT EXISTS produtos_empresa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_interno TEXT,
                    gtin TEXT,
                    nome_produto TEXT NOT NULL,
                    descricao_original TEXT,
                    descricao_enriquecida TEXT,
                    descricao_comercial TEXT,
                    categoria TEXT,
                    subcategoria TEXT,
                    marca TEXT,
                    modelo TEXT,
                    peso REAL,
                    peso_liquido REAL,
                    unidade_medida TEXT,
                    dimensoes JSON,
                    composicao TEXT,
                    ingredientes TEXT,
                    preco_custo REAL,
                    preco_venda REAL,
                    margem_lucro REAL,
                    estoque_atual INTEGER,
                    fornecedor TEXT,
                    origem_pais TEXT,
                    origem_tabela TEXT,
                    origem_id TEXT,
                    metadados_extras JSON,
                    status_produto TEXT DEFAULT 'ativo',
                    requer_classificacao BOOLEAN DEFAULT 1,
                    prioridade_classificacao INTEGER DEFAULT 1,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_cadastro TEXT,
                    ativo BOOLEAN DEFAULT 1,
                    
                    -- Índices inline
                    UNIQUE(origem_tabela, origem_id)
                )
            """,
            
            # Tabela de classificações (versão expandida)
            "classificacoes": """
                CREATE TABLE IF NOT EXISTS classificacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    versao_classificacao INTEGER DEFAULT 1,
                    
                    -- Classificação NCM
                    ncm_codigo TEXT,
                    ncm_descricao TEXT,
                    ncm_capitulo INTEGER,
                    ncm_posicao INTEGER,
                    ncm_subposicao INTEGER,
                    ncm_item INTEGER,
                    ncm_subitem INTEGER,
                    confianca_ncm REAL,
                    justificativa_ncm TEXT,
                    
                    -- Classificação CEST
                    cest_codigo TEXT,
                    cest_descricao TEXT,
                    cest_segmento INTEGER,
                    cest_item INTEGER,
                    cest_codigo_item INTEGER,
                    confianca_cest REAL,
                    justificativa_cest TEXT,
                    
                    -- Outras classificações fiscais
                    ipi_codigo TEXT,
                    icms_origem TEXT,
                    icms_tributacao TEXT,
                    pis_cofins_codigo TEXT,
                    
                    -- Metadados da classificação
                    metodo_classificacao TEXT, -- automatico, manual, hibrido
                    contexto_empresa_aplicado JSON,
                    palavras_chave_utilizadas JSON,
                    produtos_similares_referencia JSON,
                    
                    -- Status e aprovação
                    status TEXT DEFAULT 'pendente', -- pendente, aprovado, rejeitado, revisao, corrigido
                    nivel_confianca_geral REAL,
                    requer_revisao_humana BOOLEAN DEFAULT 0,
                    aprovado_por TEXT,
                    data_classificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_aprovacao TIMESTAMP,
                    data_ultima_revisao TIMESTAMP,
                    
                    -- Observações e notas
                    observacoes TEXT,
                    notas_revisor TEXT,
                    referencias_legais TEXT,
                    
                    -- Rastreabilidade
                    usuario_classificacao TEXT,
                    versao_agentes TEXT,
                    tempo_processamento REAL,
                    
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    UNIQUE(produto_id, versao_classificacao)
                )
            """,
            
            # Tabela de ações dos agentes (expandida para auditoria)
            "agente_acoes": """
                CREATE TABLE IF NOT EXISTS agente_acoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    classificacao_id INTEGER,
                    sessao_classificacao TEXT, -- UUID da sessão
                    
                    -- Identificação do agente
                    agente_nome TEXT NOT NULL,
                    agente_versao TEXT,
                    acao_tipo TEXT NOT NULL,
                    acao_subtipo TEXT,
                    
                    -- Dados da execução
                    input_dados JSON,
                    output_resultado JSON,
                    output_alternativas JSON, -- outras opções consideradas
                    
                    -- Análise e justificativa
                    justificativa TEXT,
                    confianca REAL,
                    score_relevancia REAL,
                    metodos_utilizados JSON,
                    
                    -- Performance
                    tempo_execucao REAL,
                    memoria_utilizada INTEGER,
                    tokens_processados INTEGER,
                    custo_estimado REAL,
                    
                    -- Status e erro
                    sucesso BOOLEAN DEFAULT 1,
                    status_execucao TEXT DEFAULT 'concluido',
                    erro_codigo TEXT,
                    erro_detalhes TEXT,
                    erro_stack_trace TEXT,
                    
                    -- Contexto da execução
                    contexto_empresa JSON,
                    variaveis_ambiente JSON,
                    configuracoes_agente JSON,
                    
                    -- Auditoria
                    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_sessao TEXT,
                    ip_origem TEXT,
                    
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    FOREIGN KEY (classificacao_id) REFERENCES classificacoes (id)
                )
            """,
            
            # Tabela de consultas dos agentes (expandida)
            "agente_consultas": """
                CREATE TABLE IF NOT EXISTS agente_consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    agente_acao_id INTEGER,
                    sessao_classificacao TEXT,
                    
                    -- Identificação da consulta
                    agente_nome TEXT NOT NULL,
                    tipo_consulta TEXT NOT NULL,
                    fonte_dados TEXT, -- faiss, postgresql, sqlite, api_externa
                    
                    -- Query details
                    query_original TEXT NOT NULL,
                    query_processada TEXT,
                    query_embeddings BLOB,
                    parametros_busca JSON,
                    filtros_aplicados JSON,
                    
                    -- Resultados
                    resultados_encontrados INTEGER DEFAULT 0,
                    resultado_detalhes JSON,
                    resultado_ranking JSON,
                    melhor_match JSON,
                    
                    -- Métricas de relevância
                    relevancia_score REAL,
                    confianca_resultado REAL,
                    score_semantic_similarity REAL,
                    
                    -- Performance
                    tempo_resposta REAL,
                    latencia_rede REAL,
                    cache_hit BOOLEAN DEFAULT 0,
                    
                    -- Status
                    sucesso BOOLEAN DEFAULT 1,
                    erro_detalhes TEXT,
                    
                    -- Auditoria
                    data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    FOREIGN KEY (agente_acao_id) REFERENCES agente_acoes (id)
                )
            """,
            
            # Tabela de histórico de mudanças (expandida)
            "historico_mudancas": """
                CREATE TABLE IF NOT EXISTS historico_mudancas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    
                    -- Referências
                    produto_id INTEGER,
                    classificacao_id INTEGER,
                    tabela_afetada TEXT NOT NULL,
                    registro_id INTEGER NOT NULL,
                    
                    -- Tipo da mudança
                    tipo_mudanca TEXT NOT NULL,
                    operacao TEXT NOT NULL, -- INSERT, UPDATE, DELETE
                    campo_alterado TEXT,
                    
                    -- Valores
                    valor_anterior JSON,
                    valor_novo JSON,
                    valor_diff JSON, -- diferenças específicas
                    
                    -- Contexto da mudança
                    motivo TEXT,
                    categoria_mudanca TEXT, -- correcao, melhoria, requisito_legal
                    impacto_estimado TEXT, -- baixo, medio, alto
                    
                    -- Aprovação e validação
                    requer_aprovacao BOOLEAN DEFAULT 0,
                    aprovacao_status TEXT, -- pendente, aprovado, rejeitado
                    aprovado_por TEXT,
                    data_aprovacao TIMESTAMP,
                    
                    -- Auditoria
                    usuario TEXT NOT NULL,
                    ip_origem TEXT,
                    user_agent TEXT,
                    sessao_id TEXT,
                    data_mudanca TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Reversão
                    reversivel BOOLEAN DEFAULT 1,
                    mudanca_pai_id INTEGER, -- para rastrear reversões
                    
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    FOREIGN KEY (classificacao_id) REFERENCES classificacoes (id),
                    FOREIGN KEY (mudanca_pai_id) REFERENCES historico_mudancas (id)
                )
            """,
            
            # Tabela de métricas de performance
            "metricas_performance": """
                CREATE TABLE IF NOT EXISTS metricas_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo_inicio TIMESTAMP NOT NULL,
                    periodo_fim TIMESTAMP NOT NULL,
                    tipo_metrica TEXT NOT NULL, -- diaria, semanal, mensal
                    
                    -- Métricas de produtos
                    total_produtos INTEGER DEFAULT 0,
                    produtos_ativos INTEGER DEFAULT 0,
                    produtos_novos INTEGER DEFAULT 0,
                    
                    -- Métricas de classificação
                    total_classificacoes INTEGER DEFAULT 0,
                    classificacoes_automaticas INTEGER DEFAULT 0,
                    classificacoes_manuais INTEGER DEFAULT 0,
                    classificacoes_hibridas INTEGER DEFAULT 0,
                    
                    -- Métricas de aprovação
                    aprovacoes_automaticas INTEGER DEFAULT 0,
                    aprovacoes_manuais INTEGER DEFAULT 0,
                    rejeicoes INTEGER DEFAULT 0,
                    revisoes_pendentes INTEGER DEFAULT 0,
                    
                    -- Métricas de qualidade
                    tempo_medio_classificacao REAL,
                    confianca_media_ncm REAL,
                    confianca_media_cest REAL,
                    taxa_sucesso_agentes REAL,
                    
                    -- Métricas de agentes
                    performance_agentes JSON,
                    erro_rate_agentes JSON,
                    tempo_resposta_agentes JSON,
                    
                    -- Golden Set
                    produtos_golden_set INTEGER DEFAULT 0,
                    contribuicoes_golden_set INTEGER DEFAULT 0,
                    
                    -- Recursos utilizados
                    tokens_llm_utilizados INTEGER DEFAULT 0,
                    custo_estimado_llm REAL DEFAULT 0,
                    tempo_total_processamento REAL DEFAULT 0,
                    
                    -- Dados detalhados (JSON)
                    detalhes_completos JSON,
                    
                    -- Auditoria
                    data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_calculo TEXT
                )
            """,
            
            # Tabela de configurações
            "configuracoes_sistema": """
                CREATE TABLE IF NOT EXISTS configuracoes_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT UNIQUE NOT NULL,
                    valor JSON NOT NULL,
                    tipo_configuracao TEXT NOT NULL, -- sistema, agente, interface
                    descricao TEXT,
                    valor_padrao JSON,
                    validacao_schema JSON,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_atualizacao TEXT
                )
            """,
            
            # Tabela de cache de consultas
            "cache_consultas": """
                CREATE TABLE IF NOT EXISTS cache_consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash_consulta TEXT UNIQUE NOT NULL,
                    tipo_consulta TEXT NOT NULL,
                    query_original TEXT NOT NULL,
                    parametros JSON,
                    resultado JSON NOT NULL,
                    score_confianca REAL,
                    hits INTEGER DEFAULT 1,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_ultimo_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ttl_seconds INTEGER DEFAULT 3600,
                    ativo BOOLEAN DEFAULT 1
                )
            """
        }
    
    @classmethod
    def get_indexes(cls) -> List[str]:
        """Retorna lista de índices para otimização"""
        
        return [
            # Índices para produtos_empresa
            "CREATE INDEX IF NOT EXISTS idx_produtos_gtin ON produtos_empresa(gtin)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos_empresa(nome_produto)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos_empresa(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_status ON produtos_empresa(status_produto)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_origem ON produtos_empresa(origem_tabela, origem_id)",
            
            # Índices para classificacoes
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_produto ON classificacoes(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_ncm ON classificacoes(ncm_codigo)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_cest ON classificacoes(cest_codigo)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_status ON classificacoes(status)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_data ON classificacoes(data_classificacao)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_confianca ON classificacoes(nivel_confianca_geral)",
            
            # Índices para agente_acoes
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_produto ON agente_acoes(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_agente ON agente_acoes(agente_nome)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_sessao ON agente_acoes(sessao_classificacao)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_data ON agente_acoes(data_execucao)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_sucesso ON agente_acoes(sucesso)",
            
            # Índices para agente_consultas
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_produto ON agente_consultas(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_agente ON agente_consultas(agente_nome)",
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_tipo ON agente_consultas(tipo_consulta)",
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_data ON agente_consultas(data_consulta)",
            
            # Índices para historico_mudancas
            "CREATE INDEX IF NOT EXISTS idx_historico_produto ON historico_mudancas(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_historico_tabela ON historico_mudancas(tabela_afetada)",
            "CREATE INDEX IF NOT EXISTS idx_historico_usuario ON historico_mudancas(usuario)",
            "CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_mudancas(data_mudanca)",
            "CREATE INDEX IF NOT EXISTS idx_historico_tipo ON historico_mudancas(tipo_mudanca)",
            
            # Índices para performance
            "CREATE INDEX IF NOT EXISTS idx_metricas_periodo ON metricas_performance(periodo_inicio, periodo_fim)",
            "CREATE INDEX IF NOT EXISTS idx_metricas_tipo ON metricas_performance(tipo_metrica)",
            
            # Índices para cache
            "CREATE INDEX IF NOT EXISTS idx_cache_hash ON cache_consultas(hash_consulta)",
            "CREATE INDEX IF NOT EXISTS idx_cache_tipo ON cache_consultas(tipo_consulta)",
            "CREATE INDEX IF NOT EXISTS idx_cache_ativo ON cache_consultas(ativo)",
            "CREATE INDEX IF NOT EXISTS idx_cache_ttl ON cache_consultas(data_criacao, ttl_seconds)"
        ]
    
    @classmethod
    def get_triggers(cls) -> List[str]:
        """Retorna triggers para manutenção automática"""
        
        return [
            # Trigger para atualizar data_atualizacao
            """
            CREATE TRIGGER IF NOT EXISTS update_produtos_timestamp 
                AFTER UPDATE ON produtos_empresa
            BEGIN
                UPDATE produtos_empresa 
                SET data_atualizacao = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
            """,
            
            # Trigger para atualizar data_atualizacao em empresa_info
            """
            CREATE TRIGGER IF NOT EXISTS update_empresa_timestamp 
                AFTER UPDATE ON empresa_info
            BEGIN
                UPDATE empresa_info 
                SET data_atualizacao = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
            """,
            
            # Trigger para invalidar cache relacionado
            """
            CREATE TRIGGER IF NOT EXISTS invalidate_cache_on_classification 
                AFTER INSERT ON classificacoes
            BEGIN
                UPDATE cache_consultas 
                SET ativo = 0 
                WHERE query_original LIKE '%' || NEW.produto_id || '%';
            END
            """,
            
            # Trigger para limpeza automática de cache expirado
            """
            CREATE TRIGGER IF NOT EXISTS cleanup_expired_cache 
                AFTER INSERT ON cache_consultas
            BEGIN
                DELETE FROM cache_consultas 
                WHERE ativo = 1 
                AND (julianday('now') - julianday(data_criacao)) * 86400 > ttl_seconds;
            END
            """
        ]
    
    @classmethod
    def create_database_schema(cls, db_path: str, empresa_config: Dict[str, Any]) -> bool:
        """Cria schema completo do banco da empresa"""
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Configurar PRAGMA para performance
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute("PRAGMA cache_size = 10000")
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Criar tabelas
                tables = cls.get_table_definitions()
                for table_name, table_sql in tables.items():
                    cursor.execute(table_sql)
                    print(f"✅ Tabela {table_name} criada")
                
                # Criar índices
                indexes = cls.get_indexes()
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                # Criar triggers
                triggers = cls.get_triggers()
                for trigger_sql in triggers:
                    cursor.execute(trigger_sql)
                
                # Inserir configurações iniciais
                cls._insert_initial_data(cursor, empresa_config)
                
                conn.commit()
                print(f"✅ Schema completo criado para empresa: {db_path}")
                
                return True
                
        except Exception as e:
            print(f"❌ Erro ao criar schema: {str(e)}")
            return False
    
    @classmethod
    def _insert_initial_data(cls, cursor, empresa_config: Dict[str, Any]):
        """Insere dados iniciais no banco da empresa"""
        
        # Configurações padrão do sistema
        configuracoes_iniciais = [
            ("agentes.timeout_seconds", 300, "agente", "Timeout para execução de agentes"),
            ("classificacao.confianca_minima", 0.7, "sistema", "Confiança mínima para aprovação automática"),
            ("cache.ttl_default", 3600, "sistema", "TTL padrão para cache de consultas"),
            ("auditoria.log_level", "INFO", "sistema", "Nível de log para auditoria"),
        ]
        
        for chave, valor, tipo, descricao in configuracoes_iniciais:
            cursor.execute("""
                INSERT OR IGNORE INTO configuracoes_sistema 
                (chave, valor, tipo_configuracao, descricao, valor_padrao)
                VALUES (?, ?, ?, ?, ?)
            """, (chave, json.dumps(valor), tipo, descricao, json.dumps(valor)))
        
        # Inserir informações da empresa
        cursor.execute("""
            INSERT OR REPLACE INTO empresa_info 
            (id, nome, cnpj, tipo_atividade, descricao_atividade, canal_venda, 
             porte_empresa, regime_tributario, configuracoes_classificacao, origem_db_config)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            empresa_config.get('nome', ''),
            empresa_config.get('cnpj', ''),
            empresa_config.get('tipo_atividade', ''),
            empresa_config.get('descricao_atividade', ''),
            empresa_config.get('canal_venda', ''),
            empresa_config.get('porte_empresa', ''),
            empresa_config.get('regime_tributario', ''),
            json.dumps(empresa_config.get('configuracoes_classificacao', {})),
            json.dumps(empresa_config.get('origem_db_config', {}))
        ))

    @classmethod
    def validate_schema(cls, db_path: str) -> Dict[str, Any]:
        """Valida integridade do schema do banco"""
        
        validation_result = {
            "valid": True,
            "version": None,
            "missing_tables": [],
            "missing_indexes": [],
            "issues": []
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar versão do schema
                cursor.execute("SELECT valor FROM configuracoes_sistema WHERE chave = 'schema.version'")
                version = cursor.fetchone()
                validation_result["version"] = version[0] if version else "unknown"
                
                # Verificar tabelas existentes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = set(row[0] for row in cursor.fetchall())
                
                expected_tables = set(cls.get_table_definitions().keys())
                missing_tables = expected_tables - existing_tables
                
                validation_result["missing_tables"] = list(missing_tables)
                
                if missing_tables:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Tabelas faltando: {missing_tables}")
                
                # Verificar índices (simplificado)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                existing_indexes = set(row[0] for row in cursor.fetchall())
                
                # Análise básica de performance
                cursor.execute("ANALYZE")
                
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Erro na validação: {str(e)}")
        
        return validation_result
