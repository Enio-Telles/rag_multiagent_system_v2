"""
Configuração e integração dos serviços principais
Resolve dependências entre componentes do sistema
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.empresa_context_manager_simple import EmpresaContextManager
from src.core.dependency_injection_simple import ServiceContainer, service_container
from src.services.auditoria_service import CentralAuditService, audit_service
from src.database.empresa_schema_manager import EmpresaSchemaManager


class SystemConfiguration:
    """Configuração centralizada do sistema"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.logs_path = self.base_path / "logs"
        self.config_path = self.base_path / "config"
        
        # Garantir que diretórios existem
        for path in [self.data_path, self.logs_path, self.config_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Caminhos específicos
        self.central_db_path = str(self.data_path / "central" / "sistema_central.db")
        self.empresas_db_path = str(self.data_path / "empresas")
        self.audit_db_path = str(self.data_path / "audit" / "central_audit.db")
        self.golden_set_path = str(self.data_path / "golden_set" / "golden_set.db")
        
        # Criar diretórios específicos
        for path in [
            self.data_path / "central",
            self.data_path / "empresas", 
            self.data_path / "audit",
            self.data_path / "golden_set"
        ]:
            path.mkdir(parents=True, exist_ok=True)


class SystemInitializer:
    """Inicialização completa do sistema"""
    
    def __init__(self):
        self.config = SystemConfiguration()
        self.schema_manager = EmpresaSchemaManager()
        
    def initialize_system(self) -> bool:
        """Inicializa todo o sistema com dependências corretas"""
        
        try:
            print("🚀 Iniciando sistema RAG Multi-Agent...")
            
            # 1. Criar banco central
            self._create_central_database()
            
            # 2. Inicializar auditoria
            self._initialize_audit_system()
            
            # 3. Configurar serviços
            self._configure_services()
            
            # 4. Registrar empresas padrão
            self._setup_default_companies()
            
            # 5. Validar sistema
            self._validate_system()
            
            print("✅ Sistema inicializado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {str(e)}")
            return False
    
    def _create_central_database(self):
        """Cria banco de dados central"""
        
        print("📊 Criando banco central...")
        
        # Garantir diretório
        os.makedirs(os.path.dirname(self.config.central_db_path), exist_ok=True)
        
        with sqlite3.connect(self.config.central_db_path) as conn:
            cursor = conn.cursor()
            
            # Configurações de performance
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Tabela de empresas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    razao_social TEXT,
                    cnpj TEXT UNIQUE,
                    database_path TEXT NOT NULL,
                    ativa BOOLEAN DEFAULT TRUE,
                    configuracoes JSON,
                    
                    -- Auditoria
                    criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    criada_por TEXT,
                    
                    -- Estatísticas
                    total_produtos INTEGER DEFAULT 0,
                    total_classificacoes INTEGER DEFAULT 0,
                    ultima_sincronizacao TIMESTAMP
                )
            """)
            
            # Tabela de usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nome_completo TEXT,
                    ativo BOOLEAN DEFAULT TRUE,
                    
                    -- Dados de acesso
                    ultimo_login TIMESTAMP,
                    tentativas_login INTEGER DEFAULT 0,
                    bloqueado_ate TIMESTAMP,
                    
                    -- Auditoria
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    criado_por TEXT
                )
            """)
            
            # Tabela de permissões
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuario_empresa_permissoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    empresa_id INTEGER NOT NULL,
                    papel TEXT NOT NULL, -- admin, analista, readonly
                    
                    -- Permissões específicas
                    pode_classificar BOOLEAN DEFAULT FALSE,
                    pode_aprovar BOOLEAN DEFAULT FALSE,
                    pode_configurar BOOLEAN DEFAULT FALSE,
                    pode_exportar BOOLEAN DEFAULT FALSE,
                    pode_auditar BOOLEAN DEFAULT FALSE,
                    
                    -- Auditoria
                    concedida_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    concedida_por TEXT,
                    ativa BOOLEAN DEFAULT TRUE,
                    
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                    UNIQUE(usuario_id, empresa_id)
                )
            """)
            
            # Tabela de configurações do sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sistema_configuracoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT UNIQUE NOT NULL,
                    valor TEXT NOT NULL,
                    tipo TEXT NOT NULL, -- string, integer, boolean, json
                    descricao TEXT,
                    categoria TEXT,
                    
                    -- Auditoria
                    atualizada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizada_por TEXT
                )
            """)
            
            # Índices
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_empresas_ativa ON empresas(ativa)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(ativo)",
                "CREATE INDEX IF NOT EXISTS idx_permissoes_usuario ON usuario_empresa_permissoes(usuario_id, ativa)",
                "CREATE INDEX IF NOT EXISTS idx_permissoes_empresa ON usuario_empresa_permissoes(empresa_id, ativa)",
                "CREATE INDEX IF NOT EXISTS idx_config_categoria ON sistema_configuracoes(categoria)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            
    def _initialize_audit_system(self):
        """Inicializa sistema de auditoria"""
        
        print("📝 Inicializando sistema de auditoria...")
        
        # O CentralAuditService já cuida da criação das tabelas
        # Apenas testamos a conexão
        test_event = audit_service.log_event(
            audit_service.AuditEvent(
                event_id=None,
                event_type=audit_service.AuditEventType.SYSTEM_ERROR,
                severity=audit_service.AuditSeverity.LOW,
                empresa_id=None,
                user_id="system",
                session_id=None,
                resource_type="system",
                resource_id="initialization",
                action_performed="system_startup",
                ip_address=None,
                user_agent=None,
                api_endpoint=None,
                http_method=None,
                before_data=None,
                after_data={"status": "initializing"},
                metadata={"component": "SystemInitializer"},
                success=True,
                error_message=None,
                duration_ms=None,
                timestamp=datetime.utcnow()
            )
        )
        
        if test_event:
            print("✅ Sistema de auditoria configurado")
        else:
            raise Exception("Falha ao configurar sistema de auditoria")
    
    def _configure_services(self):
        """Configura container de serviços"""
        
        print("⚙️ Configurando serviços...")
        
        # Configurar container global
        from src.core.dependency_injection import service_container
        
        # Registrar serviços principais
        service_container.register_singleton("config", lambda: self.config)
        service_container.register_singleton("schema_manager", lambda: self.schema_manager)
        service_container.register_singleton("audit_service", lambda: audit_service)
        
        # Registrar context manager
        context_manager = EmpresaContextManager(self.config.central_db_path)
        service_container.register_singleton("context_manager", lambda: context_manager)
        
        # Registrar database services (serão criados por empresa)
        service_container.register_factory("database_service", self._create_database_service)
        
        print("✅ Serviços configurados")
    
    def _create_database_service(self):
        """Factory para criar serviços de banco por empresa"""
        
        from src.core.empresa_context_manager import empresa_context_manager
        
        current_context = empresa_context_manager.current_context
        if not current_context:
            raise Exception("Contexto de empresa necessário para database service")
        
        # Criar database service específico da empresa
        return {
            "empresa_id": current_context.empresa_id,
            "database_path": current_context.database_path,
            "schema_manager": self.schema_manager
        }
    
    def _setup_default_companies(self):
        """Configura empresas padrão para demonstração"""
        
        print("🏢 Configurando empresas padrão...")
        
        companies = [
            {
                "nome": "Empresa Demo 1",
                "razao_social": "Empresa Demonstração Um Ltda",
                "cnpj": "11.111.111/0001-11"
            },
            {
                "nome": "Empresa Demo 2", 
                "razao_social": "Empresa Demonstração Dois Ltda",
                "cnpj": "22.222.222/0001-22"
            },
            {
                "nome": "Empresa Demo 3",
                "razao_social": "Empresa Demonstração Três Ltda", 
                "cnpj": "33.333.333/0001-33"
            }
        ]
        
        with sqlite3.connect(self.config.central_db_path) as conn:
            cursor = conn.cursor()
            
            for company in companies:
                # Verificar se empresa já existe
                cursor.execute("SELECT id FROM empresas WHERE nome = ?", (company["nome"],))
                if cursor.fetchone():
                    continue
                
                # Definir caminho do banco da empresa
                empresa_db_path = os.path.join(
                    self.config.empresas_db_path,
                    f"empresa_{company['nome'].lower().replace(' ', '_')}.db"
                )
                
                # Inserir empresa
                cursor.execute("""
                    INSERT INTO empresas (nome, razao_social, cnpj, database_path, criada_por)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    company["nome"],
                    company["razao_social"], 
                    company["cnpj"],
                    empresa_db_path,
                    "system"
                ))
                
                empresa_id = cursor.lastrowid
                
                # Criar banco da empresa
                self.schema_manager.create_empresa_database(empresa_db_path)
                
                print(f"✅ Empresa '{company['nome']}' configurada (ID: {empresa_id})")
            
            conn.commit()
        
        # Criar usuário administrador padrão
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Cria usuário administrador padrão"""
        
        print("👤 Criando usuário administrador...")
        
        import hashlib
        
        # Hash simples para demo (em produção usar bcrypt)
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        with sqlite3.connect(self.config.central_db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar se admin já existe
            cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
            if cursor.fetchone():
                print("✅ Usuário admin já existe")
                return
            
            # Criar usuário admin
            cursor.execute("""
                INSERT INTO usuarios (username, email, password_hash, nome_completo, criado_por)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", "admin@sistema.com", password_hash, "Administrador do Sistema", "system"))
            
            admin_id = cursor.lastrowid
            
            # Dar permissões para todas as empresas
            cursor.execute("SELECT id FROM empresas WHERE ativa = TRUE")
            empresas = cursor.fetchall()
            
            for (empresa_id,) in empresas:
                cursor.execute("""
                    INSERT INTO usuario_empresa_permissoes (
                        usuario_id, empresa_id, papel,
                        pode_classificar, pode_aprovar, pode_configurar,
                        pode_exportar, pode_auditar, concedida_por
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    admin_id, empresa_id, "admin",
                    True, True, True, True, True, "system"
                ))
            
            conn.commit()
            
        print("✅ Usuário administrador criado (admin/admin123)")
    
    def _validate_system(self):
        """Valida se sistema foi inicializado corretamente"""
        
        print("🔍 Validando sistema...")
        
        # Verificar banco central
        if not os.path.exists(self.config.central_db_path):
            raise Exception("Banco central não foi criado")
        
        # Verificar banco de auditoria
        if not os.path.exists(self.config.audit_db_path):
            raise Exception("Banco de auditoria não foi criado")
        
        # Verificar empresas
        with sqlite3.connect(self.config.central_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM empresas WHERE ativa = TRUE")
            empresas_count = cursor.fetchone()[0]
            
            if empresas_count == 0:
                raise Exception("Nenhuma empresa configurada")
            
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = TRUE")
            users_count = cursor.fetchone()[0]
            
            if users_count == 0:
                raise Exception("Nenhum usuário configurado")
        
        print(f"✅ Sistema validado: {empresas_count} empresas, {users_count} usuários")


# Classe utilitária para gerenciamento do sistema
class SystemManager:
    """Gerenciador principal do sistema"""
    
    def __init__(self):
        self.config = SystemConfiguration()
        self.initializer = SystemInitializer()
        
    def start_system(self) -> bool:
        """Inicia o sistema completo"""
        
        return self.initializer.initialize_system()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtém status completo do sistema"""
        
        try:
            status = {
                "sistema_ativo": True,
                "timestamp": datetime.utcnow().isoformat(),
                "componentes": {}
            }
            
            # Verificar banco central
            if os.path.exists(self.config.central_db_path):
                with sqlite3.connect(self.config.central_db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM empresas WHERE ativa = TRUE")
                    empresas_ativas = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = TRUE") 
                    usuarios_ativos = cursor.fetchone()[0]
                    
                    status["componentes"]["banco_central"] = {
                        "status": "OK",
                        "empresas_ativas": empresas_ativas,
                        "usuarios_ativos": usuarios_ativos
                    }
            else:
                status["componentes"]["banco_central"] = {"status": "ERRO", "erro": "Banco não encontrado"}
            
            # Verificar auditoria
            if os.path.exists(self.config.audit_db_path):
                status["componentes"]["auditoria"] = {"status": "OK"}
            else:
                status["componentes"]["auditoria"] = {"status": "ERRO", "erro": "Banco de auditoria não encontrado"}
            
            # Verificar bancos das empresas
            empresas_db_status = []
            
            if os.path.exists(self.config.central_db_path):
                with sqlite3.connect(self.config.central_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, nome, database_path FROM empresas WHERE ativa = TRUE")
                    
                    for empresa_id, nome, db_path in cursor.fetchall():
                        if os.path.exists(db_path):
                            empresas_db_status.append({
                                "empresa_id": empresa_id,
                                "nome": nome, 
                                "status": "OK"
                            })
                        else:
                            empresas_db_status.append({
                                "empresa_id": empresa_id,
                                "nome": nome,
                                "status": "ERRO",
                                "erro": "Banco não encontrado"
                            })
            
            status["componentes"]["bancos_empresas"] = empresas_db_status
            
            return status
            
        except Exception as e:
            return {
                "sistema_ativo": False,
                "erro": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Instância global do gerenciador
system_manager = SystemManager()
