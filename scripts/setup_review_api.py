"""
Script para inicializar e executar a API de Revisão - Fase 4
"""

import sys
import os
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def criar_tabelas():
    """
    Cria as tabelas necessárias no banco de dados
    """
    try:
        from src.database.connection import create_tables, test_connection
        
        print("🔄 Verificando conexão com banco de dados...")
        if not test_connection():
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            print("   Verifique as configurações no arquivo .env")
            return False
        
        print("✅ Conexão OK")
        print("🔄 Criando tabelas...")
        
        create_tables()
        
        print("✅ Tabelas criadas com sucesso!")
        print("   - classificacoes_revisao")
        print("   - golden_set_entries")
        print("   - metricas_qualidade")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def importar_classificacoes_existentes():
    """
    Importa classificações existentes dos arquivos JSON
    """
    try:
        from src.database.connection import SessionLocal
        from src.feedback.review_service import ReviewService
        import glob
        
        print("🔄 Importando classificações existentes...")
        
        # Buscar arquivos JSON de classificação
        data_dir = Path("data/processed")
        json_files = list(data_dir.glob("classificacao_*.json"))
        
        if not json_files:
            print("⚠️  Nenhum arquivo de classificação encontrado em data/processed/")
            return True
        
        # Usar o arquivo mais recente
        arquivo_mais_recente = max(json_files, key=lambda f: f.stat().st_mtime)
        print(f"📂 Importando: {arquivo_mais_recente.name}")
        
        review_service = ReviewService()
        db = SessionLocal()
        
        try:
            resultado = review_service.importar_classificacoes_json(
                db=db,
                caminho_arquivo=str(arquivo_mais_recente)
            )
            
            print(f"✅ Importação concluída!")
            print(f"   📊 Total processado: {resultado['total']}")
            print(f"   ✅ Importadas: {resultado['importadas']}")
            print(f"   ❌ Erros: {resultado['erros']}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False

def verificar_dependencias():
    """
    Verifica se as dependências estão instaladas
    """
    dependencias = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic")
    ]
    
    print("🔍 Verificando dependências...")
    faltantes = []
    
    for modulo, nome in dependencias:
        try:
            __import__(modulo)
            print(f"   ✅ {nome}")
        except ImportError:
            print(f"   ❌ {nome}")
            faltantes.append(modulo)
    
    if faltantes:
        print(f"\n⚠️  Dependências faltantes: {', '.join(faltantes)}")
        print("   Execute: pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary")
        return False
    
    return True

def executar_api():
    """
    Executa a API de revisão
    """
    try:
        import uvicorn
        from src.api.review_api import app
        
        print("🚀 Iniciando API de Revisão...")
        print("   📍 URL: http://localhost:8000")
        print("   📚 Documentação: http://localhost:8000/api/docs")
        print("   🔄 Swagger UI: http://localhost:8000/api/redoc")
        print("\n   Pressione Ctrl+C para parar")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 API encerrada pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar API: {e}")

def main():
    """
    Função principal de inicialização
    """
    print("🚀 INICIALIZAÇÃO DA API DE REVISÃO HUMANA - FASE 4")
    print("=" * 60)
    
    # 1. Verificar dependências
    if not verificar_dependencias():
        return False
    
    # 2. Criar tabelas
    if not criar_tabelas():
        return False
    
    # 3. Importar classificações existentes
    if not importar_classificacoes_existentes():
        print("⚠️  Continuando sem importar classificações existentes...")
    
    # 4. Executar API
    print("\n" + "=" * 60)
    executar_api()
    
    return True

def apenas_criar_tabelas():
    """
    Apenas cria as tabelas sem executar a API
    """
    print("🔧 CRIAÇÃO DE TABELAS - FASE 4")
    print("=" * 60)
    
    if verificar_dependencias() and criar_tabelas():
        print("\n✅ Tabelas criadas com sucesso!")
        print("   Execute novamente com --run para iniciar a API")
        return True
    
    return False

def apenas_importar():
    """
    Apenas importa classificações existentes
    """
    print("📥 IMPORTAÇÃO DE CLASSIFICAÇÕES - FASE 4")
    print("=" * 60)
    
    if importar_classificacoes_existentes():
        print("\n✅ Importação concluída!")
        return True
    
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="API de Revisão Humana")
    parser.add_argument("--action", choices=["setup", "run", "import", "tables"], 
                       default="setup", help="Ação a executar")
    
    args = parser.parse_args()
    
    if args.action == "setup":
        success = main()
    elif args.action == "run":
        executar_api()
        success = True
    elif args.action == "import":
        success = apenas_importar()
    elif args.action == "tables":
        success = apenas_criar_tabelas()
    
    if args.action != "run":
        sys.exit(0 if success else 1)
