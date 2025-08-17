"""
Context Manager Pattern para Isolamento Multiempresa
Implementa o padrão de contexto de empresa para garantir isolamento total
"""

from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
import threading
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class EmpresaContext:
    """Contexto da empresa ativa"""
    empresa_id: int
    cnpj: str
    nome: str
    db_path: str
    schema_config: Dict[str, Any]
    user_permissions: Dict[str, bool]

class EmpresaContextManager:
    """
    Gerenciador de contexto multiempresa com thread safety
    Garante que cada requisição opere no contexto correto
    """
    
    def __init__(self):
        self._context = threading.local()
        self._empresa_configs = {}
    
    @property
    def current_context(self) -> Optional[EmpresaContext]:
        """Retorna o contexto atual da thread"""
        return getattr(self._context, 'empresa', None)
    
    @contextmanager
    def empresa_context(self, empresa_id: int, user_id: str) -> Generator[EmpresaContext, None, None]:
        """
        Context manager para operações no contexto de uma empresa
        
        Usage:
            with context_manager.empresa_context(123, "user123") as ctx:
                # Todas as operações aqui são no contexto da empresa 123
                resultado = classificar_produto(produto_data)
        """
        try:
            # Carregar configuração da empresa
            empresa_config = self._load_empresa_config(empresa_id)
            
            # Validar permissões do usuário
            user_permissions = self._validate_user_permissions(user_id, empresa_id)
            
            # Criar contexto
            context = EmpresaContext(
                empresa_id=empresa_id,
                cnpj=empresa_config['cnpj'],
                nome=empresa_config['nome'],
                db_path=f"data/empresas/empresa_{empresa_id}.db",
                schema_config=empresa_config,
                user_permissions=user_permissions
            )
            
            # Definir contexto na thread local
            self._context.empresa = context
            
            # Log de auditoria
            self._log_context_access(user_id, empresa_id, "CONTEXT_ENTER")
            
            yield context
            
        finally:
            # Limpar contexto
            self._context.empresa = None
            self._log_context_access(user_id, empresa_id, "CONTEXT_EXIT")
    
    def _load_empresa_config(self, empresa_id: int) -> Dict[str, Any]:
        """Carrega configuração da empresa do cache ou banco"""
        if empresa_id not in self._empresa_configs:
            # Carregar do banco centralizado
            with get_central_db() as db:
                empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
                if not empresa:
                    raise EmpresaNotFoundError(f"Empresa {empresa_id} não encontrada")
                
                self._empresa_configs[empresa_id] = {
                    'cnpj': empresa.cnpj,
                    'nome': empresa.nome,
                    'ativo': empresa.ativo,
                    'tipo_atividade': empresa.tipo_atividade,
                    'canal_venda': empresa.canal_venda
                }
        
        return self._empresa_configs[empresa_id]
    
    def _validate_user_permissions(self, user_id: str, empresa_id: int) -> Dict[str, bool]:
        """Valida e retorna permissões do usuário para a empresa"""
        with get_central_db() as db:
            user_empresa = db.query(UserEmpresa).filter(
                UserEmpresa.user_id == user_id,
                UserEmpresa.empresa_id == empresa_id
            ).first()
            
            if not user_empresa:
                raise UnauthorizedError(f"Usuário {user_id} não tem acesso à empresa {empresa_id}")
            
            return {
                'read': user_empresa.can_read,
                'write': user_empresa.can_write,
                'approve': user_empresa.can_approve,
                'admin': user_empresa.is_admin
            }
    
    def _log_context_access(self, user_id: str, empresa_id: int, action: str):
        """Registra acesso ao contexto para auditoria"""
        from src.services.auditoria_service import AuditoriaService
        
        AuditoriaService.log_access(
            user_id=user_id,
            empresa_id=empresa_id,
            action=action,
            resource="EMPRESA_CONTEXT",
            timestamp=datetime.utcnow()
        )

# Instância global do context manager
empresa_context_manager = EmpresaContextManager()
