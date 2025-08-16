# ============================================================================
# src/vectorstore/faiss_store.py - Armazenamento Vetorial
# ============================================================================

import faiss
import sqlite3
import numpy as np
import json
from typing import List, Dict, Any, Optional
from .embedder import Embedder

class FaissMetadataStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Índice de produto interno
        self.metadata_db = None
        self.embedder = Embedder()
        
    def initialize_metadata_db(self, db_path: str):
        """Inicializa banco de metadados SQLite."""
        self.metadata_db = sqlite3.connect(db_path, check_same_thread=False)
        
        # Criar tabela de metadados
        self.metadata_db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id INTEGER,
                text TEXT,
                metadata TEXT
            )
        """)
        self.metadata_db.commit()
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Adiciona documentos ao índice vetorial."""
        print(f"🔄 Vetorizando {len(chunks)} chunks...")
        
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)
        
        # Normalizar embeddings para uso com IndexFlatIP
        faiss.normalize_L2(embeddings)
        
        # Adicionar ao índice FAISS
        start_id = self.index.ntotal
        self.index.add(embeddings)
        
        # Salvar metadados
        for i, chunk in enumerate(chunks):
            vector_id = start_id + i
            self.metadata_db.execute(
                "INSERT INTO chunks (vector_id, text, metadata) VALUES (?, ?, ?)",
                (vector_id, chunk['text'], json.dumps(chunk['metadata']))
            )
        
        self.metadata_db.commit()
        print(f"✅ {len(chunks)} chunks adicionados ao índice.")
    
    def search(self, query: str, k: int = 5, metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """Busca semântica com filtro opcional de metadados."""
        # Gerar embedding da query
        query_embedding = self.embedder.embed_batch([query])
        faiss.normalize_L2(query_embedding)
        
        # Buscar no FAISS
        scores, indices = self.index.search(query_embedding, k * 10)  # Buscar mais para filtrar
        
        results = []
        cursor = self.metadata_db.cursor()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Índice inválido
                continue
                
            cursor.execute("SELECT text, metadata FROM chunks WHERE vector_id = ?", (int(idx),))
            row = cursor.fetchone()
            
            if row:
                text, metadata_json = row
                metadata = json.loads(metadata_json)
                
                # Aplicar filtro de metadados se especificado
                if metadata_filter:
                    match = all(metadata.get(k) == v for k, v in metadata_filter.items())
                    if not match:
                        continue
                
                results.append({
                    'text': text,
                    'metadata': metadata,
                    'score': float(score)
                })
                
                if len(results) >= k:
                    break
        
        return results
    
    def save_index(self, index_path: str):
        """Salva o índice FAISS."""
        faiss.write_index(self.index, index_path)
        print(f"✅ Índice salvo em: {index_path}")
    
    def load_index(self, index_path: str, metadata_db_path: str = None):
        """Carrega o índice FAISS e conecta à base de metadados."""
        self.index = faiss.read_index(index_path)
        print(f"✅ Índice carregado de: {index_path}")
        
        # Conectar à base de metadados
        if metadata_db_path:
            self._connect_metadata_db(metadata_db_path)
        else:
            # Inferir caminho da base de metadados baseado no índice
            db_path = index_path.replace('faiss_index.faiss', 'metadata.db')
            self._connect_metadata_db(db_path)
    
    def _connect_metadata_db(self, db_path: str):
        """Conecta à base de metadados existente."""
        self.metadata_db = sqlite3.connect(db_path)
        print(f"✅ Base de metadados conectada: {db_path}")
    
    def get_stats(self):
        """Retorna estatísticas do índice."""
        if self.index is None:
            return {"total_vectors": 0, "dimension": self.dimension}
        
        stats = {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__
        }
        
        if self.metadata_db:
            cursor = self.metadata_db.cursor()
            cursor.execute("SELECT COUNT(*) FROM metadata")
            metadata_count = cursor.fetchone()[0]
            stats["metadata_records"] = metadata_count
        
        return stats