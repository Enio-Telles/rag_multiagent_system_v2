#!/usr/bin/env python3
"""
Script de Validação do Sistema SQLite Unificado
Verifica se todas as funcionalidades estão operacionais após atualizações
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.append('src')

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_files():
    """Verifica arquivos essenciais"""
    print_header("VERIFICAÇÃO DE ARQUIVOS")
    
    required_files = [
        ("data/unified_rag_system.db", "Banco SQLite Unificado"),
        ("src/services/unified_sqlite_service.py", "Serviço SQLite Unificado"),
        ("src/api/api_unified.py", "API Principal Unificada"),
        ("src/api/review_api_unified.py", "API de Revisão Unificada"),
        ("src/main.py", "Main Atualizado"),
        ("start_unified_system.py", "Sistema de Inicialização"),
        ("test_sqlite_simple.py", "Teste de Validação")
    ]
    
    all_ok = True
    for file_path, description in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if file_path.endswith('.db'):
                size_mb = size / (1024*1024)
                print(f"✅ {description}: {size_mb:.1f}MB")
            else:
                print(f"✅ {description}: {size:,} bytes")
        else:
            print(f"❌ {description}: FALTANDO - {file_path}")
            all_ok = False
    
    return all_ok

def test_unified_service():
    """Testa serviço SQLite unificado"""
    print_header("TESTE DO SERVIÇO SQLITE UNIFICADO")
    
    try:
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service()
        
        # Testar estatísticas
        stats = service.get_dashboard_stats()
        
        print(f"📊 Estatísticas do Sistema:")
        print(f"   NCMs: {stats['total_ncms']:,}")
        print(f"   CESTs: {stats['total_cests']:,}")
        print(f"   Mapeamentos: {stats.get('total_mapeamentos', 0):,}")
        print(f"   Classificações: {stats['total_classificacoes']:,}")
        
        # Testar busca NCM
        ncm_result = service.buscar_ncm("8517")
        if ncm_result:
            print(f"✅ Busca NCM: {ncm_result['codigo']} - {ncm_result['descricao'][:50]}...")
        else:
            print(f"❌ Busca NCM falhou")
            return False
        
        # Testar busca CEST
        cests = service.buscar_cests_para_ncm("8517")
        if cests:
            print(f"✅ Busca CEST: {len(cests)} CESTs encontrados para NCM 8517")
        else:
            print(f"⚠️  Nenhum CEST encontrado para NCM 8517 (pode ser normal)")
        
        print(f"✅ Serviço SQLite funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no serviço: {e}")
        return False

def test_main_classify():
    """Testa comando principal de classificação"""
    print_header("TESTE DO COMANDO CLASSIFY")
    
    try:
        # Testar importação
        from main import _classify_produto_unified, _get_sample_produtos
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service()
        produtos_teste = _get_sample_produtos(2)
        
        print(f"📝 Testando classificação de {len(produtos_teste)} produtos...")
        
        for i, produto in enumerate(produtos_teste, 1):
            start_time = time.time()
            
            resultado = _classify_produto_unified(produto, service)
            
            tempo_ms = int((time.time() - start_time) * 1000)
            
            print(f"   {i}. {produto['descricao_produto'][:40]}...")
            print(f"      NCM: {resultado['ncm_sugerido']}")
            print(f"      CEST: {resultado.get('cest_sugerido', 'N/A')}")
            print(f"      Confiança: {resultado.get('confianca_sugerida', 0):.2f}")
            print(f"      Tempo: {tempo_ms}ms")
        
        print(f"✅ Comando classify funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no comando classify: {e}")
        return False

def test_command_execution():
    """Testa execução de comandos via terminal"""
    print_header("TESTE DE COMANDOS VIA TERMINAL")
    
    try:
        # Testar comando principal
        print("🧪 Testando: python src/main.py classify --limit 2")
        
        result = subprocess.run([
            "python", "src/main.py", "classify", "--limit", "2"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Comando executado com sucesso!")
            # Verificar se gerou arquivo de saída
            output_files = list(Path(".").glob("resultados_classificacao_*.json"))
            if output_files:
                latest_file = max(output_files, key=os.path.getctime)
                print(f"   📁 Arquivo gerado: {latest_file}")
            return True
        else:
            print(f"❌ Comando falhou: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Comando demorou muito para executar")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False

def test_api_availability():
    """Testa se APIs estão funcionando"""
    print_header("TESTE DE DISPONIBILIDADE DAS APIS")
    
    # Verificar se há processos rodando nas portas
    try:
        # Testar API principal
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Principal (8000): Online")
            api_main = True
        else:
            print("⚠️  API Principal (8000): Offline")
            api_main = False
    except:
        print("⚠️  API Principal (8000): Offline")
        api_main = False
    
    try:
        # Testar API de revisão
        response = requests.get("http://localhost:8001/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Revisão (8001): Online")
            api_review = True
        else:
            print("⚠️  API Revisão (8001): Offline")
            api_review = False
    except:
        print("⚠️  API Revisão (8001): Offline")
        api_review = False
    
    if not api_main and not api_review:
        print("💡 Para iniciar APIs: python start_unified_system.py")
    
    return api_main or api_review

def run_complete_validation():
    """Executa validação completa"""
    print("🚀 VALIDAÇÃO COMPLETA DO SISTEMA SQLITE UNIFICADO")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'files': check_files(),
        'service': test_unified_service(),
        'classify': test_main_classify(),
        'commands': test_command_execution(),
        'apis': test_api_availability()
    }
    
    # Relatório final
    print_header("RELATÓRIO FINAL")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"📊 Resultados:")
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n🎯 Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 SISTEMA VALIDADO COM SUCESSO!")
        print("   Sistema SQLite unificado está 100% operacional")
        return 0
    elif passed_tests >= total_tests * 0.8:  # 80% dos testes
        print("⚠️  SISTEMA PARCIALMENTE VALIDADO")
        print("   Funcionalidades principais estão operacionais")
        return 0
    else:
        print("❌ SISTEMA COM PROBLEMAS")
        print("   Verifique os erros e execute correções necessárias")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_complete_validation()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏸️  Validação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro inesperado: {e}")
        sys.exit(1)
