#!/usr/bin/env python3
"""
Script para corrigir completamente a estrutura da tabela golden_set no PostgreSQL.
Adiciona todas as colunas faltantes necessárias para o sistema funcionar.
"""

import psycopg2
import logging
from psycopg2 import sql

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Conecta com o banco PostgreSQL usando as credenciais do ambiente."""
    try:
        # Configurações do banco (mesmas credenciais usadas pelo sistema)
        connection = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="db_04565289005297",
            user="postgres",
            password="sefin"
        )
        return connection
    except Exception as e:
        logger.error(f"Erro ao conectar com banco: {e}")
        return None

def check_columns_exist(cursor, table_name, columns):
    """Verifica quais colunas existem na tabela."""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    
    existing_columns = {row[0] for row in cursor.fetchall()}
    return existing_columns

def fix_golden_set_complete():
    """Adiciona todas as colunas faltantes à tabela golden_set."""
    
    connection = get_db_connection()
    if not connection:
        logger.error("❌ Não foi possível conectar ao banco de dados")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Definir todas as colunas que deveriam existir
        required_columns = {
            'explicacao_expansao': 'TEXT',
            'explicacao_agregacao': 'TEXT', 
            'explicacao_ncm': 'TEXT',
            'explicacao_cest': 'TEXT',
            'explicacao_reconciliacao': 'TEXT',
            'palavras_chave_fiscais': 'TEXT',
            'categoria_produto': 'VARCHAR(100)',
            'material_predominante': 'VARCHAR(100)',
            'aplicacoes_uso': 'TEXT',
            'caracteristicas_tecnicas': 'TEXT',
            'contexto_uso': 'TEXT',
            'similaridade_produtos': 'TEXT'
        }
        
        # Verificar quais colunas já existem
        existing_columns = check_columns_exist(cursor, 'golden_set', required_columns.keys())
        
        logger.info(f"✅ Colunas existentes: {sorted(existing_columns)}")
        
        # Adicionar colunas faltantes
        missing_columns = set(required_columns.keys()) - existing_columns
        
        if not missing_columns:
            logger.info("✅ Todas as colunas já existem na tabela golden_set!")
            return True
            
        logger.info(f"🔧 Adicionando {len(missing_columns)} colunas faltantes...")
        
        for column_name in sorted(missing_columns):
            column_type = required_columns[column_name]
            
            try:
                alter_sql = f"ALTER TABLE golden_set ADD COLUMN {column_name} {column_type};"
                cursor.execute(alter_sql)
                logger.info(f"  ✅ Coluna '{column_name}' adicionada ({column_type})")
                
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    logger.info(f"  ℹ️ Coluna '{column_name}' já existe")
                else:
                    logger.error(f"  ❌ Erro ao adicionar '{column_name}': {e}")
                    
        # Confirmar as mudanças
        connection.commit()
        
        # Verificar o resultado final
        final_columns = check_columns_exist(cursor, 'golden_set', required_columns.keys())
        missing_final = set(required_columns.keys()) - final_columns
        
        if not missing_final:
            logger.info("✅ Todas as colunas foram adicionadas com sucesso!")
            
            # Mostrar estatísticas da tabela
            cursor.execute("SELECT COUNT(*) FROM golden_set")
            count = cursor.fetchone()[0]
            logger.info(f"📊 Tabela golden_set tem {count} registros")
            
            return True
        else:
            logger.error(f"❌ Ainda faltam colunas: {sorted(missing_final)}")
            return False
            
    except psycopg2.Error as e:
        logger.error(f"❌ Erro PostgreSQL: {e}")
        connection.rollback()
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        connection.rollback()
        return False
        
    finally:
        cursor.close()
        connection.close()
        logger.info("🔗 Conexão com banco fechada")

def main():
    """Função principal."""
    logger.info("🚀 Script de Correção Completa - Tabela golden_set no PostgreSQL")
    logger.info("="*70)
    
    success = fix_golden_set_complete()
    
    if success:
        logger.info("="*70)
        logger.info("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("🎯 A tabela golden_set agora tem todas as colunas necessárias")
        logger.info("🚀 O sistema pode ser reiniciado normalmente")
    else:
        logger.error("="*70)
        logger.error("❌ FALHA NA CORREÇÃO!")
        logger.error("🔧 Verifique os logs acima para detalhes")

if __name__ == "__main__":
    main()
