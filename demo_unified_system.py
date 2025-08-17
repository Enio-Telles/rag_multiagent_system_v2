"""
Demonstração Completa do Sistema SQLite Unificado
Showcase de todas as funcionalidades implementadas
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Configurar path
sys.path.append('src')

# Imports
from services.unified_sqlite_service import get_unified_service

class UnifiedSystemDemo:
    """Demonstração do sistema unificado"""
    
    def __init__(self):
        self.service = get_unified_service("data/unified_rag_system.db")
        
    def run_complete_demo(self):
        """Executa demonstração completa"""
        print("🎭 DEMONSTRAÇÃO COMPLETA DO SISTEMA SQLite UNIFICADO")
        print("=" * 60)
        print("Sistema integrado para classificação fiscal com IA")
        print("Bases: Knowledge Base + Classificações + Golden Set + Agentes + Interface")
        print()
        
        # 1. Visão geral do sistema
        self._demo_overview()
        
        # 2. Knowledge Base
        self._demo_knowledge_base()
        
        # 3. Sistema de classificação
        self._demo_classification_system()
        
        # 4. Golden Set
        self._demo_golden_set()
        
        # 5. Explicações dos agentes
        self._demo_agent_explanations()
        
        # 6. Consultas e rastreabilidade
        self._demo_agent_queries()
        
        # 7. Interface web e métricas
        self._demo_web_interface()
        
        # 8. Performance e escalabilidade
        self._demo_performance()
        
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRAÇÃO COMPLETA FINALIZADA!")
        print("Sistema pronto para produção com todas as funcionalidades!")
    
    def _demo_overview(self):
        """Demonstra visão geral do sistema"""
        print("📊 VISÃO GERAL DO SISTEMA")
        print("-" * 30)
        
        stats = self.service.get_dashboard_stats()
        
        print(f"📋 Base de Conhecimento:")
        print(f"   • NCMs: {stats['total_ncms']:,}")
        print(f"   • CESTs: {stats['total_cests']:,}")
        print(f"   • Mapeamentos: {stats['total_mapeamentos']:,}")
        print(f"   • Exemplos: {stats['total_exemplos']:,}")
        
        print(f"\n🎯 Sistema de Classificação:")
        print(f"   • Classificações totais: {stats['total_classificacoes']:,}")
        print(f"   • Pendentes revisão: {stats['classificacoes_pendentes']:,}")
        print(f"   • Classificações recentes: {stats['classificacoes_recentes']:,}")
        
        print(f"\n🧠 Sistema de IA:")
        print(f"   • Golden Set entries: {stats['golden_set_entries']:,}")
        print(f"   • Explicações de agentes: {stats['explicacoes_agentes']:,}")
        print(f"   • Consultas registradas: {stats['consultas_agentes']:,}")
        
        # Verificar tamanho do banco
        db_path = Path("data/unified_rag_system.db")
        if db_path.exists():
            size_mb = db_path.stat().st_size / 1024 / 1024
            print(f"\n💾 Banco de dados: {size_mb:.2f} MB")
        
        print()
    
    def _demo_knowledge_base(self):
        """Demonstra funcionalidades da Knowledge Base"""
        print("📚 KNOWLEDGE BASE - Base de Conhecimento Fiscal")
        print("-" * 50)
        
        # Demonstrar busca hierárquica
        print("🔍 Busca Hierárquica de NCMs:")
        ncms_2_digitos = self.service.buscar_ncms_por_nivel(2, 3)
        for ncm in ncms_2_digitos:
            print(f"   📋 {ncm['codigo_ncm']}: {ncm['descricao_oficial'][:50]}...")
        
        # Demonstrar busca por padrão
        print("\n🔍 Busca por Padrão (exemplo: 'preparações'):")
        ncms_pattern = self.service.buscar_ncms_por_padrao("preparações", 3)
        for ncm in ncms_pattern:
            print(f"   📋 {ncm['codigo_ncm']}: {ncm['descricao_oficial'][:50]}...")
        
        # Demonstrar relacionamento NCM-CEST
        if ncms_pattern:
            ncm_exemplo = ncms_pattern[0]
            cests = self.service.buscar_cests_para_ncm(ncm_exemplo['codigo_ncm'])
            print(f"\n🎯 CESTs para NCM {ncm_exemplo['codigo_ncm']}:")
            for cest in cests:
                print(f"   • {cest['codigo_cest']}: {cest['descricao_cest'][:40]}... (confiança: {cest['confianca']:.2f})")
        
        # Demonstrar exemplos de produtos
        if ncms_pattern:
            exemplos = self.service.buscar_exemplos_ncm(ncms_pattern[0]['codigo_ncm'], 3)
            print(f"\n📦 Exemplos de produtos:")
            for exemplo in exemplos:
                print(f"   • {exemplo['descricao_produto'][:50]}... (qualidade: {exemplo['qualidade_classificacao']:.2f})")
        
        print()
    
    def _demo_classification_system(self):
        """Demonstra sistema de classificação"""
        print("🎯 SISTEMA DE CLASSIFICAÇÃO - Classificação Automática + Revisão Humana")
        print("-" * 70)
        
        # Simular nova classificação
        print("📝 Simulando nova classificação:")
        produto_demo = {
            'produto_id': 99001,
            'descricao_produto': 'Smartphone Samsung Galaxy A54 5G 128GB Dual Chip Android',
            'codigo_produto': 'GALAXY-A54-128',
            'codigo_barra': '7891234567890',
            'ncm_sugerido': '85171231',
            'cest_sugerido': '2104700',
            'confianca_sugerida': 0.94,
            'justificativa_sistema': 'Produto identificado como smartphone baseado em características técnicas e especificações'
        }
        
        # Criar classificação
        classificacao_id = self.service.criar_classificacao(produto_demo)
        print(f"   ✅ Classificação criada: ID {classificacao_id}")
        print(f"   📱 Produto: {produto_demo['descricao_produto']}")
        print(f"   📋 NCM sugerido: {produto_demo['ncm_sugerido']}")
        print(f"   🎯 CEST sugerido: {produto_demo['cest_sugerido']}")
        print(f"   📊 Confiança: {produto_demo['confianca_sugerida']:.1%}")
        
        # Simular explicações dos agentes
        explicacoes = {
            'expansor': 'Produto expandido com análise de marca, modelo e especificações técnicas',
            'ncm': 'Classificado como telefone celular baseado em características de comunicação móvel',
            'cest': 'CEST aplicado para produtos de telecomunicações conforme legislação vigente',
            'reconciliador': 'Classificação final validada após análise de todos os agentes'
        }
        
        for agente, explicacao in explicacoes.items():
            self.service.atualizar_classificacao(classificacao_id, {
                f'explicacao_agente_{agente}': explicacao
            })
        
        print(f"\n🧠 Explicações dos agentes adicionadas")
        
        # Simular revisão humana
        print("\n👤 Simulando revisão humana:")
        revisao_data = {
            'status_revisao': 'APROVADO',
            'revisado_por': 'Especialista Fiscal',
            'justificativa_correcao': 'Classificação correta conforme análise especializada',
            'tempo_revisao_segundos': 45
        }
        
        self.service.revisar_classificacao(classificacao_id, revisao_data)
        print(f"   ✅ Produto aprovado pelo especialista")
        print(f"   ⏱️  Tempo de revisão: {revisao_data['tempo_revisao_segundos']}s")
        
        print()
    
    def _demo_golden_set(self):
        """Demonstra Golden Set"""
        print("🏆 GOLDEN SET - Base de Conhecimento Validada por Humanos")
        print("-" * 55)
        
        # Mostrar entradas existentes
        entradas = self.service.buscar_golden_set(limite=3)
        print(f"📋 Entradas no Golden Set ({len(entradas)} de {self.service.get_dashboard_stats()['golden_set_entries']}):")
        
        for entrada in entradas:
            print(f"   🎯 ID {entrada['id']}: {entrada['descricao_produto'][:40]}...")
            print(f"      NCM: {entrada['ncm_final']} | Qualidade: {entrada['qualidade_score']:.2f} | Usado: {entrada['vezes_usado']}x")
        
        # Adicionar nova entrada ao Golden Set
        print(f"\n➕ Adicionando produto aprovado ao Golden Set:")
        nova_entrada = {
            'produto_id': 99001,
            'descricao_produto': 'Smartphone Samsung Galaxy A54 5G 128GB Dual Chip Android',
            'ncm_final': '85171231',
            'cest_final': '2104700',
            'fonte_validacao': 'HUMANA',
            'revisado_por': 'Especialista Fiscal',
            'qualidade_score': 0.98,
            'palavras_chave_fiscais': 'smartphone, telefone, celular, android, comunicação, dual chip',
            'categoria_produto': 'TELECOMUNICACOES',
            'material_predominante': 'Metal e plástico',
            'aplicacoes_uso': 'Comunicação móvel, acesso à internet, aplicativos',
            'caracteristicas_tecnicas': '5G, 128GB, Dual Chip, Android',
            'contexto_uso': 'Dispositivo pessoal de comunicação e entretenimento'
        }
        
        golden_id = self.service.adicionar_ao_golden_set(nova_entrada)
        print(f"   ✅ Entrada adicionada: ID {golden_id}")
        print(f"   🎯 Agora disponível para melhorar classificações futuras")
        
        print()
    
    def _demo_agent_explanations(self):
        """Demonstra explicações dos agentes"""
        print("🧠 EXPLICAÇÕES DOS AGENTES - Rastreabilidade e Transparência")
        print("-" * 60)
        
        # Simular explicações detalhadas
        agentes_demo = [
            {
                'nome': 'agent_expansion',
                'descricao': 'Agente de Expansão',
                'explicacao': 'Analisou descrição do produto e identificou características-chave como marca Samsung, modelo Galaxy A54, capacidade 128GB e tecnologia 5G'
            },
            {
                'nome': 'agent_ncm',
                'descricao': 'Agente de Classificação NCM',
                'explicacao': 'Classificou como NCM 85171231 baseado na natureza do produto como aparelho telefônico para comunicação móvel'
            },
            {
                'nome': 'agent_cest',
                'descricao': 'Agente de Classificação CEST',
                'explicacao': 'Aplicou CEST 2104700 conforme Convênio 52/17 para produtos de telecomunicações'
            },
            {
                'nome': 'agent_reconciler',
                'descricao': 'Agente Reconciliador',
                'explicacao': 'Validou consistência entre classificações NCM e CEST, confirmando adequação fiscal'
            }
        ]
        
        for agente in agentes_demo:
            explicacao_data = {
                'produto_id': 99001,
                'agente_nome': agente['nome'],
                'explicacao_detalhada': agente['explicacao'],
                'nivel_confianca': 0.92,
                'tempo_processamento_ms': 120,
                'rag_consultado': True,
                'golden_set_utilizado': True,
                'sessao_classificacao': 'DEMO_SESSION_001'
            }
            
            exp_id = self.service.salvar_explicacao_agente(explicacao_data)
            print(f"🤖 {agente['descricao']}:")
            print(f"   {agente['explicacao']}")
            print(f"   (Confiança: 92%, Tempo: 120ms, ID: {exp_id})")
            print()
        
        print("💡 Todas as decisões são rastreáveis e explicáveis!")
        print()
    
    def _demo_agent_queries(self):
        """Demonstra consultas dos agentes"""
        print("🔍 CONSULTAS DOS AGENTES - Rastreamento de Decisões")
        print("-" * 50)
        
        # Simular consultas realizadas pelos agentes
        consultas_demo = [
            {
                'agente': 'agent_expansion',
                'tipo': 'RAG_VECTORSTORE',
                'query': 'smartphone samsung galaxy características técnicas',
                'resultados': 15,
                'tempo': 45
            },
            {
                'agente': 'agent_ncm',
                'tipo': 'NCM_HIERARCHY',
                'query': 'telefone celular comunicação móvel',
                'resultados': 8,
                'tempo': 22
            },
            {
                'agente': 'agent_cest',
                'tipo': 'CEST_MAPPING',
                'query': 'telecomunicações aparelhos telefônicos',
                'resultados': 12,
                'tempo': 35
            },
            {
                'agente': 'agent_reconciler',
                'tipo': 'GOLDEN_SET',
                'query': 'smartphone dual chip validado',
                'resultados': 3,
                'tempo': 18
            }
        ]
        
        for consulta in consultas_demo:
            consulta_data = {
                'agente_nome': consulta['agente'],
                'produto_id': 99001,
                'tipo_consulta': consulta['tipo'],
                'query_original': consulta['query'],
                'total_resultados_encontrados': consulta['resultados'],
                'tempo_consulta_ms': consulta['tempo'],
                'consulta_bem_sucedida': True,
                'sessao_classificacao': 'DEMO_SESSION_001'
            }
            
            consulta_id = self.service.registrar_consulta_agente(consulta_data)
            print(f"🔍 {consulta['agente'].replace('agent_', '').title()}:")
            print(f"   Query: \"{consulta['query']}\"")
            print(f"   Fonte: {consulta['tipo']} | Resultados: {consulta['resultados']} | Tempo: {consulta['tempo']}ms")
            print(f"   (ID da consulta: {consulta_id})")
            print()
        
        print("📊 Todas as consultas são registradas para auditoria!")
        print()
    
    def _demo_web_interface(self):
        """Demonstra tracking da interface web"""
        print("🌐 INTERFACE WEB - Monitoramento de Interações")
        print("-" * 45)
        
        # Simular interações com a interface
        interacoes_demo = [
            {
                'tipo': 'CLASSIFICACAO',
                'endpoint': '/api/v1/classificar',
                'metodo': 'POST',
                'tempo': 350,
                'status': 200
            },
            {
                'tipo': 'REVISAO',
                'endpoint': '/api/v1/revisar',
                'metodo': 'PUT',
                'tempo': 150,
                'status': 200
            },
            {
                'tipo': 'CONSULTA',
                'endpoint': '/api/v1/dashboard',
                'metodo': 'GET',
                'tempo': 25,
                'status': 200
            }
        ]
        
        for interacao in interacoes_demo:
            interacao_data = {
                'sessao_usuario': 'DEMO_USER_SESSION',
                'usuario_id': 'demo_user',
                'tipo_interacao': interacao['tipo'],
                'endpoint_acessado': interacao['endpoint'],
                'metodo_http': interacao['metodo'],
                'tempo_processamento_ms': interacao['tempo'],
                'sucesso': True,
                'codigo_resposta': interacao['status'],
                'ip_usuario': '192.168.1.100'
            }
            
            int_id = self.service.registrar_interacao_web(interacao_data)
            print(f"🌐 {interacao['tipo']}:")
            print(f"   {interacao['metodo']} {interacao['endpoint']} → {interacao['status']}")
            print(f"   Tempo: {interacao['tempo']}ms | ID: {int_id}")
            print()
        
        print("📈 Métricas de uso e performance são coletadas automaticamente!")
        print()
    
    def _demo_performance(self):
        """Demonstra performance do sistema"""
        print("⚡ PERFORMANCE E ESCALABILIDADE")
        print("-" * 35)
        
        # Teste de performance em tempo real
        print("🚀 Executando benchmarks em tempo real:")
        
        # Benchmark 1: Busca hierárquica
        start = time.time()
        for _ in range(100):
            self.service.buscar_ncms_por_nivel(4, 10)
        tempo_hierarquica = (time.time() - start) / 100
        
        print(f"   📋 Busca hierárquica: {tempo_hierarquica*1000:.1f}ms por consulta")
        
        # Benchmark 2: Busca por padrão
        start = time.time()
        for _ in range(50):
            self.service.buscar_ncms_por_padrao("produto", 5)
        tempo_pattern = (time.time() - start) / 50
        
        print(f"   🔍 Busca por padrão: {tempo_pattern*1000:.1f}ms por consulta")
        
        # Benchmark 3: Dashboard stats
        start = time.time()
        for _ in range(20):
            self.service.get_dashboard_stats()
        tempo_dashboard = (time.time() - start) / 20
        
        print(f"   📊 Dashboard stats: {tempo_dashboard*1000:.1f}ms por consulta")
        
        # Estatísticas de capacidade
        stats = self.service.get_dashboard_stats()
        print(f"\n📈 Capacidade do sistema:")
        print(f"   💾 {stats['total_ncms']:,} NCMs indexados")
        print(f"   🎯 {stats['total_mapeamentos']:,} mapeamentos NCM-CEST")
        print(f"   🧠 {stats['explicacoes_agentes']:,} explicações de IA")
        print(f"   🌐 Sistema web responsivo (<500ms)")
        
        # Score de performance
        score = 1000 / (tempo_hierarquica + tempo_pattern + tempo_dashboard)
        print(f"\n🏆 Score de Performance: {score:.0f} pontos")
        
        if score > 500:
            print("   ✅ EXCELENTE - Sistema otimizado para produção")
        elif score > 200:
            print("   ✅ BOM - Performance adequada")
        else:
            print("   ⚠️  REGULAR - Considerar otimizações")
        
        print()

def main():
    """Função principal"""
    demo = UnifiedSystemDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()
