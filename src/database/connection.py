"""
Conexão com banco de dados - PostgreSQL com fallback para SQLite
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from .models import Base

# Configurar logging
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def get_database_url():
    """
    Constrói a URL de conexão do banco baseada nas variáveis de ambiente.
    Fallback para SQLite se PostgreSQL não estiver configurado.
    """
    db_type = os.getenv('DB_TYPE', 'postgresql')
    
    if db_type == 'sqlite':
        # SQLite para desenvolvimento/testes - usar o banco unificado
        db_path = Path(__file__).parent.parent.parent / "data" / "unified_rag_system.db"
        db_path.parent.mkdir(exist_ok=True)
        return f"sqlite:///{db_path}"
    
    # PostgreSQL para produção
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME')
    
    if not all([user, password, database]):
        # Fallback para SQLite se PostgreSQL não estiver configurado
        logger.warning("PostgreSQL não configurado completamente, usando SQLite")
        db_path = Path(__file__).parent.parent.parent / "data" / "unified_rag_system.db"
        db_path.parent.mkdir(exist_ok=True)
        return f"sqlite:///{db_path}"
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

# String de conexão
DATABASE_URL = get_database_url()

# Criar engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=False
    )

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """
    Cria todas as tabelas no banco de dados
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False

def get_db():
    """
    Dependency para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """
    Testa a conexão com o banco de dados
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(f"✅ Conexão com banco estabelecida: {DATABASE_URL}")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Erro na conexão com banco de dados: {e}")
        return False
