#!/usr/bin/env python3
"""
Demo Prático da Interface Web - Sistema de Revisão Humana
Este script demonstra como usar a API REST para revisão de classificações
"""

import requests
import json
import time
from datetime import datetime

class DemoInterfaceWeb:
    def __init__(self, api_base="http://localhost:8000/api"):
        self.api_base = api_base
    
    def verificar_api_online(self):
        """Verifica se a API está rodando"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API está online e funcionando")
                return True
        except requests.exceptions.RequestException:
            print("❌ API não está rodando. Execute: python src/main.py setup-review --start-api")
            return False
    
    def listar_pendentes(self, limite=10):
        """Lista classificações pendentes de revisão"""
        print(f"\n📋 Buscando {limite} classificações pendentes...")
        
        try:
            response = requests.get(
                f"{self.api_base}/classificacoes/pendentes", 
                params={"limite": limite}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Encontradas {data['total']} classificações pendentes")
                
                for i, item in enumerate(data['classificacoes'][:3], 1):
                    print(f"\n{i}. ID: {item['id']}")
                    print(f"   📦 Produto: {item['codigo_produto']}")
                    print(f"   📝 Descrição: {item['descricao_produto'][:60]}...")
                    print(f"   🎯 NCM Sugerido: {item['ncm_sugerido']}")
                    print(f"   🏷️ CEST Sugerido: {item.get('cest_sugerido', 'N/A')}")
                    print(f"   📊 Confiança: {item['confianca_original']:.2f}")
                
                return data['classificacoes']
            else:
                print(f"❌ Erro: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar pendentes: {e}")
            return []
    
    def processar_revisao(self, classificacao_id, ncm_final, cest_final, status, comentarios="", revisor="demo@sistema.com"):
        """Processa uma revisão humana"""
        print(f"\n✅ Processando revisão da classificação {classificacao_id}...")
        
        dados_revisao = {
            "classificacao_id": classificacao_id,
            "ncm_final": ncm_final,
            "cest_final": cest_final,
            "status_revisao": status,
            "comentarios": comentarios,
            "revisado_por": revisor
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/revisao/processar",
                json=dados_revisao
            )
            
            if response.status_code == 200:
                resultado = response.json()
                print(f"🎉 Revisão processada com sucesso!")
                print(f"   Status: {resultado['status']}")
                print(f"   Golden Set: {'✅ Adicionado' if resultado.get('adicionado_golden_set') else '❌ Não'}")
                return resultado
            else:
                print(f"❌ Erro: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao processar revisão: {e}")
            return None
    
    def ver_dashboard(self):
        """Exibe estatísticas do dashboard"""
        print(f"\n📊 Dashboard do Sistema - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.api_base}/dashboard/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                print(f"📈 Total de Classificações: {stats['total_classificacoes']:,}")
                print(f"⏳ Pendentes: {stats['pendentes']:,}")
                print(f"✅ Aprovadas: {stats['aprovadas']:,}")
                print(f"❌ Rejeitadas: {stats['rejeitadas']:,}")
                print(f"📊 Taxa de Aprovação: {stats['taxa_aprovacao']:.1%}")
                print(f"🎯 Confiança Média: {stats['confianca_media']:.2f}")
                
                if 'golden_set' in stats:
                    print(f"🏆 Golden Set: {stats['golden_set'].get('total_entradas', 0):,} entradas")
                
                return stats
            else:
                print(f"❌ Erro: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao buscar dashboard: {e}")
            return None
    
    def demo_completo(self):
        """Executa uma demonstração completa do sistema"""
        print("🚀 DEMO COMPLETO DA INTERFACE WEB")
        print("=" * 60)
        
        # 1. Verificar se API está online
        if not self.verificar_api_online():
            return
        
        # 2. Ver dashboard inicial
        stats_inicial = self.ver_dashboard()
        if not stats_inicial:
            return
        
        # 3. Listar classificações pendentes
        pendentes = self.listar_pendentes(5)
        if not pendentes:
            print("ℹ️ Nenhuma classificação pendente encontrada")
            return
        
        # 4. Processar algumas revisões de exemplo
        print(f"\n🔄 Processando revisões de exemplo...")
        
        for i, item in enumerate(pendentes[:3]):
            print(f"\n--- Revisão {i+1}/3 ---")
            
            # Simular aprovação se confiança alta, rejeição se baixa
            if item['confianca_original'] > 0.8:
                resultado = self.processar_revisao(
                    classificacao_id=item['id'],
                    ncm_final=item['ncm_sugerido'],
                    cest_final=item.get('cest_sugerido'),
                    status="aprovado",
                    comentarios=f"Aprovado - confiança alta ({item['confianca_original']:.2f})",
                    revisor="demo_especialista@empresa.com"
                )
            else:
                # Simular correção
                resultado = self.processar_revisao(
                    classificacao_id=item['id'], 
                    ncm_final="22021000",  # NCM corrigido
                    cest_final="03.002.00",  # CEST corrigido
                    status="rejeitado",
                    comentarios=f"Corrigido - confiança baixa ({item['confianca_original']:.2f})",
                    revisor="demo_especialista@empresa.com"
                )
            
            if resultado:
                print(f"✅ Revisão {i+1} processada com sucesso")
            
            time.sleep(1)  # Pausa entre revisões
        
        # 5. Ver dashboard final
        print(f"\n📊 Dashboard após as revisões:")
        stats_final = self.ver_dashboard()
        
        # 6. Mostrar diferenças
        if stats_inicial and stats_final:
            print(f"\n📈 Mudanças após as revisões:")
            print(f"   Pendentes: {stats_inicial['pendentes']} → {stats_final['pendentes']} ({stats_final['pendentes'] - stats_inicial['pendentes']:+d})")
            print(f"   Aprovadas: {stats_inicial['aprovadas']} → {stats_final['aprovadas']} ({stats_final['aprovadas'] - stats_inicial['aprovadas']:+d})")
            print(f"   Rejeitadas: {stats_inicial['rejeitadas']} → {stats_final['rejeitadas']} ({stats_final['rejeitadas'] - stats_inicial['rejeitadas']:+d})")
        
        print(f"\n🎉 Demo concluído! Acesse http://localhost:8000/api/docs para mais detalhes")

def main():
    """Função principal"""
    print("🌐 Demo da Interface Web - Sistema de Revisão Humana")
    print("Certifique-se de que a API está rodando: python src/main.py setup-review --start-api")
    print()
    
    demo = DemoInterfaceWeb()
    
    while True:
        print("\nEscolha uma opção:")
        print("1. 🔍 Ver dashboard")
        print("2. 📋 Listar pendentes")
        print("3. ✅ Processar revisão manual")
        print("4. 🚀 Demo completo automatizado")
        print("5. ❌ Sair")
        
        escolha = input("\nDigite sua escolha (1-5): ").strip()
        
        if escolha == "1":
            demo.ver_dashboard()
            
        elif escolha == "2":
            limite = input("Quantas classificações listar (padrão 10)? ").strip()
            limite = int(limite) if limite.isdigit() else 10
            demo.listar_pendentes(limite)
            
        elif escolha == "3":
            # Revisão manual
            pendentes = demo.listar_pendentes(5)
            if pendentes:
                try:
                    id_escolhido = int(input("Digite o ID da classificação para revisar: "))
                    ncm = input("NCM final: ").strip()
                    cest = input("CEST final (ou Enter para vazio): ").strip() or None
                    status = input("Status (aprovado/rejeitado): ").strip()
                    comentarios = input("Comentários: ").strip()
                    
                    demo.processar_revisao(id_escolhido, ncm, cest, status, comentarios)
                except ValueError:
                    print("❌ ID inválido")
                    
        elif escolha == "4":
            demo.demo_completo()
            
        elif escolha == "5":
            print("👋 Saindo...")
            break
            
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()
