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
from database.connection import engine, SessionLocal
from config import Config

class EnhancedSQLiteStorage:
    """Sistema de armazenamento SQLite aprimorado para centralizar todos os dados"""
    
    def __init__(self):
        self.config = Config()
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.session = None
        
    def initialize_database(self):
        """Inicializa o banco de dados SQLite com todas as tabelas"""
        print("🔧 Inicializando banco de dados SQLite aprimorado...")
        
        # Criar todas as tabelas
        try:
            UnifiedBase.metadata.create_all(bind=self.engine)
            print("✅ Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            return False
        
        # Obter sessão
        self.session = self.SessionLocal()
        
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
            
            # Converter DataFrame para lista de dicionários se necessário
            if hasattr(produtos, 'to_dict'):
                produtos_list = produtos.to_dict('records')
            else:
                produtos_list = produtos
            
            # Salvar produtos no SQLite como base de produtos
            count = 0
            for produto in produtos_list:
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
                            data_classificacao=datetime.now()
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
            return None
    
    def _save_agent_explanation(self, classificacao_id: int, produto_id: int, 
                               agent_name: str, trace_data: Dict, session_id: str):
        """Salva explicação detalhada de um agente"""
        try:
            # Extrair informações do trace
            result = trace_data.get('result', {})
            reasoning = trace_data.get('reasoning', '')
            
            explicacao = ExplicacaoAgente(
                produto_id=produto_id,
                classificacao_id=classificacao_id,
                agente_nome=agent_name,
                agente_versao="2.0",
                input_original=trace_data.get('input', ''),
                contexto_utilizado=trace_data.get('context', {}),
                resultado_agente=result,
                explicacao_detalhada=reasoning,
                nivel_confianca=result.get('confianca', 0.0) if isinstance(result, dict) else 0.0,
                tempo_processamento_ms=trace_data.get('tempo_ms', 0),
                data_execucao=datetime.now(),
                sessao_classificacao=session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            self.session.add(explicacao)
            
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar explicação do agente {agent_name}: {e}")
    
    def _save_agent_query(self, produto_id: int, consulta_data: Dict, session_id: str):
        """Salva consulta realizada por um agente"""
        try:
            consulta = ConsultaAgente(
                agente_nome=consulta_data.get('agente', 'UNKNOWN'),
                produto_id=produto_id,
                sessao_classificacao=session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                tipo_consulta=consulta_data.get('tipo_consulta', 'GENERIC'),
                query_original=consulta_data.get('query', ''),
                query_processada=consulta_data.get('query_processada'),
                parametros_busca=consulta_data.get('parametros', {}),
                total_resultados_encontrados=consulta_data.get('total_resultados', 0),
                resultados_utilizados=consulta_data.get('resultados', {}),
                tempo_consulta_ms=consulta_data.get('tempo_ms', 0),
                fonte_dados=consulta_data.get('fonte', 'UNKNOWN'),
                data_consulta=datetime.now(),
                consulta_bem_sucedida=consulta_data.get('sucesso', True),
                qualidade_resultados=consulta_data.get('qualidade', 1.0)
            )
            
            self.session.add(consulta)
            
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar consulta: {e}")
    
    def _save_expanded_description(self, classificacao_id: int, expansion_result: Dict):
        """Salva descrição enriquecida do Expansion Agent na classificação"""
        try:
            classificacao = self.session.query(ClassificacaoRevisao).get(classificacao_id)
            if classificacao:
                # Salvar dados enriquecidos nos campos específicos
                classificacao.explicacao_agente_expansao = expansion_result.get('descricao_expandida', '')
                
                # Extrair informações estruturadas
                if 'categoria_principal' in expansion_result:
                    classificacao.complexidade_produto = expansion_result['categoria_principal'][:20]
                
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar descrição enriquecida: {e}")
    
    def save_golden_set_entry(self, produto_data: Dict, validation_data: Dict, user: str):
        """Salva entrada no Golden Set validada pela interface web"""
        print(f"🏆 Adicionando ao Golden Set: {produto_data.get('descricao_produto', '')[:50]}...")
        
        try:
            golden_entry = GoldenSetEntry(
                produto_id=produto_data.get('produto_id', 0),
                descricao_produto=produto_data.get('descricao_produto', ''),
                descricao_completa=produto_data.get('descricao_completa'),
                codigo_produto=produto_data.get('codigo_produto'),
                gtin_validado=validation_data.get('gtin_final'),
                ncm_final=validation_data.get('ncm_final'),
                cest_final=validation_data.get('cest_final'),
                confianca_original=produto_data.get('confianca_consolidada', 0.0),
                fonte_validacao='HUMANA',
                justificativa_inclusao=validation_data.get('justificativa', ''),
                revisado_por=user,
                data_adicao=datetime.now(),
                qualidade_score=1.0,  # Máxima qualidade para validação humana
                ativo=True
            )
            
            self.session.add(golden_entry)
            self.session.commit()
            
            print(f"✅ Entrada adicionada ao Golden Set com ID {golden_entry.id}")
            return golden_entry.id
            
        except Exception as e:
            print(f"❌ Erro ao adicionar ao Golden Set: {e}")
            if self.session:
                self.session.rollback()
            return None
    
    def get_classification_statistics(self):
        """Retorna estatísticas das classificações armazenadas"""
        try:
            stats = {
                'total_classificacoes': self.session.query(ClassificacaoRevisao).count(),
                'pendentes_revisao': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='PENDENTE_REVISAO').count(),
                'aprovadas': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='APROVADA').count(),
                'corrigidas': self.session.query(ClassificacaoRevisao).filter_by(status_revisao='CORRIGIDA').count(),
                'total_explicacoes': self.session.query(ExplicacaoAgente).count(),
                'total_consultas': self.session.query(ConsultaAgente).count(),
                'total_golden_set': self.session.query(GoldenSetEntry).filter_by(ativo=True).count()
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def reset_database_for_new_extraction(self, empresa_id: str = None):
        """Reinicia o banco para nova extração (por empresa)"""
        print(f"🔄 Reiniciando banco de dados para nova extração (empresa: {empresa_id})...")
        
        try:
            # Limpar tabelas de dados variáveis
            self.session.query(ClassificacaoRevisao).delete()
            self.session.query(ExplicacaoAgente).delete()
            self.session.query(ConsultaAgente).delete()
            self.session.query(InteracaoWeb).delete()
            
            # Manter Golden Set e estruturas fixas (NCM, CEST)
            
            self.session.commit()
            
            print(f"✅ Banco reiniciado para nova extração")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao reiniciar banco: {e}")
            if self.session:
                self.session.rollback()
            return False
    
    def close(self):
        """Fecha conexão com o banco"""
        if self.session:
            self.session.close()


def main():
    """Função principal para testar o sistema"""
    print("🚀 Sistema de Armazenamento SQLite Aprimorado")
    print("=" * 60)
    
    storage = EnhancedSQLiteStorage()
    
    try:
        # Inicializar banco
        if not storage.initialize_database():
            print("❌ Falha na inicialização do banco")
            return
        
        # Importar dados do PostgreSQL
        imported = storage.import_postgresql_data(limit=20)
        print(f"📊 {imported} produtos importados")
        
        # Mostrar estatísticas
        stats = storage.get_classification_statistics()
        print("\n📈 Estatísticas do Banco:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
    
    finally:
        storage.close()


if __name__ == "__main__":
    main()
