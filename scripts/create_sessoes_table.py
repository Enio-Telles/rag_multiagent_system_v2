"""
Script para criar tabela de sessões de processamento
"""

import sqlite3
import os
from pathlib import Path

def create_sessoes_table():
    """Criar tabela para controlar sessões de processamento"""
    
    # Caminho do banco SQLite unificado
    db_path = Path("../data/unified_rag_system.db")
    
    if not db_path.exists():
        print("❌ Banco de dados unificado não encontrado. Execute primeiro o setup.")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Criar tabela de sessões de processamento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_processamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessao_id TEXT UNIQUE NOT NULL,
                tipo_processo TEXT NOT NULL,
                status TEXT DEFAULT 'iniciado',
                progresso INTEGER DEFAULT 0,
                total_items INTEGER DEFAULT 0,
                items_processados INTEGER DEFAULT 0,
                mensagem TEXT,
                parametros TEXT,
                data_inicio TEXT NOT NULL,
                data_atualizacao TEXT NOT NULL,
                data_conclusao TEXT,
                erro_detalhes TEXT
            )
        """)
        
        # Criar índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessao_id ON sessoes_processamento(sessao_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON sessoes_processamento(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_inicio ON sessoes_processamento(data_inicio)")
        
        conn.commit()
        conn.close()
        
        print("✅ Tabela 'sessoes_processamento' criada com sucesso")
        print("📊 Índices criados para otimização de consultas")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {str(e)}")

if __name__ == "__main__":
    create_sessoes_table()
