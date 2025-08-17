#!/usr/bin/env python3
"""
Migração Simplificada ABC Farma para SQLite
Versão otimizada sem embeddings para teste
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
import sqlite3
import hashlib

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.unified_sqlite_models import UnifiedBase, ABCFarmaProduct
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class ABCFarmaMigratorSimple:
    """Migrador simplificado de dados ABC Farma para SQLite"""
    
    def __init__(self, db_path: str = "data/unified_rag_system.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Criar tabelas se não existirem"""
        print("🔄 Criando tabelas...")
        UnifiedBase.metadata.create_all(self.engine)
        print("✅ Tabelas criadas!")
        
    def load_abc_farma_data(self) -> pd.DataFrame:
        """Carregar dados ABC Farma do Excel"""
        excel_path = os.path.join("data", "raw", "Tabela_ABC_Farma_GTIN_modificado.xlsx")
        
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Arquivo {excel_path} não encontrado!")
            
        print(f"🔄 Carregando dados de {excel_path}...")
        
        try:
            df = pd.read_excel(excel_path)
            print(f"✅ Dados carregados: {len(df)} registros")
            
            # Verificar colunas
            print(f"Colunas: {list(df.columns)}")
            
            # Filtrar apenas medicamentos se possível
            if 'CATEGORIA' in df.columns:
                medicamentos_df = df[df['CATEGORIA'].str.contains(
                    'MEDICAMENTO', case=False, na=False
                )]
                print(f"📊 Produtos farmacêuticos identificados: {len(medicamentos_df)}")
                return medicamentos_df
            else:
                print("⚠️ Coluna 'CATEGORIA' não encontrada. Usando todos os dados.")
                return df
                
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise
            
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar nomes das colunas"""
        column_mapping = {
            'codigo_barra': 'codigo_barra',
            'MARCA': 'marca',
            'DESCRICAO COMPLETA': 'descricao_completa',
            'DESCRICAO1': 'descricao1',
            'DESCRICAO2': 'descricao2',
            'características específicas (dosagem, embalagem, quantidade)': 'apresentacao',
            'características específicas (principio ativo do medicamento)': 'principio_ativo',
            'CATEGORIA': 'categoria'
        }
        
        print("🔄 Normalizando nomes das colunas...")
        
        # Renomear colunas existentes
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
                print(f"✅ Renomeado: '{old_name}' -> '{new_name}'")
                
        return df
        
    def clean_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remover duplicatas por código de barras"""
        print(f"🔄 Verificando duplicatas...")
        original_count = len(df)
        
        # Remover duplicatas por código de barras
        df_clean = df.drop_duplicates(subset=['codigo_barra'], keep='first')
        
        duplicates_removed = original_count - len(df_clean)
        print(f"✅ Removidas {duplicates_removed} duplicatas")
        print(f"📊 Registros únicos: {len(df_clean)}")
        
        return df_clean
        
    def process_abc_farma_record(self, row: pd.Series) -> dict:
        """Processar um registro ABC Farma (versão simplificada)"""
        
        # Dados básicos
        codigo_barra = str(row.get('codigo_barra', '')).strip()
        if not codigo_barra or codigo_barra == 'nan':
            codigo_barra = f"ABC_{hashlib.md5(str(row).encode()).hexdigest()[:10]}"
            
        descricao_completa = str(row.get('descricao_completa', '')).strip()
        if not descricao_completa or descricao_completa == 'nan':
            descricao_completa = f"Produto Farmacêutico {codigo_barra}"
            
        # Preparar dados para inserção (sem embeddings por enquanto)
        data = {
            'codigo_barra': codigo_barra,
            'gtin': codigo_barra,  # Usar mesmo valor
            'descricao_completa': descricao_completa,
            'descricao1': str(row.get('descricao1', ''))[:500] or None,
            'descricao2': str(row.get('descricao2', ''))[:500] or None,
            'marca': str(row.get('marca', ''))[:200] or None,
            'laboratorio': str(row.get('marca', ''))[:200] or None,  # Usar marca como laboratório
            'categoria': str(row.get('categoria', ''))[:100] or None,
            'principio_ativo': str(row.get('principio_ativo', ''))[:500] or None,
            'apresentacao': str(row.get('apresentacao', ''))[:300] or None,
            'ncm_farmaceutico': "30049099",
            'cest_farmaceutico': "13.001.00",
            'fonte_dados': "ABC_FARMA",
            'confiabilidade_dados': 1.0,
            'validado_farmaceutico': True,
            'ativo': True,
            'embedding_descricao': None,  # Sem embeddings inicialmente
            'embedding_principio_ativo': None
        }
        
        # Tags de busca
        tags = []
        if data['marca']: tags.append(data['marca'].lower())
        if data['categoria']: tags.append(data['categoria'].lower())
        if data['principio_ativo']: 
            tags.extend([p.strip().lower() for p in data['principio_ativo'].split() if len(p.strip()) > 2])
        
        data['tags_busca'] = list(set(tags))[:10]  # Limitar tags
        
        return data
        
    def migrate_data(self, batch_size: int = 100):
        """Migrar dados ABC Farma para SQLite"""
        
        # Carregar dados
        df = self.load_abc_farma_data()
        df = self.normalize_column_names(df)
        df = self.clean_duplicates(df)
        
        session = self.Session()
        
        try:
            # Verificar se já existem dados
            existing_count = session.query(ABCFarmaProduct).count()
            if existing_count > 0:
                print(f"⚠️  Já existem {existing_count} registros ABC Farma.")
                print("🔄 Removendo dados existentes...")
                session.query(ABCFarmaProduct).delete()
                session.commit()
                
            print(f"🔄 Iniciando migração de {len(df)} registros...")
            
            total_migrated = 0
            total_errors = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                batch_records = []
                
                for idx, row in batch.iterrows():
                    try:
                        record_data = self.process_abc_farma_record(row)
                        batch_records.append(ABCFarmaProduct(**record_data))
                        
                    except Exception as e:
                        print(f"⚠️  Erro no registro {idx}: {e}")
                        total_errors += 1
                        continue
                        
                # Inserir lote
                if batch_records:
                    try:
                        session.add_all(batch_records)
                        session.commit()
                        total_migrated += len(batch_records)
                        
                        print(f"✅ Migrados {total_migrated}/{len(df)} registros "
                              f"(Erros: {total_errors})")
                              
                    except Exception as e:
                        print(f"❌ Erro ao inserir lote: {e}")
                        session.rollback()
                        total_errors += len(batch_records)
                        
            print(f"🎉 Migração concluída!")
            print(f"✅ Total migrado: {total_migrated}")
            print(f"❌ Total erros: {total_errors}")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def test_search(self):
        """Testar busca básica"""
        session = self.Session()
        
        try:
            # Contar produtos
            total = session.query(ABCFarmaProduct).count()
            print(f"📊 Total de produtos ABC Farma: {total}")
            
            # Buscar por texto
            dipirona = session.query(ABCFarmaProduct).filter(
                ABCFarmaProduct.descricao_completa.contains('DIPIRONA')
            ).limit(5).all()
            
            print(f"🔍 Produtos com 'DIPIRONA': {len(dipirona)}")
            for product in dipirona:
                print(f"  - {product.descricao_completa[:60]}...")
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
        finally:
            session.close()

def main():
    """Função principal"""
    print("=" * 60)
    print("🏥 MIGRAÇÃO SIMPLES ABC FARMA PARA SQLITE")
    print("=" * 60)
    
    try:
        migrator = ABCFarmaMigratorSimple()
        
        # 1. Criar tabelas
        migrator.create_tables()
        
        # 2. Migrar dados
        migrator.migrate_data()
        
        # 3. Testar busca
        migrator.test_search()
        
        print("🎉 Migração ABC Farma simples concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
