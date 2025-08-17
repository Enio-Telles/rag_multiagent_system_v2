#!/usr/bin/env python3
"""
Verificar estrutura do banco SQLite
"""

import sqlite3
from pathlib import Path

def check_database_structure():
    """Verifica a estrutura do banco de dados"""
    
    db_path = Path("data/unified_rag_system.db")
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    print(f"📊 Verificando banco: {db_path}")
    print(f"📁 Tamanho: {db_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print(f"\n📋 TABELAS ENCONTRADAS ({len(tables)}):")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"  📁 {table_name}: {count:,} registros")
            
            # Para ABC Farma, mostrar algumas informações adicionais
            if 'abc' in table_name.lower() or 'farma' in table_name.lower():
                print(f"     🔍 Detalhes da tabela ABC Farma:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"     📊 Colunas: {len(columns)}")
                
                # Mostrar algumas colunas importantes
                important_cols = ['descricao', 'principio_ativo', 'laboratorio', 'ncm']
                for col in columns:
                    col_name = col[1]
                    if any(imp in col_name.lower() for imp in important_cols):
                        print(f"        - {col_name}")
        
        # Verificar se existe alguma tabela ABC Farma
        abc_tables = [t[0] for t in tables if 'abc' in t[0].lower() or 'farma' in t[0].lower()]
        
        # Verificar explicitamente pela tabela abc_farma_products
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='abc_farma_products';")
        abc_specific = cursor.fetchone()
        
        if abc_specific:
            print(f"\n✅ Tabela abc_farma_products encontrada!")
            abc_tables.append('abc_farma_products')
        
        if abc_tables:
            print(f"\n✅ ABC Farma encontrado: {abc_tables}")
            
            # Testar uma consulta
            table_name = abc_tables[0]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            samples = cursor.fetchall()
            
            print(f"\n📋 PRIMEIROS 3 REGISTROS de {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            for i, sample in enumerate(samples, 1):
                print(f"\n  Registro {i}:")
                for j, value in enumerate(sample[:5]):  # Mostrar só primeiras 5 colunas
                    print(f"    {columns[j]}: {value}")
        else:
            print(f"\n❌ Nenhuma tabela ABC Farma encontrada!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

if __name__ == "__main__":
    check_database_structure()
