"""
Sistema de Gerenciamento de Banco de Dados por Empresa
Cria e gerencia bancos SQLite separados para cada empresa
Mantém o Golden Set como referência compartilhada
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class EmpresaDatabaseManager:
    """Gerencia bancos de dados segregados por empresa"""
    
    def __init__(self, base_path: str = "data/empresas"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.golden_set_db = "data/golden_set_shared.db"
        
    def get_empresa_db_path(self, empresa_id: int) -> str:
        """Retorna o caminho do banco de dados da empresa"""
        return str(self.base_path / f"empresa_{empresa_id}.db")
    
    def create_empresa_database(self, empresa_id: int, empresa_info: Dict[str, Any]) -> str:
        """Cria um novo banco de dados para a empresa"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de informações da empresa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresa_info (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    cnpj TEXT,
                    tipo_atividade TEXT NOT NULL,
                    descricao_atividade TEXT,
                    canal_venda TEXT NOT NULL,
                    porte_empresa TEXT,
                    regime_tributario TEXT,
                    segmento_cest_preferencial INTEGER,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de produtos da empresa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos_empresa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gtin TEXT,
                    nome_produto TEXT NOT NULL,
                    descricao_original TEXT,
                    descricao_enriquecida TEXT,
                    categoria TEXT,
                    marca TEXT,
                    peso REAL,
                    unidade_medida TEXT,
                    preco REAL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ativo BOOLEAN DEFAULT 1
                )
            """)
            
            # Tabela de classificações por produto
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classificacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    ncm_codigo TEXT,
                    ncm_descricao TEXT,
                    cest_codigo TEXT,
                    cest_descricao TEXT,
                    confianca_ncm REAL,
                    confianca_cest REAL,
                    status TEXT DEFAULT 'pendente', -- pendente, aprovado, rejeitado, revisao
                    aprovado_por TEXT,
                    data_classificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_aprovacao TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id)
                )
            """)
            
            # Tabela de ações dos agentes por produto
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agente_acoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    classificacao_id INTEGER NOT NULL,
                    agente_nome TEXT NOT NULL, -- expansion, ncm, cest, aggregation, reconciler
                    acao_tipo TEXT NOT NULL, -- busca, classificacao, validacao, correcao
                    input_dados TEXT, -- JSON com dados de entrada
                    output_resultado TEXT, -- JSON com resultado da ação
                    justificativa TEXT,
                    confianca REAL,
                    tempo_execucao REAL, -- em segundos
                    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sucesso BOOLEAN DEFAULT 1,
                    erro_detalhes TEXT,
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    FOREIGN KEY (classificacao_id) REFERENCES classificacoes (id)
                )
            """)
            
            # Tabela de consultas realizadas pelos agentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agente_consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    agente_nome TEXT NOT NULL,
                    tipo_consulta TEXT NOT NULL, -- semantic_search, database_lookup, api_call
                    query_original TEXT NOT NULL,
                    query_processada TEXT,
                    resultados_encontrados INTEGER DEFAULT 0,
                    resultado_detalhes TEXT, -- JSON com resultados completos
                    relevancia_score REAL,
                    tempo_resposta REAL,
                    data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sucesso BOOLEAN DEFAULT 1,
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id)
                )
            """)
            
            # Tabela de histórico de mudanças
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_mudancas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    classificacao_id INTEGER,
                    tipo_mudanca TEXT NOT NULL, -- criacao, atualizacao, aprovacao, rejeicao
                    campo_alterado TEXT,
                    valor_anterior TEXT,
                    valor_novo TEXT,
                    usuario TEXT,
                    motivo TEXT,
                    data_mudanca TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos_empresa (id),
                    FOREIGN KEY (classificacao_id) REFERENCES classificacoes (id)
                )
            """)
            
            # Tabela de métricas de performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_calculo DATE NOT NULL,
                    total_produtos INTEGER DEFAULT 0,
                    total_classificacoes INTEGER DEFAULT 0,
                    aprovacoes_automaticas INTEGER DEFAULT 0,
                    aprovacoes_manuais INTEGER DEFAULT 0,
                    rejeicoes INTEGER DEFAULT 0,
                    tempo_medio_classificacao REAL,
                    confianca_media_ncm REAL,
                    confianca_media_cest REAL,
                    produtos_golden_set INTEGER DEFAULT 0,
                    taxa_sucesso REAL,
                    dados_detalhados TEXT -- JSON com métricas detalhadas
                )
            """)
            
            # Inserir informações da empresa
            cursor.execute("""
                INSERT OR REPLACE INTO empresa_info 
                (id, nome, cnpj, tipo_atividade, descricao_atividade, canal_venda, 
                 porte_empresa, regime_tributario, segmento_cest_preferencial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id,
                empresa_info.get('nome', ''),
                empresa_info.get('cnpj', ''),
                empresa_info.get('tipo_atividade', ''),
                empresa_info.get('descricao_atividade', ''),
                empresa_info.get('canal_venda', ''),
                empresa_info.get('porte_empresa', ''),
                empresa_info.get('regime_tributario', ''),
                empresa_info.get('segmento_cest_preferencial', None)
            ))
            
            # Criar índices para performance
            self._create_indexes(cursor)
            
            conn.commit()
            
        print(f"✅ Banco de dados criado para empresa {empresa_id}: {db_path}")
        return db_path
    
    def _create_indexes(self, cursor):
        """Cria índices para otimizar consultas"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_produtos_gtin ON produtos_empresa(gtin)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos_empresa(nome_produto)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_produto ON classificacoes(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_ncm ON classificacoes(ncm_codigo)",
            "CREATE INDEX IF NOT EXISTS idx_classificacoes_cest ON classificacoes(cest_codigo)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_produto ON agente_acoes(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_agente_acoes_agente ON agente_acoes(agente_nome)",
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_produto ON agente_consultas(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_agente_consultas_agente ON agente_consultas(agente_nome)",
            "CREATE INDEX IF NOT EXISTS idx_historico_produto ON historico_mudancas(produto_id)",
            "CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_mudancas(data_mudanca)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def insert_produto(self, empresa_id: int, produto_data: Dict[str, Any]) -> int:
        """Insere um novo produto no banco da empresa"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO produtos_empresa 
                (gtin, nome_produto, descricao_original, descricao_enriquecida, 
                 categoria, marca, peso, unidade_medida, preco)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                produto_data.get('gtin'),
                produto_data.get('nome_produto'),
                produto_data.get('descricao_original'),
                produto_data.get('descricao_enriquecida'),
                produto_data.get('categoria'),
                produto_data.get('marca'),
                produto_data.get('peso'),
                produto_data.get('unidade_medida'),
                produto_data.get('preco')
            ))
            
            produto_id = cursor.lastrowid
            
            # Registrar histórico
            cursor.execute("""
                INSERT INTO historico_mudancas 
                (produto_id, tipo_mudanca, usuario, motivo)
                VALUES (?, 'criacao', ?, ?)
            """, (produto_id, produto_data.get('usuario', 'sistema'), 'Produto criado'))
            
            conn.commit()
            
        return produto_id
    
    def insert_classificacao(self, empresa_id: int, produto_id: int, 
                           classificacao_data: Dict[str, Any]) -> int:
        """Insere uma nova classificação para um produto"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO classificacoes 
                (produto_id, ncm_codigo, ncm_descricao, cest_codigo, cest_descricao,
                 confianca_ncm, confianca_cest, status, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                produto_id,
                classificacao_data.get('ncm_codigo'),
                classificacao_data.get('ncm_descricao'),
                classificacao_data.get('cest_codigo'),
                classificacao_data.get('cest_descricao'),
                classificacao_data.get('confianca_ncm'),
                classificacao_data.get('confianca_cest'),
                classificacao_data.get('status', 'pendente'),
                classificacao_data.get('observacoes')
            ))
            
            classificacao_id = cursor.lastrowid
            
            # Registrar histórico
            cursor.execute("""
                INSERT INTO historico_mudancas 
                (produto_id, classificacao_id, tipo_mudanca, usuario, motivo)
                VALUES (?, ?, 'criacao', ?, ?)
            """, (produto_id, classificacao_id, 
                  classificacao_data.get('usuario', 'sistema'), 
                  'Classificação criada'))
            
            conn.commit()
            
        return classificacao_id
    
    def insert_agente_acao(self, empresa_id: int, acao_data: Dict[str, Any]) -> int:
        """Registra uma ação de agente"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agente_acoes 
                (produto_id, classificacao_id, agente_nome, acao_tipo, 
                 input_dados, output_resultado, justificativa, confianca,
                 tempo_execucao, sucesso, erro_detalhes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acao_data.get('produto_id'),
                acao_data.get('classificacao_id'),
                acao_data.get('agente_nome'),
                acao_data.get('acao_tipo'),
                json.dumps(acao_data.get('input_dados', {}), ensure_ascii=False),
                json.dumps(acao_data.get('output_resultado', {}), ensure_ascii=False),
                acao_data.get('justificativa'),
                acao_data.get('confianca'),
                acao_data.get('tempo_execucao'),
                acao_data.get('sucesso', True),
                acao_data.get('erro_detalhes')
            ))
            
            acao_id = cursor.lastrowid
            conn.commit()
            
        return acao_id
    
    def insert_agente_consulta(self, empresa_id: int, consulta_data: Dict[str, Any]) -> int:
        """Registra uma consulta de agente"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agente_consultas 
                (produto_id, agente_nome, tipo_consulta, query_original,
                 query_processada, resultados_encontrados, resultado_detalhes,
                 relevancia_score, tempo_resposta, sucesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                consulta_data.get('produto_id'),
                consulta_data.get('agente_nome'),
                consulta_data.get('tipo_consulta'),
                consulta_data.get('query_original'),
                consulta_data.get('query_processada'),
                consulta_data.get('resultados_encontrados', 0),
                json.dumps(consulta_data.get('resultado_detalhes', {}), ensure_ascii=False),
                consulta_data.get('relevancia_score'),
                consulta_data.get('tempo_resposta'),
                consulta_data.get('sucesso', True)
            ))
            
            consulta_id = cursor.lastrowid
            conn.commit()
            
        return consulta_id
    
    def get_empresa_stats(self, empresa_id: int) -> Dict[str, Any]:
        """Obtém estatísticas da empresa"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        if not os.path.exists(db_path):
            return {"erro": "Banco da empresa não encontrado"}
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute("SELECT COUNT(*) FROM produtos_empresa WHERE ativo = 1")
            total_produtos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM classificacoes")
            total_classificacoes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM classificacoes WHERE status = 'aprovado'")
            aprovadas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM classificacoes WHERE status = 'pendente'")
            pendentes = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(confianca_ncm), AVG(confianca_cest) FROM classificacoes")
            confiancas = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(DISTINCT agente_nome) FROM agente_acoes")
            agentes_ativos = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT agente_nome, COUNT(*) as total_acoes 
                FROM agente_acoes 
                GROUP BY agente_nome
                ORDER BY total_acoes DESC
            """)
            acoes_por_agente = dict(cursor.fetchall())
            
            return {
                "empresa_id": empresa_id,
                "total_produtos": total_produtos,
                "total_classificacoes": total_classificacoes,
                "classificacoes_aprovadas": aprovadas,
                "classificacoes_pendentes": pendentes,
                "confianca_media_ncm": round(confiancas[0] or 0, 2),
                "confianca_media_cest": round(confiancas[1] or 0, 2),
                "agentes_ativos": agentes_ativos,
                "acoes_por_agente": acoes_por_agente,
                "taxa_aprovacao": round(aprovadas / total_classificacoes * 100, 1) if total_classificacoes > 0 else 0
            }
    
    def get_produto_detalhado(self, empresa_id: int, produto_id: int) -> Dict[str, Any]:
        """Obtém detalhes completos de um produto incluindo histórico de agentes"""
        db_path = self.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Dados do produto
            cursor.execute("SELECT * FROM produtos_empresa WHERE id = ?", (produto_id,))
            produto = dict(cursor.fetchone() or {})
            
            if not produto:
                return {"erro": "Produto não encontrado"}
            
            # Classificações
            cursor.execute("SELECT * FROM classificacoes WHERE produto_id = ? ORDER BY data_classificacao DESC", (produto_id,))
            classificacoes = [dict(row) for row in cursor.fetchall()]
            
            # Ações dos agentes
            cursor.execute("""
                SELECT * FROM agente_acoes 
                WHERE produto_id = ? 
                ORDER BY data_execucao DESC
            """, (produto_id,))
            acoes = []
            for row in cursor.fetchall():
                acao = dict(row)
                # Parse JSON fields
                try:
                    acao['input_dados'] = json.loads(acao['input_dados'] or '{}')
                    acao['output_resultado'] = json.loads(acao['output_resultado'] or '{}')
                except:
                    pass
                acoes.append(acao)
            
            # Consultas dos agentes
            cursor.execute("""
                SELECT * FROM agente_consultas 
                WHERE produto_id = ? 
                ORDER BY data_consulta DESC
            """, (produto_id,))
            consultas = []
            for row in cursor.fetchall():
                consulta = dict(row)
                # Parse JSON fields
                try:
                    consulta['resultado_detalhes'] = json.loads(consulta['resultado_detalhes'] or '{}')
                except:
                    pass
                consultas.append(consulta)
            
            # Histórico de mudanças
            cursor.execute("""
                SELECT * FROM historico_mudancas 
                WHERE produto_id = ? 
                ORDER BY data_mudanca DESC
            """, (produto_id,))
            historico = [dict(row) for row in cursor.fetchall()]
            
            return {
                "produto": produto,
                "classificacoes": classificacoes,
                "acoes_agentes": acoes,
                "consultas_agentes": consultas,
                "historico_mudancas": historico
            }
    
    def list_empresas_databases(self) -> List[Dict[str, Any]]:
        """Lista todos os bancos de empresas criados"""
        empresas = []
        
        for db_file in self.base_path.glob("empresa_*.db"):
            empresa_id = int(db_file.stem.split('_')[1])
            
            try:
                with sqlite3.connect(str(db_file)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT * FROM empresa_info WHERE id = ?", (empresa_id,))
                    info = dict(cursor.fetchone() or {})
                    
                    if info:
                        stats = self.get_empresa_stats(empresa_id)
                        empresas.append({
                            "empresa_id": empresa_id,
                            "database_path": str(db_file),
                            "info": info,
                            "stats": stats
                        })
            except Exception as e:
                print(f"Erro ao ler banco da empresa {empresa_id}: {e}")
        
        return empresas

    def create_golden_set_shared(self):
        """Cria o banco do Golden Set compartilhado entre todas as empresas"""
        with sqlite3.connect(self.golden_set_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS golden_set_produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gtin TEXT UNIQUE,
                    nome_produto TEXT NOT NULL,
                    descricao_padronizada TEXT,
                    ncm_codigo TEXT NOT NULL,
                    ncm_descricao TEXT,
                    cest_codigo TEXT,
                    cest_descricao TEXT,
                    categoria_padrao TEXT,
                    subcategoria TEXT,
                    confianca_validacao REAL DEFAULT 1.0,
                    origem_validacao TEXT, -- manual, automatica, consensus
                    numero_validacoes INTEGER DEFAULT 0,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ativo BOOLEAN DEFAULT 1,
                    observacoes TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS golden_set_validacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_golden_id INTEGER NOT NULL,
                    empresa_origem_id INTEGER,
                    validador TEXT,
                    tipo_validacao TEXT, -- manual, automatica
                    confianca REAL,
                    observacoes TEXT,
                    data_validacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_golden_id) REFERENCES golden_set_produtos (id)
                )
            """)
            
            # Índices para o Golden Set
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_golden_gtin ON golden_set_produtos(gtin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_golden_ncm ON golden_set_produtos(ncm_codigo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_golden_cest ON golden_set_produtos(cest_codigo)")
            
            conn.commit()
            
        print(f"✅ Golden Set compartilhado criado: {self.golden_set_db}")
