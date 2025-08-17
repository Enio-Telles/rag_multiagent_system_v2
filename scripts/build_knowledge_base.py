#!/usr/bin/env python3
"""
scripts/build_knowledge_base.py
Construção da Base de Conhecimento SQLite Unificada

Este script migra todas as fontes de dados (JSON/CSV) para um banco SQLite único.
Substitui o antigo ncm_mapping.json por consultas SQL eficientes.
"""

import json
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Adicionar o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from config import Config
from ingestion.data_loader import DataLoader
from database.knowledge_models import (
    KnowledgeBase, NCMHierarchy, CestCategory, NCMCestMapping, 
    ProdutoExemplo, KnowledgeBaseMetadata, create_performance_indexes
)
from services.knowledge_base_service import KnowledgeBaseService
from sqlalchemy import and_

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLiteKnowledgeBaseBuilder:
    """
    Construtor da Base de Conhecimento SQLite Unificada
    Migra todos os dados de JSON/CSV para SQLite com estrutura otimizada
    """
    
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        
        # Garantir que os diretórios existam
        knowledge_dir = Path("data/knowledge_base")
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar serviço da base de conhecimento
        self.kb_service = KnowledgeBaseService()
        
        # Contadores para estatísticas
        self.stats = {
            'ncms_inseridos': 0,
            'cests_inseridos': 0,
            'mapeamentos_inseridos': 0,
            'exemplos_inseridos': 0,
            'erros': 0
        }
    
    def build_sqlite_knowledge_base(self) -> bool:
        """
        Método principal - constrói a base de conhecimento SQLite completa
        """
        logger.info("🚀 Iniciando construção da Base de Conhecimento SQLite")
        
        try:
            # 1. Criar estrutura do banco
            self._create_database_structure()
            
            # 2. Popular NCMs
            self._populate_ncm_hierarchy()
            
            # 3. Popular CESTs
            self._populate_cest_categories()
            
            # 4. Criar mapeamentos NCM-CEST
            self._create_ncm_cest_mappings()
            
            # 5. Popular produtos exemplo
            self._populate_product_examples()
            
            # 6. Aplicar herança hierárquica
            self._apply_cest_inheritance()
            
            # 7. Criar metadados
            self._create_metadata()
            
            # 8. Verificar integridade
            self._verify_integrity()
            
            # 9. Estatísticas finais
            self._print_final_statistics()
            
            logger.info("🎉 Base de conhecimento SQLite construída com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na construção da base: {e}")
            return False
    
    def _create_database_structure(self):
        """
        Cria a estrutura do banco SQLite
        """
        logger.info("🏗️ Criando estrutura do banco SQLite...")
        self.kb_service.create_tables()
        logger.info("✅ Estrutura criada com sucesso")
    
    def _normalize_ncm(self, ncm_code: str) -> str:
        """Normaliza código NCM removendo pontos e espaços."""
        return str(ncm_code).replace(".", "").replace(" ", "").strip()
    
    def _populate_ncm_hierarchy(self):
        """
        Popula a tabela de hierarquia NCM
        """
        logger.info("📋 Populando hierarquia NCM...")
        
        ncm_data = self.data_loader.load_ncm_descriptions()
        if not ncm_data:
            logger.warning("⚠️ Nenhum dado NCM carregado")
            return
        
        # Use conjunto para rastrear códigos processados
        codigos_processados = set()
        
        with self.kb_service.get_session() as session:
            batch_count = 0
            
            for item in ncm_data:
                try:
                    codigo = self._normalize_ncm(item.get("Código", ""))
                    if not codigo:
                        continue
                    
                    # Verificar se já foi processado
                    if codigo in codigos_processados:
                        continue
                    
                    # Verificar se já existe no banco
                    existing = session.query(NCMHierarchy).filter_by(codigo_ncm=codigo).first()
                    if existing:
                        continue
                    
                    codigos_processados.add(codigo)
                    
                    # Determinar hierarquia
                    nivel = len(codigo)
                    codigo_pai = None
                    
                    # Determinar código pai baseado no nível
                    if nivel > 2:
                        # Buscar o pai mais próximo existente
                        for parent_len in range(nivel - 1, 1, -1):
                            potential_parent = codigo[:parent_len]
                            # Verificar se existe (simplificado - em produção seria consulta)
                            if parent_len in [2, 4, 6]:  # Níveis válidos da estrutura NCM
                                codigo_pai = potential_parent
                                break
                    
                    # Criar registro NCM
                    ncm_record = NCMHierarchy(
                        codigo_ncm=codigo,
                        descricao_oficial=item.get("Descricao_Completa", "").strip(),
                        descricao_curta=item.get("Descricao_Completa", "").strip()[:200],
                        nivel_hierarquico=nivel,
                        codigo_pai=codigo_pai,
                        ativo=True
                    )
                    
                    session.add(ncm_record)
                    self.stats['ncms_inseridos'] += 1
                    batch_count += 1
                    
                    # Commit em lotes para performance
                    if batch_count >= 1000:
                        session.commit()
                        batch_count = 0
                        logger.info(f"  Processados {self.stats['ncms_inseridos']} NCMs...")
                
                except Exception as e:
                    logger.error(f"Erro ao processar NCM {item}: {e}")
                    self.stats['erros'] += 1
            
            # Commit final
            session.commit()
        
        logger.info(f"✅ {self.stats['ncms_inseridos']} NCMs inseridos na hierarquia")
    
    def _populate_cest_categories(self):
        """
        Popula a tabela de categorias CEST
        """
        logger.info("🎯 Populando categorias CEST...")
        
        cest_data = self.data_loader.load_cest_mapping()
        if cest_data is None or cest_data.empty:
            logger.warning("⚠️ Nenhum dado CEST carregado")
            return
        
        # Agregar CESTs únicos
        cests_unicos = {}
        
        for _, item in cest_data.iterrows():
            try:
                cest_code = str(item.get("CEST", "")).strip()
                if not cest_code or cest_code == 'nan':
                    continue
                
                if cest_code not in cests_unicos:
                    # Tratar valores que podem ser float/NaN
                    descricao_raw = item.get("DESCRICAO", "") or item.get("DESCRIÇÃO", "")
                    if pd.isna(descricao_raw):
                        descricao = ""
                    else:
                        descricao = str(descricao_raw).strip()
                    
                    cests_unicos[cest_code] = {
                        'codigo_cest': cest_code,
                        'descricao_cest': descricao,
                        'categoria_produto': self._extract_product_category(item),
                        'ativo': True
                    }
            
            except Exception as e:
                logger.error(f"Erro ao processar CEST {item}: {e}")
                self.stats['erros'] += 1
        
        # Inserir no banco
        with self.kb_service.get_session() as session:
            for cest_info in cests_unicos.values():
                try:
                    # Verificar se já existe no banco
                    existing = session.query(CestCategory).filter_by(codigo_cest=cest_info['codigo_cest']).first()
                    if existing:
                        continue
                    
                    cest_record = CestCategory(**cest_info)
                    session.add(cest_record)
                    self.stats['cests_inseridos'] += 1
                
                except Exception as e:
                    logger.error(f"Erro ao inserir CEST {cest_info['codigo_cest']}: {e}")
                    self.stats['erros'] += 1
            
            session.commit()
        
        logger.info(f"✅ {self.stats['cests_inseridos']} CESTs únicos inseridos")
    
    def _extract_product_category(self, cest_item) -> Optional[str]:
        """
        Extrai categoria do produto dos dados CEST
        """
        # Tentar extrair categoria da descrição ou outros campos
        descricao_raw = cest_item.get("DESCRICAO", "") or cest_item.get("DESCRIÇÃO", "")
        if pd.isna(descricao_raw):
            descricao = ""
        else:
            descricao = str(descricao_raw).strip()
        
        # Lógica simples para extrair categoria (pode ser melhorada)
        descricao_lower = descricao.lower()
        if "medicamento" in descricao_lower:
            return "MEDICAMENTOS"
        elif "alimento" in descricao_lower or "bebida" in descricao_lower:
            return "ALIMENTOS_BEBIDAS"
        elif "combustível" in descricao_lower:
            return "COMBUSTIVEIS"
        elif "construção" in descricao_lower or "material" in descricao_lower:
            return "MATERIAIS_CONSTRUCAO"
        
        return "GERAL"
    
    def _create_ncm_cest_mappings(self):
        """
        Cria os mapeamentos NCM-CEST
        """
        logger.info("🔗 Criando mapeamentos NCM-CEST...")
        
        cest_data = self.data_loader.load_cest_mapping()
        if cest_data is None or cest_data.empty:
            logger.warning("⚠️ Nenhum dado CEST disponível para mapeamento")
            return
        
        with self.kb_service.get_session() as session:
            # Buscar NCMs existentes para validação
            ncms_existentes = set(
                row[0] for row in session.query(NCMHierarchy.codigo_ncm).filter(NCMHierarchy.ativo == True).all()
            )
            
            # Buscar CESTs existentes para validação
            cests_existentes = set(
                row[0] for row in session.query(CestCategory.codigo_cest).filter(CestCategory.ativo == True).all()
            )
            
            for _, item in cest_data.iterrows():
                try:
                    # Extrair códigos
                    ncm_input = str(item.get("NCM_SH", "") or item.get("NCM/SH", "")).strip()
                    cest_code = str(item.get("CEST", "")).strip()
                    
                    if not ncm_input or not cest_code:
                        continue
                    
                    # Normalizar NCM
                    ncm_normalizado = self._normalize_ncm(ncm_input)
                    
                    # Encontrar melhor match para NCM
                    ncm_match = self._find_best_ncm_match(ncm_normalizado, ncms_existentes)
                    
                    if ncm_match and cest_code in cests_existentes:
                        # Verificar se mapeamento já existe
                        exists = session.query(NCMCestMapping).filter(
                            NCMCestMapping.ncm_codigo == ncm_match,
                            NCMCestMapping.cest_codigo == cest_code
                        ).first()
                        
                        if not exists:
                            mapping = NCMCestMapping(
                                ncm_codigo=ncm_match,
                                cest_codigo=cest_code,
                                tipo_relacao='DIRETO',
                                confianca_mapeamento=1.0,
                                fonte_dados='CEST_RO',
                                ativo=True
                            )
                            
                            session.add(mapping)
                            self.stats['mapeamentos_inseridos'] += 1
                
                except Exception as e:
                    logger.error(f"Erro ao criar mapeamento {item}: {e}")
                    self.stats['erros'] += 1
            
            session.commit()
        
        logger.info(f"✅ {self.stats['mapeamentos_inseridos']} mapeamentos NCM-CEST criados")
    
    def _find_best_ncm_match(self, ncm_input: str, ncms_existentes: set) -> Optional[str]:
        """
        Encontra o melhor match de NCM considerando hierarquia
        """
        # Primeiro, tenta match exato
        if ncm_input in ncms_existentes:
            return ncm_input
        
        # Busca códigos mais específicos (que começam com o input)
        for ncm in ncms_existentes:
            if ncm.startswith(ncm_input) and len(ncm) >= len(ncm_input):
                return ncm
        
        # Busca códigos mais gerais (códigos pai)
        for length in range(len(ncm_input) - 1, 1, -1):
            partial_code = ncm_input[:length]
            if partial_code in ncms_existentes:
                return partial_code
        
        return None
    
    def _populate_product_examples(self):
        """
        Popula produtos exemplo
        """
        logger.info("🛍️ Populando produtos exemplo...")
        
        product_data = self.data_loader.load_produtos_selecionados()
        if product_data is None or product_data.empty:
            logger.warning("⚠️ Nenhum produto exemplo carregado")
            return
        
        with self.kb_service.get_session() as session:
            # Buscar NCMs existentes
            ncms_existentes = set(
                row[0] for row in session.query(NCMHierarchy.codigo_ncm).filter(NCMHierarchy.ativo == True).all()
            )
            
            for _, item in product_data.iterrows():
                try:
                    ncm_input = str(item.get("ncm", "")).strip()
                    gtin = str(item.get("gtin", "")).strip()
                    
                    if not ncm_input or not gtin:
                        continue
                    
                    # Normalizar e encontrar NCM
                    ncm_normalizado = self._normalize_ncm(ncm_input)
                    ncm_match = self._find_best_ncm_match(ncm_normalizado, ncms_existentes)
                    
                    if ncm_match:
                        # Verificar se produto já existe
                        exists = session.query(ProdutoExemplo).filter(
                            ProdutoExemplo.gtin == gtin
                        ).first()
                        
                        if not exists:
                            produto = ProdutoExemplo(
                                ncm_codigo=ncm_match,
                                gtin=gtin,
                                descricao_produto=item.get("descricao", "").strip(),
                                fonte_dados='PRODUTOS_SELECIONADOS',
                                qualidade_classificacao=0.8,
                                ativo=True
                            )
                            
                            session.add(produto)
                            self.stats['exemplos_inseridos'] += 1
                
                except Exception as e:
                    logger.error(f"Erro ao inserir produto {item}: {e}")
                    self.stats['erros'] += 1
            
            session.commit()
        
        logger.info(f"✅ {self.stats['exemplos_inseridos']} produtos exemplo inseridos")
    
    def _apply_cest_inheritance(self):
        """
        Aplica herança hierárquica de CESTs
        """
        logger.info("🌳 Aplicando herança hierárquica de CESTs...")
        
        with self.kb_service.get_session() as session:
            # Buscar NCMs sem CESTs próprios
            ncms_sem_cest = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.ativo == True,
                    ~NCMHierarchy.codigo_ncm.in_(
                        session.query(NCMCestMapping.ncm_codigo).filter(NCMCestMapping.ativo == True)
                    )
                )
            ).order_by(NCMHierarchy.nivel_hierarquico.desc()).all()
            
            inherited_count = 0
            
            for ncm in ncms_sem_cest:
                # Buscar CESTs do pai mais próximo
                parent_cests = self._find_parent_cests(ncm.codigo_ncm, session)
                
                if parent_cests:
                    for parent_cest in parent_cests:
                        # Criar mapeamento herdado
                        inherited_mapping = NCMCestMapping(
                            ncm_codigo=ncm.codigo_ncm,
                            cest_codigo=parent_cest['cest_codigo'],
                            tipo_relacao='HERDADO',
                            confianca_mapeamento=parent_cest['confianca'] * 0.8,  # Reduz confiança
                            fonte_dados=f"HERANCA_{parent_cest['fonte']}",
                            ativo=True
                        )
                        
                        session.add(inherited_mapping)
                    
                    inherited_count += 1
            
            session.commit()
        
        logger.info(f"✅ {inherited_count} NCMs receberam CESTs por herança")
    
    def _find_parent_cests(self, ncm_code: str, session) -> list:
        """
        Encontra CESTs do NCM pai mais próximo
        """
        for length in range(len(ncm_code) - 1, 1, -1):
            parent_code = ncm_code[:length]
            
            parent_cests = session.query(
                NCMCestMapping.cest_codigo,
                NCMCestMapping.confianca_mapeamento,
                NCMCestMapping.fonte_dados
            ).filter(
                and_(
                    NCMCestMapping.ncm_codigo == parent_code,
                    NCMCestMapping.ativo == True,
                    NCMCestMapping.tipo_relacao == 'DIRETO'  # Só herdar de mapeamentos diretos
                )
            ).all()
            
            if parent_cests:
                return [
                    {
                        'cest_codigo': cest.cest_codigo,
                        'confianca': cest.confianca_mapeamento,
                        'fonte': cest.fonte_dados
                    }
                    for cest in parent_cests
                ]
        
        return []
    
    def _create_metadata(self):
        """
        Cria registros de metadados da base
        """
        logger.info("📊 Criando metadados da base...")
        
        with self.kb_service.get_session() as session:
            metadata = KnowledgeBaseMetadata(
                versao_base="1.0.0",
                total_ncms=self.stats['ncms_inseridos'],
                total_cests=self.stats['cests_inseridos'],
                total_mapeamentos=self.stats['mapeamentos_inseridos'],
                total_exemplos=self.stats['exemplos_inseridos'],
                fontes_utilizadas=json.dumps([
                    "descricoes_ncm.json",
                    "CEST_RO.json", 
                    "Anexos_conv_92_15_corrigido.json",
                    "produtos_selecionados.json"
                ]),
                ativo=True
            )
            
            session.add(metadata)
            session.commit()
        
        logger.info("✅ Metadados criados")
    
    def _verify_integrity(self):
        """
        Verifica integridade da base construída
        """
        logger.info("🔍 Verificando integridade da base...")
        
        integrity_check = self.kb_service.verificar_integridade()
        
        if integrity_check['integridade_ok']:
            logger.info("✅ Integridade verificada com sucesso")
        else:
            logger.warning("⚠️ Problemas de integridade encontrados:")
            for problema in integrity_check['problemas']:
                logger.warning(f"  - {problema}")
    
    def _print_final_statistics(self):
        """
        Imprime estatísticas finais
        """
        logger.info("\n📊 ESTATÍSTICAS FINAIS DA BASE SQLITE:")
        logger.info("=" * 60)
        
        # Obter estatísticas do serviço
        stats = self.kb_service.obter_estatisticas()
        
        logger.info(f"📋 Total de NCMs: {stats['total_ncms']:,}")
        logger.info(f"🎯 Total de CESTs: {stats['total_cests']:,}")
        logger.info(f"🔗 Total de mapeamentos: {stats['total_mapeamentos']:,}")
        logger.info(f"📦 Total de exemplos: {stats['total_exemplos']:,}")
        
        if 'ncms_por_nivel' in stats:
            logger.info("📈 NCMs por nível hierárquico:")
            for nivel, qtd in stats['ncms_por_nivel'].items():
                logger.info(f"   Nível {nivel}: {qtd:,} NCMs")
        
        logger.info(f"❌ Erros durante construção: {self.stats['erros']}")
        logger.info("=" * 60)


if __name__ == "__main__":
    builder = SQLiteKnowledgeBaseBuilder()
    success = builder.build_sqlite_knowledge_base()
    
    if success:
        logger.info("🎉 Migração para SQLite concluída com sucesso!")
        logger.info("💡 O arquivo ncm_mapping.json não é mais necessário")
        logger.info("🔄 Atualize o HybridRouter para usar KnowledgeBaseService")
    else:
        logger.error("❌ Falha na migração para SQLite")
        sys.exit(1)