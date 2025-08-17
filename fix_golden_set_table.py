#!/usr/bin/env python3
"""
Script para corrigir a estrutura da tabela golden_set no PostgreSQL.
Adiciona a coluna 'descricao_completa' que está faltando.
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
    """Conecta com o banco PostgreSQL usando as credenciais do ambiente."""
    try:
        # Configurações do banco (ajuste conforme seu ambiente)
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

def fix_golden_set_table():
    """Adiciona a coluna descricao_completa à tabela golden_set se ela não existir."""
    
    connection = get_db_connection()
    if not connection:
        logger.error("❌ Não foi possível conectar com o banco de dados")
        return False
    
    try:
        cursor = connection.cursor()
        
        logger.info("🔍 Verificando estrutura atual da tabela golden_set...")
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'golden_set' 
            AND column_name = 'descricao_completa'
        """)
        
        existing_column = cursor.fetchone()
        
        if existing_column:
            logger.info("✅ Coluna 'descricao_completa' já existe na tabela golden_set")
            return True
        
        logger.info("⚡ Adicionando coluna 'descricao_completa' à tabela golden_set...")
        
        # Adicionar a coluna que está faltando
        cursor.execute("""
            ALTER TABLE golden_set 
            ADD COLUMN descricao_completa TEXT
        """)
        
        # Confirmar mudanças
        connection.commit()
        logger.info("✅ Coluna 'descricao_completa' adicionada com sucesso!")
        
        # Verificar a estrutura atualizada
        logger.info("🔍 Verificando estrutura atualizada...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'golden_set'
            AND column_name IN ('descricao_produto', 'descricao_completa')
            ORDER BY ordinal_position
        """)
        
        results = cursor.fetchall()
        logger.info("📊 Colunas de descrição na tabela golden_set:")
        for row in results:
            logger.info(f"   {row[0]}: {row[1]} (nullable: {row[2]})")
        
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
    logger.info("🚀 Script de Correção - Tabela golden_set no PostgreSQL")
    logger.info("=" * 60)
    
    logger.info("🎯 Problema: Coluna 'descricao_completa' não existe na tabela golden_set")
    logger.info("🔧 Solução: Adicionar coluna TEXT para descrições completas")
    logger.info("")
    
    success = fix_golden_set_table()
    
    if success:
        logger.info("✅ CORREÇÃO APLICADA COM SUCESSO!")
        logger.info("💡 Agora você pode executar novamente:")
        logger.info("   python src/main.py setup-review --start-api")
        logger.info("")
        logger.info("🌐 URLs disponíveis:")
        logger.info("   📊 Dashboard: http://localhost:8000/api/v1/dashboard/stats")
        logger.info("   🎯 Interface: http://localhost:8000/static/interface_revisao.html")
    else:
        logger.error("❌ ERRO na aplicação da correção")
        logger.error("💡 Verifique as credenciais do banco de dados")

if __name__ == "__main__":
    main()
