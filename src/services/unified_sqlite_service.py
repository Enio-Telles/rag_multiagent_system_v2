"""
Serviço Unificado SQLite - Gerencia todas as operações do sistema
Substitui todos os serviços individuais por uma interface unificada
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import sqlite3
from sqlalchemy import create_engine, func, text, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Configurar path
sys.path.append('src')

# Imports dos modelos
from database.unified_sqlite_models import (
    UnifiedBase, NCMHierarchy, CestCategory, NCMCestMapping, ProdutoExemplo,
    ClassificacaoRevisao, GoldenSetEntry, ExplicacaoAgente, ConsultaAgente,
    MetricasQualidade, EstadoOrdenacao, InteracaoWeb, CorrecaoIdentificada,
    EmbeddingProduto, KnowledgeBaseMetadata, ABCFarmaProduct
)

logger = logging.getLogger(__name__)

class UnifiedSQLiteService:
    """Serviço unificado para todas as operações SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Inicializa o serviço unificado"""
        if db_path is None:
            db_path = Path("data") / "unified_rag_system.db"
        
        self.db_path = Path(db_path)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Verificar se banco existe
        if not self.db_path.exists():
            logger.warning(f"Banco SQLite não encontrado: {self.db_path}")
            self._create_database()
    
    def _create_database(self):
        """Cria banco de dados se não existir"""
        logger.info("Criando banco de dados SQLite...")
        self.db_path.parent.mkdir(exist_ok=True)
        UnifiedBase.metadata.create_all(self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager para sessões do banco"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na sessão: {e}")
            raise
        finally:
            session.close()
    
    # =====================
    # KNOWLEDGE BASE OPERATIONS
    # =====================
    
    def buscar_ncm(self, codigo_ncm: str) -> Optional[Dict]:
        """Busca NCM por código"""
        with self.get_session() as session:
            ncm = session.query(NCMHierarchy).filter(
                NCMHierarchy.codigo_ncm == codigo_ncm,
                NCMHierarchy.ativo == True
            ).first()
            
            if ncm:
                return {
                    'codigo_ncm': ncm.codigo_ncm,
                    'codigo': ncm.codigo_ncm,  # Adicionar campo 'codigo' para compatibilidade
                    'descricao': ncm.descricao_oficial,  # Adicionar campo 'descricao' para compatibilidade
                    'descricao_oficial': ncm.descricao_oficial,
                    'descricao_curta': ncm.descricao_curta,
                    'nivel_hierarquico': ncm.nivel_hierarquico,
                    'codigo_pai': ncm.codigo_pai
                }
            return None
    
    def buscar_ncms_por_nivel(self, nivel: int, limite: int = 100) -> List[Dict]:
        """Busca NCMs por nível hierárquico"""
        with self.get_session() as session:
            ncms = session.query(NCMHierarchy).filter(
                NCMHierarchy.nivel_hierarquico == nivel,
                NCMHierarchy.ativo == True
            ).limit(limite).all()
            
            return [self._ncm_to_dict(ncm) for ncm in ncms]
    
    def buscar_ncms_por_padrao(self, padrao: str, limite: int = 20) -> List[Dict]:
        """Busca NCMs por padrão na descrição"""
        with self.get_session() as session:
            ncms = session.query(NCMHierarchy).filter(
                or_(
                    NCMHierarchy.descricao_oficial.ilike(f'%{padrao}%'),
                    NCMHierarchy.descricao_curta.ilike(f'%{padrao}%'),
                    NCMHierarchy.codigo_ncm.like(f'{padrao}%')
                ),
                NCMHierarchy.ativo == True
            ).limit(limite).all()
            
            return [self._ncm_to_dict(ncm) for ncm in ncms]
    
    def buscar_cest(self, codigo_cest: str) -> Optional[Dict]:
        """Busca CEST por código"""
        with self.get_session() as session:
            cest = session.query(CestCategory).filter(
                CestCategory.codigo_cest == codigo_cest,
                CestCategory.ativo == True
            ).first()
            
            if cest:
                return {
                    'codigo_cest': cest.codigo_cest,
                    'descricao_cest': cest.descricao_cest,
                    'descricao_resumida': cest.descricao_resumida,
                    'categoria_produto': cest.categoria_produto
                }
            return None
    
    def buscar_cests_para_ncm(self, codigo_ncm: str) -> List[Dict]:
        """Busca CESTs relacionados a um NCM"""
        with self.get_session() as session:
            mappings = session.query(NCMCestMapping, CestCategory).join(
                CestCategory, NCMCestMapping.cest_codigo == CestCategory.codigo_cest
            ).filter(
                NCMCestMapping.ncm_codigo == codigo_ncm,
                NCMCestMapping.ativo == True,
                CestCategory.ativo == True
            ).all()
            
            return [{
                'codigo_cest': cest.codigo_cest,
                'descricao_cest': cest.descricao_cest,
                'tipo_relacao': mapping.tipo_relacao,
                'confianca': mapping.confianca_mapeamento
            } for mapping, cest in mappings]
    
    def buscar_ncms_para_cest(self, codigo_cest: str) -> List[Dict]:
        """Busca NCMs relacionados a um CEST"""
        with self.get_session() as session:
            mappings = session.query(NCMCestMapping, NCMHierarchy).join(
                NCMHierarchy, NCMCestMapping.ncm_codigo == NCMHierarchy.codigo_ncm
            ).filter(
                NCMCestMapping.cest_codigo == codigo_cest,
                NCMCestMapping.ativo == True,
                NCMHierarchy.ativo == True
            ).all()
            
            return [{
                'codigo_ncm': ncm.codigo_ncm,
                'descricao_oficial': ncm.descricao_oficial,
                'tipo_relacao': mapping.tipo_relacao,
                'confianca': mapping.confianca_mapeamento
            } for mapping, ncm in mappings]
    
    def buscar_exemplos_ncm(self, codigo_ncm: str, limite: int = 10) -> List[Dict]:
        """Busca exemplos de produtos para um NCM"""
        with self.get_session() as session:
            exemplos = session.query(ProdutoExemplo).filter(
                ProdutoExemplo.ncm_codigo == codigo_ncm,
                ProdutoExemplo.ativo == True
            ).order_by(
                desc(ProdutoExemplo.qualidade_classificacao),
                desc(ProdutoExemplo.verificado_humano)
            ).limit(limite).all()
            
            return [{
                'gtin': exemplo.gtin,
                'descricao_produto': exemplo.descricao_produto,
                'marca': exemplo.marca,
                'modelo': exemplo.modelo,
                'categoria_produto': exemplo.categoria_produto,
                'qualidade_classificacao': exemplo.qualidade_classificacao,
                'verificado_humano': exemplo.verificado_humano
            } for exemplo in exemplos]
    
    # =====================
    # CLASSIFICAÇÃO OPERATIONS
    # =====================
    
    def criar_classificacao(self, produto_data: Dict) -> int:
        """Cria nova classificação"""
        with self.get_session() as session:
            classificacao = ClassificacaoRevisao(
                produto_id=produto_data.get('produto_id'),
                descricao_produto=produto_data.get('descricao_produto'),
                descricao_completa=produto_data.get('descricao_completa'),
                codigo_produto=produto_data.get('codigo_produto'),
                codigo_barra=produto_data.get('codigo_barra'),
                gtin_original=produto_data.get('gtin_original'),
                ncm_original=produto_data.get('ncm_original'),
                cest_original=produto_data.get('cest_original'),
                ncm_sugerido=produto_data.get('ncm_sugerido'),
                cest_sugerido=produto_data.get('cest_sugerido'),
                confianca_sugerida=produto_data.get('confianca_sugerida'),
                justificativa_sistema=produto_data.get('justificativa_sistema'),
                dados_trace_json=produto_data.get('dados_trace_json')
            )
            
            session.add(classificacao)
            session.flush()
            return classificacao.id
    
    def atualizar_classificacao(self, classificacao_id: int, updates: Dict) -> bool:
        """Atualiza classificação existente"""
        with self.get_session() as session:
            classificacao = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.id == classificacao_id
            ).first()
            
            if classificacao:
                for key, value in updates.items():
                    if hasattr(classificacao, key):
                        setattr(classificacao, key, value)
                return True
            return False
    
    def buscar_classificacoes_pendentes(self, limite: int = 50, offset: int = 0) -> List[Dict]:
        """Busca classificações pendentes de revisão"""
        with self.get_session() as session:
            classificacoes = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
            ).order_by(desc(ClassificacaoRevisao.data_criacao)).offset(offset).limit(limite).all()
            
            return [self._classificacao_to_dict(c) for c in classificacoes]
    
    def buscar_classificacao_por_id(self, classificacao_id: int) -> Optional[Dict]:
        """Busca classificação por ID"""
        with self.get_session() as session:
            classificacao = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.id == classificacao_id
            ).first()
            
            if classificacao:
                return self._classificacao_to_dict(classificacao)
            return None
    
    def revisar_classificacao(self, classificacao_id: int, revisao_data: Dict) -> bool:
        """Aplica revisão humana à classificação"""
        with self.get_session() as session:
            classificacao = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.id == classificacao_id
            ).first()
            
            if classificacao:
                classificacao.status_revisao = revisao_data.get('status_revisao', 'CORRIGIDO')
                classificacao.ncm_corrigido = revisao_data.get('ncm_corrigido')
                classificacao.cest_corrigido = revisao_data.get('cest_corrigido')
                classificacao.justificativa_correcao = revisao_data.get('justificativa_correcao')
                classificacao.revisado_por = revisao_data.get('revisado_por')
                classificacao.data_revisao = datetime.now()
                classificacao.tempo_revisao_segundos = revisao_data.get('tempo_revisao_segundos')
                
                # Registrar correção se necessário
                if revisao_data.get('status_revisao') == 'CORRIGIDO':
                    self._registrar_correcao(session, classificacao_id, revisao_data)
                
                return True
            return False
    
    # =====================
    # GOLDEN SET OPERATIONS
    # =====================
    
    def adicionar_ao_golden_set(self, produto_data: Dict) -> int:
        """Adiciona entrada ao Golden Set"""
        with self.get_session() as session:
            entrada = GoldenSetEntry(
                produto_id=produto_data.get('produto_id'),
                descricao_produto=produto_data.get('descricao_produto'),
                descricao_completa=produto_data.get('descricao_completa'),
                codigo_produto=produto_data.get('codigo_produto'),
                gtin_validado=produto_data.get('gtin_validado'),
                ncm_final=produto_data.get('ncm_final'),
                cest_final=produto_data.get('cest_final'),
                confianca_original=produto_data.get('confianca_original'),
                fonte_validacao=produto_data.get('fonte_validacao', 'HUMANA'),
                justificativa_inclusao=produto_data.get('justificativa_inclusao'),
                revisado_por=produto_data.get('revisado_por'),
                qualidade_score=produto_data.get('qualidade_score', 1.0),
                **{k: v for k, v in produto_data.items() if k.startswith('explicacao_') or k.startswith('palavras_') or k.startswith('categoria_')}
            )
            
            session.add(entrada)
            session.flush()
            return entrada.id
    
    def buscar_golden_set(self, ncm: Optional[str] = None, limite: int = 50) -> List[Dict]:
        """Busca entradas do Golden Set"""
        with self.get_session() as session:
            query = session.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == True)
            
            if ncm:
                query = query.filter(GoldenSetEntry.ncm_final == ncm)
            
            entradas = query.order_by(
                desc(GoldenSetEntry.qualidade_score),
                desc(GoldenSetEntry.vezes_usado)
            ).limit(limite).all()
            
            return [self._golden_set_to_dict(e) for e in entradas]
    
    def usar_golden_set_entry(self, entry_id: int):
        """Registra uso de uma entrada do Golden Set"""
        with self.get_session() as session:
            entrada = session.query(GoldenSetEntry).filter(
                GoldenSetEntry.id == entry_id
            ).first()
            
            if entrada:
                entrada.vezes_usado += 1
                entrada.ultima_utilizacao = datetime.now()
    
    # =====================
    # AGENT EXPLANATIONS
    # =====================
    
    def salvar_explicacao_agente(self, explicacao_data: Dict) -> int:
        """Salva explicação de um agente"""
        with self.get_session() as session:
            explicacao = ExplicacaoAgente(
                produto_id=explicacao_data.get('produto_id'),
                classificacao_id=explicacao_data.get('classificacao_id'),
                agente_nome=explicacao_data.get('agente_nome'),
                agente_versao=explicacao_data.get('agente_versao', '1.0'),
                input_original=explicacao_data.get('input_original'),
                contexto_utilizado=explicacao_data.get('contexto_utilizado'),
                etapas_processamento=explicacao_data.get('etapas_processamento'),
                palavras_chave_identificadas=explicacao_data.get('palavras_chave_identificadas'),
                produtos_similares_encontrados=explicacao_data.get('produtos_similares_encontrados'),
                resultado_agente=explicacao_data.get('resultado_agente'),
                explicacao_detalhada=explicacao_data.get('explicacao_detalhada'),
                justificativa_tecnica=explicacao_data.get('justificativa_tecnica'),
                nivel_confianca=explicacao_data.get('nivel_confianca'),
                rag_consultado=explicacao_data.get('rag_consultado', False),
                golden_set_utilizado=explicacao_data.get('golden_set_utilizado', False),
                base_ncm_consultada=explicacao_data.get('base_ncm_consultada', False),
                exemplos_utilizados=explicacao_data.get('exemplos_utilizados'),
                tempo_processamento_ms=explicacao_data.get('tempo_processamento_ms'),
                memoria_utilizada_mb=explicacao_data.get('memoria_utilizada_mb'),
                tokens_llm_utilizados=explicacao_data.get('tokens_llm_utilizados'),
                sessao_classificacao=explicacao_data.get('sessao_classificacao')
            )
            
            session.add(explicacao)
            session.flush()
            return explicacao.id
    
    def buscar_explicacoes_produto(self, produto_id: int) -> List[Dict]:
        """Busca explicações de todos os agentes para um produto"""
        with self.get_session() as session:
            explicacoes = session.query(ExplicacaoAgente).filter(
                ExplicacaoAgente.produto_id == produto_id
            ).order_by(ExplicacaoAgente.data_execucao).all()
            
            return [self._explicacao_to_dict(e) for e in explicacoes]
    
    def buscar_consultas_produto(self, produto_id: int) -> List[Dict]:
        """Busca consultas realizadas para um produto"""
        with self.get_session() as session:
            consultas = session.query(ConsultaAgente).filter(
                ConsultaAgente.produto_id == produto_id
            ).order_by(ConsultaAgente.data_consulta).all()
            
            return [self._consulta_to_dict(c) for c in consultas]
    
    def registrar_metrica_qualidade(self, metrica_data: Dict) -> int:
        """Registra métrica de qualidade"""
        with self.get_session() as session:
            metrica = MetricasQualidade(
                produto_id=metrica_data.get('produto_id'),
                tipo_metrica=metrica_data.get('tipo_metrica'),
                valor_metrica=metrica_data.get('valor_metrica'),
                detalhes_metrica=metrica_data.get('detalhes_metrica'),
                data_calculo=metrica_data.get('data_calculo', datetime.now()),
                versao_algoritmo=metrica_data.get('versao_algoritmo', '1.0')
            )
            
            session.add(metrica)
            session.flush()
            return metrica.id
    
    def buscar_produtos_por_descricao(self, termo: str, limite: int = 20) -> List[Dict]:
        """Busca produtos por descrição"""
        with self.get_session() as session:
            classificacoes = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.descricao_produto.ilike(f'%{termo}%')
            ).limit(limite).all()
            
            return [self._classificacao_to_dict(c) for c in classificacoes]
    
    def buscar_produtos_por_codigo(self, termo: str, limite: int = 20) -> List[Dict]:
        """Busca produtos por código"""
        with self.get_session() as session:
            classificacoes = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.codigo_produto.ilike(f'%{termo}%')
            ).limit(limite).all()
            
            return [self._classificacao_to_dict(c) for c in classificacoes]
    
    def buscar_produtos_por_codigo_barra(self, termo: str, limite: int = 20) -> List[Dict]:
        """Busca produtos por código de barras"""
        with self.get_session() as session:
            classificacoes = session.query(ClassificacaoRevisao).filter(
                or_(
                    ClassificacaoRevisao.codigo_barra.ilike(f'%{termo}%'),
                    ClassificacaoRevisao.gtin_original.ilike(f'%{termo}%')
                )
            ).limit(limite).all()
            
            return [self._classificacao_to_dict(c) for c in classificacoes]
    
    def buscar_classificacoes_para_exportacao(self, filtros: Optional[Dict] = None, 
                                            incluir_explicacoes: bool = True,
                                            incluir_consultas: bool = True) -> List[Dict]:
        """Busca classificações para exportação"""
        with self.get_session() as session:
            query = session.query(ClassificacaoRevisao)
            
            # Aplicar filtros se fornecidos
            if filtros:
                if 'status_revisao' in filtros:
                    query = query.filter(ClassificacaoRevisao.status_revisao == filtros['status_revisao'])
                if 'data_inicio' in filtros:
                    query = query.filter(ClassificacaoRevisao.data_criacao >= filtros['data_inicio'])
                if 'data_fim' in filtros:
                    query = query.filter(ClassificacaoRevisao.data_criacao <= filtros['data_fim'])
            
            classificacoes = query.all()
            
            resultados = []
            for c in classificacoes:
                dados = self._classificacao_to_dict(c)
                
                if incluir_explicacoes:
                    dados['explicacoes'] = self.buscar_explicacoes_produto(c.produto_id)
                
                if incluir_consultas:
                    dados['consultas'] = self.buscar_consultas_produto(c.produto_id)
                
                resultados.append(dados)
            
            return resultados
    
    def get_revision_stats(self) -> Dict:
        """Obtém estatísticas específicas de revisão"""
        with self.get_session() as session:
            total = session.query(ClassificacaoRevisao).count()
            pendentes = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == 'PENDENTE_REVISAO'
            ).count()
            aprovadas = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == 'APROVADO'
            ).count()
            corrigidas = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.status_revisao == 'CORRIGIDO'
            ).count()
            
            return {
                'total_classificacoes': total,
                'pendentes_revisao': pendentes,
                'aprovadas': aprovadas,
                'corrigidas': corrigidas,
                'taxa_revisao': ((total - pendentes) / total * 100) if total > 0 else 0
            }
    
    # =====================
    # AGENT QUERIES
    # =====================
    
    def registrar_consulta_agente(self, consulta_data: Dict) -> int:
        """Registra consulta realizada por um agente"""
        with self.get_session() as session:
            consulta = ConsultaAgente(
                agente_nome=consulta_data.get('agente_nome'),
                produto_id=consulta_data.get('produto_id'),
                sessao_classificacao=consulta_data.get('sessao_classificacao'),
                tipo_consulta=consulta_data.get('tipo_consulta'),
                query_original=consulta_data.get('query_original'),
                query_processada=consulta_data.get('query_processada'),
                parametros_busca=consulta_data.get('parametros_busca'),
                filtros_aplicados=consulta_data.get('filtros_aplicados'),
                limite_resultados=consulta_data.get('limite_resultados'),
                total_resultados_encontrados=consulta_data.get('total_resultados_encontrados'),
                resultados_utilizados=consulta_data.get('resultados_utilizados'),
                score_relevancia_medio=consulta_data.get('score_relevancia_medio'),
                tempo_consulta_ms=consulta_data.get('tempo_consulta_ms'),
                fonte_dados=consulta_data.get('fonte_dados'),
                consulta_bem_sucedida=consulta_data.get('consulta_bem_sucedida', True),
                qualidade_resultados=consulta_data.get('qualidade_resultados'),
                feedback_agente=consulta_data.get('feedback_agente')
            )
            
            session.add(consulta)
            session.flush()
            return consulta.id
    
    # =====================
    # EMPRESA CONTEXTO
    # =====================
    
    def cadastrar_informacao_empresa(self, dados_empresa: Dict) -> int:
        """Cadastra informações da empresa"""
        from database.models import InformacaoEmpresa
        
        with self.get_session() as session:
            empresa = InformacaoEmpresa(
                tipo_atividade=dados_empresa.get('tipo_atividade'),
                descricao_atividade=dados_empresa.get('descricao_atividade'),
                segmento_mercado=dados_empresa.get('segmento_mercado'),
                canal_venda=dados_empresa.get('canal_venda'),
                regiao_atuacao=dados_empresa.get('regiao_atuacao'),
                porte_empresa=dados_empresa.get('porte_empresa'),
                regime_tributario=dados_empresa.get('regime_tributario'),
                observacoes=dados_empresa.get('observacoes'),
                ativo=dados_empresa.get('ativo', True),
                data_criacao=datetime.now(),
                data_atualizacao=datetime.now()
            )
            
            session.add(empresa)
            session.flush()
            return empresa.id
    
    def obter_informacao_empresa(self) -> Optional[Dict]:
        """Obtém informações da empresa ativa"""
        from database.models import InformacaoEmpresa
        
        with self.get_session() as session:
            empresa = session.query(InformacaoEmpresa).filter(
                InformacaoEmpresa.ativo == True
            ).first()
            
            if not empresa:
                return None
                
            return {
                'id': empresa.id,
                'tipo_atividade': empresa.tipo_atividade,
                'descricao_atividade': empresa.descricao_atividade,
                'segmento_mercado': empresa.segmento_mercado,
                'canal_venda': empresa.canal_venda,
                'regiao_atuacao': empresa.regiao_atuacao,
                'porte_empresa': empresa.porte_empresa,
                'regime_tributario': empresa.regime_tributario,
                'observacoes': empresa.observacoes,
                'ativo': empresa.ativo,
                'data_criacao': empresa.data_criacao.isoformat() if empresa.data_criacao else None,
                'data_atualizacao': empresa.data_atualizacao.isoformat() if empresa.data_atualizacao else None
            }
    
    def atualizar_informacao_empresa(self, empresa_id: int, dados_atualizacao: Dict) -> bool:
        """Atualiza informações da empresa"""
        from database.models import InformacaoEmpresa
        
        with self.get_session() as session:
            empresa = session.query(InformacaoEmpresa).filter(
                InformacaoEmpresa.id == empresa_id
            ).first()
            
            if not empresa:
                return False
            
            # Atualizar campos fornecidos
            for campo, valor in dados_atualizacao.items():
                if hasattr(empresa, campo):
                    setattr(empresa, campo, valor)
            
            empresa.data_atualizacao = datetime.now()
            session.commit()
            return True
    
    def registrar_contexto_classificacao(self, dados_contexto: Dict) -> int:
        """Registra contexto aplicado em uma classificação"""
        from database.models import ContextoClassificacao
        
        with self.get_session() as session:
            contexto = ContextoClassificacao(
                produto_id=dados_contexto.get('produto_id'),
                empresa_id=dados_contexto.get('empresa_id'),
                agente_nome=dados_contexto.get('agente_nome'),
                contexto_aplicado=dados_contexto.get('contexto_aplicado'),
                impacto_classificacao=dados_contexto.get('impacto_classificacao'),
                cest_aplicado_contexto=dados_contexto.get('cest_aplicado_contexto'),
                justificativa_contexto=dados_contexto.get('justificativa_contexto'),
                data_aplicacao=datetime.now()
            )
            
            session.add(contexto)
            session.flush()
            return contexto.id

    # =====================
    # METRICS AND MONITORING
    # =====================    def calcular_metricas_periodo(self, data_inicio: datetime, data_fim: datetime) -> Dict:
        """Calcula métricas para um período"""
        with self.get_session() as session:
            # Classificações no período
            classificacoes = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.data_criacao.between(data_inicio, data_fim)
            ).all()
            
            total_classificacoes = len(classificacoes)
            revisadas = [c for c in classificacoes if c.status_revisao != 'PENDENTE_REVISAO']
            aprovadas = [c for c in revisadas if c.status_revisao == 'APROVADO']
            corrigidas = [c for c in revisadas if c.status_revisao == 'CORRIGIDO']
            
            # Calcular métricas
            taxa_aprovacao = len(aprovadas) / len(revisadas) if revisadas else 0
            confianca_media = sum(c.confianca_sugerida for c in classificacoes if c.confianca_sugerida) / total_classificacoes if total_classificacoes else 0
            
            return {
                'total_classificacoes': total_classificacoes,
                'total_revisadas': len(revisadas),
                'total_aprovadas': len(aprovadas),
                'total_corrigidas': len(corrigidas),
                'taxa_aprovacao': taxa_aprovacao,
                'confianca_media': confianca_media
            }
    
    def get_dashboard_stats(self) -> Dict:
        """Obtém estatísticas para o dashboard"""
        with self.get_session() as session:
            # Estatísticas gerais
            stats = {
                'total_ncms': session.query(NCMHierarchy).filter(NCMHierarchy.ativo == True).count(),
                'total_cests': session.query(CestCategory).filter(CestCategory.ativo == True).count(),
                'total_mapeamentos': session.query(NCMCestMapping).filter(NCMCestMapping.ativo == True).count(),
                'total_exemplos': session.query(ProdutoExemplo).filter(ProdutoExemplo.ativo == True).count(),
                'total_classificacoes': session.query(ClassificacaoRevisao).count(),
                'classificacoes_pendentes': session.query(ClassificacaoRevisao).filter(
                    ClassificacaoRevisao.status_revisao == 'PENDENTE_REVISAO'
                ).count(),
                'golden_set_entries': session.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == True).count(),
                'explicacoes_agentes': session.query(ExplicacaoAgente).count(),
                'consultas_agentes': session.query(ConsultaAgente).count()
            }
            
            # Estatísticas recentes (últimos 7 dias)
            data_limite = datetime.now() - timedelta(days=7)
            stats['classificacoes_recentes'] = session.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.data_criacao >= data_limite
            ).count()
            
            return stats
    
    # =====================
    # WEB INTERFACE TRACKING
    # =====================
    
    def registrar_interacao_web(self, interacao_data: Dict) -> int:
        """Registra interação com a interface web"""
        with self.get_session() as session:
            interacao = InteracaoWeb(
                sessao_usuario=interacao_data.get('sessao_usuario'),
                usuario_id=interacao_data.get('usuario_id'),
                tipo_interacao=interacao_data.get('tipo_interacao'),
                endpoint_acessado=interacao_data.get('endpoint_acessado'),
                metodo_http=interacao_data.get('metodo_http'),
                dados_entrada=interacao_data.get('dados_entrada'),
                dados_saida=interacao_data.get('dados_saida'),
                tempo_processamento_ms=interacao_data.get('tempo_processamento_ms'),
                sucesso=interacao_data.get('sucesso', True),
                codigo_resposta=interacao_data.get('codigo_resposta', 200),
                mensagem_erro=interacao_data.get('mensagem_erro'),
                ip_usuario=interacao_data.get('ip_usuario'),
                user_agent=interacao_data.get('user_agent')
            )
            
            session.add(interacao)
            session.flush()
            return interacao.id
    
    # =====================
    # UTILITY METHODS
    # =====================
    
    def _ncm_to_dict(self, ncm: NCMHierarchy) -> Dict:
        """Converte NCM para dicionário"""
        return {
            'codigo_ncm': ncm.codigo_ncm,
            'descricao_oficial': ncm.descricao_oficial,
            'descricao_curta': ncm.descricao_curta,
            'nivel_hierarquico': ncm.nivel_hierarquico,
            'codigo_pai': ncm.codigo_pai,
            'ativo': ncm.ativo
        }
    
    def _classificacao_to_dict(self, classificacao: ClassificacaoRevisao) -> Dict:
        """Converte classificação para dicionário"""
        return {
            'id': classificacao.id,
            'produto_id': classificacao.produto_id,
            'descricao_produto': classificacao.descricao_produto,
            'descricao_completa': classificacao.descricao_completa,
            'codigo_produto': classificacao.codigo_produto,
            'codigo_barra': classificacao.codigo_barra,
            'gtin_original': classificacao.gtin_original,
            'ncm_original': classificacao.ncm_original,
            'cest_original': classificacao.cest_original,
            'ncm_sugerido': classificacao.ncm_sugerido,
            'cest_sugerido': classificacao.cest_sugerido,
            'confianca_sugerida': classificacao.confianca_sugerida,
            'status_revisao': classificacao.status_revisao,
            'ncm_corrigido': classificacao.ncm_corrigido,
            'cest_corrigido': classificacao.cest_corrigido,
            'justificativa_correcao': classificacao.justificativa_correcao,
            'revisado_por': classificacao.revisado_por,
            'data_revisao': classificacao.data_revisao.isoformat() if classificacao.data_revisao else None,
            'data_criacao': classificacao.data_criacao.isoformat() if classificacao.data_criacao else None
        }
    
    def _golden_set_to_dict(self, entrada: GoldenSetEntry) -> Dict:
        """Converte entrada do Golden Set para dicionário"""
        return {
            'id': entrada.id,
            'produto_id': entrada.produto_id,
            'descricao_produto': entrada.descricao_produto,
            'ncm_final': entrada.ncm_final,
            'cest_final': entrada.cest_final,
            'qualidade_score': entrada.qualidade_score,
            'vezes_usado': entrada.vezes_usado,
            'revisado_por': entrada.revisado_por,
            'data_adicao': entrada.data_adicao.isoformat() if entrada.data_adicao else None
        }
    
    def _explicacao_to_dict(self, explicacao: ExplicacaoAgente) -> Dict:
        """Converte explicação para dicionário"""
        return {
            'id': explicacao.id,
            'agente_nome': explicacao.agente_nome,
            'explicacao_detalhada': explicacao.explicacao_detalhada,
            'nivel_confianca': explicacao.nivel_confianca,
            'tempo_processamento_ms': explicacao.tempo_processamento_ms,
            'data_execucao': explicacao.data_execucao.isoformat() if explicacao.data_execucao else None
        }
    
    def _consulta_to_dict(self, consulta: ConsultaAgente) -> Dict:
        """Converte consulta para dicionário"""
        return {
            'id': consulta.id,
            'agente_nome': consulta.agente_nome,
            'tipo_consulta': consulta.tipo_consulta,
            'query_original': consulta.query_original,
            'total_resultados_encontrados': consulta.total_resultados_encontrados,
            'tempo_consulta_ms': consulta.tempo_consulta_ms,
            'consulta_bem_sucedida': consulta.consulta_bem_sucedida,
            'data_consulta': consulta.data_consulta.isoformat() if consulta.data_consulta else None
        }
    
    def _registrar_correcao(self, session: Session, classificacao_id: int, revisao_data: Dict):
        """Registra correção identificada"""
        # Implementar lógica de registro de correções
        pass
    
    def contar_registros(self) -> Dict[str, int]:
        """Conta registros em todas as tabelas"""
        with self.get_session() as session:
            return {
                'ncms': session.query(NCMHierarchy).filter(NCMHierarchy.ativo == True).count(),
                'cests': session.query(CestCategory).filter(CestCategory.ativo == True).count(),
                'mapeamentos': session.query(NCMCestMapping).filter(NCMCestMapping.ativo == True).count(),
                'exemplos': session.query(ProdutoExemplo).filter(ProdutoExemplo.ativo == True).count(),
                'classificacoes': session.query(ClassificacaoRevisao).count(),
                'golden_set': session.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == True).count(),
                'explicacoes': session.query(ExplicacaoAgente).count(),
                'consultas': session.query(ConsultaAgente).count(),
                'abc_farma': session.query(ABCFarmaProduct).filter(ABCFarmaProduct.ativo == True).count()
            }

    # ============================================================================
    # ABC FARMA SEARCH METHODS
    # ============================================================================
    
    def search_abc_farma_by_text(self, query: str, limit: int = 10) -> List[Dict]:
        """Busca produtos ABC Farma por texto"""
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip().lower()
        
        with self.get_session() as session:
            # Busca por descrição similar
            results = session.query(ABCFarmaProduct).filter(
                and_(
                    ABCFarmaProduct.ativo == True,
                    or_(
                        ABCFarmaProduct.descricao_completa.ilike(f'%{query}%'),
                        ABCFarmaProduct.principio_ativo.ilike(f'%{query}%'),
                        ABCFarmaProduct.laboratorio.ilike(f'%{query}%')
                    )
                )
            ).limit(limit).all()
            
            return [self._abc_farma_to_dict(product) for product in results]
    
    def search_abc_farma_by_principio_ativo(self, principio_ativo: str, limit: int = 10) -> List[Dict]:
        """Busca produtos ABC Farma por princípio ativo"""
        if not principio_ativo:
            return []
        
        with self.get_session() as session:
            results = session.query(ABCFarmaProduct).filter(
                and_(
                    ABCFarmaProduct.ativo == True,
                    ABCFarmaProduct.principio_ativo.ilike(f'%{principio_ativo.strip()}%')
                )
            ).limit(limit).all()
            
            return [self._abc_farma_to_dict(product) for product in results]
    
    def _abc_farma_to_dict(self, product: 'ABCFarmaProduct') -> Dict:
        """Converte produto ABC Farma para dicionário"""
        return {
            'id': product.id,
            'ean': product.codigo_barra,  # Usar codigo_barra como EAN
            'descricao': product.descricao_completa,  # Campo principal
            'principio_ativo': product.principio_ativo,
            'laboratorio': product.laboratorio,
            'ncm': product.ncm_farmaceutico,
            'classe_terapeutica': getattr(product, 'categoria_terapeutica', None),
            'tipo_produto': getattr(product, 'categoria', None),
            'concentracao': product.concentracao,
            'forma_farmaceutica': product.forma_farmaceutica,
            'registro_ms': getattr(product, 'registro_anvisa', None),
            'pmc_0': getattr(product, 'pmc_0', None),
            'pmc_12': getattr(product, 'pmc_12', None),
            'pmc_17': getattr(product, 'pmc_17', None),
            'pmc_18': getattr(product, 'pmc_18', None),
            'pmc_20': getattr(product, 'pmc_20', None),
            'created_at': getattr(product, 'data_cadastro', None),
            'updated_at': getattr(product, 'data_atualizacao', None)
        }

# Instância global do serviço
unified_service = None

def get_unified_service(db_path: Optional[str] = None) -> UnifiedSQLiteService:
    """Obtém instância global do serviço unificado"""
    global unified_service
    if unified_service is None:
        unified_service = UnifiedSQLiteService(db_path)
    return unified_service
