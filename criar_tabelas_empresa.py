"""
Script para criar tabelas de contexto da empresa no banco de dados
"""

import sys
sys.path.append('src')

from database.connection import engine
from database.models import Base, InformacaoEmpresa, ContextoClassificacao
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_tabelas_empresa():
    """Cria as tabelas necessárias para o contexto da empresa"""
    
    print("🔧 CRIANDO TABELAS DE CONTEXTO DA EMPRESA")
    print("=" * 50)
    
    try:
        # Criar apenas as tabelas específicas de empresa
        print("\n📋 Criando tabela 'informacoes_empresa'...")
        InformacaoEmpresa.__table__.create(engine, checkfirst=True)
        print("✅ Tabela 'informacoes_empresa' criada com sucesso")
        
        print("\n📋 Criando tabela 'contextos_classificacao'...")
        ContextoClassificacao.__table__.create(engine, checkfirst=True)
        print("✅ Tabela 'contextos_classificacao' criada com sucesso")
        
        print("\n🎉 TODAS AS TABELAS CRIADAS COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = criar_tabelas_empresa()
    if sucesso:
        print("\n🚀 Tabelas prontas para uso!")
    else:
        print("\n⚠️ Problemas na criação das tabelas")
