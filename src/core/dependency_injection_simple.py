"""
Container de Injeção de Dependências Simplificado
Gerencia ciclo de vida de serviços com isolamento por empresa
"""

from typing import Dict, Any, Callable, Optional
from threading import Lock
from dataclasses import dataclass
import sqlite3
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

class ServiceContainer:
    """Container de injeção de dependências simplificado"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._scoped_services: Dict[str, Dict[int, Any]] = {}
        self._lock = Lock()
    
    def register_singleton(self, interface: str, factory: Callable[[], Any]):
        """Registra um serviço singleton"""
        with self._lock:
            self._factories[f"{interface}_singleton"] = factory
    
    def register_scoped(self, interface: str, factory: Callable[[EmpresaContext], Any]):
        """Registra um serviço com escopo de empresa"""
        with self._lock:
            self._factories[f"{interface}_scoped"] = factory
            if interface not in self._scoped_services:
                self._scoped_services[interface] = {}
    
    def register_factory(self, interface: str, factory: Callable[[], Any]):
        """Registra uma factory"""
        with self._lock:
            self._factories[f"{interface}_factory"] = factory
    
    def get(self, interface: str, context: EmpresaContext = None) -> Any:
        """Obtém uma instância do serviço"""
        with self._lock:
            # Singleton
            singleton_key = f"{interface}_singleton"
            if singleton_key in self._factories:
                if interface not in self._services:
                    self._services[interface] = self._factories[singleton_key]()
                return self._services[interface]
            
            # Scoped
            scoped_key = f"{interface}_scoped" 
            if scoped_key in self._factories and context:
                if context.empresa_id not in self._scoped_services[interface]:
                    self._scoped_services[interface][context.empresa_id] = self._factories[scoped_key](context)
                return self._scoped_services[interface][context.empresa_id]
            
            # Factory
            factory_key = f"{interface}_factory"
            if factory_key in self._factories:
                return self._factories[factory_key]()
            
            raise ValueError(f"Serviço '{interface}' não registrado")


# Implementações de serviços base
class DatabaseService:
    """Serviço base de banco de dados"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtém conexão com o banco"""
        if not self._connection:
            self._connection = sqlite3.connect(self.database_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """Fecha conexão"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Container global
service_container = ServiceContainer()
