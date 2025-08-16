#!/usr/bin/env python3
"""
Script para migração: renomear gtin_original para codigo_barra
"""

import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import engine, test_connection

def aplicar_migracao_codigo_barra():
    """Migrar de GTIN para codigo_barra"""
    
    print("🔧 Iniciando migração GTIN → codigo_barra...")
    
    # Testar conexão ao banco
    if not test_connection():
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
        
    print(f"✅ Conectado ao banco de dados")
    
    operacoes_realizadas = []
    
    # 1. Adicionar coluna codigo_barra
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE classificacoes_revisao 
                ADD COLUMN codigo_barra VARCHAR(50);
            """))
            operacoes_realizadas.append("codigo_barra adicionada")
            print("✅ Coluna 'codigo_barra' adicionada")
    except (OperationalError, ProgrammingError) as e:
        if "already exists" in str(e) or "duplicate column" in str(e):
            print("⚠️  Coluna 'codigo_barra' já existe")
        else:
            print(f"❌ Erro ao adicionar 'codigo_barra': {e}")
    
    # 2. Migrar dados de gtin_original para codigo_barra
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE classificacoes_revisao 
                SET codigo_barra = gtin_original 
                WHERE gtin_original IS NOT NULL 
                  AND (codigo_barra IS NULL OR codigo_barra = '');
            """))
            
            if result.rowcount > 0:
                operacoes_realizadas.append(f"{result.rowcount} códigos migrados")
                print(f"✅ Migrados {result.rowcount} códigos de gtin_original para codigo_barra")
            else:
                print("⚠️  Nenhum dado migrado")
                
    except Exception as e:
        print(f"❌ Erro na migração de dados: {e}")
    
    # 3. Adicionar campos para revisão humana do código de barras
    campos_revisao = [
        ("codigo_barra_status", "VARCHAR(20) DEFAULT 'PENDENTE_VERIFICACAO'"),
        ("codigo_barra_corrigido", "VARCHAR(50)"),
        ("codigo_barra_observacoes", "TEXT")
    ]
    
    for nome_campo, definicao in campos_revisao:
        try:
            with engine.begin() as conn:
                conn.execute(text(f"""
                    ALTER TABLE classificacoes_revisao 
                    ADD COLUMN {nome_campo} {definicao};
                """))
                operacoes_realizadas.append(f"{nome_campo} adicionado")
                print(f"✅ Campo '{nome_campo}' adicionado")
        except (OperationalError, ProgrammingError) as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print(f"⚠️  Campo '{nome_campo}' já existe")
            else:
                print(f"❌ Erro ao adicionar '{nome_campo}': {e}")
    
    # 4. Verificar estrutura final
    verificar_estrutura_codigo_barra()
    
    print(f"\n🎯 Migração concluída!")
    print(f"📊 Operações realizadas: {len(operacoes_realizadas)}")
    if operacoes_realizadas:
        for op in operacoes_realizadas:
            print(f"  ✅ {op}")
    
    return True

def verificar_estrutura_codigo_barra():
    """Verificar a estrutura relacionada ao código de barras"""
    
    print("\n🔍 Verificando estrutura código de barras...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'classificacoes_revisao'
                  AND (column_name LIKE '%codigo_barra%' OR column_name LIKE '%gtin%')
                  AND table_schema = 'public'
                ORDER BY column_name;
            """))
            
            colunas = result.fetchall()
            
            print(f"📋 Colunas relacionadas a código de barras ({len(colunas)}):")
            
            campos_esperados = [
                'codigo_barra', 'codigo_barra_status', 'codigo_barra_corrigido', 
                'codigo_barra_observacoes'
            ]
            
            colunas_encontradas = [col[0] for col in colunas]
            
            for campo in campos_esperados:
                if campo in colunas_encontradas:
                    print(f"   ✅ {campo}")
                else:
                    print(f"   ❌ {campo} - FALTANDO")
            
            print(f"\n📝 Todas as colunas código/GTIN:")
            for col_name, data_type, is_nullable in colunas:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"   • {col_name} ({data_type}) {nullable}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

if __name__ == "__main__":
    print("🚀 Script de Migração - GTIN → codigo_barra")
    print("=" * 60)
    
    success = aplicar_migracao_codigo_barra()
    
    if success:
        print("\n✅ Migração aplicada com sucesso!")
        print("🔄 Próximos passos:")
        print("   1. Atualizar modelos do banco de dados")
        print("   2. Atualizar API para usar codigo_barra")
        print("   3. Atualizar interface web")
        print("   4. Remover validação automática pelos agentes")
    else:
        print("\n❌ Erro na migração - verifique os logs acima")
        sys.exit(1)
