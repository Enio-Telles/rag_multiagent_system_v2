"""
Gerenciador de Contexto de Empresa Simplificado
Isola dados entre empresas usando context managers
"""

import sqlite3
from typing import Optional, Dict, Any
from contextlib import contextmanager
from threading import local
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmpresaContext:
    """Contexto de uma empresa específica"""
    empresa_id: int
    database_path: str
    user_id: str
    session_id: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}

class EmpresaContextManager:
    """Gerenciador de contexto thread-safe para empresas"""
    
    def __init__(self, central_db_path: str):
        self.central_db_path = central_db_path
        self._thread_local = local()
    
    @property
    def current_context(self) -> Optional[EmpresaContext]:
        """Obtém o contexto atual da thread"""
        return getattr(self._thread_local, 'context', None)
    
    @contextmanager
    def empresa_context(self, empresa_id: int, user_id: str, session_id: str = None):
        """Context manager para isolamento de empresa"""
        
        # Buscar dados da empresa
        empresa_data = self._get_empresa_data(empresa_id)
        if not empresa_data:
            raise ValueError(f"Empresa {empresa_id} não encontrada")
        
        # Buscar permissões do usuário
        permissions = self._get_user_permissions(user_id, empresa_id)
        
        # Criar contexto
        context = EmpresaContext(
            empresa_id=empresa_id,
            database_path=empresa_data['database_path'],
            user_id=user_id,
            session_id=session_id,
            permissions=permissions
        )
        
        # Armazenar contexto na thread
        old_context = getattr(self._thread_local, 'context', None)
        self._thread_local.context = context
        
        try:
            yield context
        finally:
            # Restaurar contexto anterior
            self._thread_local.context = old_context
    
    def _get_empresa_data(self, empresa_id: int) -> Optional[Dict[str, Any]]:
        """Busca dados da empresa no banco central"""
        
        try:
            with sqlite3.connect(self.central_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, nome, database_path, ativa
                    FROM empresas 
                    WHERE id = ? AND ativa = TRUE
                """, (empresa_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            print(f"Erro ao buscar empresa {empresa_id}: {str(e)}")
            return None
    
    def _get_user_permissions(self, user_id: str, empresa_id: int) -> Dict[str, bool]:
        """Busca permissões do usuário para a empresa"""
        
        try:
            with sqlite3.connect(self.central_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT pode_classificar, pode_aprovar, pode_configurar,
                           pode_exportar, pode_auditar
                    FROM usuario_empresa_permissoes uep
                    JOIN usuarios u ON u.id = uep.usuario_id
                    WHERE u.username = ? AND uep.empresa_id = ? AND uep.ativa = TRUE
                """, (user_id, empresa_id))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'pode_classificar': bool(row['pode_classificar']),
                        'pode_aprovar': bool(row['pode_aprovar']),
                        'pode_configurar': bool(row['pode_configurar']),
                        'pode_exportar': bool(row['pode_exportar']),
                        'pode_auditar': bool(row['pode_auditar'])
                    }
                else:
                    return {}
                    
        except Exception as e:
            print(f"Erro ao buscar permissões: {str(e)}")
            return {}

# Instância global
empresa_context_manager = None
