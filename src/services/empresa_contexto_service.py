"""
Serviço para gerenciar informações da empresa e contexto de classificação
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
import logging
from datetime import datetime

from database.models import InformacaoEmpresa, ContextoClassificacao, ClassificacaoRevisao
from database.connection import get_db

logger = logging.getLogger(__name__)


class EmpresaContextoService:
    """
    Serviço responsável por gerenciar informações da empresa
    e aplicar contexto nas classificações
    """
    
    def __init__(self):
        self.contexto_cache = {}  # Cache para contexto da empresa ativa
    
    def cadastrar_empresa(
        self,
        db: Session,
        empresa_id: str,
        dados_empresa: Dict[str, Any],
        usuario: str = "Sistema"
    ) -> InformacaoEmpresa:
        """
        Cadastra ou atualiza informações da empresa
        
        Args:
            db: Sessão do banco
            empresa_id: ID único da empresa (CNPJ)
            dados_empresa: Dados da empresa
            usuario: Usuário responsável pelo cadastro
            
        Returns:
            InformacaoEmpresa: Objeto criado/atualizado
        """
        try:
            # Verificar se empresa já existe
            empresa_existente = db.query(InformacaoEmpresa).filter(
                InformacaoEmpresa.empresa_id == empresa_id
            ).first()
            
            if empresa_existente:
                # Atualizar dados existentes
                for campo, valor in dados_empresa.items():
                    if hasattr(empresa_existente, campo):
                        setattr(empresa_existente, campo, valor)
                
                empresa_existente.data_atualizacao = datetime.now()
                empresa = empresa_existente
                logger.info(f"📊 Empresa {empresa_id} atualizada")
            else:
                # Criar nova empresa
                empresa = InformacaoEmpresa(
                    empresa_id=empresa_id,
                    cadastrado_por=usuario,
                    **dados_empresa
                )
                db.add(empresa)
                logger.info(f"✅ Nova empresa {empresa_id} cadastrada")
            
            db.commit()
            db.refresh(empresa)
            
            # Limpar cache
            self.contexto_cache.clear()
            
            return empresa
            
        except Exception as e:
            logger.error(f"❌ Erro ao cadastrar empresa {empresa_id}: {e}")
            db.rollback()
            raise
    
    def obter_empresa(self, db: Session, empresa_id: str) -> Optional[InformacaoEmpresa]:
        """Obtém informações da empresa"""
        return db.query(InformacaoEmpresa).filter(
            InformacaoEmpresa.empresa_id == empresa_id,
            InformacaoEmpresa.ativo == True
        ).first()
    
    def obter_contexto_empresa(self, db: Session, empresa_id: str) -> Dict[str, Any]:
        """
        Obtém contexto completo da empresa para uso pelos agentes
        """
        # Verificar cache primeiro
        if empresa_id in self.contexto_cache:
            return self.contexto_cache[empresa_id]
        
        empresa = self.obter_empresa(db, empresa_id)
        if not empresa:
            logger.warning(f"⚠️ Empresa {empresa_id} não encontrada")
            return {}
        
        contexto = {
            "empresa_id": empresa.empresa_id,
            "razao_social": empresa.razao_social,
            "atividade_descricao": empresa.atividade_descricao,
            "modalidade_venda": empresa.modalidade_venda,
            "tipo_estabelecimento": empresa.tipo_estabelecimento,
            "segmento_cest_aplicavel": empresa.segmento_cest_aplicavel,
            "observacoes_classificacao": empresa.observacoes_classificacao,
            "categorias_produtos": empresa.categorias_produtos or [],
            "contexto_agentes": empresa.contexto_agentes or {},
            "preferencias_classificacao": empresa.preferencias_classificacao or {},
            "cnae_principal": empresa.cnae_principal,
            "estados_atuacao": empresa.estados_atuacao or [],
            "regime_tributario": empresa.regime_tributario
        }
        
        # Cache do contexto
        self.contexto_cache[empresa_id] = contexto
        
        logger.info(f"🏢 Contexto da empresa {empresa_id} carregado")
        return contexto
    
    def aplicar_contexto_classificacao(
        self,
        db: Session,
        produto_id: int,
        empresa_id: str,
        classificacao_id: Optional[int] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aplica contexto da empresa à classificação de um produto
        
        Args:
            db: Sessão do banco
            produto_id: ID do produto
            empresa_id: ID da empresa
            classificacao_id: ID da classificação (opcional)
            contexto_adicional: Contexto adicional específico
            
        Returns:
            Dict com contexto aplicado
        """
        try:
            # Obter contexto da empresa
            contexto_empresa = self.obter_contexto_empresa(db, empresa_id)
            
            if not contexto_empresa:
                return {}
            
            # Montar contexto específico para os agentes
            contexto_agentes = {
                "expansion_agent": {
                    "atividade_empresa": contexto_empresa.get("atividade_descricao"),
                    "categorias_tipicas": contexto_empresa.get("categorias_produtos", []),
                    "modalidade_venda": contexto_empresa.get("modalidade_venda"),
                },
                "ncm_agent": {
                    "cnae_principal": contexto_empresa.get("cnae_principal"),
                    "tipo_estabelecimento": contexto_empresa.get("tipo_estabelecimento"),
                    "observacoes": contexto_empresa.get("observacoes_classificacao"),
                },
                "cest_agent": {
                    "modalidade_venda": contexto_empresa.get("modalidade_venda"),
                    "segmento_cest_sugerido": contexto_empresa.get("segmento_cest_aplicavel"),
                    "regime_tributario": contexto_empresa.get("regime_tributario"),
                    "estados_atuacao": contexto_empresa.get("estados_atuacao", []),
                    "observacoes_cest": self._gerar_observacoes_cest(contexto_empresa),
                },
                "reconciler_agent": {
                    "preferencias": contexto_empresa.get("preferencias_classificacao", {}),
                    "contexto_geral": contexto_empresa.get("observacoes_classificacao"),
                }
            }
            
            # Adicionar contexto adicional se fornecido
            if contexto_adicional:
                for agente, contexto_agente in contexto_agentes.items():
                    if agente in contexto_adicional:
                        contexto_agente.update(contexto_adicional[agente])
            
            # Salvar contexto aplicado no banco
            contexto_aplicado = ContextoClassificacao(
                produto_id=produto_id,
                classificacao_id=classificacao_id,
                empresa_id=empresa_id,
                contexto_geral=contexto_empresa,
                contexto_especifico=contexto_agentes,
                modalidade_venda_aplicada=contexto_empresa.get("modalidade_venda"),
                segmento_cest_considerado=contexto_empresa.get("segmento_cest_aplicavel"),
                observacoes_contexto=f"Contexto aplicado automaticamente para empresa {empresa_id}"
            )
            
            db.add(contexto_aplicado)
            db.commit()
            
            logger.info(f"🎯 Contexto aplicado para produto {produto_id} da empresa {empresa_id}")
            
            return contexto_agentes
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar contexto: {e}")
            db.rollback()
            return {}
    
    def _gerar_observacoes_cest(self, contexto_empresa: Dict[str, Any]) -> str:
        """Gera observações específicas para classificação CEST"""
        observacoes = []
        
        modalidade = contexto_empresa.get("modalidade_venda")
        if modalidade == "porta_a_porta":
            observacoes.append("IMPORTANTE: Empresa realiza vendas porta a porta - considerar CEST segmento 28")
        elif modalidade == "online":
            observacoes.append("Empresa atua no comércio eletrônico - verificar regulamentações específicas")
        elif modalidade == "atacado":
            observacoes.append("Empresa atua no atacado - considerar isenções e regras específicas")
        
        segmento = contexto_empresa.get("segmento_cest_aplicavel")
        if segmento:
            observacoes.append(f"Segmento CEST sugerido pela atividade da empresa: {segmento}")
        
        regime = contexto_empresa.get("regime_tributario")
        if regime == "simples_nacional":
            observacoes.append("Empresa no Simples Nacional - verificar aplicabilidade do CEST")
        
        return "; ".join(observacoes)
    
    def listar_empresas(self, db: Session) -> List[InformacaoEmpresa]:
        """Lista todas as empresas ativas"""
        return db.query(InformacaoEmpresa).filter(
            InformacaoEmpresa.ativo == True
        ).order_by(InformacaoEmpresa.razao_social).all()
    
    def obter_historico_contexto(
        self,
        db: Session,
        produto_id: Optional[int] = None,
        empresa_id: Optional[str] = None
    ) -> List[ContextoClassificacao]:
        """Obtém histórico de contexto aplicado"""
        query = db.query(ContextoClassificacao)
        
        if produto_id:
            query = query.filter(ContextoClassificacao.produto_id == produto_id)
        
        if empresa_id:
            query = query.filter(ContextoClassificacao.empresa_id == empresa_id)
        
        return query.order_by(ContextoClassificacao.data_aplicacao.desc()).all()


# Instância global
empresa_contexto_service = EmpresaContextoService()
