#!/usr/bin/env python3
"""
Script para migrar banco de dados - adicionar colunas de explicação dos agentes
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Obter conexão com o banco de dados PostgreSQL"""
    try:
        # Usar configurações específicas do sistema
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='db_04565289005297',
            user='postgres',
            password='sefin'
        )
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise

def column_exists(cursor, table_name, column_name):
    """Verificar se uma coluna existe em uma tabela"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def add_columns_if_not_exist(cursor, table_name, columns):
    """Adicionar colunas se elas não existirem"""
    for column_name, column_definition in columns.items():
        if not column_exists(cursor, table_name, column_name):
            try:
                query = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                    sql.Identifier(table_name),
                    sql.Identifier(column_name),
                    sql.SQL(column_definition)
                )
                cursor.execute(query)
                logger.info(f"✅ Coluna {column_name} adicionada à tabela {table_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar coluna {column_name}: {e}")
                raise
        else:
            logger.info(f"⚠️ Coluna {column_name} já existe na tabela {table_name}")

def create_explicacoes_agentes_table(cursor):
    """Criar tabela explicacoes_agentes se não existir"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = 'explicacoes_agentes'
        );
    """)
    
    if not cursor.fetchone()[0]:
        try:
            cursor.execute("""
                CREATE TABLE explicacoes_agentes (
                    id SERIAL PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    classificacao_id INTEGER,
                    agente_nome VARCHAR(50) NOT NULL,
                    agente_versao VARCHAR(20) DEFAULT '1.0',
                    input_original TEXT,
                    contexto_utilizado JSONB,
                    etapas_processamento JSONB,
                    decisoes_tomadas JSONB,
                    output_gerado TEXT,
                    confianca_resultado NUMERIC(5,2),
                    tempo_processamento_ms INTEGER,
                    tokens_utilizados INTEGER,
                    memoria_utilizada_mb NUMERIC(8,2),
                    observacoes TEXT,
                    timestamp_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadados_extras JSONB
                );
                
                CREATE INDEX idx_explicacoes_agentes_produto_id ON explicacoes_agentes(produto_id);
                CREATE INDEX idx_explicacoes_agentes_agente_nome ON explicacoes_agentes(agente_nome);
                CREATE INDEX idx_explicacoes_agentes_timestamp ON explicacoes_agentes(timestamp_execucao);
            """)
            logger.info("✅ Tabela explicacoes_agentes criada com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabela explicacoes_agentes: {e}")
            raise
    else:
        logger.info("⚠️ Tabela explicacoes_agentes já existe")

def main():
    """Função principal de migração"""
    logger.info("🚀 Iniciando migração do banco de dados...")
    
    try:
        # Conectar ao banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("✅ Conectado ao banco de dados")
        
        # 1. Adicionar colunas de explicação à tabela classificacoes_revisao
        logger.info("📋 Adicionando colunas de explicação à tabela classificacoes_revisao...")
        
        explicacao_columns = {
            'explicacao_agente_expansao': 'TEXT',
            'explicacao_agente_ncm': 'TEXT', 
            'explicacao_agente_cest': 'TEXT',
            'explicacao_agente_reconciliador': 'TEXT',
            'tempo_revisao_segundos': 'INTEGER',
            'complexidade_produto': 'VARCHAR(20)'
        }
        
        add_columns_if_not_exist(cursor, 'classificacoes_revisao', explicacao_columns)
        
        # 2. Adicionar colunas enriquecidas à tabela golden_set_entries
        logger.info("📋 Adicionando colunas enriquecidas à tabela golden_set_entries...")
        
        golden_set_columns = {
            'categoria_principal': 'VARCHAR(100)',
            'subcategoria': 'VARCHAR(100)', 
            'marca_identificada': 'VARCHAR(100)',
            'modelo_produto': 'VARCHAR(100)',
            'caracteristicas_tecnicas': 'TEXT',
            'contexto_uso': 'TEXT',
            'similaridade_produtos': 'TEXT'
        }
        
        add_columns_if_not_exist(cursor, 'golden_set_entries', golden_set_columns)
        
        # 3. Criar tabela explicacoes_agentes
        logger.info("📋 Criando tabela explicacoes_agentes...")
        create_explicacoes_agentes_table(cursor)
        
        # Commit das alterações
        conn.commit()
        logger.info("✅ Migração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a migração: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("🔌 Conexão com banco encerrada")

if __name__ == "__main__":
    main()
