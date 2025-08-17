#!/usr/bin/env python3
"""
Serviço Unificado para busca e classificação com ABC Farma
Inclui busca por similaridade usando embeddings
Autor: Sistema IA RAG v2
"""

import os
import sys
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.unified_sqlite_models import (
    UnifiedBase, ABCFarmaProduct, ProdutoExemplo, 
    NCMHierarchy, CestCategory, ClassificacaoRevisao
)
from sqlalchemy import create_engine, text, func, and_, or_
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class UnifiedRAGService:
    """Serviço unificado para busca RAG com ABC Farma"""
    
    def __init__(self, db_path: str = "unified_rag_system.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Modelo de embeddings (carregado sob demanda)
        self._embedding_model = None
        
    @property
    def embedding_model(self):
        """Carregamento lazy do modelo de embeddings"""
        if self._embedding_model is None:
            logger.info("Carregando modelo de embeddings...")
            self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Modelo de embeddings carregado!")
        return self._embedding_model
        
    def generate_embedding(self, text: str) -> np.ndarray:
        """Gerar embedding para um texto"""
        if not text or text.strip() == "":
            text = "produto"
        return self.embedding_model.encode(str(text)[:1000])
        
    def search_abc_farma_by_similarity(
        self, 
        query: str, 
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Buscar produtos ABC Farma por similaridade semântica
        
        Args:
            query: Texto da consulta
            limit: Limite de resultados
            similarity_threshold: Limite mínimo de similaridade
            
        Returns:
            Lista de produtos com scores de similaridade
        """
        session = self.Session()
        
        try:
            logger.info(f"Buscando produtos ABC Farma similares a: '{query}'")
            
            # Gerar embedding da consulta
            query_embedding = self.generate_embedding(query)
            
            # Buscar produtos ativos
            products = session.query(ABCFarmaProduct).filter(
                ABCFarmaProduct.ativo == True
            ).limit(1000).all()  # Limitar busca inicial
            
            if not products:
                logger.warning("Nenhum produto ABC Farma encontrado")
                return []
                
            similarities = []
            
            for product in products:
                if product.embedding_descricao:
                    try:
                        # Deserializar embedding do produto
                        product_embedding = pickle.loads(product.embedding_descricao)
                        
                        # Calcular similaridade cosseno
                        similarity = np.dot(query_embedding, product_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
                        )
                        
                        # Filtrar por threshold
                        if similarity >= similarity_threshold:
                            similarities.append({
                                'product': product,
                                'similarity': float(similarity),
                                'codigo_barra': product.codigo_barra,
                                'descricao': product.descricao_completa,
                                'marca': product.marca,
                                'principio_ativo': product.principio_ativo,
                                'categoria': product.categoria,
                                'ncm': product.ncm_farmaceutico,
                                'cest': product.cest_farmaceutico
                            })
                            
                    except Exception as e:
                        logger.debug(f"Erro ao processar embedding do produto {product.id}: {e}")
                        continue
                        
            # Ordenar por similaridade
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Atualizar contador de consultas
            for item in similarities[:limit]:
                try:
                    product = item['product']
                    product.vezes_consultado = (product.vezes_consultado or 0) + 1
                    product.ultima_consulta = datetime.now()
                except:
                    pass
                    
            session.commit()
            
            logger.info(f"Encontrados {len(similarities)} produtos similares")
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            return []
        finally:
            session.close()
            
    def search_abc_farma_by_text(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Buscar produtos ABC Farma por texto (busca tradicional)
        """
        session = self.Session()
        
        try:
            query_lower = query.lower()
            
            # Busca por texto em múltiplos campos
            products = session.query(ABCFarmaProduct).filter(
                and_(
                    ABCFarmaProduct.ativo == True,
                    or_(
                        ABCFarmaProduct.descricao_completa.contains(query),
                        ABCFarmaProduct.descricao1.contains(query),
                        ABCFarmaProduct.marca.contains(query),
                        ABCFarmaProduct.principio_ativo.contains(query),
                        ABCFarmaProduct.categoria.contains(query),
                        ABCFarmaProduct.codigo_barra.contains(query)
                    )
                )
            ).limit(limit).all()
            
            results = []
            for product in products:
                results.append({
                    'product': product,
                    'similarity': 1.0,  # Busca exata
                    'codigo_barra': product.codigo_barra,
                    'descricao': product.descricao_completa,
                    'marca': product.marca,
                    'principio_ativo': product.principio_ativo,
                    'categoria': product.categoria,
                    'ncm': product.ncm_farmaceutico,
                    'cest': product.cest_farmaceutico
                })
                
                # Atualizar contador
                product.vezes_consultado = (product.vezes_consultado or 0) + 1
                product.ultima_consulta = datetime.now()
                
            session.commit()
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca por texto: {e}")
            return []
        finally:
            session.close()
            
    def search_abc_farma_hybrid(
        self, 
        query: str, 
        limit: int = 10,
        use_similarity: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca híbrida: combina busca por texto e similaridade
        """
        
        # Busca por texto primeiro
        text_results = self.search_abc_farma_by_text(query, limit)
        
        if not use_similarity or len(text_results) >= limit:
            return text_results
            
        # Complementar com busca por similaridade
        similarity_results = self.search_abc_farma_by_similarity(
            query, 
            limit - len(text_results),
            similarity_threshold=0.4
        )
        
        # Remover duplicatas
        existing_codes = {r['codigo_barra'] for r in text_results}
        filtered_similarity = [
            r for r in similarity_results 
            if r['codigo_barra'] not in existing_codes
        ]
        
        # Combinar resultados
        combined_results = text_results + filtered_similarity
        return combined_results[:limit]
        
    def get_pharmaceutical_classification(
        self, 
        produto_descricao: str,
        codigo_barra: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obter classificação farmacêutica baseada em ABC Farma
        """
        session = self.Session()
        
        try:
            # Buscar produto similar
            similar_products = self.search_abc_farma_hybrid(
                produto_descricao, 
                limit=3,
                use_similarity=True
            )
            
            if not similar_products:
                # Classificação padrão para produtos farmacêuticos
                return {
                    'ncm_sugerido': '30049099',
                    'cest_sugerido': '13.001.00',
                    'confiabilidade': 0.5,
                    'fonte': 'PADRAO_FARMACEUTICO',
                    'produtos_referencia': []
                }
                
            # Pegar o produto mais similar
            best_match = similar_products[0]
            
            # Buscar outros produtos com mesmo NCM/CEST
            similar_ncm_products = session.query(ABCFarmaProduct).filter(
                and_(
                    ABCFarmaProduct.ncm_farmaceutico == best_match['ncm'],
                    ABCFarmaProduct.ativo == True
                )
            ).limit(5).all()
            
            return {
                'ncm_sugerido': best_match['ncm'],
                'cest_sugerido': best_match['cest'],
                'confiabilidade': best_match['similarity'],
                'fonte': 'ABC_FARMA',
                'produto_referencia': {
                    'codigo_barra': best_match['codigo_barra'],
                    'descricao': best_match['descricao'],
                    'marca': best_match['marca'],
                    'principio_ativo': best_match['principio_ativo']
                },
                'produtos_similares': [
                    {
                        'codigo_barra': p.codigo_barra,
                        'descricao': p.descricao_completa,
                        'marca': p.marca
                    } for p in similar_ncm_products
                ],
                'total_produtos_referencia': len(similar_ncm_products)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter classificação farmacêutica: {e}")
            return {
                'ncm_sugerido': '30049099',
                'cest_sugerido': '13.001.00',
                'confiabilidade': 0.1,
                'fonte': 'ERRO',
                'erro': str(e)
            }
        finally:
            session.close()
            
    def is_pharmaceutical_product(self, descricao: str) -> bool:
        """
        Verificar se um produto é farmacêutico usando ABC Farma
        """
        pharmaceutical_keywords = [
            'medicamento', 'remedio', 'farmaco', 'droga', 'comprimido',
            'capsula', 'xarope', 'pomada', 'creme', 'gel', 'suspensao',
            'injecao', 'ampola', 'vitamina', 'suplemento', 'antibiotico',
            'analgesico', 'anti-inflamatorio', 'descongestionante'
        ]
        
        descricao_lower = descricao.lower()
        
        # Verificação por palavras-chave
        for keyword in pharmaceutical_keywords:
            if keyword in descricao_lower:
                return True
                
        # Verificação por similaridade com ABC Farma
        similar_products = self.search_abc_farma_by_similarity(
            descricao, 
            limit=1,
            similarity_threshold=0.6
        )
        
        return len(similar_products) > 0
        
    def get_abc_farma_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas da base ABC Farma"""
        session = self.Session()
        
        try:
            stats = {}
            
            # Contadores básicos
            stats['total_products'] = session.query(ABCFarmaProduct).count()
            stats['active_products'] = session.query(ABCFarmaProduct).filter(
                ABCFarmaProduct.ativo == True
            ).count()
            
            # Top marcas
            top_brands = session.query(
                ABCFarmaProduct.marca,
                func.count(ABCFarmaProduct.id).label('count')
            ).filter(
                ABCFarmaProduct.ativo == True
            ).group_by(
                ABCFarmaProduct.marca
            ).order_by(
                func.count(ABCFarmaProduct.id).desc()
            ).limit(10).all()
            
            stats['top_brands'] = [
                {'marca': brand, 'count': count} 
                for brand, count in top_brands if brand
            ]
            
            # Top categorias
            top_categories = session.query(
                ABCFarmaProduct.categoria,
                func.count(ABCFarmaProduct.id).label('count')
            ).filter(
                ABCFarmaProduct.ativo == True
            ).group_by(
                ABCFarmaProduct.categoria
            ).order_by(
                func.count(ABCFarmaProduct.id).desc()
            ).limit(10).all()
            
            stats['top_categories'] = [
                {'categoria': cat, 'count': count} 
                for cat, count in top_categories if cat
            ]
            
            # Produtos mais consultados
            most_consulted = session.query(ABCFarmaProduct).filter(
                and_(
                    ABCFarmaProduct.ativo == True,
                    ABCFarmaProduct.vezes_consultado > 0
                )
            ).order_by(
                ABCFarmaProduct.vezes_consultado.desc()
            ).limit(5).all()
            
            stats['most_consulted'] = [
                {
                    'codigo_barra': p.codigo_barra,
                    'descricao': p.descricao_completa[:100],
                    'marca': p.marca,
                    'consultas': p.vezes_consultado
                } for p in most_consulted
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas ABC Farma: {e}")
            return {'error': str(e)}
        finally:
            session.close()

# Instância global do serviço
_unified_service_instance = None

def get_unified_service() -> UnifiedRAGService:
    """Obter instância singleton do serviço unificado"""
    global _unified_service_instance
    if _unified_service_instance is None:
        _unified_service_instance = UnifiedRAGService()
    return _unified_service_instance
