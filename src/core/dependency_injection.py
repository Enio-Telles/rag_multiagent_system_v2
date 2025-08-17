"""
Dependency Injection Container para Multiempresa
Gerencia dependências e conexões de banco por empresa
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional
from abc import ABC, abstractmethod
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class DatabaseConfig:
    """Configuração de conexão de banco"""
    db_type: str  # 'sqlite', 'postgresql'
    connection_string: str
    schema: Optional[str] = None
    pool_size: int = 5

class ServiceContainer:
    """
    Container de injeção de dependência para serviços multiempresa
    Gerencia instâncias de serviços por contexto de empresa
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]):
        """Registra um serviço singleton (uma instância para toda aplicação)"""
        self._singletons[interface.__name__] = implementation()
    
    def register_scoped(self, interface: Type[T], factory: Callable[[EmpresaContext], T]):
        """Registra um serviço com escopo de empresa (uma instância por empresa)"""
        self._factories[interface.__name__] = factory
    
    def get_service(self, interface: Type[T], context: 'EmpresaContext' = None) -> T:
        """Resolve um serviço do container"""
        service_name = interface.__name__
        
        # Singleton services
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Scoped services (por empresa)
        if service_name in self._factories:
            if not context:
                from src.core.empresa_context_manager import empresa_context_manager
                context = empresa_context_manager.current_context
                if not context:
                    raise ValueError(f"Contexto de empresa requerido para serviço {service_name}")
            
            # Cache por empresa
            cache_key = f"{service_name}_{context.empresa_id}"
            if cache_key not in self._services:
                self._services[cache_key] = self._factories[service_name](context)
            
            return self._services[cache_key]
        
        raise ValueError(f"Serviço {service_name} não registrado")

# Container global
container = ServiceContainer()

class DatabaseService(ABC):
    """Interface abstrata para serviços de banco"""
    
    @abstractmethod
    def get_connection(self):
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()):
        pass

class SQLiteEmpresaService(DatabaseService):
    """Implementação SQLite para banco de empresa"""
    
    def __init__(self, context: 'EmpresaContext'):
        self.context = context
        self.db_path = context.db_path
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

class PostgreSQLOrigemService(DatabaseService):
    """Implementação PostgreSQL para banco de origem"""
    
    def __init__(self, context: 'EmpresaContext'):
        self.context = context
        # Configuração vem do contexto da empresa
        self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Constrói string de conexão baseada no contexto"""
        config = self.context.schema_config.get('origem_db', {})
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    @contextmanager
    def get_connection(self):
        import psycopg2
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

# Registro de serviços
def setup_container():
    """Configura o container com os serviços necessários"""
    
    # Serviços com escopo de empresa
    container.register_scoped(
        DatabaseService, 
        lambda ctx: SQLiteEmpresaService(ctx)
    )
    
    # Outros serviços...
    container.register_scoped(
        'ClassificacaoService',
        lambda ctx: ClassificacaoService(container.get_service(DatabaseService, ctx))
    )

# Decorator para injeção automática
def inject_services(*service_types):
    """Decorator para injeção automática de dependências"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Injetar serviços nos kwargs
            for service_type in service_types:
                service_name = service_type.__name__.lower().replace('service', '')
                if service_name not in kwargs:
                    kwargs[service_name] = container.get_service(service_type)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example:
# @inject_services(DatabaseService, ClassificacaoService)
# def classificar_produto(produto_data, database_service, classificacao_service):
#     # Serviços injetados automaticamente no contexto correto
#     return classificacao_service.classificar(produto_data)
