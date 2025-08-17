# ============================================================================
# src/ingestion/data_loader.py - Carregador de Dados
# ============================================================================

import pandas as pd
import json
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from config import Config
from database.connection import get_database_url

class DataLoader:
    def __init__(self):
        self.config = Config()
        self.engine = self._create_db_engine()
    
    def _create_db_engine(self):
        """Cria engine de conexão com o banco de dados usando o sistema de fallback."""
        database_url = get_database_url()
        print(f"🔗 Conectando ao banco: {database_url.split('://')[0]}...")
        return create_engine(database_url)
    
    def load_produtos_from_db(self, force_postgresql: bool = False, limit: int = None) -> pd.DataFrame:
        """Carrega produtos da base de dados usando a lógica do extracao_dados.py.
        
        Args:
            force_postgresql: Se True, força conexão direta ao PostgreSQL ignorando fallback
            limit: Número máximo de produtos a carregar (None = todos)
        """
        
        # Determinar se estamos usando SQLite ou PostgreSQL
        if force_postgresql:
            print("🔗 Forçando conexão PostgreSQL...")
            database_url = f"postgresql://{self.config.DB_CONFIG['user']}:{self.config.DB_CONFIG['password']}@{self.config.DB_CONFIG['host']}:{self.config.DB_CONFIG['port']}/{self.config.DB_CONFIG['database']}"
            try:
                engine = create_engine(database_url)
                # Testar conexão
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.engine = engine
                is_sqlite = False
                print("✅ Conexão PostgreSQL estabelecida com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
                print("💡 Dica: Verifique as credenciais no arquivo .env")
                raise
        else:
            database_url = get_database_url()
            is_sqlite = database_url.startswith('sqlite')
        
        if is_sqlite:
            # Para SQLite, verificar se temos dados importados ou usar dados de exemplo
            print("🔄 Verificando dados no SQLite...")
            try:
                # Tentar carregar da tabela de classificações se existir
                limit_clause = f"LIMIT {limit}" if limit else "LIMIT 100"
                query = f"""
                SELECT 
                    id as produto_id,
                    descricao_produto,
                    codigo_produto,
                    codigo_barra,
                    ncm_original,
                    cest_original
                FROM classificacao_revisao
                {limit_clause}
                """
                df = pd.read_sql_query(query, self.engine)
                if len(df) > 0:
                    print(f"✅ {len(df)} produtos carregados do SQLite (tabela de classificações).")
                    return df
            except Exception as e:
                print(f"ℹ️ Tabela de classificações não encontrada: {e}")
            
            # Fallback: criar dados de exemplo
            print("🔄 Criando dados de exemplo para teste...")
            return self._create_sample_data(limit)
        else:
            # PostgreSQL original - query robusta apenas com campos essenciais
            limit_clause = f"LIMIT {limit}" if limit else ""
            query = f"""
            SELECT 
                produto_id,
                descricao_produto,
                codigo_produto,
                codigo_barra,
                ncm,
                cest,
                DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
                COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
            FROM {self.config.DB_CONFIG['schema']}.produto
            WHERE descricao_produto IS NOT NULL 
            AND LENGTH(TRIM(descricao_produto)) > 5
            ORDER BY 
                CASE WHEN codigo_barra IS NOT NULL AND LENGTH(codigo_barra) > 8 THEN 1 ELSE 2 END,
                id_agregados DESC
            {limit_clause}
            """
            
            print("🔄 Carregando produtos da base PostgreSQL com query otimizada...")
            try:
                df = pd.read_sql_query(query, self.engine)
                print(f"✅ {len(df)} produtos carregados do PostgreSQL.")
                
                # Adicionar informações de debug
                produtos_com_gtin = df[df['codigo_barra'].notna() & (df['codigo_barra'] != '')].shape[0]
                produtos_com_ncm = df[df['ncm'].notna() & (df['ncm'] != '')].shape[0]
                produtos_com_cest = df[df['cest'].notna() & (df['cest'] != '')].shape[0]
                
                print(f"   📊 Produtos com GTIN: {produtos_com_gtin:,}")
                print(f"   📊 Produtos com NCM: {produtos_com_ncm:,}")
                print(f"   📊 Produtos com CEST: {produtos_com_cest:,}")
                
                return df
                
            except Exception as e:
                print(f"❌ Erro ao carregar dados do PostgreSQL: {e}")
                print("   Tentando query alternativa...")
                
                # Query alternativa mais simples
                query_simple = f"""
                SELECT 
                    produto_id,
                    descricao_produto,
                    COALESCE(codigo_produto, '') as codigo_produto,
                    COALESCE(codigo_barra, '') as codigo_barra,
                    COALESCE(ncm, '') as ncm,
                    COALESCE(cest, '') as cest
                FROM {self.config.DB_CONFIG['schema']}.produto
                WHERE descricao_produto IS NOT NULL 
                LIMIT 1000
                """
                
                try:
                    df = pd.read_sql_query(query_simple, self.engine)
                    print(f"✅ {len(df)} produtos carregados com query simplificada.")
                    return df
                except Exception as e2:
                    print(f"❌ Erro também na query simplificada: {e2}")
                    print("🔄 Usando dados de exemplo...")
                    return self._create_sample_data()
        return df
    
    def _create_sample_data(self, limit: int = None) -> pd.DataFrame:
        """Cria dados de exemplo para teste quando não há banco disponível."""
        sample_data = [
            {
                'produto_id': 1,
                'descricao_produto': 'Refrigerante Coca-Cola 350ml lata',
                'codigo_produto': 'COCA350',
                'codigo_barra': '7894900011517',
                'ncm': '22021000',
                'cest': '03.002.00'
            },
            {
                'produto_id': 2,
                'descricao_produto': 'Água mineral natural 500ml',
                'codigo_produto': 'AGUA500',
                'codigo_barra': '7891234567890',
                'ncm': '22011000',
                'cest': None
            },
            {
                'produto_id': 3,
                'descricao_produto': 'Paracetamol 500mg 20 comprimidos',
                'codigo_produto': 'PARA500',
                'codigo_barra': '7896789012345',
                'ncm': '30049099',
                'cest': '28.034.00'
            },
            {
                'produto_id': 4,
                'descricao_produto': 'Smartphone Samsung Galaxy A54',
                'codigo_produto': 'SAMA54',
                'codigo_barra': '8801643718705',
                'ncm': '85171211',
                'cest': '21.001.00'
            },
            {
                'produto_id': 5,
                'descricao_produto': 'Notebook Dell Inspiron 15 3000',
                'codigo_produto': 'DELL3000',
                'codigo_barra': '8806088188461',
                'ncm': '84713012',
                'cest': '21.013.00'
            }
        ]
        
        df = pd.DataFrame(sample_data)
        print(f"✅ {len(df)} produtos de exemplo criados para teste.")
        return df
    
    def load_ncm_descriptions(self) -> Optional[Dict]:
        """Carrega descrições NCM do arquivo JSON."""
        ncm_file = self.config.RAW_DATA_DIR / "descricoes_ncm.json"
        if not ncm_file.exists():
            print(f"⚠️ Arquivo NCM não encontrado: {ncm_file}")
            return None
        
        with open(ncm_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_cest_mapping(self) -> Optional[pd.DataFrame]:
        """Carrega mapeamento CEST do arquivo CSV/Excel/JSON."""
        cest_files = [
            self.config.RAW_DATA_DIR / "CEST_RO.json",  # Novo arquivo principal
            self.config.RAW_DATA_DIR / "Anexos_conv_92_15_corrigido.json",
            self.config.RAW_DATA_DIR / "conv_142_formatado.json",  # Novo arquivo adicionado
            self.config.RAW_DATA_DIR / "Anexos_conv_92_15.csv",
            self.config.RAW_DATA_DIR / "Anexos_conv_92_15.xlsx"
        ]
        
        all_data = []
        
        for cest_file in cest_files:
            if cest_file.exists():
                try:
                    print(f"📁 Carregando CEST de: {cest_file.name}")
                    
                    if cest_file.suffix == '.json':
                        with open(cest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Tratamento específico para CEST_RO.json
                        if cest_file.name == "CEST_RO.json":
                            df = pd.DataFrame(data)
                            # Normalizar colunas para formato padrão
                            if 'NCM/SH' in df.columns:
                                df['NCM_SH'] = df['NCM/SH']
                            if 'DESCRIÇÃO' in df.columns:
                                df['DESCRICAO'] = df['DESCRIÇÃO']
                            # Filtrar apenas registros vigentes
                            if 'Situação' in df.columns:
                                df = df[df['Situação'].str.lower() == 'vigente']
                                print(f"   ✅ {len(df)} registros vigentes filtrados de CEST_RO")
                        
                        # Tratamento específico para conv_142_formatado.json
                        elif cest_file.name == "conv_142_formatado.json":
                            df = pd.DataFrame(data)
                            # Normalizar colunas para formato padrão
                            if 'ncm' in df.columns:
                                df['NCM_SH'] = df['ncm']
                            if 'descricao_oficial_cest' in df.columns:
                                df['DESCRICAO'] = df['descricao_oficial_cest']
                            if 'cest' in df.columns:
                                df['CEST'] = df['cest']
                            if 'segmento' in df.columns:
                                df['SEGMENTO'] = df['segmento']
                            if 'Anexo' in df.columns:
                                df['ANEXO'] = df['Anexo']
                            print(f"   ✅ {len(df)} registros carregados de conv_142_formatado")
                        else:
                            df = pd.DataFrame(data)
                            
                        all_data.append(df)
                        
                    elif cest_file.suffix == '.csv':
                        df = pd.read_csv(cest_file)
                        all_data.append(df)
                    else:
                        df = pd.read_excel(cest_file)
                        all_data.append(df)
                        
                except Exception as e:
                    print(f"⚠️ Erro ao carregar {cest_file.name}: {e}")
        
        if all_data:
            # Combinar todos os DataFrames
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"✅ {len(combined_df)} registros CEST combinados de {len(all_data)} arquivos.")
            return combined_df
        
        print("⚠️ Nenhum arquivo CEST encontrado.")
        return None
    
    def load_produtos_selecionados(self) -> Optional[pd.DataFrame]:
        """Carrega produtos selecionados do arquivo JSON."""
        produtos_file = self.config.RAW_DATA_DIR / "produtos_selecionados.json"
        if not produtos_file.exists():
            print(f"⚠️ Arquivo produtos_selecionados.json não encontrado: {produtos_file}")
            return None
        
        try:
            print(f"📁 Carregando produtos selecionados de: {produtos_file.name}")
            with open(produtos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            print(f"✅ {len(df)} produtos selecionados carregados.")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar produtos_selecionados.json: {e}")
            return None
    
    def load_abc_farma_gtin(self) -> Optional[pd.DataFrame]:
        """Carrega dados da Tabela ABC Farma GTIN modificado."""
        abc_farma_file = self.config.RAW_DATA_DIR / "Tabela_ABC_Farma_GTIN_modificado.xlsx"
        if not abc_farma_file.exists():
            print(f"⚠️ Arquivo ABC Farma não encontrado: {abc_farma_file}")
            return None
        
        try:
            print(f"📁 Carregando ABC Farma de: {abc_farma_file.name}")
            df = pd.read_excel(abc_farma_file)
            
            # Normalizar nomes das colunas
            df.columns = df.columns.str.strip().str.upper()
            
            # Renomear colunas para padronização
            column_mapping = {
                'CODIGO_BARRA': 'codigo_barra',
                'DESCRICAO COMPLETA': 'descricao_completa',
                'DESCRICAO1': 'descricao1',
                'DESCRICAO2': 'descricao2',
                'MARCA': 'marca',
                'CATEGORIA': 'categoria'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]
            
            # Filtrar apenas medicamentos (capítulo 30 do NCM e segmento 13 do CEST)
            if 'categoria' in df.columns:
                medicamentos_df = df[df['categoria'].str.upper() == 'MEDICAMENTO'].copy()
                print(f"   ✅ {len(medicamentos_df)} medicamentos filtrados de {len(df)} registros totais")
                return medicamentos_df
            else:
                print(f"   ✅ {len(df)} registros carregados (sem filtro de categoria)")
                return df
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar Tabela_ABC_Farma_GTIN_modificado.xlsx: {e}")
            return None
    
    def load_nesh_text(self) -> Optional[str]:
        """Carrega texto da NESH."""
        nesh_file = self.config.RAW_DATA_DIR / "nesh-2022.pdf"
        if not nesh_file.exists():
            print(f"⚠️ Arquivo NESH não encontrado: {nesh_file}")
            return None
        
        try:
            # Tentar importar PyPDF2 para extração de texto
            try:
                import PyPDF2
                
                print(f"📁 Extraindo texto de: {nesh_file.name}")
                with open(nesh_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    
                    # Extrair texto de todas as páginas (limitado a 50 páginas para performance)
                    max_pages = min(50, len(pdf_reader.pages))
                    for page_num in range(max_pages):
                        page = pdf_reader.pages[page_num]
                        text_content += page.extract_text() + "\n"
                    
                    print(f"✅ Texto extraído de {max_pages} páginas da NESH")
                    return text_content
                    
            except ImportError:
                print("⚠️ PyPDF2 não instalado. Para extrair texto de PDF, instale: pip install PyPDF2")
                # Fallback: retornar informações básicas sobre NESH
                return self._get_nesh_fallback_content()
                
        except Exception as e:
            print(f"⚠️ Erro ao extrair texto da NESH: {e}")
            return self._get_nesh_fallback_content()
    
    def _get_nesh_fallback_content(self) -> str:
        """Retorna conteúdo básico sobre NESH quando não é possível extrair do PDF."""
        return """
        NESH - Nomenclatura Específica do Sistema Harmonizado
        
        A NESH é um sistema de classificação de mercadorias baseado no Sistema Harmonizado (SH)
        e é utilizada para fins de comércio exterior no Brasil.
        
        Principais características:
        - Baseada no Sistema Harmonizado internacional
        - Utilizada para classificação de produtos para importação/exportação
        - Relacionada com a NCM (Nomenclatura Comum do Mercosul)
        - Importante para determinação de tributos e regulamentações
        
        Para análise completa, é recomendado consultar o documento oficial da NESH.
        """