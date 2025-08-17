#!/usr/bin/env python3
"""
Sistema de Armazenamento SQLite Aprimorado
Centraliza TODOS os dados no SQLite incluindo:
- Dados do PostgreSQL
- Classificações dos agentes
- Descrições enriquecidas
- Explicações detalhadas
- Consultas dos agentes
- Golden Set da interface web
"""

import os
import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.unified_sqlite_models import (
    UnifiedBase, ClassificacaoRevisao, ExplicacaoAgente, 
    ConsultaAgente, GoldenSetEntry, EmbeddingProduto,
    ABCFarmaProduct, NCMHierarchy, CestCategory,
    InteracaoWeb, CorrecaoIdentificada
)
from database.connection import UnifiedSQLiteManager
from config import Config

class EnhancedSQLiteStorage:
    """Sistema de armazenamento SQLite aprimorado para centralizar todos os dados"""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = UnifiedSQLiteManager()
        self.session = None
        
    def initialize_database(self):
        """Inicializa o banco de dados SQLite com todas as tabelas"""
        print("🔧 Inicializando banco de dados SQLite aprimorado...")
        
        # Criar todas as tabelas
        self.db_manager.create_all_tables()
        
        # Obter sessão
        self.session = self.db_manager.get_session()
        
        print("✅ Banco de dados SQLite inicializado com sucesso!")
        return True
    
    def import_postgresql_data(self, limit: int = None):
        """Importa dados do PostgreSQL para o SQLite"""
        print(f"📥 Importando dados do PostgreSQL para SQLite (limit={limit})...")
        
        try:
            # Importar via data_loader
            from ingestion.data_loader import DataLoader
            data_loader = DataLoader()
            
            # Carregar produtos do PostgreSQL
            produtos = data_loader.load_produtos_from_db(limit=limit)
            print(f"   📊 {len(produtos)} produtos carregados do PostgreSQL")
            
            # Salvar produtos no SQLite como base de produtos
            count = 0
            for produto in produtos:
                try:
                    # Verificar se produto já existe
                    existing = self.session.query(ClassificacaoRevisao).filter_by(
                        produto_id=produto.get('produto_id', 0)
                    ).first()
                    
                    if not existing:
                        # Criar nova classificação
                        classificacao = ClassificacaoRevisao(
                            produto_id=produto.get('produto_id', 0),
                            descricao_produto=produto.get('descricao_produto', ''),
                            descricao_completa=produto.get('descricao_completa'),
                            codigo_produto=produto.get('codigo_produto'),
                            codigo_barra=produto.get('codigo_barra'),
                            gtin_original=produto.get('gtin'),
                            status_revisao='PENDENTE_REVISAO',
                            data_classificacao=datetime.now(),
                            fonte_dados='POSTGRESQL'
                        )
                        
                        self.session.add(classificacao)
                        count += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Erro ao importar produto {produto.get('produto_id')}: {e}")
                    continue
            
            # Commit das mudanças
            self.session.commit()
            print(f"✅ {count} produtos importados do PostgreSQL para SQLite")
            
            return count
            
        except Exception as e:
            print(f"❌ Erro ao importar dados do PostgreSQL: {e}")
            if self.session:
                self.session.rollback()
            return 0
    
    def save_classification_with_explanations(self, produto: Dict, resultado_classificacao: Dict, 
                                            agent_traces: Dict, session_id: str = None):
        """Salva classificação completa com todas as explicações dos agentes"""
        print(f"💾 Salvando classificação completa para produto {produto.get('produto_id', 'N/A')}...")
        
        try:
            # 1. Salvar/atualizar classificação principal
            classificacao = self.session.query(ClassificacaoRevisao).filter_by(
                produto_id=produto.get('produto_id', 0)
            ).first()
            
            if not classificacao:
                classificacao = ClassificacaoRevisao(
                    produto_id=produto.get('produto_id', 0),
                    descricao_produto=produto.get('descricao_produto', ''),
                    status_revisao='PENDENTE_REVISAO'
                )
                self.session.add(classificacao)
                self.session.flush()  # Para obter o ID
            
            # Atualizar com resultados da classificação
            classificacao.ncm_sugerido = resultado_classificacao.get('ncm_classificado')
            classificacao.cest_sugerido = resultado_classificacao.get('cest_classificado')
            classificacao.confianca_sugerida = resultado_classificacao.get('confianca_consolidada')
            classificacao.justificativa_sistema = resultado_classificacao.get('justificativa_final')
            classificacao.dados_trace_json = agent_traces
            classificacao.data_classificacao = datetime.now()
            
            # 2. Salvar explicações de cada agente
            if agent_traces:
                for agent_name, trace_data in agent_traces.items():
                    if trace_data and isinstance(trace_data, dict):
                        self._save_agent_explanation(
                            classificacao.id,
                            produto.get('produto_id', 0),
                            agent_name,
                            trace_data,
                            session_id
                        )
            
            # 3. Salvar consultas realizadas pelos agentes
            consultas = resultado_classificacao.get('consultas_realizadas', [])
            for consulta in consultas:
                if isinstance(consulta, dict):
                    self._save_agent_query(
                        produto.get('produto_id', 0),
                        consulta,
                        session_id
                    )
            
            # 4. Salvar descrição enriquecida do Expansion Agent
            expansion_result = agent_traces.get('expansion', {}).get('result', {}) if agent_traces else {}
            if expansion_result and isinstance(expansion_result, dict):
                self._save_expanded_description(classificacao.id, expansion_result)
            
            # Commit das mudanças
            self.session.commit()
            
            print(f"✅ Classificação completa salva para produto {produto.get('produto_id')}")
            return classificacao.id
            
        except Exception as e:
            print(f"❌ Erro ao salvar classificação completa: {e}")
            if self.session:
                self.session.rollback()
            return None\n    \n    def _save_agent_explanation(self, classificacao_id: int, produto_id: int, \n                               agent_name: str, trace_data: Dict, session_id: str):\n        \"\"\"Salva explicação detalhada de um agente\"\"\"\n        try:\n            # Extrair informações do trace\n            result = trace_data.get('result', {})\n            reasoning = trace_data.get('reasoning', '')\n            \n            explicacao = ExplicacaoAgente(\n                produto_id=produto_id,\n                classificacao_id=classificacao_id,\n                agente_nome=agent_name,\n                agente_versao=\"2.0\",\n                input_original=trace_data.get('input', ''),\n                contexto_utilizado=trace_data.get('context', {}),\n                resultado_agente=result,\n                explicacao_detalhada=reasoning,\n                nivel_confianca=result.get('confianca', 0.0) if isinstance(result, dict) else 0.0,\n                tempo_processamento_ms=trace_data.get('tempo_ms', 0),\n                data_execucao=datetime.now(),\n                sessao_classificacao=session_id or f\"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}\"\n            )\n            \n            self.session.add(explicacao)\n            \n        except Exception as e:\n            print(f\"   ⚠️ Erro ao salvar explicação do agente {agent_name}: {e}\")\n    \n    def _save_agent_query(self, produto_id: int, consulta_data: Dict, session_id: str):\n        \"\"\"Salva consulta realizada por um agente\"\"\"\n        try:\n            consulta = ConsultaAgente(\n                agente_nome=consulta_data.get('agente', 'UNKNOWN'),\n                produto_id=produto_id,\n                sessao_classificacao=session_id or f\"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}\",\n                tipo_consulta=consulta_data.get('tipo_consulta', 'GENERIC'),\n                query_original=consulta_data.get('query', ''),\n                query_processada=consulta_data.get('query_processada'),\n                parametros_busca=consulta_data.get('parametros', {}),\n                total_resultados_encontrados=consulta_data.get('total_resultados', 0),\n                resultados_utilizados=consulta_data.get('resultados', {}),\n                tempo_consulta_ms=consulta_data.get('tempo_ms', 0),\n                fonte_dados=consulta_data.get('fonte', 'UNKNOWN'),\n                data_consulta=datetime.now(),\n                consulta_bem_sucedida=consulta_data.get('sucesso', True),\n                qualidade_resultados=consulta_data.get('qualidade', 1.0)\n            )\n            \n            self.session.add(consulta)\n            \n        except Exception as e:\n            print(f\"   ⚠️ Erro ao salvar consulta: {e}\")\n    \n    def _save_expanded_description(self, classificacao_id: int, expansion_result: Dict):\n        \"\"\"Salva descrição enriquecida do Expansion Agent na classificação\"\"\"\n        try:\n            classificacao = self.session.query(ClassificacaoRevisao).get(classificacao_id)\n            if classificacao:\n                # Salvar dados enriquecidos nos campos específicos\n                classificacao.explicacao_agente_expansao = expansion_result.get('descricao_expandida', '')\n                \n                # Extrair informações estruturadas\n                if 'categoria_principal' in expansion_result:\n                    classificacao.categoria_produto = expansion_result['categoria_principal']\n                \n                if 'material_predominante' in expansion_result:\n                    classificacao.material_predominante = expansion_result['material_predominante']\n                \n                if 'caracteristicas_tecnicas' in expansion_result:\n                    classificacao.caracteristicas_tecnicas = ', '.join(expansion_result['caracteristicas_tecnicas'])\n                \n                if 'aplicacoes_uso' in expansion_result:\n                    classificacao.aplicacoes_uso = ', '.join(expansion_result['aplicacoes_uso'])\n                \n                if 'palavras_chave_fiscais' in expansion_result:\n                    classificacao.palavras_chave_fiscais = ', '.join(expansion_result['palavras_chave_fiscais'])\n                \n        except Exception as e:\n            print(f\"   ⚠️ Erro ao salvar descrição enriquecida: {e}\")\n    \n    def save_golden_set_entry(self, produto_data: Dict, validation_data: Dict, user: str):\n        \"\"\"Salva entrada no Golden Set validada pela interface web\"\"\"\n        print(f\"🏆 Adicionando ao Golden Set: {produto_data.get('descricao_produto', '')[:50]}...\")\n        \n        try:\n            golden_entry = GoldenSetEntry(\n                produto_id=produto_data.get('produto_id', 0),\n                descricao_produto=produto_data.get('descricao_produto', ''),\n                descricao_completa=produto_data.get('descricao_completa'),\n                codigo_produto=produto_data.get('codigo_produto'),\n                gtin_validado=validation_data.get('gtin_final'),\n                ncm_final=validation_data.get('ncm_final'),\n                cest_final=validation_data.get('cest_final'),\n                confianca_original=produto_data.get('confianca_consolidada', 0.0),\n                fonte_validacao='HUMANA',\n                justificativa_inclusao=validation_data.get('justificativa', ''),\n                revisado_por=user,\n                data_adicao=datetime.now(),\n                qualidade_score=1.0,  # Máxima qualidade para validação humana\n                ativo=True\n            )\n            \n            self.session.add(golden_entry)\n            self.session.commit()\n            \n            print(f\"✅ Entrada adicionada ao Golden Set com ID {golden_entry.id}\")\n            return golden_entry.id\n            \n        except Exception as e:\n            print(f\"❌ Erro ao adicionar ao Golden Set: {e}\")\n            if self.session:\n                self.session.rollback()\n            return None\n    \n    def get_classification_statistics(self):\n        \"\"\"Retorna estatísticas das classificações armazenadas\"\"\"\n        try:\n            stats = {\n                'total_classificacoes': self.session.query(ClassificacaoRevisao).count(),\n                'pendentes_revisao': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='PENDENTE_REVISAO').count(),\n                'aprovadas': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='APROVADA').count(),\n                'corrigidas': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='CORRIGIDA').count(),\n                'total_explicacoes': self.session.query(ExplicacaoAgente).count(),\n                'total_consultas': self.session.query(ConsultaAgente).count(),\n                'total_golden_set': self.session.query(GoldenSetEntry).filter_by(ativo=True).count()\n            }\n            \n            return stats\n            \n        except Exception as e:\n            print(f\"❌ Erro ao obter estatísticas: {e}\")\n            return {}\n    \n    def reset_database_for_new_extraction(self, empresa_id: str = None):\n        \"\"\"Reinicia o banco para nova extração (por empresa)\"\"\"\n        print(f\"🔄 Reiniciando banco de dados para nova extração (empresa: {empresa_id})...\")\n        \n        try:\n            # Limpar tabelas de dados variáveis\n            self.session.query(ClassificacaoRevisao).delete()\n            self.session.query(ExplicacaoAgente).delete()\n            self.session.query(ConsultaAgente).delete()\n            self.session.query(InteracaoWeb).delete()\n            \n            # Manter Golden Set e estruturas fixas (NCM, CEST)\n            \n            self.session.commit()\n            \n            print(f\"✅ Banco reiniciado para nova extração\")\n            return True\n            \n        except Exception as e:\n            print(f\"❌ Erro ao reiniciar banco: {e}\")\n            if self.session:\n                self.session.rollback()\n            return False\n    \n    def close(self):\n        \"\"\"Fecha conexão com o banco\"\"\"\n        if self.session:\n            self.session.close()\n\n\ndef main():\n    \"\"\"Função principal para testar o sistema\"\"\"\n    print(\"🚀 Sistema de Armazenamento SQLite Aprimorado\")\n    print(\"=\" * 60)\n    \n    storage = EnhancedSQLiteStorage()\n    \n    try:\n        # Inicializar banco\n        if not storage.initialize_database():\n            print(\"❌ Falha na inicialização do banco\")\n            return\n        \n        # Importar dados do PostgreSQL\n        imported = storage.import_postgresql_data(limit=20)\n        print(f\"📊 {imported} produtos importados\")\n        \n        # Mostrar estatísticas\n        stats = storage.get_classification_statistics()\n        print(\"\\n📈 Estatísticas do Banco:\")\n        for key, value in stats.items():\n            print(f\"   {key}: {value}\")\n        \n    except Exception as e:\n        print(f\"❌ Erro na execução: {e}\")\n    \n    finally:\n        storage.close()\n\n\nif __name__ == \"__main__\":\n    main()\n
