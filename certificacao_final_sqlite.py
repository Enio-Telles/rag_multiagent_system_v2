#!/usr/bin/env python3
"""
CERTIFICAÇÃO FINAL DA INTEGRAÇÃO SQLITE COM MAIN.PY
"""

def test_final_certification():
    """Teste final de certificação"""
    
    print("=" * 60)
    print("CERTIFICACAO FINAL - INTEGRACAO SQLITE")
    print("=" * 60)
    
    # 1. Verificar se main.py classify funciona com SQLite
    print("\n1. TESTE COMANDO CLASSIFY --FROM-DB")
    
    import subprocess
    import os
    
    try:
        result = subprocess.run(
            ["python", "src/main.py", "classify", "--from-db", "--limit", "2"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd(),
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Verificar indicadores de sucesso
            checks = [
                ("Sistema Unificado SQLite", "Usando sistema SQLite"),
                ("sistema: unified_sqlite", "Salvando com tag SQLite"),
                ("NCM:", "NCM classificado"),
                ("CEST:", "CEST classificado"),
                ("Confiança:", "Confiança calculada")
            ]
            
            success_count = 0
            for check, description in checks:
                if check in output:
                    print(f"   OK: {description}")
                    success_count += 1
                else:
                    print(f"   FALHA: {description}")
            
            if success_count >= 4:
                print("   RESULTADO: COMANDO FUNCIONANDO COM SQLITE")
            else:
                print("   RESULTADO: COMANDO COM PROBLEMAS")
                return False
        else:
            print(f"   ERRO: Comando falhou - {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    # 2. Verificar arquivos de saída
    print("\n2. VERIFICAR ARQUIVOS DE SAIDA")
    
    import glob
    
    json_files = glob.glob("resultados_classificacao_unified_*.json")
    csv_files = glob.glob("resultados_classificacao_unified_*.csv")
    
    if json_files and csv_files:
        latest_json = max(json_files, key=os.path.getctime)
        latest_csv = max(csv_files, key=os.path.getctime)
        
        print(f"   OK: JSON criado - {latest_json}")
        print(f"   OK: CSV criado - {latest_csv}")
        
        # Verificar conteúdo do JSON
        try:
            import json
            with open(latest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('sistema') == 'unified' and data.get('total_produtos', 0) > 0:
                print(f"   OK: JSON válido com {data['total_produtos']} produtos")
            else:
                print("   FALHA: JSON inválido")
                return False
                
        except Exception as e:
            print(f"   ERRO: Não foi possível ler JSON - {e}")
            return False
    else:
        print("   FALHA: Arquivos de saída não encontrados")
        return False
    
    # 3. Verificar base de dados SQLite
    print("\n3. VERIFICAR BASE SQLITE")
    
    try:
        import sys
        sys.path.append('src')
        from services.unified_sqlite_service import get_unified_service
        
        service = get_unified_service()
        stats = service.get_dashboard_stats()
        
        print(f"   OK: NCMs: {stats['total_ncms']:,}")
        print(f"   OK: CESTs: {stats['total_cests']:,}")
        print(f"   OK: Classificações: {stats['total_classificacoes']:,}")
        
        if stats['total_ncms'] > 10000 and stats['total_cests'] > 1000:
            print("   OK: Base de dados populada")
        else:
            print("   FALHA: Base de dados incompleta")
            return False
            
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("CERTIFICACAO CONCLUIDA COM SUCESSO!")
    print("SISTEMA MAIN.PY CLASSIFY --FROM-DB INTEGRADO COM SQLITE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_final_certification()
    exit(0 if success else 1)
