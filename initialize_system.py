"""
Script principal para inicialização do sistema RAG Multi-Agent
Execute este script para configurar todo o ambiente
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

try:
    from src.core.system_manager import system_manager
    from src.services.auditoria_service import audit_service, AuditEventType, AuditSeverity
    import json
    from datetime import datetime
    
    def main():
        """Função principal de inicialização"""
        
        print("=" * 60)
        print("🚀 SISTEMA RAG MULTI-AGENT v2.0")
        print("   Sistema de Classificação Multi-Empresa")
        print("=" * 60)
        print()
        
        try:
            # Inicializar sistema
            success = system_manager.start_system()
            
            if not success:
                print("❌ Falha na inicialização do sistema")
                return 1
            
            # Verificar status
            status = system_manager.get_system_status()
            
            print("\n📊 STATUS DO SISTEMA:")
            print("-" * 40)
            
            if status.get("sistema_ativo"):
                print("✅ Sistema: ATIVO")
                
                # Mostrar componentes
                componentes = status.get("componentes", {})
                
                # Banco central
                central = componentes.get("banco_central", {})
                if central.get("status") == "OK":
                    print(f"✅ Banco Central: OK ({central.get('empresas_ativas', 0)} empresas, {central.get('usuarios_ativos', 0)} usuários)")
                else:
                    print(f"❌ Banco Central: {central.get('erro', 'Erro desconhecido')}")
                
                # Auditoria
                auditoria = componentes.get("auditoria", {})
                if auditoria.get("status") == "OK":
                    print("✅ Sistema de Auditoria: OK")
                else:
                    print(f"❌ Sistema de Auditoria: {auditoria.get('erro', 'Erro desconhecido')}")
                
                # Bancos das empresas
                empresas_db = componentes.get("bancos_empresas", [])
                empresas_ok = len([e for e in empresas_db if e.get("status") == "OK"])
                empresas_total = len(empresas_db)
                
                if empresas_total > 0:
                    print(f"✅ Bancos de Empresas: {empresas_ok}/{empresas_total} ativos")
                    
                    for empresa in empresas_db:
                        status_icon = "✅" if empresa.get("status") == "OK" else "❌"
                        print(f"   {status_icon} {empresa.get('nome', 'N/A')}")
                
            else:
                print(f"❌ Sistema: INATIVO - {status.get('erro', 'Erro desconhecido')}")
                return 1
            
            print()
            print("🔧 CONFIGURAÇÕES DE ACESSO:")
            print("-" * 40)
            print("👤 Usuário Admin:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@sistema.com")
            print()
            
            print("📁 ESTRUTURA DE DADOS:")
            print("-" * 40)
            config = system_manager.config
            print(f"📊 Banco Central: {config.central_db_path}")
            print(f"📝 Auditoria: {config.audit_db_path}")
            print(f"🏢 Empresas: {config.empresas_db_path}/")
            print(f"🏆 Golden Set: {config.golden_set_path}")
            print()
            
            print("🎯 PRÓXIMOS PASSOS:")
            print("-" * 40)
            print("1. ⚡ Iniciar API: python -m src.api.multiempresa_api")
            print("2. 🧪 Executar Testes: python test_sistema_completo.py")
            print("3. 🌐 Acessar Interface: http://localhost:8000/docs")
            print("4. 📊 Dashboard: http://localhost:3000 (após configurar frontend)")
            print()
            
            # Log de inicialização bem-sucedida
            audit_service.log_event(
                audit_service.AuditEvent(
                    event_id=None,
                    event_type=AuditEventType.SYSTEM_ERROR,
                    severity=AuditSeverity.LOW,
                    empresa_id=None,
                    user_id="system",
                    session_id=None,
                    resource_type="system",
                    resource_id="initialization",
                    action_performed="system_startup_complete",
                    ip_address=None,
                    user_agent=None,
                    api_endpoint=None,
                    http_method=None,
                    before_data=None,
                    after_data={"status": "success", "componentes": len(status.get("componentes", {}))},
                    metadata={"version": "2.0", "timestamp": datetime.utcnow().isoformat()},
                    success=True,
                    error_message=None,
                    duration_ms=None,
                    timestamp=datetime.utcnow()
                )
            )
            
            print("✅ Sistema inicializado com sucesso!")
            print("📝 Evento de inicialização registrado na auditoria")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO: {str(e)}")
            print("\n🔧 DIAGNÓSTICO:")
            print("- Verifique se todos os diretórios têm permissão de escrita")
            print("- Confirme que não há outros processos usando os bancos de dados")
            print("- Execute como administrador se necessário")
            
            # Log de erro na inicialização
            try:
                audit_service.log_event(
                    audit_service.AuditEvent(
                        event_id=None,
                        event_type=AuditEventType.SYSTEM_ERROR,
                        severity=AuditSeverity.CRITICAL,
                        empresa_id=None,
                        user_id="system",
                        session_id=None,
                        resource_type="system",
                        resource_id="initialization",
                        action_performed="system_startup_failed",
                        ip_address=None,
                        user_agent=None,
                        api_endpoint=None,
                        http_method=None,
                        before_data=None,
                        after_data=None,
                        metadata={"error": str(e)},
                        success=False,
                        error_message=str(e),
                        duration_ms=None,
                        timestamp=datetime.utcnow()
                    )
                )
            except:
                pass  # Se auditoria falhar, não queremos mascarar o erro original
            
            return 1

    if __name__ == "__main__":
        exit_code = main()
        sys.exit(exit_code)

except ImportError as e:
    print(f"❌ ERRO DE IMPORTAÇÃO: {str(e)}")
    print("\n🔧 POSSÍVEIS SOLUÇÕES:")
    print("1. Instale as dependências: pip install -r requirements.txt")
    print("2. Verifique se está no diretório correto")
    print("3. Configure o PYTHONPATH corretamente")
    sys.exit(1)
