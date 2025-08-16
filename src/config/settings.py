"""
Configurações modernas da aplicação usando Pydantic
Separação clara entre configurações secretas e não-secretas
"""
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Dict, Any
import os

class DatabaseSettings(BaseModel):
    """Configurações específicas do banco de dados"""
    connection_pool_size: int = 10
    connection_timeout: int = 30
    query_timeout: int = 60
    retry_attempts: int = 3

class LLMSettings(BaseModel):
    """Configurações dos modelos de linguagem"""
    default_model: str = "llama3.1:8b"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 120
    retry_attempts: int = 3
    
    # Modelos específicos por agente
    expansion_model: str = "llama3.1:8b"
    ncm_model: str = "llama3.1:8b"
    cest_model: str = "llama3.1:8b"
    reconciler_model: str = "llama3.1:8b"

class VectorStoreSettings(BaseModel):
    """Configurações do armazenamento vetorial"""
    dimension: int = 384
    index_type: str = "IndexFlatIP"
    similarity_threshold: float = 0.7
    max_results: int = 50
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

class ClassificationSettings(BaseModel):
    """Configurações específicas da classificação"""
    min_confidence_threshold: float = 0.6
    enable_cest_validation: bool = True
    enable_ncm_hierarchy_validation: bool = True
    max_alternative_suggestions: int = 3
    group_similarity_threshold: float = 0.78
    enable_intelligent_grouping: bool = True
    
    # Configurações de validação rigorosa
    enforce_cest_format: bool = True
    enforce_cest_ncm_binding: bool = True
    reject_invalid_bindings: bool = True

class QualitySettings(BaseModel):
    """Configurações de qualidade e auditoria"""
    enable_comprehensive_audit: bool = True
    save_detailed_traces: bool = True
    min_group_size_for_analysis: int = 5
    confidence_distribution_analysis: bool = True
    enable_drift_detection: bool = True
    log_validation_errors: bool = True

class PerformanceSettings(BaseModel):
    """Configurações de performance"""
    batch_size: int = 50
    parallel_processing: bool = False
    max_workers: int = 4
    cache_embeddings: bool = True
    cache_ttl_hours: int = 24

class PathSettings(BaseModel):
    """Configurações de caminhos e arquivos"""
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    knowledge_base_dir: Path = data_dir / "knowledge_base"
    reference_data_dir: Path = data_dir / "reference"
    logs_dir: Path = project_root / "logs"
    
    # Arquivos específicos
    ncm_mapping_file: str = "ncm_mapping.json"
    cest_catalog_file: str = "cest_catalog.json"
    faiss_index_file: str = "faiss_index.faiss"
    metadata_db_file: str = "metadata.db"

class SecretSettings(BaseSettings):
    """Configurações secretas carregadas do .env"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "fiscaldb"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SCHEMA: str = "dbo"
    
    # LLM APIs
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    # Security
    SECRET_KEY: str = "dev-secret-key"
    JWT_SECRET: str = "dev-jwt-secret"
    
    # Monitoring
    SENTRY_DSN: str | None = None
    LOG_LEVEL: str = "INFO"

class ApplicationConfig:
    """Configuração principal da aplicação"""
    
    def __init__(self):
        self.secrets = SecretSettings()
        self.database = DatabaseSettings()
        self.llm = LLMSettings()
        self.vectorstore = VectorStoreSettings()
        self.classification = ClassificationSettings()
        self.quality = QualitySettings()
        self.performance = PerformanceSettings()
        self.paths = PathSettings()
        
        # Garantir que diretórios existem
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Cria diretórios necessários se não existirem"""
        directories = [
            self.paths.data_dir,
            self.paths.raw_data_dir,
            self.paths.processed_data_dir,
            self.paths.knowledge_base_dir,
            self.paths.reference_data_dir,
            self.paths.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Constrói URL de conexão do banco"""
        return (f"postgresql://{self.secrets.DB_USER}:{self.secrets.DB_PASSWORD}"
                f"@{self.secrets.DB_HOST}:{self.secrets.DB_PORT}/{self.secrets.DB_NAME}")
    
    def get_llm_config(self, agent_name: str = None) -> Dict[str, Any]:
        """Retorna configuração específica do LLM para um agente"""
        base_config = {
            "base_url": self.secrets.OLLAMA_BASE_URL,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "timeout": self.llm.timeout,
            "retry_attempts": self.llm.retry_attempts
        }
        
        # Modelo específico por agente
        model_mapping = {
            "expansion": self.llm.expansion_model,
            "ncm": self.llm.ncm_model,
            "cest": self.llm.cest_model,
            "reconciler": self.llm.reconciler_model
        }
        
        base_config["model"] = model_mapping.get(agent_name, self.llm.default_model)
        return base_config

# Instância global da configuração
config = ApplicationConfig()
