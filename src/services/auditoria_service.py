"""
Sistema de Auditoria Centralizada
Rastreamento completo de todas as ações no sistema multiempresa
"""

import sqlite3
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import threading
import hashlib
import uuid
from contextlib import contextmanager

class AuditEventType(str, Enum):
    """Tipos de eventos de auditoria"""
    # Autenticação
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    
    # Acesso a empresa
    EMPRESA_ACCESS = "EMPRESA_ACCESS"
    EMPRESA_SWITCH = "EMPRESA_SWITCH"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # Operações CRUD
    CREATE_RECORD = "CREATE_RECORD"
    READ_RECORD = "READ_RECORD"
    UPDATE_RECORD = "UPDATE_RECORD"
    DELETE_RECORD = "DELETE_RECORD"
    
    # Classificação
    CLASSIFICATION_START = "CLASSIFICATION_START"
    CLASSIFICATION_COMPLETE = "CLASSIFICATION_COMPLETE"
    CLASSIFICATION_ERROR = "CLASSIFICATION_ERROR"
    AGENT_ACTION = "AGENT_ACTION"
    
    # Aprovação/Revisão
    APPROVAL_SUBMIT = "APPROVAL_SUBMIT"
    APPROVAL_APPROVE = "APPROVAL_APPROVE"
    APPROVAL_REJECT = "APPROVAL_REJECT"
    
    # Sistema
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    BACKUP_CREATE = "BACKUP_CREATE"
    SCHEMA_MIGRATION = "SCHEMA_MIGRATION"

class AuditSeverity(str, Enum):
    """Níveis de severidade"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class AuditEvent:
    """Estrutura de um evento de auditoria"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    empresa_id: Optional[int]
    user_id: Optional[str]
    session_id: Optional[str]
    
    # Dados da operação
    resource_type: Optional[str]  # produto, classificacao, usuario
    resource_id: Optional[str]
    action_performed: str
    
    # Contexto
    ip_address: Optional[str]
    user_agent: Optional[str]
    api_endpoint: Optional[str]
    http_method: Optional[str]
    
    # Dados específicos
    before_data: Optional[Dict[str, Any]]
    after_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    
    # Resultado
    success: bool
    error_message: Optional[str]
    duration_ms: Optional[float]
    
    # Timestamp
    timestamp: datetime
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

class CentralAuditService:
    """Serviço centralizado de auditoria"""
    
    def __init__(self, audit_db_path: str = "data/audit/central_audit.db"):
        self.audit_db_path = audit_db_path
        self._ensure_audit_database()
        self._thread_local = threading.local()
        self._session_context = {}
    
    def _ensure_audit_database(self):
        """Garante que o banco de auditoria existe com schema correto"""
        
        import os
        os.makedirs(os.path.dirname(self.audit_db_path), exist_ok=True)
        
        with sqlite3.connect(self.audit_db_path) as conn:
            cursor = conn.cursor()
            
            # Configurações de performance
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 20000")
            
            # Tabela principal de auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    
                    -- Contexto organizacional
                    empresa_id INTEGER,
                    user_id TEXT,
                    session_id TEXT,
                    
                    -- Recurso afetado
                    resource_type TEXT,
                    resource_id TEXT,
                    action_performed TEXT NOT NULL,
                    
                    -- Contexto técnico
                    ip_address TEXT,
                    user_agent TEXT,
                    api_endpoint TEXT,
                    http_method TEXT,
                    
                    -- Dados da operação
                    before_data JSON,
                    after_data JSON,
                    metadata JSON,
                    
                    -- Resultado
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    duration_ms REAL,
                    
                    -- Hash para integridade
                    data_hash TEXT,
                    
                    -- Timestamp
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de acessos a banco de dados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_acessos_bd (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    database_path TEXT NOT NULL,
                    operation_type TEXT NOT NULL, -- SELECT, INSERT, UPDATE, DELETE
                    table_name TEXT,
                    query_hash TEXT,
                    affected_rows INTEGER,
                    execution_time_ms REAL,
                    success BOOLEAN NOT NULL,
                    error_details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar índices separadamente
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_acessos_empresa ON auditoria_acessos_bd(empresa_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_acessos_user ON auditoria_acessos_bd(user_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_acessos_operation ON auditoria_acessos_bd(operation_type, timestamp)")
            
            # Tabela de sessões de usuário
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_sessoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    empresa_id INTEGER,
                    
                    -- Dados da sessão
                    login_timestamp TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP NOT NULL,
                    logout_timestamp TIMESTAMP,
                    session_duration_seconds INTEGER,
                    
                    -- Contexto técnico
                    ip_address TEXT,
                    user_agent TEXT,
                    device_fingerprint TEXT,
                    
                    -- Estatísticas da sessão
                    actions_performed INTEGER DEFAULT 0,
                    api_calls_made INTEGER DEFAULT 0,
                    errors_encountered INTEGER DEFAULT 0,
                    
                    -- Status
                    status TEXT DEFAULT 'active', -- active, expired, terminated
                    termination_reason TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de métricas de auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_metricas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo_inicio TIMESTAMP NOT NULL,
                    periodo_fim TIMESTAMP NOT NULL,
                    
                    -- Métricas por empresa
                    empresa_id INTEGER,
                    
                    -- Contadores de eventos
                    total_eventos INTEGER DEFAULT 0,
                    eventos_criticos INTEGER DEFAULT 0,
                    eventos_erro INTEGER DEFAULT 0,
                    eventos_sucesso INTEGER DEFAULT 0,
                    
                    -- Métricas de usuário
                    usuarios_unicos INTEGER DEFAULT 0,
                    sessoes_ativas INTEGER DEFAULT 0,
                    logins_sucesso INTEGER DEFAULT 0,
                    logins_falha INTEGER DEFAULT 0,
                    
                    -- Métricas de operação
                    operacoes_crud INTEGER DEFAULT 0,
                    classificacoes_realizadas INTEGER DEFAULT 0,
                    aprovacoes_feitas INTEGER DEFAULT 0,
                    
                    -- Performance
                    tempo_medio_operacao REAL,
                    taxa_erro_geral REAL,
                    
                    -- Dados detalhados
                    detalhes_json JSON,
                    
                    calculado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_eventos_empresa_timestamp ON auditoria_eventos(empresa_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_eventos_user_timestamp ON auditoria_eventos(user_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_eventos_type ON auditoria_eventos(event_type)",
                "CREATE INDEX IF NOT EXISTS idx_eventos_severity ON auditoria_eventos(severity)",
                "CREATE INDEX IF NOT EXISTS idx_eventos_resource ON auditoria_eventos(resource_type, resource_id)",
                "CREATE INDEX IF NOT EXISTS idx_acessos_empresa ON auditoria_acessos_bd(empresa_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sessoes_user ON auditoria_sessoes(user_id, login_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sessoes_status ON auditoria_sessoes(status, last_activity)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
    
    def log_event(self, event: AuditEvent) -> str:
        """Registra um evento de auditoria"""
        
        try:
            # Calcular hash para integridade
            event_data = asdict(event)
            event_data['timestamp'] = event.timestamp.isoformat()
            data_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()
            
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO auditoria_eventos (
                        event_id, event_type, severity, empresa_id, user_id, session_id,
                        resource_type, resource_id, action_performed,
                        ip_address, user_agent, api_endpoint, http_method,
                        before_data, after_data, metadata,
                        success, error_message, duration_ms, data_hash, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type.value, event.severity.value,
                    event.empresa_id, event.user_id, event.session_id,
                    event.resource_type, event.resource_id, event.action_performed,
                    event.ip_address, event.user_agent, event.api_endpoint, event.http_method,
                    json.dumps(event.before_data) if event.before_data else None,
                    json.dumps(event.after_data) if event.after_data else None,
                    json.dumps(event.metadata) if event.metadata else None,
                    event.success, event.error_message, event.duration_ms,
                    data_hash, event.timestamp
                ))
                
                conn.commit()
                
            return event.event_id
            
        except Exception as e:
            # Log crítico - falha na auditoria
            print(f"CRITICAL: Falha ao registrar evento de auditoria: {str(e)}")
            return None
    
    def log_database_access(self, empresa_id: int, user_id: str, database_path: str,
                          operation_type: str, table_name: str = None,
                          query_hash: str = None, affected_rows: int = 0,
                          execution_time_ms: float = 0, success: bool = True,
                          error_details: str = None):
        """Registra acesso a banco de dados"""
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO auditoria_acessos_bd (
                        empresa_id, user_id, database_path, operation_type,
                        table_name, query_hash, affected_rows, execution_time_ms,
                        success, error_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    empresa_id, user_id, database_path, operation_type,
                    table_name, query_hash, affected_rows, execution_time_ms,
                    success, error_details
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"CRITICAL: Falha ao registrar acesso BD: {str(e)}")
    
    def start_session(self, user_id: str, empresa_id: int = None,
                     ip_address: str = None, user_agent: str = None) -> str:
        """Inicia uma nova sessão de usuário"""
        
        session_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO auditoria_sessoes (
                        session_id, user_id, empresa_id, login_timestamp,
                        last_activity, ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, user_id, empresa_id, datetime.utcnow(),
                    datetime.utcnow(), ip_address, user_agent
                ))
                
                conn.commit()
                
            # Log evento de login
            self.log_event(AuditEvent(
                event_id=None,
                event_type=AuditEventType.LOGIN_SUCCESS,
                severity=AuditSeverity.LOW,
                empresa_id=empresa_id,
                user_id=user_id,
                session_id=session_id,
                resource_type="session",
                resource_id=session_id,
                action_performed="login",
                ip_address=ip_address,
                user_agent=user_agent,
                api_endpoint="/api/auth/login",
                http_method="POST",
                before_data=None,
                after_data={"session_id": session_id},
                metadata=None,
                success=True,
                error_message=None,
                duration_ms=None,
                timestamp=datetime.utcnow()
            ))
            
            return session_id
            
        except Exception as e:
            print(f"CRITICAL: Falha ao iniciar sessão: {str(e)}")
            return None
    
    def end_session(self, session_id: str, termination_reason: str = "logout"):
        """Finaliza uma sessão de usuário"""
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar dados da sessão
                cursor.execute("""
                    SELECT user_id, empresa_id, login_timestamp 
                    FROM auditoria_sessoes 
                    WHERE session_id = ? AND status = 'active'
                """, (session_id,))
                
                session_data = cursor.fetchone()
                if not session_data:
                    return
                
                user_id, empresa_id, login_timestamp = session_data
                
                # Calcular duração
                login_time = datetime.fromisoformat(login_timestamp.replace('Z', '+00:00'))
                duration = (datetime.utcnow() - login_time).total_seconds()
                
                # Atualizar sessão
                cursor.execute("""
                    UPDATE auditoria_sessoes 
                    SET logout_timestamp = ?, session_duration_seconds = ?,
                        status = 'terminated', termination_reason = ?
                    WHERE session_id = ?
                """, (datetime.utcnow(), duration, termination_reason, session_id))
                
                conn.commit()
                
            # Log evento de logout
            self.log_event(AuditEvent(
                event_id=None,
                event_type=AuditEventType.LOGOUT,
                severity=AuditSeverity.LOW,
                empresa_id=empresa_id,
                user_id=user_id,
                session_id=session_id,
                resource_type="session",
                resource_id=session_id,
                action_performed="logout",
                ip_address=None,
                user_agent=None,
                api_endpoint="/api/auth/logout",
                http_method="POST",
                before_data=None,
                after_data={"duration_seconds": duration},
                metadata={"termination_reason": termination_reason},
                success=True,
                error_message=None,
                duration_ms=None,
                timestamp=datetime.utcnow()
            ))
            
        except Exception as e:
            print(f"CRITICAL: Falha ao finalizar sessão: {str(e)}")
    
    def get_audit_logs(self, empresa_id: int = None, user_id: str = None,
                      start_date: datetime = None, end_date: datetime = None,
                      event_types: List[AuditEventType] = None,
                      severity: AuditSeverity = None,
                      limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Busca logs de auditoria com filtros"""
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Construir query com filtros
                where_conditions = []
                params = []
                
                if empresa_id:
                    where_conditions.append("empresa_id = ?")
                    params.append(empresa_id)
                
                if user_id:
                    where_conditions.append("user_id = ?")
                    params.append(user_id)
                
                if start_date:
                    where_conditions.append("timestamp >= ?")
                    params.append(start_date)
                
                if end_date:
                    where_conditions.append("timestamp <= ?")
                    params.append(end_date)
                
                if event_types:
                    placeholders = ",".join(["?" for _ in event_types])
                    where_conditions.append(f"event_type IN ({placeholders})")
                    params.extend([et.value for et in event_types])
                
                if severity:
                    where_conditions.append("severity = ?")
                    params.append(severity.value)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                query = f"""
                    SELECT * FROM auditoria_eventos 
                    {where_clause}
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """
                
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                logs = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for log in logs:
                    for field in ['before_data', 'after_data', 'metadata']:
                        if log[field]:
                            try:
                                log[field] = json.loads(log[field])
                            except:
                                pass
                
                return logs
                
        except Exception as e:
            print(f"Erro ao buscar logs de auditoria: {str(e)}")
            return []
    
    def generate_audit_report(self, empresa_id: int, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Gera relatório de auditoria para período"""
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                # Estatísticas gerais
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT session_id) as total_sessions,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_operations,
                        AVG(duration_ms) as avg_duration_ms
                    FROM auditoria_eventos 
                    WHERE empresa_id = ? AND timestamp BETWEEN ? AND ?
                """, (empresa_id, start_date, end_date))
                
                stats = cursor.fetchone()
                
                # Eventos por tipo
                cursor.execute("""
                    SELECT event_type, COUNT(*) as count 
                    FROM auditoria_eventos 
                    WHERE empresa_id = ? AND timestamp BETWEEN ? AND ?
                    GROUP BY event_type 
                    ORDER BY count DESC
                """, (empresa_id, start_date, end_date))
                
                events_by_type = dict(cursor.fetchall())
                
                # Usuários mais ativos
                cursor.execute("""
                    SELECT user_id, COUNT(*) as actions 
                    FROM auditoria_eventos 
                    WHERE empresa_id = ? AND timestamp BETWEEN ? AND ?
                    GROUP BY user_id 
                    ORDER BY actions DESC 
                    LIMIT 10
                """, (empresa_id, start_date, end_date))
                
                top_users = dict(cursor.fetchall())
                
                # Erros mais comuns
                cursor.execute("""
                    SELECT error_message, COUNT(*) as count 
                    FROM auditoria_eventos 
                    WHERE empresa_id = ? AND timestamp BETWEEN ? AND ? AND success = 0
                    GROUP BY error_message 
                    ORDER BY count DESC 
                    LIMIT 10
                """, (empresa_id, start_date, end_date))
                
                common_errors = dict(cursor.fetchall())
                
                return {
                    "periodo": {
                        "inicio": start_date.isoformat(),
                        "fim": end_date.isoformat()
                    },
                    "estatisticas_gerais": {
                        "total_eventos": stats[0],
                        "usuarios_unicos": stats[1],
                        "sessoes_totais": stats[2],
                        "operacoes_sucesso": stats[3],
                        "operacoes_falha": stats[4],
                        "tempo_medio_ms": stats[5],
                        "taxa_sucesso": (stats[3] / stats[0] * 100) if stats[0] > 0 else 0
                    },
                    "eventos_por_tipo": events_by_type,
                    "usuarios_mais_ativos": top_users,
                    "erros_mais_comuns": common_errors,
                    "gerado_em": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            print(f"Erro ao gerar relatório de auditoria: {str(e)}")
            return {}

# Instância global do serviço de auditoria
audit_service = CentralAuditService()

# Decorators para auditoria automática
def audit_action(event_type: AuditEventType, severity: AuditSeverity = AuditSeverity.LOW,
                resource_type: str = None):
    """Decorator para auditoria automática de funções"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            # Extrair contexto da requisição atual
            from src.core.empresa_context_manager import empresa_context_manager
            context = empresa_context_manager.current_context
            
            event = AuditEvent(
                event_id=None,
                event_type=event_type,
                severity=severity,
                empresa_id=context.empresa_id if context else None,
                user_id=getattr(context, 'user_id', None) if context else None,
                session_id=getattr(context, 'session_id', None) if context else None,
                resource_type=resource_type,
                resource_id=None,
                action_performed=func.__name__,
                ip_address=None,
                user_agent=None,
                api_endpoint=None,
                http_method=None,
                before_data=None,
                after_data=None,
                metadata={"function": func.__name__, "args_count": len(args), "kwargs_count": len(kwargs)},
                success=True,
                error_message=None,
                duration_ms=None,
                timestamp=start_time
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Calcular duração
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                event.duration_ms = duration
                event.success = True
                
                audit_service.log_event(event)
                
                return result
                
            except Exception as e:
                # Calcular duração mesmo em caso de erro
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                event.duration_ms = duration
                event.success = False
                event.error_message = str(e)
                event.severity = AuditSeverity.HIGH
                
                audit_service.log_event(event)
                
                raise e
        
        return wrapper
    return decorator

# Context manager para auditoria de operações
@contextmanager
def audit_operation(event_type: AuditEventType, resource_type: str, resource_id: str,
                   severity: AuditSeverity = AuditSeverity.LOW):
    """Context manager para auditoria de operações complexas"""
    
    start_time = datetime.utcnow()
    
    from src.core.empresa_context_manager import empresa_context_manager
    context = empresa_context_manager.current_context
    
    event = AuditEvent(
        event_id=None,
        event_type=event_type,
        severity=severity,
        empresa_id=context.empresa_id if context else None,
        user_id=getattr(context, 'user_id', None) if context else None,
        session_id=getattr(context, 'session_id', None) if context else None,
        resource_type=resource_type,
        resource_id=resource_id,
        action_performed=event_type.value,
        ip_address=None,
        user_agent=None,
        api_endpoint=None,
        http_method=None,
        before_data=None,
        after_data=None,
        metadata=None,
        success=True,
        error_message=None,
        duration_ms=None,
        timestamp=start_time
    )
    
    try:
        yield event
        
        # Operação bem-sucedida
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        event.duration_ms = duration
        event.success = True
        
        audit_service.log_event(event)
        
    except Exception as e:
        # Operação falhada
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        event.duration_ms = duration
        event.success = False
        event.error_message = str(e)
        event.severity = AuditSeverity.HIGH
        
        audit_service.log_event(event)
        
        raise e
