# src/config.py - Configurações Centralizadas
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
    FEEDBACK_DIR = DATA_DIR / "feedback"
    
    # Database
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'schema': os.getenv('DB_SCHEMA', 'dbo')
    }
    
    # Ollama
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    
    # Vector Store
    VECTOR_DIMENSION = int(os.getenv('VECTOR_DIMENSION', '384'))
    FAISS_INDEX_TYPE = os.getenv('FAISS_INDEX_TYPE', 'IndexFlatIP')
    
    # Knowledge Base Settings
    MAX_GTIN_EXAMPLES = int(os.getenv('MAX_GTIN_EXAMPLES', '100'))
    
    # Knowledge Base Files
    NCM_MAPPING_FILE = KNOWLEDGE_BASE_DIR / "ncm_mapping.json"
    FAISS_INDEX_FILE = KNOWLEDGE_BASE_DIR / "faiss_index.faiss"
    METADATA_DB_FILE = KNOWLEDGE_BASE_DIR / "metadata.db"