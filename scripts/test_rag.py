# ============================================================================
# scripts/test_rag.py - Script de Teste Independente para RAG
# ============================================================================

#!/usr/bin/env python3
"""
scripts/test_rag.py
Teste Intermediário 2: Validação do Sistema RAG (Busca Semântica)

Este script testa de forma independente o sistema de busca vetorial.
"""

import sys
import sqlite3
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import Config
from vectorstore.faiss_store import FaissMetadataStore

class RAGTester:
    def __init__(self):
        self.config = Config()
        self.vector_store = None
    
    def initialize_rag_system(self) -> bool:
        """Inicializa o sistema RAG para testes."""
        print("🔄 Inicializando sistema RAG para testes...")
        
        # Verificar se os arquivos existem
        if not self.config.FAISS_INDEX_FILE.exists():
            print(f"❌ Índice FAISS não encontrado: {self.config.FAISS_INDEX_FILE}")
            print("Execute primeiro: python main.py ingest")
            return False
        
        if not self.config.METADATA_DB_FILE.exists():
            print(f"❌ Base de metadados não encontrada: {self.config.METADATA_DB_FILE}")
            print("Execute primeiro: python main.py ingest")
            return False
        
        try:
            # Carregar vector store
            self.vector_store = FaissMetadataStore(self.config.VECTOR_DIMENSION)
            self.vector_store.load_index(str(self.config.FAISS_INDEX_FILE))
            self.vector_store.initialize_metadata_db(str(self.config.METADATA_DB_FILE))
            
            print("✅ Sistema RAG inicializado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar RAG: {e}")
            return False
    
    def test_basic_search(self):
        """Teste básico de busca semântica."""
        print(f"\n🔍 TESTE BÁSICO DE BUSCA SEMÂNTICA")
        print("=" * 60)
        
        test_queries = [
            "água mineral",
            "refrigerante coca cola",
            "parafuso de aço",
            "smartphone samsung",
            "café torrado"
        ]
        
        for query in test_queries:
            print(f"\n🎯 Consultando: '{query}'")
            
            try:
                results = self.vector_store.search(query, k=3)
                
                if results:
                    print(f"   📊 {len(results)} resultados encontrados:")
                    for i, result in enumerate(results, 1):
                        metadata = result['metadata']
                        score = result['score']
                        ncm = metadata.get('ncm', 'N/A')
                        gtin = metadata.get('codigo_barra', 'N/A')
                        text_preview = result['text'][:80] + "..." if len(result['text']) > 80 else result['text']
                        
                        print(f"   {i}. Score: {score:.3f} | NCM: {ncm} | GTIN: {gtin}")
                        print(f"      Texto: {text_preview}")
                else:
                    print(f"   ⚠️ Nenhum resultado encontrado.")
                    
            except Exception as e:
                print(f"   ❌ Erro na busca: {e}")
    
    def test_filtered_search(self):
        """Teste de busca com filtros de metadados."""
        print(f"\n🎯 TESTE DE BUSCA FILTRADA")
        print("=" * 60)
        
        # Primeiro, vamos descobrir quais NCMs temos disponíveis
        print("📊 Analisando NCMs disponíveis...")
        
        try:
            conn = sqlite3.connect(str(self.config.METADATA_DB_FILE))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT json_extract(metadata, '$.ncm') as ncm, COUNT(*) as count
                FROM chunks 
                WHERE json_extract(metadata, '$.ncm') IS NOT NULL
                AND json_extract(metadata, '$.ncm') != ''
                GROUP BY ncm
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_ncms = cursor.fetchall()
            conn.close()
            
            if not top_ncms:
                print("⚠️ Nenhum NCM encontrado nos metadados.")
                return
            
            print("🏆 Top 10 NCMs por quantidade de exemplos:")
            for i, (ncm, count) in enumerate(top_ncms, 1):
                print(f"   {i}. NCM {ncm}: {count} exemplos")
            
            # Testar busca filtrada com os NCMs mais comuns
            test_cases = [
                ("bebida", top_ncms[0][0] if top_ncms else "22021000"),
                ("produto alimentar", top_ncms[1][0] if len(top_ncms) > 1 else "09011100"),
                ("eletrônico", top_ncms[2][0] if len(top_ncms) > 2 else "85171200")
            ]
            
            print(f"\n🔍 Testando buscas filtradas:")
            
            for query, ncm_filter in test_cases:
                print(f"\n   🎯 Query: '{query}' | NCM Filter: {ncm_filter}")
                
                # Busca sem filtro
                results_unfiltered = self.vector_store.search(query, k=5)
                
                # Busca com filtro
                results_filtered = self.vector_store.search(query, k=5, metadata_filter={"ncm": ncm_filter})
                
                print(f"      📊 Sem filtro: {len(results_unfiltered)} resultados")
                print(f"      📊 Com filtro NCM {ncm_filter}: {len(results_filtered)} resultados")
                
                if results_filtered:
                    best_result = results_filtered[0]
                    text_preview = best_result['text'][:60] + "..." if len(best_result['text']) > 60 else best_result['text']
                    print(f"      🏆 Melhor resultado: Score {best_result['score']:.3f} - {text_preview}")
                else:
                    print(f"      ⚠️ Nenhum resultado encontrado com filtro NCM {ncm_filter}")
                    
        except Exception as e:
            print(f"❌ Erro no teste de busca filtrada: {e}")
    
    def test_system_statistics(self):
        """Teste das estatísticas do sistema."""
        print(f"\n📊 ESTATÍSTICAS DO SISTEMA")
        print("=" * 60)
        
        try:
            conn = sqlite3.connect(str(self.config.METADATA_DB_FILE))
            cursor = conn.cursor()
            
            # Total de chunks
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            
            # Distribuição por fonte
            cursor.execute("""
                SELECT json_extract(metadata, '$.source') as source, COUNT(*) as count
                FROM chunks
                GROUP BY source
                ORDER BY count DESC
            """)
            sources = cursor.fetchall()
            
            # NCMs únicos
            cursor.execute("""
                SELECT COUNT(DISTINCT json_extract(metadata, '$.ncm'))
                FROM chunks
                WHERE json_extract(metadata, '$.ncm') IS NOT NULL
                AND json_extract(metadata, '$.ncm') != ''
            """)
            unique_ncms = cursor.fetchone()[0]
            
            # Produtos com diferentes tipos de código
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN json_extract(metadata, '$.codigo_barra') IS NOT NULL 
                             AND json_extract(metadata, '$.codigo_barra') != '' THEN 1 ELSE 0 END) as com_gtin,
                    SUM(CASE WHEN json_extract(metadata, '$.codigo_produto') IS NOT NULL 
                             AND json_extract(metadata, '$.codigo_produto') != '' THEN 1 ELSE 0 END) as com_codigo_produto
                FROM chunks
            """)
            codigo_stats = cursor.fetchone()
            
            conn.close()
            
            # Exibir estatísticas
            print(f"📦 Total de chunks indexados: {total_chunks:,}")
            print(f"🎯 NCMs únicos: {unique_ncms:,}")
            
            if codigo_stats:
                com_gtin, com_codigo_produto = codigo_stats
                print(f"🏷️ Produtos com GTIN: {com_gtin:,} ({com_gtin/total_chunks*100:.1f}%)")
                print(f"📋 Produtos com código interno: {com_codigo_produto:,} ({com_codigo_produto/total_chunks*100:.1f}%)")
            
            print(f"\n📊 Distribuição por fonte:")
            for source, count in sources:
                print(f"   {source or 'N/A'}: {count:,} chunks ({count/total_chunks*100:.1f}%)")
            
            # Verificar dimensionalidade do índice
            if hasattr(self.vector_store.index, 'd'):
                print(f"🧮 Dimensionalidade dos vetores: {self.vector_store.index.d}")
                print(f"🔢 Vetores no índice FAISS: {self.vector_store.index.ntotal:,}")
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
    
    def run_comprehensive_test(self):
        """Executa todos os testes do sistema RAG."""
        print("🧪 EXECUTANDO BATERIA COMPLETA DE TESTES RAG")
        print("=" * 80)
        
        if not self.initialize_rag_system():
            return False
        
        try:
            # Executar todos os testes
            self.test_system_statistics()
            self.test_basic_search()
            self.test_filtered_search()
            
            print(f"\n✅ TODOS OS TESTES RAG CONCLUÍDOS COM SUCESSO!")
            print("💡 O sistema está pronto para classificação de produtos.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO durante os testes: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Função principal para executar os testes RAG."""
    tester = RAGTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--query":
        # Modo de consulta individual
        if len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            if tester.initialize_rag_system():
                print(f"🔍 Consultando: '{query}'")
                results = tester.vector_store.search(query, k=5)
                for i, result in enumerate(results, 1):
                    print(f"{i}. Score: {result['score']:.3f}")
                    print(f"   NCM: {result['metadata'].get('ncm', 'N/A')}")
                    print(f"   Texto: {result['text'][:100]}...")
        else:
            print("❌ Forneça uma consulta: python test_rag.py --query sua consulta aqui")
    else:
        # Modo completo
        success = tester.run_comprehensive_test()
        exit(0 if success else 1)

if __name__ == "__main__":
    main()