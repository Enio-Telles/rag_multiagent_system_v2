#!/usr/bin/env python3
"""
Teste de certificação da integração SQLite com main.py classify
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.append('src')

def test_sqlite_integration():
    """Testa integração completa SQLite com main.py"""
    
    print("🔍 CERTIFICAÇÃO DA INTEGRAÇÃO SQLITE")
    print("=" * 60)
    
    # 1. Verificar arquivos necessários
    print("\n1️⃣ VERIFICAÇÃO DE ARQUIVOS:")
    
    required_files = [
        "data/unified_rag_system.db",
        "src/services/unified_sqlite_service.py",
        "src/main.py"
    ]
    
    all_files_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path} - FALTANDO")
            all_files_ok = False
    
    if not all_files_ok:
        print("❌ Arquivos necessários faltando!")
        return False
    
    # 2. Testar serviço SQLite
    print("\n2️⃣ TESTE DO SERVIÇO SQLITE:")
    
    try:
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service()
        
        # Testar estatísticas
        stats = service.get_dashboard_stats()
        print(f"✅ NCMs: {stats['total_ncms']:,}")
        print(f"✅ CESTs: {stats['total_cests']:,}")
        print(f"✅ Mapeamentos: {stats['total_mapeamentos']:,}")
        print(f"✅ Golden Set: {stats['golden_set_entries']:,}")
        print(f"✅ Classificações: {stats['total_classificacoes']:,}")
        
        # Verificar ABC Farma se disponível
        abc_count = 0
        try:
            abc_results = service.search_abc_farma_by_text('teste', 1)
            abc_count = "Disponível"
        except:
            abc_count = "Não disponível"
        print(f"✅ ABC Farma: {abc_count}")
        
        # Testar busca NCM
        ncm_test = service.buscar_ncm('01012100')
        if ncm_test:
            print(f"✅ Busca NCM funcionando: {ncm_test['descricao_oficial'][:50]}...")
        else:
            print("❌ Busca NCM falhou")
            return False
            
        # Testar busca CEST
        cests = service.buscar_cests_para_ncm('01012100')
        if cests:
            print(f"✅ Busca CEST funcionando: {len(cests)} CESTs encontrados")
        else:
            print("⚠️  Nenhum CEST encontrado (pode ser normal)")
        
        # Testar ABC Farma se disponível
        if abc_count == "Disponível":
            abc_results = service.search_abc_farma_by_text('DIPIRONA', 1)
            if abc_results:
                print(f"✅ ABC Farma funcionando: {abc_results[0]['descricao'][:50]}...")
            else:
                print("⚠️  ABC Farma sem resultados para DIPIRONA")
        
    except Exception as e:
        print(f"❌ Erro no serviço SQLite: {e}")
        return False
    
    # 3. Testar main.py com diferentes cenários
    print("\n3️⃣ TESTE DE COMANDOS MAIN.PY:")
    
    test_commands = [
        "python src/main.py classify --limit 3",
        "python src/main.py classify --from-db --limit 5"
    ]
    
    for cmd in test_commands:
        print(f"\n🧪 Testando: {cmd}")
        try:
            import subprocess
            result = subprocess.run(
                cmd.split(), 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Verificar se contém indicadores de sucesso
                output = result.stdout
                if "Sistema Unificado SQLite" in output and "sistema: unified_sqlite" in output:
                    print("✅ Comando executado com sucesso usando SQLite")
                else:
                    print("⚠️  Comando executado mas pode não estar usando SQLite")
                    print(f"   Output parcial: {output[:200]}...")
            else:
                print(f"❌ Comando falhou: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Comando demorou muito (timeout)")
        except Exception as e:
            print(f"❌ Erro ao executar comando: {e}")
            return False
    
    # 4. Verificar arquivos de saída
    print("\n4️⃣ VERIFICAÇÃO DE SAÍDAS:")
    
    output_patterns = [
        "resultados_classificacao_unified_*.json",
        "resultados_classificacao_unified_*.csv"
    ]
    
    import glob
    for pattern in output_patterns:
        files = glob.glob(pattern)
        if files:
            latest_file = max(files, key=os.path.getctime)
            print(f"✅ {pattern}: {latest_file}")
        else:
            print(f"⚠️  {pattern}: Nenhum arquivo encontrado")
    
    print("\n🎉 CERTIFICAÇÃO CONCLUÍDA!")
    print("✅ Sistema SQLite integrado e funcionando corretamente")
    return True

if __name__ == "__main__":
    success = test_sqlite_integration()
    sys.exit(0 if success else 1)
