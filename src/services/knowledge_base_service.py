"""
Serviço de Acesso à Base de Conhecimento SQLite
Substitui o carregamento de JSON por consultas SQL eficientes
"""

import sqlite3
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy import create_engine, and_, or_, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
import logging
import json
from contextlib import contextmanager

from database.knowledge_models import (
    KnowledgeBase, NCMHierarchy, CestCategory, NCMCestMapping, 
    ProdutoExemplo, KnowledgeBaseMetadata, create_performance_indexes
)

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    Serviço para acesso eficiente à base de conhecimento SQLite
    """
    
    def __init__(self, db_path: str = "data/knowledge_base/knowledge_base.sqlite"):
        """
        Inicializa o serviço da base de conhecimento
        
        Args:
            db_path: Caminho para o arquivo SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuração do SQLAlchemy
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            poolclass=StaticPool,
            pool_pre_ping=True,
            connect_args={
                'check_same_thread': False,
                'timeout': 30
            }
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Cache em memória para consultas frequentes
        self._cache_ncm_hierarchy = {}
        self._cache_cest_mappings = {}
        self._cache_enabled = True
        
        logger.info(f"KnowledgeBaseService inicializado com: {self.db_path}")
    
    @contextmanager
    def get_session(self):
        """
        Context manager para sessões do SQLAlchemy
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """
        Cria todas as tabelas na base de conhecimento
        """
        try:
            KnowledgeBase.metadata.create_all(bind=self.engine)
            create_performance_indexes(self.engine)
            logger.info("Tabelas da base de conhecimento criadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
    
    # === CONSULTAS NCM ===
    
    def buscar_ncm_por_codigo(self, codigo_ncm: str) -> Optional[Dict]:
        """
        Busca um NCM específico por código
        """
        if self._cache_enabled and codigo_ncm in self._cache_ncm_hierarchy:
            return self._cache_ncm_hierarchy[codigo_ncm]
        
        with self.get_session() as session:
            ncm = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.codigo_ncm == codigo_ncm,
                    NCMHierarchy.ativo == True
                )
            ).first()
            
            if ncm:
                result = {
                    'codigo_ncm': ncm.codigo_ncm,
                    'descricao_oficial': ncm.descricao_oficial,
                    'descricao_curta': ncm.descricao_curta,
                    'nivel_hierarquico': ncm.nivel_hierarquico,
                    'codigo_pai': ncm.codigo_pai
                }
                
                if self._cache_enabled:
                    self._cache_ncm_hierarchy[codigo_ncm] = result
                
                return result
        
        return None
    
    def buscar_ncms_hierarquia(self, codigo_base: str) -> List[Dict]:
        """
        Busca todos os NCMs em uma hierarquia (ex: todos os NCMs que começam com '8542')
        """
        with self.get_session() as session:
            ncms = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.codigo_ncm.like(f"{codigo_base}%"),
                    NCMHierarchy.ativo == True
                )
            ).order_by(NCMHierarchy.nivel_hierarquico, NCMHierarchy.codigo_ncm).all()
            
            return [
                {
                    'codigo_ncm': ncm.codigo_ncm,
                    'descricao_oficial': ncm.descricao_oficial,
                    'descricao_curta': ncm.descricao_curta,
                    'nivel_hierarquico': ncm.nivel_hierarquico,
                    'codigo_pai': ncm.codigo_pai
                }
                for ncm in ncms
            ]
    
    def buscar_ncms_por_palavras(self, palavras: List[str], limite: int = 20) -> List[Dict]:
        """
        Busca NCMs por palavras-chave na descrição
        """
        with self.get_session() as session:
            # Constrói query com LIKE para cada palavra
            filtros = []
            for palavra in palavras:
                filtros.append(
                    or_(
                        NCMHierarchy.descricao_oficial.like(f"%{palavra}%"),
                        NCMHierarchy.descricao_curta.like(f"%{palavra}%")
                    )
                )
            
            ncms = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.ativo == True,
                    *filtros
                )
            ).order_by(NCMHierarchy.nivel_hierarquico.desc()).limit(limite).all()
            
            return [
                {
                    'codigo_ncm': ncm.codigo_ncm,
                    'descricao_oficial': ncm.descricao_oficial,
                    'descricao_curta': ncm.descricao_curta,
                    'nivel_hierarquico': ncm.nivel_hierarquico
                }
                for ncm in ncms
            ]
    
    # === CONSULTAS CEST ===
    
    def buscar_cests_por_ncm(self, codigo_ncm: str) -> List[Dict]:
        """
        Busca todos os CESTs associados a um NCM
        """
        cache_key = f"cest_{codigo_ncm}"
        if self._cache_enabled and cache_key in self._cache_cest_mappings:
            return self._cache_cest_mappings[cache_key]
        
        with self.get_session() as session:
            # Busca direto e por hierarquia
            cests = session.query(
                CestCategory.codigo_cest,
                CestCategory.descricao_cest,
                CestCategory.descricao_resumida,
                CestCategory.categoria_produto,
                NCMCestMapping.tipo_relacao,
                NCMCestMapping.confianca_mapeamento
            ).join(
                NCMCestMapping, CestCategory.codigo_cest == NCMCestMapping.cest_codigo
            ).filter(
                and_(
                    NCMCestMapping.ncm_codigo == codigo_ncm,
                    NCMCestMapping.ativo == True,
                    CestCategory.ativo == True
                )
            ).order_by(NCMCestMapping.confianca_mapeamento.desc()).all()
            
            result = [
                {
                    'codigo_cest': cest.codigo_cest,
                    'descricao_cest': cest.descricao_cest,
                    'descricao_resumida': cest.descricao_resumida,
                    'categoria_produto': cest.categoria_produto,
                    'tipo_relacao': cest.tipo_relacao,
                    'confianca': cest.confianca_mapeamento
                }
                for cest in cests
            ]
            
            if self._cache_enabled:
                self._cache_cest_mappings[cache_key] = result
            
            return result
    
    def buscar_cests_hierarquia_ncm(self, codigo_ncm: str) -> List[Dict]:
        """
        Busca CESTs incluindo hierarquia do NCM (busca em NCMs pais)
        """
        all_cests = []
        
        # Primeiro busca CESTs diretos
        cests_diretos = self.buscar_cests_por_ncm(codigo_ncm)
        all_cests.extend(cests_diretos)
        
        # Depois busca por hierarquia (códigos pai)
        ncm_info = self.buscar_ncm_por_codigo(codigo_ncm)
        if ncm_info and ncm_info.get('codigo_pai'):
            codigo_pai = ncm_info['codigo_pai']
            cests_herdados = self.buscar_cests_por_ncm(codigo_pai)
            
            # Marca como herdados
            for cest in cests_herdados:
                cest['tipo_relacao'] = 'HERDADO'
                cest['confianca'] = cest['confianca'] * 0.8  # Reduz confiança para herdados
            
            all_cests.extend(cests_herdados)
        
        # Remove duplicatas e ordena por confiança
        cests_unicos = {}
        for cest in all_cests:
            codigo = cest['codigo_cest']
            if codigo not in cests_unicos or cest['confianca'] > cests_unicos[codigo]['confianca']:
                cests_unicos[codigo] = cest
        
        return sorted(cests_unicos.values(), key=lambda x: x['confianca'], reverse=True)
    
    def buscar_cest_por_codigo(self, codigo_cest: str) -> Optional[Dict]:
        """
        Busca um CEST específico por código
        """
        with self.get_session() as session:
            cest = session.query(CestCategory).filter(
                and_(
                    CestCategory.codigo_cest == codigo_cest,
                    CestCategory.ativo == True
                )
            ).first()
            
            if cest:
                return {
                    'codigo_cest': cest.codigo_cest,
                    'descricao_cest': cest.descricao_cest,
                    'descricao_resumida': cest.descricao_resumida,
                    'categoria_produto': cest.categoria_produto
                }
        
        return None
    
    # === CONSULTAS PRODUTOS EXEMPLO ===
    
    def buscar_exemplos_por_ncm(self, codigo_ncm: str, limite: int = 10) -> List[Dict]:
        """
        Busca produtos exemplo para um NCM
        """
        with self.get_session() as session:
            exemplos = session.query(ProdutoExemplo).filter(
                and_(
                    ProdutoExemplo.ncm_codigo == codigo_ncm,
                    ProdutoExemplo.ativo == True
                )
            ).order_by(
                ProdutoExemplo.qualidade_classificacao.desc(),
                ProdutoExemplo.verificado_humano.desc()
            ).limit(limite).all()
            
            return [
                {
                    'gtin': exemplo.gtin,
                    'descricao_produto': exemplo.descricao_produto,
                    'marca': exemplo.marca,
                    'modelo': exemplo.modelo,
                    'categoria_produto': exemplo.categoria_produto,
                    'material_predominante': exemplo.material_predominante,
                    'aplicacao_uso': exemplo.aplicacao_uso,
                    'qualidade_classificacao': exemplo.qualidade_classificacao,
                    'verificado_humano': exemplo.verificado_humano
                }
                for exemplo in exemplos
            ]
    
    def buscar_produto_por_gtin(self, gtin: str) -> Optional[Dict]:
        """
        Busca um produto específico por GTIN
        """
        with self.get_session() as session:
            produto = session.query(ProdutoExemplo).filter(
                and_(
                    ProdutoExemplo.gtin == gtin,
                    ProdutoExemplo.ativo == True
                )
            ).first()
            
            if produto:
                return {
                    'gtin': produto.gtin,
                    'descricao_produto': produto.descricao_produto,
                    'ncm_codigo': produto.ncm_codigo,
                    'marca': produto.marca,
                    'modelo': produto.modelo,
                    'categoria_produto': produto.categoria_produto,
                    'qualidade_classificacao': produto.qualidade_classificacao
                }
        
        return None
    
    # === ESTATÍSTICAS ===
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas da base de conhecimento
        """
        with self.get_session() as session:
            stats = {}
            
            stats['total_ncms'] = session.query(NCMHierarchy).filter(NCMHierarchy.ativo == True).count()
            stats['total_cests'] = session.query(CestCategory).filter(CestCategory.ativo == True).count()
            stats['total_mapeamentos'] = session.query(NCMCestMapping).filter(NCMCestMapping.ativo == True).count()
            stats['total_exemplos'] = session.query(ProdutoExemplo).filter(ProdutoExemplo.ativo == True).count()
            
            # Estatísticas por nível hierárquico
            niveis = session.query(
                NCMHierarchy.nivel_hierarquico,
                func.count(NCMHierarchy.id).label('quantidade')
            ).filter(
                NCMHierarchy.ativo == True
            ).group_by(NCMHierarchy.nivel_hierarquico).all()
            
            stats['ncms_por_nivel'] = {str(nivel): qtd for nivel, qtd in niveis}
            
            return stats
    
    # === MÉTODOS DE COMPATIBILIDADE ===
    
    def get_ncm_mapping(self) -> Dict:
        """
        Método de compatibilidade para substituir o carregamento do ncm_mapping.json
        Retorna estrutura similar ao JSON original para facilitar migração
        """
        mapping = {}
        
        with self.get_session() as session:
            # Busca todos os NCMs ativos
            ncms = session.query(NCMHierarchy).filter(NCMHierarchy.ativo == True).all()
            
            for ncm in ncms:
                # Busca CESTs associados
                cests = self.buscar_cests_por_ncm(ncm.codigo_ncm)
                
                # Busca exemplos
                exemplos = self.buscar_exemplos_por_ncm(ncm.codigo_ncm, limite=5)
                
                mapping[ncm.codigo_ncm] = {
                    'descricao': ncm.descricao_oficial,
                    'descricao_curta': ncm.descricao_curta,
                    'nivel': ncm.nivel_hierarquico,
                    'cests': [cest['codigo_cest'] for cest in cests],
                    'cests_detalhado': cests,
                    'exemplos': exemplos
                }
        
        logger.info(f"Mapeamento NCM carregado com {len(mapping)} entradas")
        return mapping
    
    # === CACHE ===
    
    def limpar_cache(self):
        """
        Limpa o cache em memória
        """
        self._cache_ncm_hierarchy.clear()
        self._cache_cest_mappings.clear()
        logger.info("Cache da base de conhecimento limpo")
    
    def habilitar_cache(self, enabled: bool = True):
        """
        Habilita/desabilita o cache
        """
        self._cache_enabled = enabled
        if not enabled:
            self.limpar_cache()
    
    # === VERIFICAÇÃO DE INTEGRIDADE ===
    
    def verificar_integridade(self) -> Dict:
        """
        Verifica a integridade da base de conhecimento
        """
        with self.get_session() as session:
            problemas = []
            
            # Verifica NCMs sem descrição
            ncms_sem_descricao = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.ativo == True,
                    or_(
                        NCMHierarchy.descricao_oficial == None,
                        NCMHierarchy.descricao_oficial == ''
                    )
                )
            ).count()
            
            if ncms_sem_descricao > 0:
                problemas.append(f"{ncms_sem_descricao} NCMs sem descrição")
            
            # Verifica CESTs órfãos
            cests_orfaos = session.query(CestCategory).filter(
                and_(
                    CestCategory.ativo == True,
                    ~CestCategory.codigo_cest.in_(
                        session.query(NCMCestMapping.cest_codigo).filter(NCMCestMapping.ativo == True)
                    )
                )
            ).count()
            
            if cests_orfaos > 0:
                problemas.append(f"{cests_orfaos} CESTs sem mapeamento para NCM")
            
            # Verifica produtos sem NCM válido
            produtos_invalidos = session.query(ProdutoExemplo).filter(
                and_(
                    ProdutoExemplo.ativo == True,
                    ~ProdutoExemplo.ncm_codigo.in_(
                        session.query(NCMHierarchy.codigo_ncm).filter(NCMHierarchy.ativo == True)
                    )
                )
            ).count()
            
            if produtos_invalidos > 0:
                problemas.append(f"{produtos_invalidos} produtos com NCM inválido")
            
            return {
                'integridade_ok': len(problemas) == 0,
                'problemas': problemas,
                'timestamp': func.now()
            }
    
    # === MÉTODOS AUXILIARES PARA TESTES ===
    
    def buscar_ncms_por_nivel(self, nivel: int) -> List[Dict]:
        """
        Busca NCMs por nível hierárquico
        """
        with self.get_session() as session:
            ncms = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.nivel_hierarquico == nivel,
                    NCMHierarchy.ativo == True
                )
            ).all()
            
            return [self._ncm_to_dict(ncm) for ncm in ncms]
    
    def buscar_ncms_por_padrao(self, padrao: str) -> List[Dict]:
        """
        Busca NCMs que correspondem a um padrão
        """
        with self.get_session() as session:
            ncms = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.codigo_ncm.like(f"{padrao}%"),
                    NCMHierarchy.ativo == True
                )
            ).all()
            
            return [self._ncm_to_dict(ncm) for ncm in ncms]
    
    def buscar_cests_para_ncm(self, codigo_ncm: str) -> List[Dict]:
        """
        Alias para buscar_cests_por_ncm para compatibilidade
        """
        return self.buscar_cests_por_ncm(codigo_ncm)
    
    def buscar_ncms_para_cest(self, codigo_cest: str) -> List[Dict]:
        """
        Busca NCMs que mapeiam para um CEST específico
        """
        with self.get_session() as session:
            mappings = session.query(NCMCestMapping).filter(
                and_(
                    NCMCestMapping.cest_codigo == codigo_cest,
                    NCMCestMapping.ativo == True
                )
            ).all()
            
            ncm_codes = [m.ncm_codigo for m in mappings]
            
            if not ncm_codes:
                return []
            
            ncms = session.query(NCMHierarchy).filter(
                and_(
                    NCMHierarchy.codigo_ncm.in_(ncm_codes),
                    NCMHierarchy.ativo == True
                )
            ).all()
            
            return [self._ncm_to_dict(ncm) for ncm in ncms]
    
    def contar_registros(self, tabela: str) -> int:
        """
        Conta registros em uma tabela específica
        """
        with self.get_session() as session:
            if tabela == 'ncm_hierarchy':
                return session.query(NCMHierarchy).filter(NCMHierarchy.ativo == True).count()
            elif tabela == 'cest_categories':
                return session.query(CestCategory).filter(CestCategory.ativo == True).count()
            elif tabela == 'ncm_cest_mappings':
                return session.query(NCMCestMapping).filter(NCMCestMapping.ativo == True).count()
            elif tabela == 'produto_exemplos':
                return session.query(ProdutoExemplo).count()
            else:
                raise ValueError(f"Tabela '{tabela}' não reconhecida")
    
    def _ncm_to_dict(self, ncm: NCMHierarchy) -> Dict:
        """
        Converte objeto NCMHierarchy para dicionário
        """
        return {
            'codigo_ncm': ncm.codigo_ncm,
            'descricao_oficial': ncm.descricao_oficial,
            'descricao_curta': ncm.descricao_curta,
            'nivel_hierarquico': ncm.nivel_hierarquico,
            'codigo_pai': ncm.codigo_pai,
            'ativo': ncm.ativo
        }


# Instância global do serviço
_knowledge_service = None

def get_knowledge_service() -> KnowledgeBaseService:
    """
    Retorna instância singleton do serviço da base de conhecimento
    """
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeBaseService()
    return _knowledge_service
