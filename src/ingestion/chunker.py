# ============================================================================
# src/ingestion/chunker.py - Processamento de Chunks
# ============================================================================

import pandas as pd
from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide texto em chunks com metadados."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            chunk = {
                'text': chunk_text,
                'metadata': {
                    **metadata,
                    'chunk_id': len(chunks),
                    'start_pos': start,
                    'end_pos': end
                }
            }
            chunks.append(chunk)
            
            start += self.chunk_size - self.overlap
        
        return chunks
    
    def chunk_produtos(self, produtos_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Converte produtos em chunks para vetorização."""
        chunks = []
        
        for _, produto in produtos_df.iterrows():
            chunk = {
                'text': produto['descricao_produto'],
                'metadata': {
                    'source': 'produtos',
                    'produto_id': produto['produto_id'],
                    'codigo_produto': produto['codigo_produto'],
                    'codigo_barra': produto['codigo_barra'],
                    'ncm': produto['ncm'],
                    'cest': produto['cest'] if pd.notna(produto['cest']) else None
                }
            }
            chunks.append(chunk)
        
        return chunks
