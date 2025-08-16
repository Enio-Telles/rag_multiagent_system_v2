"""
Script para atualizar o índice Golden Set - Fase 5
Executa retreinamento periódico com classificações validadas
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database.connection import SessionLocal, test_connection
from src.feedback.continuous_learning import ContinuousLearningScheduler
from src.config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Função principal para atualização do Golden Set
    """
    print("🔄 ATUALIZAÇÃO DO GOLDEN SET - APRENDIZAGEM CONTÍNUA")
    print("=" * 60)
    
    try:
        # Verificar conexão com banco
        if not test_connection():
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return False
        
        print("✅ Conexão com banco de dados OK")
        
        # Inicializar componentes
        config = Config()
        scheduler = ContinuousLearningScheduler(config)
        
        # Verificar se há dados para retreinamento
        db = SessionLocal()
        try:
            resultado = scheduler.executar_retreinamento(db, force=False)
            
            if resultado["status"] == "sucesso":
                print(f"🎉 RETREINAMENTO CONCLUÍDO!")
                print(f"   📊 Total de entradas: {resultado['total_entradas']}")
                print(f"   📂 Índice salvo em: {resultado['caminho_indice']}")
                print(f"   🗄️ Metadados em: {resultado['caminho_metadata']}")
                print(f"   📏 Dimensão: {resultado['dimensao']}")
                
            elif resultado["status"] == "desnecessario":
                print(f"ℹ️  Retreinamento desnecessário: {resultado['message']}")
                
            elif resultado["status"] == "insuficiente":
                print(f"⚠️  Retreinamento adiado: {resultado['message']}")
                
            elif resultado["status"] == "vazio":
                print("⚠️  Golden Set vazio - nenhuma classificação validada encontrada")
                
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erro na atualização do Golden Set: {e}")
        print(f"❌ Erro: {e}")
        return False

def force_update():
    """
    Força atualização mesmo com poucas entradas
    """
    print("🔄 ATUALIZAÇÃO FORÇADA DO GOLDEN SET")
    print("=" * 60)
    
    try:
        if not test_connection():
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return False
        
        config = Config()
        scheduler = ContinuousLearningScheduler(config)
        
        db = SessionLocal()
        try:
            resultado = scheduler.executar_retreinamento(db, force=True)
            
            if resultado["status"] == "sucesso":
                print(f"🎉 RETREINAMENTO FORÇADO CONCLUÍDO!")
                print(f"   📊 Total de entradas: {resultado['total_entradas']}")
                print(f"   📂 Índice salvo em: {resultado['caminho_indice']}")
                
            elif resultado["status"] == "vazio":
                print("⚠️  Golden Set vazio - nenhuma classificação validada encontrada")
                
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erro na atualização forçada: {e}")
        print(f"❌ Erro: {e}")
        return False

def verificar_status():
    """
    Verifica status do Golden Set
    """
    print("📊 STATUS DO GOLDEN SET")
    print("=" * 60)
    
    try:
        if not test_connection():
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return
        
        from src.database.models import GoldenSetEntry
        
        db = SessionLocal()
        try:
            # Contadores
            total_entradas = db.query(GoldenSetEntry).count()
            nao_retreinadas = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.incluido_em_retreinamento == False
            ).count()
            retreinadas = total_entradas - nao_retreinadas
            
            print(f"📈 Total de entradas no Golden Set: {total_entradas}")
            print(f"✅ Já incluídas em retreinamento: {retreinadas}")
            print(f"🆕 Novas (não retreinadas): {nao_retreinadas}")
            
            # Verificar índices existentes
            config = Config()
            golden_index_path = config.KNOWLEDGE_BASE_DIR / "golden_set_index.faiss"
            golden_metadata_path = config.KNOWLEDGE_BASE_DIR / "golden_metadata.db"
            
            if golden_index_path.exists():
                size_mb = golden_index_path.stat().st_size / (1024 * 1024)
                print(f"📂 Índice Golden Set: ✅ ({size_mb:.1f} MB)")
            else:
                print(f"📂 Índice Golden Set: ❌ (não encontrado)")
            
            if golden_metadata_path.exists():
                size_mb = golden_metadata_path.stat().st_size / (1024 * 1024)
                print(f"🗄️ Metadados Golden Set: ✅ ({size_mb:.1f} MB)")
            else:
                print(f"🗄️ Metadados Golden Set: ❌ (não encontrado)")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciamento do Golden Set")
    parser.add_argument("--action", choices=["update", "force", "status"], 
                       default="update", help="Ação a executar")
    
    args = parser.parse_args()
    
    if args.action == "update":
        success = main()
        sys.exit(0 if success else 1)
    elif args.action == "force":
        success = force_update()
        sys.exit(0 if success else 1)
    elif args.action == "status":
        verificar_status()
        sys.exit(0)
