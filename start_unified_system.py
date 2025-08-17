#!/usr/bin/env python3
"""
Script de Inicialização do Sistema Unificado
Inicia as APIs integradas com SQLite unificado
"""

import sys
import subprocess
import time
import signal
import os
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """Verifica dependências necessárias"""
    print("🔍 Verificando dependências...")
    
    # Verificar arquivos principais
    required_files = [
        "data/unified_rag_system.db",
        "src/services/unified_sqlite_service.py",
        "src/api/api_unified.py", 
        "src/api/review_api_unified.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Arquivos necessários não encontrados:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\n💡 Execute primeiro: python src/main_unified.py migrate")
        return False
    
    # Verificar tamanho do banco
    db_path = Path("data/unified_rag_system.db")
    db_size = db_path.stat().st_size
    print(f"✅ Banco SQLite: {db_size / (1024*1024):.1f} MB")
    
    # Testar conexão com banco
    try:
        sys.path.append('src')
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service(str(db_path))
        counts = service.contar_registros()
        total_registros = sum(counts.values())
        
        print(f"✅ Registros no banco: {total_registros:,}")
        print(f"   - NCMs: {counts.get('ncm_estruturado', 0):,}")
        print(f"   - CESTs: {counts.get('cest_estruturado', 0):,}")
        print(f"   - Classificações: {counts.get('classificacao', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com banco: {e}")
        return False

def start_unified_api():
    """Inicia API principal unificada"""
    print("\n🚀 Iniciando API Principal Unificada (porta 8000)...")
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "src.api.api_unified:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
        
    except Exception as e:
        print(f"❌ Erro ao iniciar API principal: {e}")
        return None

def start_review_api():
    """Inicia API de revisão"""
    print("🚀 Iniciando Interface de Revisão (porta 8001)...")
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api.review_api_unified:app",
            "--host", "0.0.0.0",
            "--port", "8001", 
            "--reload",
            "--log-level", "info"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
        
    except Exception as e:
        print(f"❌ Erro ao iniciar interface de revisão: {e}")
        return None

def wait_for_api_ready(port, max_wait=30):
    """Aguarda API ficar disponível"""
    import requests
    
    url = f"http://localhost:{port}/api/health"
    if port == 8000:
        url = f"http://localhost:{port}/api/v1/sistema/health"
    
    print(f"⏳ Aguardando API na porta {port}...")
    
    for i in range(max_wait):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ API porta {port} pronta!")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"   ... ainda aguardando ({i}s)")
    
    print(f"❌ API porta {port} não ficou disponível em {max_wait}s")
    return False

def print_urls():
    """Imprime URLs importantes"""
    print("\n🌐 URLs DO SISTEMA:")
    print("=" * 50)
    print("📊 API Principal:")
    print("   - Documentação: http://localhost:8000/api/docs")
    print("   - Health Check: http://localhost:8000/api/v1/sistema/health")
    print("   - Dashboard:    http://localhost:8000/api/v1/dashboard/stats")
    print()
    print("📋 Interface de Revisão:")
    print("   - Interface:    http://localhost:8001")
    print("   - Documentação: http://localhost:8001/api/docs") 
    print("   - Health Check: http://localhost:8001/api/health")
    print()
    print("🔍 Endpoints Principais:")
    print("   - Buscar NCMs:   GET  /api/v1/ncm/buscar")
    print("   - Classificar:   POST /api/v1/classificar")
    print("   - Pendentes:     GET  /api/classificacoes/pendentes")
    print("   - Revisar:       POST /api/classificacoes/{id}/revisar")

def handle_shutdown(processes):
    """Manipula encerramento do sistema"""
    
    def signal_handler(sig, frame):
        print("\n🛑 Encerrando sistema...")
        
        for name, process in processes.items():
            if process and process.poll() is None:
                print(f"   - Parando {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   - Forçando parada de {name}...")
                    process.kill()
        
        print("✅ Sistema encerrado")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Função principal"""
    print("🚀 SISTEMA DE CLASSIFICAÇÃO FISCAL - INICIALIZAÇÃO UNIFICADA")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Dependências não atendidas. Sistema não iniciado.")
        return 1
    
    # Iniciar processos
    processes = {}
    
    # API Principal
    api_process = start_unified_api()
    if api_process:
        processes['API Principal'] = api_process
    else:
        print("❌ Falha ao iniciar API principal")
        return 1
    
    # Interface de Revisão
    review_process = start_review_api()
    if review_process:
        processes['Interface Revisão'] = review_process
    else:
        print("❌ Falha ao iniciar interface de revisão")
        return 1
    
    # Configurar manipulador de encerramento
    handle_shutdown(processes)
    
    # Aguardar APIs ficarem prontas
    print("\n⏳ Aguardando inicialização...")
    time.sleep(3)  # Dar tempo para iniciar
    
    api_ready = wait_for_api_ready(8000)
    review_ready = wait_for_api_ready(8001)
    
    if not (api_ready and review_ready):
        print("\n❌ Nem todas as APIs ficaram disponíveis")
        handle_shutdown(processes)
        return 1
    
    # Imprimir informações
    print_urls()
    
    print("\n🎉 SISTEMA INICIADO COM SUCESSO!")
    print("=" * 50)
    print("💡 Pressione Ctrl+C para encerrar")
    print()
    
    # Manter processos rodando
    try:
        while True:
            # Verificar se processos ainda estão rodando
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"❌ {name} parou inesperadamente")
                    return 1
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        handle_shutdown(processes)
    
    return 0

if __name__ == "__main__":
    # Mudar para diretório do script
    os.chdir(Path(__file__).parent)
    
    sys.exit(main())
