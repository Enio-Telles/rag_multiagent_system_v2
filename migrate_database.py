#!/usr/bin/env python3
"""
Script para aplicar migração: adicionar colunas relacionadas a GTIN e descrição completa
"""

import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import engine, test_connection

def aplicar_migracao():
    """Aplicar migração para adicionar novas colunas"""
    
    print("🔧 Iniciando migração do banco de dados...")
    
    # Testar conexão ao banco
    if not test_connection():
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
        
    print(f"✅ Conectado ao banco de dados")
    
    # Lista de colunas a serem adicionadas
    colunas_adicionadas = []
    
    # Lista de comandos SQL para executar
    comandos = [
        ("descricao_completa", "ALTER TABLE classificacoes_revisao ADD COLUMN descricao_completa TEXT;"),
        ("gtin_original", "ALTER TABLE classificacoes_revisao ADD COLUMN gtin_original VARCHAR(50);"),
        ("gtin_status", "ALTER TABLE classificacoes_revisao ADD COLUMN gtin_status VARCHAR(20) DEFAULT 'PENDENTE';"),
        ("gtin_corrigido", "ALTER TABLE classificacoes_revisao ADD COLUMN gtin_corrigido VARCHAR(50);"),
        ("gtin_observacoes", "ALTER TABLE classificacoes_revisao ADD COLUMN gtin_observacoes TEXT;")
    ]
    
    # Executar cada comando em uma transação separada
    for nome_coluna, comando_sql in comandos:
        try:
            with engine.begin() as conn:
                conn.execute(text(comando_sql))
                colunas_adicionadas.append(nome_coluna)
                print(f"✅ Coluna '{nome_coluna}' adicionada")
        except (OperationalError, ProgrammingError) as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print(f"⚠️  Coluna '{nome_coluna}' já existe")
            else:
                print(f"❌ Erro ao adicionar '{nome_coluna}': {e}")
    
    # Migrar dados do codigo_barra para gtin_original (em transação separada)
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE classificacoes_revisao 
                SET gtin_original = codigo_barra 
                WHERE codigo_barra IS NOT NULL 
                  AND (gtin_original IS NULL OR gtin_original = '');
            """))
            
            if result.rowcount > 0:
                print(f"✅ Migrados {result.rowcount} códigos de barra para gtin_original")
            else:
                print("⚠️  Nenhum dado migrado de codigo_barra para gtin_original")
                
    except Exception as e:
        print(f"⚠️  Erro na migração de dados: {e}")
    
    print(f"\n🎯 Migração concluída!")
    print(f"📊 Colunas processadas: {len(comandos)}")
    if colunas_adicionadas:
        print(f"✅ Colunas adicionadas: {', '.join(colunas_adicionadas)}")
    
    # Verificar estrutura da tabela
    verificar_estrutura_tabela()
    
    return True

def verificar_estrutura_tabela():
    """Verificar a estrutura atual da tabela"""
    
    print("\n🔍 Verificando estrutura da tabela...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'classificacoes_revisao'
                  AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            
            colunas = result.fetchall()
            
            print(f"📋 Tabela 'classificacoes_revisao' possui {len(colunas)} colunas:")
            
            # Verificar colunas críticas
            colunas_criticas = [
                'descricao_completa', 'gtin_original', 'gtin_status', 
                'gtin_corrigido', 'gtin_observacoes'
            ]
            
            colunas_encontradas = [col[0] for col in colunas]
            
            for coluna in colunas_criticas:
                if coluna in colunas_encontradas:
                    print(f"   ✅ {coluna}")
                else:
                    print(f"   ❌ {coluna} - FALTANDO")
            
            print(f"\n📝 Todas as colunas:")
            for col_name, data_type, is_nullable in colunas:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"   • {col_name} ({data_type}) {nullable}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

if __name__ == "__main__":
    print("🚀 Script de Migração - Colunas GTIN e Descrição Completa")
    print("=" * 60)
    
    success = aplicar_migracao()
    
    if success:
        print("\n✅ Migração aplicada com sucesso!")
        print("🔄 Agora você pode executar novamente:")
        print("   python src/main.py setup-review --create-tables --import-data")
    else:
        print("\n❌ Erro na migração - verifique os logs acima")
        sys.exit(1)
