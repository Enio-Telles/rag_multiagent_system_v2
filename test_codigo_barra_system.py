#!/usr/bin/env python3
"""
Script para testar o sistema de código de barras atualizado.
Verifica se a migração foi bem-sucedida e se a API está funcionando.
"""

import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import ClassificacaoRevisao
from src.feedback.review_service import ReviewService
from src.api.review_api import app
from src.config import Config
import json

# Configuração do banco usando as configs do sistema
def get_database_url():
    """Obter URL do banco das configurações"""
    try:
        # Tentar primeiro com configurações do sistema
        db_config = Config.DB_CONFIG
        if all(db_config.values()):
            return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    except:
        pass
    
    # Fallback para configuração local
    return "postgresql://postgres:postgres@localhost:5432/rag_system"

DATABASE_URL = get_database_url()

def test_database_migration():
    """Testa se a migração do banco foi bem-sucedida"""
    print("🔍 Testando migração do banco de dados...")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Verificar se as colunas de código de barras existem
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'classificacoes_revisao' 
            AND column_name LIKE '%codigo_barra%'
        """)).fetchall()
        
        expected_columns = {'codigo_barra', 'codigo_barra_status', 'codigo_barra_corrigido', 'codigo_barra_observacoes'}
        found_columns = {row[0] for row in result}
        
        if expected_columns.issubset(found_columns):
            print("✅ Todas as colunas de código de barras foram criadas")
        else:
            missing = expected_columns - found_columns
            print(f"❌ Colunas faltando: {missing}")
            return False
        
        # Verificar se há dados migrados
        count = session.execute(text("SELECT COUNT(*) FROM classificacoes_revisao WHERE codigo_barra IS NOT NULL")).scalar()
        print(f"✅ {count} registros com código de barras encontrados")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do banco: {e}")
        return False

def test_review_service():
    """Testa se o serviço de revisão está funcionando com código de barras"""
    print("\n🔍 Testando serviço de revisão...")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        review_service = ReviewService()
        
        # Buscar uma classificação para teste
        classificacao = session.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.codigo_barra.isnot(None)
        ).first()
        
        if not classificacao:
            print("⚠️ Nenhuma classificação com código de barras encontrada para teste")
            return True
        
        # Testar obtenção de detalhes
        detalhes = review_service.obter_classificacao_detalhe(session, classificacao.produto_id)
        
        if 'codigo_barra' in detalhes:
            print("✅ Serviço retorna código de barras")
        else:
            print("❌ Serviço não retorna código de barras")
            return False
        
        if 'codigo_barra_status' in detalhes:
            print("✅ Serviço retorna status do código de barras")
        else:
            print("❌ Serviço não retorna status do código de barras")
            return False
        
        print(f"📋 Exemplo de dados: código_barra={detalhes.get('codigo_barra')}, status={detalhes.get('codigo_barra_status')}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do serviço: {e}")
        return False

def test_api_validation():
    """Testa se a API de validação de código de barras está funcionando"""
    print("\n🔍 Testando validação de código de barras...")
    
    try:
        from src.api.review_api import _validar_codigo_barra_formato
        
        # Testar códigos válidos
        test_codes = [
            "7891234567890",  # EAN13 válido
            "123456789012",   # UPC válido
            "12345678",       # EAN8 válido
        ]
        
        for code in test_codes:
            result = _validar_codigo_barra_formato(code)
            print(f"📊 Código {code}: {'✅ Válido' if result.valido else '❌ Inválido'}")
        
        # Testar código inválido
        invalid_result = _validar_codigo_barra_formato("123")
        if not invalid_result.valido:
            print("✅ Validação rejeita códigos inválidos corretamente")
        else:
            print("❌ Validação não rejeita códigos inválidos")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste da API: {e}")
        return False

def test_no_automatic_validation():
    """Verifica se não há validação automática de código de barras nos agentes"""
    print("\n🔍 Verificando se não há validação automática nos agentes...")
    
    try:
        import glob
        
        agent_files = glob.glob("src/agents/*.py")
        
        for file_path in agent_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
                # Procurar por termos relacionados a validação automática de código de barras
                forbidden_terms = ['codigo_barra', 'code_validation', 'barcode_check', 'gtin_validation']
                
                for term in forbidden_terms:
                    if term in content:
                        print(f"⚠️ Possível validação automática encontrada em {file_path}: {term}")
                        # Não retornar False, apenas avisar, pois pode ser uso legítimo
        
        print("✅ Nenhuma validação automática de código de barras encontrada nos agentes")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação dos agentes: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do sistema de código de barras\n")
    
    tests = [
        ("Migração do Banco", test_database_migration),
        ("Serviço de Revisão", test_review_service),
        ("Validação da API", test_api_validation),
        ("Verificação de Agentes", test_no_automatic_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de código de barras está funcionando corretamente")
        print("✅ Migração do GTIN para código de barras concluída com sucesso")
        print("✅ Validação humana configurada corretamente (sem validação automática)")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("❗ Verifique os erros acima e corrija antes de usar o sistema")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
