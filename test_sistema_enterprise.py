"""
Teste completo do sistema RAG Multi-Agent v2.0 - Versão Enterprise
Valida todas as funcionalidades implementadas nas fases 1 e 2
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

def test_central_database():
    """Testa banco central"""
    
    print("📊 Testando Banco Central...")
    
    try:
        from src.core.system_manager import system_manager
        
        central_db = system_manager.config.central_db_path
        
        if not os.path.exists(central_db):
            raise Exception("Banco central não encontrado")
        
        with sqlite3.connect(central_db) as conn:
            cursor = conn.cursor()
            
            # Testar empresas
            cursor.execute("SELECT COUNT(*) FROM empresas WHERE ativa = TRUE")
            empresas_count = cursor.fetchone()[0]
            
            if empresas_count == 0:
                raise Exception("Nenhuma empresa ativa encontrada")
            
            # Testar usuários
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = TRUE")
            users_count = cursor.fetchone()[0]
            
            if users_count == 0:
                raise Exception("Nenhum usuário ativo encontrado")
            
            # Testar permissões
            cursor.execute("SELECT COUNT(*) FROM usuario_empresa_permissoes WHERE ativa = TRUE")
            perms_count = cursor.fetchone()[0]
            
            print(f"   ✅ {empresas_count} empresas ativas")
            print(f"   ✅ {users_count} usuários ativos")
            print(f"   ✅ {perms_count} permissões ativas")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def test_audit_system():
    """Testa sistema de auditoria"""
    
    print("📝 Testando Sistema de Auditoria...")
    
    try:
        from src.services.auditoria_service import audit_service, AuditEventType, AuditSeverity
        
        # Testar registro de evento
        event_id = audit_service.log_event(
            audit_service.AuditEvent(
                event_id=None,
                event_type=AuditEventType.SYSTEM_ERROR,
                severity=AuditSeverity.LOW,
                empresa_id=1,
                user_id="test_user",
                session_id="test_session",
                resource_type="test",
                resource_id="test_resource",
                action_performed="test_action",
                ip_address="127.0.0.1",
                user_agent="test_agent",
                api_endpoint="/test",
                http_method="GET",
                before_data={"status": "before"},
                after_data={"status": "after"},
                metadata={"test": True},
                success=True,
                error_message=None,
                duration_ms=100.5,
                timestamp=datetime.utcnow()
            )
        )
        
        if not event_id:
            raise Exception("Falha ao registrar evento")
        
        # Testar busca de logs
        logs = audit_service.get_audit_logs(
            empresa_id=1,
            limit=10
        )
        
        if not logs:
            raise Exception("Nenhum log encontrado")
        
        # Testar relatório
        report = audit_service.generate_audit_report(
            empresa_id=1,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        if not report:
            raise Exception("Falha ao gerar relatório")
        
        print(f"   ✅ Evento registrado: {event_id}")
        print(f"   ✅ {len(logs)} logs encontrados")
        print(f"   ✅ Relatório gerado: {report.get('estatisticas_gerais', {}).get('total_eventos', 0)} eventos")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def test_empresa_context():
    """Testa gerenciamento de contexto de empresa"""
    
    print("🏢 Testando Contexto de Empresa...")
    
    try:
        from src.core.empresa_context_manager import EmpresaContextManager
        from src.core.system_manager import system_manager
        
        context_manager = EmpresaContextManager(system_manager.config.central_db_path)
        
        # Buscar uma empresa para teste
        with sqlite3.connect(system_manager.config.central_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, database_path FROM empresas WHERE ativa = TRUE LIMIT 1")
            empresa_data = cursor.fetchone()
            
            if not empresa_data:
                raise Exception("Nenhuma empresa encontrada para teste")
            
            empresa_id, nome, db_path = empresa_data
        
        # Testar contexto
        with context_manager.empresa_context(empresa_id, "test_user") as context:
            if not context:
                raise Exception("Falha ao criar contexto")
            
            if context.empresa_id != empresa_id:
                raise Exception("ID da empresa incorreto no contexto")
            
            if not context.database_path:
                raise Exception("Caminho do banco não definido")
        
        print(f"   ✅ Contexto criado para empresa {nome} (ID: {empresa_id})")
        print(f"   ✅ Database path: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def test_dependency_injection():
    """Testa container de dependências"""
    
    print("⚙️ Testando Dependency Injection...")
    
    try:
        from src.core.dependency_injection import ServiceContainer
        
        # Criar container de teste
        container = ServiceContainer()
        
        # Registrar serviços
        container.register_singleton("test_service", lambda: {"status": "OK"})
        container.register_factory("test_factory", lambda: {"timestamp": datetime.utcnow().isoformat()})
        
        # Testar singleton
        service1 = container.get("test_service")
        service2 = container.get("test_service")
        
        if service1 is not service2:
            raise Exception("Singleton não funcionando corretamente")
        
        # Testar factory
        factory1 = container.get("test_factory")
        factory2 = container.get("test_factory")
        
        if factory1 is factory2:
            raise Exception("Factory retornando mesmo objeto")
        
        print("   ✅ Singleton funcionando")
        print("   ✅ Factory funcionando")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def test_empresa_databases():
    """Testa bancos de dados das empresas"""
    
    print("🗄️ Testando Bancos das Empresas...")
    
    try:
        from src.core.system_manager import system_manager
        from src.database.empresa_schema_manager import EmpresaSchemaManager
        
        schema_manager = EmpresaSchemaManager()
        
        # Buscar empresas
        with sqlite3.connect(system_manager.config.central_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, database_path FROM empresas WHERE ativa = TRUE")
            empresas = cursor.fetchall()
        
        if not empresas:
            raise Exception("Nenhuma empresa encontrada")
        
        for empresa_id, nome, db_path in empresas:
            if not os.path.exists(db_path):
                print(f"   ⚠️ Criando banco para {nome}...")
                schema_manager.create_empresa_database(db_path)
            
            # Testar estrutura do banco
            if not schema_manager.validate_empresa_database(db_path):
                raise Exception(f"Estrutura inválida para empresa {nome}")
            
            # Testar tabelas obrigatórias
            with sqlite3.connect(db_path) as emp_conn:
                cursor = emp_conn.cursor()
                
                # Verificar tabelas principais
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (
                        'produtos', 'classificacoes', 'agentes_acoes',
                        'aprovacoes', 'auditoria_local'
                    )
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                required_tables = ['produtos', 'classificacoes', 'agentes_acoes', 'aprovacoes', 'auditoria_local']
                
                missing_tables = set(required_tables) - set(tables)
                if missing_tables:
                    raise Exception(f"Tabelas faltando em {nome}: {missing_tables}")
            
            print(f"   ✅ {nome}: estrutura válida")
        
        print(f"   ✅ {len(empresas)} bancos validados")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def test_legacy_system():
    """Testa integração com sistema antigo"""
    
    print("🔄 Testando Integração com Sistema Legacy...")
    
    try:
        from src.orchestrator.hybrid_router import HybridRouter
        
        router = HybridRouter()
        
        stats = router.vector_store.get_stats()
        print(f"   ✅ Produtos indexados: {stats.get('total_vectors', 0):,}")
        print(f"   ✅ Dimensão dos vetores: {stats.get('dimension', 0)}")
        print(f"   ✅ Tipo de índice: {stats.get('index_type', 'N/A')}")
        
        # Teste rápido de classificação
        produtos_teste = [{
            'produto_id': 9999, 
            'descricao_produto': 'Refrigerante Coca-Cola 350ml lata', 
            'codigo_produto': 'TESTE001'
        }]
        
        resultados = router.classify_products(produtos_teste)
        resultado = resultados[0]
        
        print(f"   ✅ NCM classificado: {resultado.get('ncm_classificado', 'N/A')}")
        print(f"   ✅ CEST classificado: {resultado.get('cest_classificado', 'N/A')}")
        print(f"   ✅ Confiança: {resultado.get('confianca_consolidada', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    
    print("=" * 60)
    print("🧪 TESTE COMPLETO DO SISTEMA RAG MULTI-AGENT v2.0")
    print("   Fases 1 e 2: Backend, API, Database e Audit")
    print("=" * 60)
    print()
    
    tests = [
        ("Banco Central", test_central_database),
        ("Sistema de Auditoria", test_audit_system),
        ("Contexto de Empresa", test_empresa_context),
        ("Dependency Injection", test_dependency_injection),
        ("Bancos das Empresas", test_empresa_databases),
        ("Sistema Legacy", test_legacy_system)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n🔧 {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                passed_tests += 1
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERRO - {str(e)}")
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status:<15} {test_name}")
    
    print(f"\n📈 RESUMO: {passed_tests}/{total_tests} testes passaram ({passed_tests/total_tests*100:.1f}%)")
    
    # Status por fase
    print("\n📋 STATUS POR FASE:")
    print("-" * 30)
    
    backend_tests = ["Dependency Injection", "Contexto de Empresa"]
    backend_passed = sum(1 for test in backend_tests if results.get(test, False))
    print(f"📡 Fase 1 (Backend): {backend_passed}/{len(backend_tests)} ({backend_passed/len(backend_tests)*100:.0f}%)")
    
    database_tests = ["Banco Central", "Sistema de Auditoria", "Bancos das Empresas"]
    database_passed = sum(1 for test in database_tests if results.get(test, False))
    print(f"🗄️ Fase 2 (Database): {database_passed}/{len(database_tests)} ({database_passed/len(database_tests)*100:.0f}%)")
    
    integration_tests = ["Sistema Legacy"]
    integration_passed = sum(1 for test in integration_tests if results.get(test, False))
    print(f"🔄 Integração Legacy: {integration_passed}/{len(integration_tests)} ({integration_passed/len(integration_tests)*100:.0f}%)")
    
    print()
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Fases 1 e 2 implementadas com sucesso!")
        print("🚀 Sistema pronto para Fase 3 (Frontend)")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ MAIORIA DOS TESTES PASSOU.")
        print("🔧 Corrija os problemas pendentes antes de prosseguir.")
        return 1
    else:
        print("❌ MUITOS TESTES FALHARAM.")
        print("🛑 Sistema requer correções significativas.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NOS TESTES: {str(e)}")
        print("\n🔧 DICAS DE RECUPERAÇÃO:")
        print("1. Execute 'python initialize_system.py' primeiro")
        print("2. Verifique se todas as dependências estão instaladas: pip install -r requirements.txt")
        print("3. Confirme permissões de escrita nos diretórios data/, logs/, config/")
        print("4. Para debug detalhado, execute os testes individuais")
        sys.exit(1)
