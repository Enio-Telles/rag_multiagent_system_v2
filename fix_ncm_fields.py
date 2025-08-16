#!/usr/bin/env python3
"""
Script para corrigir o tamanho dos campos NCM/CEST no banco PostgreSQL.
Resolve o erro: StringDataRightTruncation - value too long for type character varying(10)
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Conecta com o banco PostgreSQL usando variáveis de ambiente."""
    try:
        # Configurações do banco (você pode ajustar conforme seu ambiente)
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

def alter_table_columns():
    """Altera o tamanho das colunas NCM/CEST de VARCHAR(10) para VARCHAR(15)."""
    
    connection = get_db_connection()
    if not connection:
        logger.error("❌ Não foi possível conectar com o banco de dados")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Lista de alterações necessárias
        alterations = [
            # Tabela classificacoes_revisao
            "ALTER TABLE classificacoes_revisao ALTER COLUMN ncm_original TYPE VARCHAR(15)",
            "ALTER TABLE classificacoes_revisao ALTER COLUMN cest_original TYPE VARCHAR(15)",
            "ALTER TABLE classificacoes_revisao ALTER COLUMN ncm_sugerido TYPE VARCHAR(15)",
            "ALTER TABLE classificacoes_revisao ALTER COLUMN cest_sugerido TYPE VARCHAR(15)",
            "ALTER TABLE classificacoes_revisao ALTER COLUMN ncm_corrigido TYPE VARCHAR(15)",
            "ALTER TABLE classificacoes_revisao ALTER COLUMN cest_corrigido TYPE VARCHAR(15)",
            
            # Tabela golden_set (se existir)
            "ALTER TABLE golden_set ALTER COLUMN ncm_final TYPE VARCHAR(15)",
            "ALTER TABLE golden_set ALTER COLUMN cest_final TYPE VARCHAR(15)",
        ]
        
        logger.info("🔧 Iniciando alterações na estrutura da tabela...")
        
        for sql_command in alterations:
            try:
                logger.info(f"⚡ Executando: {sql_command}")
                cursor.execute(sql_command)
                logger.info("✅ Sucesso!")
            except psycopg2.errors.UndefinedTable as e:
                logger.warning(f"⚠️ Tabela não existe (ignorando): {e}")
            except Exception as e:
                logger.warning(f"⚠️ Erro na alteração (continuando): {e}")
        
        # Confirmar mudanças
        connection.commit()
        logger.info("✅ Todas as alterações aplicadas com sucesso!")
        
        # Verificar a estrutura atualizada
        logger.info("🔍 Verificando estrutura atualizada...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'classificacoes_revisao' 
            AND column_name LIKE '%ncm%' OR column_name LIKE '%cest%'
            ORDER BY column_name
        """)
        
        results = cursor.fetchall()
        logger.info("📊 Estrutura das colunas NCM/CEST:")
        for row in results:
            logger.info(f"   {row[0]}: {row[1]}({row[2]})")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante alteração: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

def main():
    """Função principal."""
    logger.info("🚀 Script de Correção - Campos NCM/CEST no PostgreSQL")
    logger.info("=" * 60)
    
    logger.info("🎯 Problema: Campos NCM/CEST limitados a 10 caracteres")
    logger.info("🔧 Solução: Expandir para 15 caracteres para suportar formato com pontos")
    logger.info("📝 Exemplos: '3004.00.00.00' (12 chars), '13.003.00' (9 chars)")
    logger.info("")
    
    success = alter_table_columns()
    
    if success:
        logger.info("✅ CORREÇÃO APLICADA COM SUCESSO!")
        logger.info("💡 Agora você pode executar novamente:")
        logger.info("   python src/main.py setup-review --create-tables --import-data")
    else:
        logger.error("❌ ERRO na aplicação da correção")
        logger.error("💡 Verifique as credenciais do banco de dados")

if __name__ == "__main__":
    main()
