# ============================================================================
# src/vectorstore/embedder.py - Geração de Embeddings
# ============================================================================

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"🔄 Carregando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("✅ Modelo de embeddings carregado.")
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Gera embeddings em lote."""
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        return embeddings   