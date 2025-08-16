"""
Sistema de Aprendizagem Contínua - Fase 5
Implementa Golden Set e retreinamento periódico
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    from sqlalchemy.orm import Session
    from database.models import GoldenSetEntry
    from vectorstore.faiss_store import FaissMetadataStore
    from config import Config
    IMPORTS_OK = True
except ImportError as e:
    logging.warning(f"Imports não disponíveis: {e}")
    IMPORTS_OK = False
    
    # Classes dummy para evitar erros
    class SentenceTransformer:
        def __init__(self, *args, **kwargs): pass
        def encode(self, *args, **kwargs): return np.array([])
    
    class Config:
        def __init__(self):
            self.KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")

logger = logging.getLogger(__name__)

class GoldenSetManager:
    """
    Gerencia o Golden Set de classificações validadas
    """
    
    def __init__(self, config: Optional[Config] = None):
        if not IMPORTS_OK:
            raise ImportError("Dependências não disponíveis para GoldenSetManager")
            
        self.config = config or Config()
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.golden_index_path = self.config.KNOWLEDGE_BASE_DIR / "golden_set_index.faiss"
        self.golden_metadata_path = self.config.KNOWLEDGE_BASE_DIR / "golden_metadata.db"
        
    def extrair_golden_set(self, db: Session) -> List[Dict[str, Any]]:
        """
        Extrai classificações validadas do banco de dados
        """
        try:
            golden_entries = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.incluido_em_retreinamento == False
            ).all()
            
            golden_set = []
            for entry in golden_entries:
                golden_set.append({
                    "id": entry.id,
                    "descricao_produto": entry.descricao_produto,
                    "codigo_produto": entry.codigo_produto,
                    "ncm_final": entry.ncm_final,
                    "cest_final": entry.cest_final,
                    "fonte_validacao": entry.fonte_validacao,
                    "confianca_original": entry.confianca_original,
                    "revisado_por": entry.revisado_por,
                    "data_validacao": entry.data_validacao
                })
            
            logger.info(f"Extraídas {len(golden_set)} entradas do Golden Set")
            return golden_set
            
        except Exception as e:
            logger.error(f"Erro ao extrair Golden Set: {e}")
            raise
    
    def criar_indice_golden_set(self, db: Session) -> Dict[str, Any]:
        """
        Cria um índice FAISS separado para o Golden Set
        """
        try:
            # Extrair Golden Set
            golden_set = self.extrair_golden_set(db)
            
            if not golden_set:
                logger.warning("Golden Set vazio, não é possível criar índice")
                return {"status": "vazio", "total_entradas": 0}
            
            # Preparar textos para embeddings
            textos = []
            metadados = []
            
            for entry in golden_set:
                # Criar texto combinado para embedding
                texto = f"{entry['descricao_produto']} NCM:{entry['ncm_final']}"
                if entry['cest_final']:
                    texto += f" CEST:{entry['cest_final']}"
                
                textos.append(texto)
                metadados.append({
                    "id": entry["id"],
                    "produto_id": entry.get("produto_id", ""),
                    "ncm": entry["ncm_final"],
                    "cest": entry["cest_final"],
                    "fonte": entry["fonte_validacao"],
                    "confianca_original": entry["confianca_original"],
                    "validado_por": entry["revisado_por"],
                    "tipo": "golden_set"
                })
            
            # Gerar embeddings
            logger.info("Gerando embeddings para Golden Set...")
            embeddings = self.embedding_model.encode(textos, show_progress_bar=True)
            embeddings = embeddings.astype('float32')
            
            # Normalizar embeddings
            faiss.normalize_L2(embeddings)
            
            # Criar índice FAISS
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(embeddings)
            
            # Salvar índice
            faiss.write_index(index, str(self.golden_index_path))
            
            # Salvar metadados
            golden_store = FaissMetadataStore(dimension)
            golden_store.create_metadata_db(str(self.golden_metadata_path))
            
            for i, metadata in enumerate(metadados):
                golden_store.add_metadata(
                    db_path=str(self.golden_metadata_path),
                    doc_id=f"golden_{metadata['id']}",
                    text=textos[i],
                    metadata=metadata
                )
            
            # Marcar entradas como incluídas no retreinamento
            self._marcar_como_retreinadas(db, golden_set)
            
            logger.info(f"Índice Golden Set criado com {len(golden_set)} entradas")
            
            return {
                "status": "sucesso",
                "total_entradas": len(golden_set),
                "caminho_indice": str(self.golden_index_path),
                "caminho_metadata": str(self.golden_metadata_path),
                "dimensao": dimension
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar índice Golden Set: {e}")
            raise
    
    def _marcar_como_retreinadas(self, db: Session, golden_set: List[Dict[str, Any]]):
        """
        Marca entradas como incluídas no retreinamento
        """
        try:
            for entry in golden_set:
                db_entry = db.query(GoldenSetEntry).filter(
                    GoldenSetEntry.id == entry["id"]
                ).first()
                
                if db_entry:
                    db_entry.incluido_em_retreinamento = True
                    db_entry.data_ultimo_retreinamento = datetime.now()
            
            db.commit()
            logger.info(f"Marcadas {len(golden_set)} entradas como retreinadas")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao marcar entradas como retreinadas: {e}")
            raise
    
    def verificar_indice_existe(self) -> bool:
        """
        Verifica se o índice Golden Set existe
        """
        return self.golden_index_path.exists() and self.golden_metadata_path.exists()

class AugmentedRetrieval:
    """
    Sistema de recuperação aumentada que combina índice principal com Golden Set
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.main_store = FaissMetadataStore(self.config.VECTOR_DIMENSION)
        self.golden_manager = GoldenSetManager(config)
        
        # Carregar índices
        self._carregar_indices()
    
    def _carregar_indices(self):
        """
        Carrega os índices principal e Golden Set
        """
        try:
            # Carregar índice principal
            if self.config.FAISS_INDEX_FILE.exists():
                self.main_store.load_index(str(self.config.FAISS_INDEX_FILE))
                logger.info("Índice principal carregado")
            else:
                logger.warning("Índice principal não encontrado")
                
            # Carregar índice Golden Set
            if self.golden_manager.verificar_indice_existe():
                self.golden_index = faiss.read_index(str(self.golden_manager.golden_index_path))
                self.golden_store = FaissMetadataStore(self.config.VECTOR_DIMENSION)
                logger.info("Índice Golden Set carregado")
            else:
                logger.info("Índice Golden Set não encontrado")
                self.golden_index = None
                self.golden_store = None
                
        except Exception as e:
            logger.error(f"Erro ao carregar índices: {e}")
            self.golden_index = None
            self.golden_store = None
    
    def buscar_contexto_aumentado(self, query: str, k_principal: int = 3, k_golden: int = 2) -> List[Dict[str, Any]]:
        """
        Busca combinando índice principal e Golden Set
        """
        resultados = []
        
        try:
            # Busca no índice principal
            if hasattr(self.main_store, 'index') and self.main_store.index is not None:
                resultados_principais = self.main_store.search(query, k=k_principal)
                for resultado in resultados_principais:
                    resultado["fonte"] = "principal"
                    resultados.append(resultado)
            
            # Busca no Golden Set
            if self.golden_index is not None and self.golden_store is not None:
                resultados_golden = self._buscar_golden_set(query, k=k_golden)
                for resultado in resultados_golden:
                    resultado["fonte"] = "golden_set"
                    resultado["peso"] = 1.5  # Dar peso maior aos exemplos validados
                    resultados.append(resultado)
            
            # Ordenar por score (considerando peso)
            resultados.sort(key=lambda x: x.get("score", 0) * x.get("peso", 1.0), reverse=True)
            
            logger.debug(f"Busca aumentada: {len(resultados)} resultados ({k_principal} principal + {k_golden} golden)")
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro na busca aumentada: {e}")
            # Fallback para busca normal
            if hasattr(self.main_store, 'index'):
                return self.main_store.search(query, k=k_principal + k_golden)
            return []
    
    def _buscar_golden_set(self, query: str, k: int = 2) -> List[Dict[str, Any]]:
        """
        Busca específica no índice Golden Set
        """
        try:
            # Gerar embedding da query
            embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            query_embedding = embedding_model.encode([query]).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Buscar no índice
            scores, indices = self.golden_index.search(query_embedding, k)
            
            resultados = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # Índice inválido
                    continue
                
                # Buscar metadados
                metadata = self.golden_store.get_metadata_by_index(
                    str(self.golden_manager.golden_metadata_path), 
                    idx
                )
                
                if metadata:
                    resultados.append({
                        "text": metadata.get("text", ""),
                        "metadata": metadata.get("metadata", {}),
                        "score": float(score),
                        "indice": int(idx),
                        "tipo": "golden_set"
                    })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro na busca Golden Set: {e}")
            return []

class ContinuousLearningScheduler:
    """
    Agendador para execução periódica do retreinamento
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.golden_manager = GoldenSetManager(config)
    
    def executar_retreinamento(self, db: Session, force: bool = False) -> Dict[str, Any]:
        """
        Executa retreinamento se necessário
        """
        try:
            # Verificar se há novas entradas no Golden Set
            novas_entradas = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.incluido_em_retreinamento == False
            ).count()
            
            if novas_entradas == 0 and not force:
                return {
                    "status": "desnecessario",
                    "message": "Não há novas entradas no Golden Set",
                    "novas_entradas": 0
                }
            
            # Verificar critério mínimo (ex: pelo menos 10 novas entradas)
            MINIMO_ENTRADAS = 10
            if novas_entradas < MINIMO_ENTRADAS and not force:
                return {
                    "status": "insuficiente",
                    "message": f"Apenas {novas_entradas} novas entradas (mínimo: {MINIMO_ENTRADAS})",
                    "novas_entradas": novas_entradas
                }
            
            # Executar retreinamento
            logger.info(f"Iniciando retreinamento com {novas_entradas} novas entradas")
            resultado = self.golden_manager.criar_indice_golden_set(db)
            
            # Registrar execução
            resultado.update({
                "executado_em": datetime.now().isoformat(),
                "novas_entradas": novas_entradas,
                "forcado": force
            })
            
            logger.info("Retreinamento concluído com sucesso")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no retreinamento: {e}")
            raise
