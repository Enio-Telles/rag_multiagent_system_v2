#!/usr/bin/env python3
"""
Migração dos dados ABC Farma para SQLite com embeddings para busca por similaridade
Autor: Sistema IA RAG v2
Data: 2024
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
import sqlite3
import pickle
import hashlib

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.unified_sqlite_models import UnifiedBase, ABCFarmaProduct
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer

class ABCFarmaMigrator:
    """Migrador de dados ABC Farma para SQLite com embeddings"""
    
    def __init__(self, db_path: str = "unified_rag_system.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Modelo para embeddings
        print("🔄 Carregando modelo de embeddings...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Modelo de embeddings carregado!")
        
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
            
            # Filtrar apenas medicamentos (categoria específica)
            if 'categoria' in df.columns:
                # Verificar se existem produtos categorizados como MEDICAMENTO
                medicamentos_df = df[df['categoria'].str.contains(
                    'MEDICAMENTO', case=False, na=False
                )]
                print(f"📊 Produtos farmacêuticos identificados: {len(medicamentos_df)}")
                
                if len(medicamentos_df) == 0:
                    print("⚠️ Nenhum medicamento encontrado. Usando todos os dados.")
                    return df
                else:
                    return medicamentos_df
            else:
                print("⚠️ Coluna 'categoria' não encontrada. Usando todos os dados.")
                return df
                
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise
            
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar nomes das colunas"""
        column_mapping = {
            # Mapeamento baseado no arquivo real
            'codigo_barra': 'codigo_barra',
            'MARCA': 'marca',
            'DESCRICAO COMPLETA': 'descricao_completa',
            'DESCRICAO1': 'descricao1',
            'DESCRICAO2': 'descricao2',
            'características específicas (dosagem, embalagem, quantidade)': 'apresentacao',
            'características específicas (principio ativo do medicamento)': 'principio_ativo',
            'CATEGORIA': 'categoria',
            
            # Mapeamentos alternativos (caso existam)
            'Codigo de Barras': 'codigo_barra',
            'Marca': 'marca',
            'Descricao Completa': 'descricao_completa',
            'Descricao1': 'descricao1',
            'Descricao2': 'descricao2',
            'Categoria': 'categoria',
            'Principio Ativo': 'principio_ativo',
            'Concentracao': 'concentracao',
            'Apresentacao': 'apresentacao',
            'Laboratorio': 'laboratorio'
        }
        
        print("🔄 Normalizando nomes das colunas...")
        print(f"Colunas originais: {list(df.columns)}")
        
        # Renomear colunas existentes
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
                print(f"✅ Renomeado: '{old_name}' -> '{new_name}'")
                
        print(f"✅ Colunas normalizadas: {list(df.columns)}")
        return df
        
    def generate_embeddings(self, text: str) -> bytes:
        """Gerar embeddings para um texto"""
        if pd.isna(text) or text == "":
            text = "produto farmacêutico"
            
        # Limitar tamanho do texto
        text = str(text)[:1000]
        
        # Gerar embedding
        embedding = self.embedding_model.encode(text)
        
        # Serializar como bytes
        return pickle.dumps(embedding.astype(np.float32))
        
    def process_abc_farma_record(self, row: pd.Series) -> dict:
        """Processar um registro ABC Farma"""
        
        # Dados básicos
        codigo_barra = str(row.get('codigo_barra', '')).strip()
        if not codigo_barra or codigo_barra == 'nan':
            codigo_barra = f"ABC_{hashlib.md5(str(row).encode()).hexdigest()[:10]}"
            
        descricao_completa = str(row.get('descricao_completa', '')).strip()
        if not descricao_completa or descricao_completa == 'nan':
            descricao_completa = f"Produto Farmacêutico {codigo_barra}"
            
        # Preparar dados para inserção
        data = {
            'codigo_barra': codigo_barra,
            'gtin': str(row.get('gtin', codigo_barra)),  # GTIN pode ser igual ao código de barras
            'descricao_completa': descricao_completa,
            'descricao1': str(row.get('descricao1', ''))[:500] or None,
            'descricao2': str(row.get('descricao2', ''))[:500] or None,
            'marca': str(row.get('marca', ''))[:200] or None,
            'laboratorio': str(row.get('laboratorio', row.get('marca', '')))[:200] or None,  # Usar marca como laboratório se não existir
            'categoria': str(row.get('categoria', ''))[:100] or None,
            'principio_ativo': str(row.get('principio_ativo', ''))[:500] or None,
            'apresentacao': str(row.get('apresentacao', ''))[:300] or None,
            'concentracao': str(row.get('concentracao', ''))[:200] or None,
            'ncm_farmaceutico': "30049099",  # NCM padrão para produtos farmacêuticos
            'cest_farmaceutico': "13.001.00",  # CEST padrão para produtos farmacêuticos
            'fonte_dados': "ABC_FARMA",
            'confiabilidade_dados': 1.0,
            'validado_farmaceutico': True,
            'ativo': True
        }
        
        # Gerar embeddings
        texto_para_embedding = f"{descricao_completa} {data['marca']} {data['principio_ativo']}"
        data['embedding_descricao'] = self.generate_embeddings(texto_para_embedding)
        
        if data['principio_ativo']:
            data['embedding_principio_ativo'] = self.generate_embeddings(data['principio_ativo'])
        
        # Tags de busca
        tags = []
        if data['marca']: tags.append(data['marca'].lower())
        if data['categoria']: tags.append(data['categoria'].lower())
        if data['principio_ativo']: tags.extend(data['principio_ativo'].lower().split())
        
        data['tags_busca'] = list(set(tags))
        
        return data
        
    def migrate_data(self, batch_size: int = 100):
        """Migrar dados ABC Farma para SQLite"""
        
        # Carregar dados
        df = self.load_abc_farma_data()
        df = self.normalize_column_names(df)
        
        session = self.Session()
        
        try:
            # Verificar se já existem dados
            existing_count = session.query(ABCFarmaProduct).count()
            if existing_count > 0:
                print(f"⚠️  Já existem {existing_count} registros ABC Farma. Deseja continuar? (s/n)")
                response = input().lower()
                if response != 's':
                    print("❌ Migração cancelada.")
                    return
                    
                # Limpar dados existentes
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
            
    def create_similarity_search_indexes(self):
        """Criar índices adicionais para busca por similaridade"""
        print("🔄 Criando índices para busca por similaridade...")
        
        with self.engine.connect() as conn:
            # Índices para FTS (Full Text Search)
            try:
                conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS abc_farma_fts USING fts5(
                        id,
                        descricao_completa,
                        marca,
                        principio_ativo,
                        categoria,
                        content=abc_farma_products
                    )
                """))
                conn.commit()
                print("✅ Índice FTS criado!")
                
            except Exception as e:
                print(f"⚠️  Erro ao criar FTS: {e}")
                
        print("✅ Índices criados!")
        
    def test_similarity_search(self, query: str = "dipirona") -> List[dict]:
        """Testar busca por similaridade"""
        print(f"🔍 Testando busca por: '{query}'")
        
        session = self.Session()
        
        try:
            # Gerar embedding da consulta
            query_embedding = self.embedding_model.encode(query)
            
            # Buscar produtos
            products = session.query(ABCFarmaProduct).filter(
                ABCFarmaProduct.ativo == True
            ).limit(1000).all()
            
            if not products:
                print("❌ Nenhum produto encontrado!")
                return []
                
            print(f"📊 Analisando {len(products)} produtos...")
            
            # Calcular similaridades
            similarities = []
            
            for product in products:
                if product.embedding_descricao:
                    try:
                        # Deserializar embedding
                        product_embedding = pickle.loads(product.embedding_descricao)
                        
                        # Calcular similaridade cosseno
                        similarity = np.dot(query_embedding, product_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
                        )
                        
                        similarities.append({
                            'product': product,
                            'similarity': float(similarity)
                        })
                        
                    except Exception as e:
                        continue
                        
            # Ordenar por similaridade
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Mostrar top 5
            print(f"🏆 Top 5 resultados mais similares:")
            for i, item in enumerate(similarities[:5]):
                product = item['product']
                similarity = item['similarity']
                
                print(f"{i+1}. {product.descricao_completa[:60]}...")
                print(f"   Marca: {product.marca}")
                print(f"   Similaridade: {similarity:.3f}")
                print(f"   Código: {product.codigo_barra}")
                print()
                
            return similarities[:10]
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
        finally:
            session.close()

def main():
    """Função principal"""
    print("=" * 60)
    print("🏥 MIGRAÇÃO ABC FARMA PARA SQLITE")
    print("=" * 60)
    
    try:
        migrator = ABCFarmaMigrator()
        
        # 1. Criar tabelas
        migrator.create_tables()
        
        # 2. Migrar dados
        migrator.migrate_data()
        
        # 3. Criar índices
        migrator.create_similarity_search_indexes()
        
        # 4. Testar busca
        migrator.test_similarity_search("dipirona")
        migrator.test_similarity_search("paracetamol")
        
        print("🎉 Migração ABC Farma concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
