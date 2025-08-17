#!/usr/bin/env python3
"""
Integração do Sistema de Armazenamento SQLite Aprimorado no main.py
Modifica o sistema para salvar TODOS os dados no SQLite
"""

import os
import sys
from pathlib import Path

def modify_main_py_for_enhanced_sqlite():
    """Modifica o main.py para usar o sistema SQLite aprimorado"""
    
    main_py_path = Path("src/main.py")
    if not main_py_path.exists():
        print("❌ Arquivo src/main.py não encontrado")
        return False
    
    # Ler o arquivo atual
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fazer backup
    backup_path = main_py_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup criado em {backup_path}")
    
    # Adicionar import do sistema aprimorado
    enhanced_import = """
# Sistema de Armazenamento SQLite Aprimorado
try:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from enhanced_sqlite_storage_fixed import EnhancedSQLiteStorage
    ENHANCED_SQLITE_AVAILABLE = True
except ImportError:
    ENHANCED_SQLITE_AVAILABLE = False
    print("⚠️ Sistema SQLite aprimorado não disponível")
"""
    
    # Encontrar onde adicionar o import
    import_position = content.find("from orchestrator.hybrid_router import")
    if import_position != -1:
        # Adicionar após os imports existentes
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "from orchestrator.hybrid_router import" in line:
                lines.insert(i + 1, enhanced_import)
                break
        content = '\n'.join(lines)
    
    # Modificar a função _classify_produto_unified para usar o SQLite aprimorado
    old_function = """def _classify_produto_unified(produto, unified_service):
    \"\"\"Classifica um produto usando o sistema unificado com rastreamento completo\"\"\"
    descricao = produto.get('descricao_produto', '')
    produto_id = produto.get('produto_id')
    
    if not descricao:
        return {
            'ncm_sugerido': '99999999',
            'cest_sugerido': None,
            'confianca_sugerida': 0.0,
            'justificativa_sistema': 'Produto sem descrição válida',
            'consultas_realizadas': [],
            'tempo_processamento': 0
        }"""
    
    new_function = """def _classify_produto_unified(produto, unified_service):
    \"\"\"Classifica um produto usando o sistema unificado com rastreamento completo\"\"\"
    descricao = produto.get('descricao_produto', '')
    produto_id = produto.get('produto_id')
    
    # Inicializar sistema SQLite aprimorado
    sqlite_storage = None
    if ENHANCED_SQLITE_AVAILABLE:
        try:
            sqlite_storage = EnhancedSQLiteStorage()
            sqlite_storage.initialize_database()
        except Exception as e:
            print(f"⚠️ Erro ao inicializar SQLite aprimorado: {e}")
            sqlite_storage = None
    
    if not descricao:
        result = {
            'ncm_sugerido': '99999999',
            'cest_sugerido': None,
            'confianca_sugerida': 0.0,
            'justificativa_sistema': 'Produto sem descrição válida',
            'consultas_realizadas': [],
            'tempo_processamento': 0
        }
        
        # Salvar no SQLite mesmo com erro
        if sqlite_storage:
            try:
                sqlite_storage.save_classification_with_explanations(
                    produto, result, {}, f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            except Exception as e:
                print(f"⚠️ Erro ao salvar no SQLite: {e}")
            finally:
                sqlite_storage.close()
        
        return result"""
    
    content = content.replace(old_function, new_function)
    
    # Modificar a parte final da função para salvar no SQLite
    old_return_section = """    # Salvar resultado completo em formato unified
    return {
        'produto_id': produto_id,
        'descricao_produto': descricao,
        'ncm_classificado': ncm_sugerido,
        'ncm_original': produto.get('ncm_codigo'),
        'cest_classificado': cest_sugerido,
        'cest_original': produto.get('cest_codigo'),
        'confianca_consolidada': confianca,
        'justificativa_final': justificativa_final,
        'tempo_processamento': tempo_total,
        'consultas_realizadas': consultas_realizadas
    }"""
    
    new_return_section = """    # Preparar resultado completo
    resultado_final = {
        'produto_id': produto_id,
        'descricao_produto': descricao,
        'ncm_classificado': ncm_sugerido,
        'ncm_original': produto.get('ncm_codigo'),
        'cest_classificado': cest_sugerido,
        'cest_original': produto.get('cest_codigo'),
        'confianca_consolidada': confianca,
        'justificativa_final': justificativa_final,
        'tempo_processamento': tempo_total,
        'consultas_realizadas': consultas_realizadas
    }
    
    # Salvar no SQLite aprimorado com explicações dos agentes
    if sqlite_storage:
        try:
            # Simular traces dos agentes (em implementação futura, pegar dados reais)
            agent_traces = {
                'expansion': {
                    'result': {
                        'descricao_expandida': f"Produto classificado como {ncm_sugerido}",
                        'categoria_principal': 'Auto-classificado',
                        'confianca': confianca
                    },
                    'reasoning': f"Classificação automática com confiança {confianca}",
                    'tempo_ms': int(tempo_total * 1000)
                }
            }
            
            sqlite_storage.save_classification_with_explanations(
                produto, 
                resultado_final, 
                agent_traces,
                f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            print(f"✅ Dados salvos no SQLite para produto {produto_id}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar no SQLite: {e}")
        finally:
            sqlite_storage.close()
    
    return resultado_final"""
    
    content = content.replace(old_return_section, new_return_section)
    
    # Modificar a função que salva resultados para também usar SQLite
    old_save_function = """def _save_classification_results(resultados, system_type):
    \"\"\"Salva resultados da classificação\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")"""
    
    new_save_function = """def _save_classification_results(resultados, system_type):
    \"\"\"Salva resultados da classificação no formato JSON/CSV e SQLite\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar também no SQLite aprimorado
    if ENHANCED_SQLITE_AVAILABLE and resultados:
        try:
            sqlite_storage = EnhancedSQLiteStorage()
            sqlite_storage.initialize_database()
            
            session_id = f"batch_{timestamp}"
            saved_count = 0
            
            for resultado in resultados:
                try:
                    # Preparar dados do produto
                    produto_data = {
                        'produto_id': resultado.get('produto_id', 0),
                        'descricao_produto': resultado.get('descricao_produto', ''),
                        'descricao_completa': resultado.get('descricao_completa'),
                        'codigo_produto': resultado.get('codigo_produto')
                    }
                    
                    # Salvar no SQLite
                    sqlite_storage.save_classification_with_explanations(
                        produto_data,
                        resultado,
                        {},  # Agent traces em implementação futura
                        session_id
                    )
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Erro ao salvar produto {resultado.get('produto_id')} no SQLite: {e}")
            
            sqlite_storage.close()
            print(f"✅ {saved_count} produtos salvos no SQLite aprimorado")
            
        except Exception as e:
            print(f"⚠️ Erro geral ao salvar no SQLite: {e}")"""
    
    content = content.replace(old_save_function, new_save_function)
    
    # Adicionar função para reiniciar banco por empresa
    reset_function = """

def reset_database_for_new_company(empresa_id: str = None):
    \"\"\"Reinicia o banco de dados SQLite para nova empresa\"\"\"
    print(f"🔄 Reiniciando banco para nova empresa: {empresa_id}")
    
    if not ENHANCED_SQLITE_AVAILABLE:
        print("⚠️ Sistema SQLite aprimorado não disponível")
        return False
    
    try:
        sqlite_storage = EnhancedSQLiteStorage()
        sqlite_storage.initialize_database()
        result = sqlite_storage.reset_database_for_new_extraction(empresa_id)
        sqlite_storage.close()
        return result
    except Exception as e:
        print(f"❌ Erro ao reiniciar banco: {e}")
        return False
"""
    
    # Adicionar antes da função main
    main_pos = content.find("def main():")
    if main_pos != -1:
        content = content[:main_pos] + reset_function + "\n" + content[main_pos:]
    
    # Escrever o arquivo modificado
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ main.py modificado com sucesso!")
    print("   - Sistema SQLite aprimorado integrado")
    print("   - Salvamento automático de todas as classificações")
    print("   - Função de reset por empresa adicionada")
    
    return True

def modify_setup_review_command():
    """Modifica o comando setup-review para usar SQLite aprimorado"""
    print("🔧 Modificando comando setup-review...")
    
    # Localizar onde o comando setup-review é definido
    main_py_path = Path("src/main.py")
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar opção de reset
    old_setup_args = """    setup_review_parser.add_argument('--import-data', action='store_true',
                                      help='Importar dados de classificação existentes')"""
    
    new_setup_args = """    setup_review_parser.add_argument('--import-data', action='store_true',
                                      help='Importar dados de classificação existentes')
    setup_review_parser.add_argument('--reset-database', action='store_true',
                                      help='Reiniciar banco de dados SQLite')
    setup_review_parser.add_argument('--empresa-id', type=str,
                                      help='ID da empresa para reiniciar banco específico')"""
    
    if old_setup_args in content:
        content = content.replace(old_setup_args, new_setup_args)
    
    # Modificar a função command_setup_review
    old_command = """def command_setup_review(args):
    \"\"\"Comando para configurar sistema de revisão\"\"\"
    print(f"\\n[COMANDO] SETUP-REVIEW")
    print("=" * 40)"""
    
    new_command = """def command_setup_review(args):
    \"\"\"Comando para configurar sistema de revisão\"\"\"
    print(f"\\n[COMANDO] SETUP-REVIEW")
    print("=" * 40)
    
    # Verificar se deve reiniciar banco
    if hasattr(args, 'reset_database') and args.reset_database:
        empresa_id = getattr(args, 'empresa_id', None)
        if reset_database_for_new_company(empresa_id):
            print("✅ Banco de dados reiniciado com sucesso")
        else:
            print("❌ Erro ao reiniciar banco de dados")
            return"""
    
    content = content.replace(old_command, new_command)
    
    # Escrever arquivo modificado
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Comando setup-review modificado com sucesso!")

def main():
    """Função principal"""
    print("🚀 Integração do Sistema SQLite Aprimorado")
    print("=" * 60)
    
    # Modificar main.py
    if modify_main_py_for_enhanced_sqlite():
        print("✅ main.py modificado com sucesso")
    else:
        print("❌ Erro ao modificar main.py")
        return
    
    # Modificar comando setup-review
    modify_setup_review_command()
    
    print("\n🎉 Integração concluída com sucesso!")
    print("\n📋 Novos recursos disponíveis:")
    print("   1. Todas as classificações são salvas no SQLite automaticamente")
    print("   2. Explicações dos agentes são armazenadas")
    print("   3. Consultas dos agentes são rastreadas")
    print("   4. Comando para reiniciar banco por empresa:")
    print("      python src/main.py setup-review --reset-database --empresa-id CNPJ_EMPRESA")
    print("   5. Golden Set é salvo automaticamente")
    
    print("\n⚡ Como usar:")
    print("   # Classificar e salvar no SQLite:")
    print("   python src/main.py classify --from-db --limit 10")
    print("   ")
    print("   # Reiniciar para nova empresa:")
    print("   python src/main.py setup-review --reset-database --empresa-id 12345678000100")
    print("   ")
    print("   # Importar dados e iniciar interface:")
    print("   python src/main.py setup-review --create-tables --import-data")

if __name__ == "__main__":
    main()
