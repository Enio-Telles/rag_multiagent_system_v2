#!/usr/bin/env python3
"""
src/main.py
Ponto de entrada principal do Sistema de Classificação Fiscal Agêntico
Versão atualizada com integração SQLite unificada

Comandos disponíveis:
- ingest: Executa a ingestão e vetorização da base de conhecimento
- classify: Classifica produtos da base de dados (integrado com SQLite unificado)
- test-mapping: Testa o banco de mapeamento estruturado
- test-rag: Testa o sistema de busca semântica
"""

import sys
import os
import argparse
import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import time
import unicodedata

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Função para sanitizar texto para Windows
def sanitize_text_for_windows(text):
    """Sanitiza texto para compatibilidade com Windows CP1252"""
    if text is None:
        return ""
    
    # Converter para string se necessário
    text = str(text)
    
    # Remover ou substituir caracteres problemáticos
    replacements = {
        '\ufffd': '',  # Replacement character
        '…': '...',    # Ellipsis
        '–': '-',      # En dash
        '—': '--',     # Em dash
        ''': "'",      # Left single quotation mark
        ''': "'",      # Right single quotation mark
        '"': '"',      # Left double quotation mark
        '"': '"',      # Right double quotation mark
        '•': '*',      # Bullet
        '€': 'EUR',    # Euro sign
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Normalizar Unicode e remover caracteres não ASCII se necessário
    try:
        # Tentar codificar para cp1252 (Windows)
        text.encode('cp1252')
        return text
    except UnicodeEncodeError:
        # Se falhar, normalizar e usar apenas caracteres ASCII
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

try:
    from config import Config
    from orchestrator.hybrid_router import HybridRouter
except ImportError as e:
    print(f"❌ Erro ao importar módulos básicos: {e}")
    sys.exit(1)

# Sistema de Armazenamento SQLite Aprimorado
try:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from enhanced_sqlite_storage_fixed import EnhancedSQLiteStorage
    ENHANCED_SQLITE_AVAILABLE = True
except ImportError:
    ENHANCED_SQLITE_AVAILABLE = False
    print("⚠️ Sistema SQLite aprimorado não disponível")

# Sistema Unificado
try:
    from services.unified_sqlite_service import get_unified_service
    UNIFIED_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Sistema unificado não disponível, usando sistema legacy: {e}")
    UNIFIED_AVAILABLE = False

def command_ingest(args):
    """Executa o processo de ingestão e vetorização."""
    print("[COMANDO] COMANDO: INGEST")
    print("=" * 60)
    
    router = HybridRouter()
    success = router.ingest_knowledge()
    
    if success:
        print("\n[OK] INGESTÃO CONCLUÍDA COM SUCESSO!")
        print("[DIRETORIO] Arquivos gerados:")
        print(f"   - Índice FAISS: {router.config.FAISS_INDEX_FILE}")
        print(f"   - Metadados: {router.config.METADATA_DB_FILE}")
    else:
        print("\n[ERRO] FALHA NA INGESTÃO!")
        return 1
    
    return 0

def command_classify(args):
    """Executa a classificação de produtos com integração SQLite unificada."""
    print("[COMANDO] COMANDO: CLASSIFY")
    print("=" * 60)
    
    # Verificar se sistema unificado está disponível
    use_unified = UNIFIED_AVAILABLE and Path("data/unified_rag_system.db").exists()
    
    if use_unified:
        print("[PROCESSANDO] Usando Sistema Unificado SQLite")
        return _classify_with_unified_system(args)
    else:
        print("[AVISO]  Usando Sistema Legacy (HybridRouter)")
        return _classify_with_legacy_system(args)

def _classify_with_unified_system(args):
    """Classifica produtos usando sistema unificado SQLite"""
    try:
        unified_service = get_unified_service("data/unified_rag_system.db")
        
        # Carregar produtos
        produtos = _load_produtos_data(args, unified_service)
        
        if not produtos:
            print("[ERRO] Nenhum produto carregado")
            return 1
        
        print(f"[PACOTE] Classificando {len(produtos)} produtos com sistema unificado...")
        
        # Executar classificação
        resultados = []
        for i, produto in enumerate(produtos, 1):
            try:
                start_time = time.time()
                
                # Buscar classificação inteligente usando dados existentes
                classificacao_data = _classify_produto_unified(produto, unified_service)
                
                # Preparar dados completos para salvar no SQLite
                dados_completos = {
                    'produto_id': produto.get('produto_id', i),
                    'descricao_produto': produto.get('descricao_produto'),
                    'codigo_produto': produto.get('codigo_produto'),
                    'codigo_barra': produto.get('codigo_barra'),
                    'ncm_original': produto.get('ncm'),
                    'cest_original': produto.get('cest'),
                    'marca_original': produto.get('marca'),
                    'categoria_original': produto.get('categoria'),
                    'ncm_sugerido': classificacao_data['ncm_sugerido'],
                    'cest_sugerido': classificacao_data.get('cest_sugerido'),
                    'confianca_sugerida': classificacao_data.get('confianca_sugerida', 0.0),
                    'justificativa_sistema': classificacao_data.get('justificativa_sistema'),
                    'fonte_dados': 'postgresql_extraction',
                    'sistema_classificacao': classificacao_data.get('sistema_origem', 'unified_sqlite'),
                    'observacoes_sistema': f"Extraído do PostgreSQL. Consultas: {len(classificacao_data.get('consultas_realizadas', []))}"
                }
                
                # Salvar no banco unificado
                classificacao_id = unified_service.criar_classificacao(dados_completos)
                
                # Salvar consultas dos agentes se disponíveis
                for consulta in classificacao_data.get('consultas_realizadas', []):
                    _salvar_consulta_agente(unified_service, classificacao_id, produto.get('produto_id'), consulta)
                
                tempo_ms = int((time.time() - start_time) * 1000)
                
                resultado = {
                    'produto_id': produto.get('produto_id', i),
                    'descricao_produto': produto.get('descricao_produto'),
                    'codigo_produto': produto.get('codigo_produto'),
                    'codigo_barra': produto.get('codigo_barra'),
                    'ncm_original': produto.get('ncm'),
                    'cest_original': produto.get('cest'),
                    'classificacao_id': classificacao_id,
                    'ncm_classificado': classificacao_data['ncm_sugerido'],
                    'cest_classificado': classificacao_data.get('cest_sugerido'),
                    'confianca_consolidada': classificacao_data.get('confianca_sugerida', 0.0),
                    'justificativa': classificacao_data.get('justificativa_sistema'),
                    'consultas_agentes': len(classificacao_data.get('consultas_realizadas', [])),
                    'tempo_processamento_ms': tempo_ms,
                    'sistema': 'unified_sqlite_complete'
                }
                
                resultados.append(resultado)
                
                # Progresso
                if i % 10 == 0 or i == len(produtos):
                    progress_text = f"   [DADOS] Processados: {i}/{len(produtos)} ({i/len(produtos)*100:.1f}%) - Último: ID {classificacao_id}"
                    print(sanitize_text_for_windows(progress_text))
                
            except Exception as e:
                logger.error(f"Erro ao processar produto {i}: {e}")
                continue
        
        # Salvar resultados
        _save_classification_results(resultados, 'unified')
        
        # Estatísticas
        _print_classification_stats(resultados)
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro no sistema unificado: {e}")
        return 1

def _classify_with_legacy_system(args):
    """Classifica produtos usando sistema legacy"""
    try:
        router = HybridRouter()
        
        # Opções de fonte de dados
        if args.from_db or args.from_db_postgresql:
            force_postgresql = getattr(args, 'from_db_postgresql', False)
            db_type = "PostgreSQL" if force_postgresql else "base de dados (com fallback)"
            print(f"[DADOS] Carregando produtos da {db_type}...")
            
            try:
                produtos_df = router.data_loader.load_produtos_from_db(force_postgresql=force_postgresql)
            except Exception as e:
                print(f"[ERRO] Erro ao carregar dados: {e}")
                return 1
            
            # Limitar quantidade se especificado
            if args.limit:
                produtos_df = produtos_df.head(args.limit)
                print(f"[LISTA] Limitando a {args.limit} produtos para teste.")
            
            produtos = produtos_df.to_dict('records')
            
        elif args.from_file:
            print(f"[DIRETORIO] Carregando produtos do arquivo: {args.from_file}")
            try:
                with open(args.from_file, 'r', encoding='utf-8') as f:
                    produtos = json.load(f)
            except Exception as e:
                print(f"[ERRO] Erro ao carregar arquivo: {e}")
                return 1
                
        else:
            # Produtos de exemplo para teste
            produtos = [
                {"produto_id": 1, "descricao_produto": "Refrigerante Coca-Cola 350ml lata", "codigo_produto": "COCA350"},
                {"produto_id": 2, "descricao_produto": "Smartphone Samsung Galaxy A54 128GB", "codigo_produto": "GALAXY54"},
                {"produto_id": 3, "descricao_produto": "Parafuso de aço inoxidável M6 x 20mm", "codigo_produto": "PAR-M6-20"}
            ]
            print("[TESTE] Usando produtos de exemplo para teste.")
        
        print(f"[PACOTE] Classificando {len(produtos)} produtos...")
        
        # Executar classificação
        resultados = router.classify_products(produtos)
        
        # Salvar resultados
        _save_classification_results(resultados, 'legacy')
        
        # Estatísticas
        _print_classification_stats(resultados)
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro no sistema legacy: {e}")
        return 1

def _load_produtos_data(args, unified_service):
    """Carrega dados de produtos para classificação com prioridade PostgreSQL"""
    if args.from_db or args.from_db_postgresql:
        print("[DADOS] Carregando produtos do banco de dados...")
        
        # Priorizar PostgreSQL quando especificado --from-db
        try:
            from config import Config
            from ingestion.data_loader import DataLoader
            
            data_loader = DataLoader()
            force_postgresql = getattr(args, 'from_db_postgresql', False) or args.from_db
            
            print(f"[CONEXAO] Tipo de conexão: {'PostgreSQL forçado' if force_postgresql else 'Fallback automático'}")
            
            produtos_df = data_loader.load_produtos_from_db(force_postgresql=force_postgresql)
            
            if args.limit:
                produtos_df = produtos_df.head(args.limit)
                print(f"[LISTA] Limitando a {args.limit} produtos para processamento.")
            
            produtos = produtos_df.to_dict('records')
            print(f"[OK] Carregados {len(produtos)} produtos do banco de dados")
            
            # Mostrar estatísticas dos dados carregados
            produtos_com_gtin = sum(1 for p in produtos if p.get('codigo_barra'))
            produtos_com_ncm = sum(1 for p in produtos if p.get('ncm'))
            produtos_com_cest = sum(1 for p in produtos if p.get('cest'))
            
            print(f"[ESTATISTICAS] Produtos com GTIN: {produtos_com_gtin}")
            print(f"[ESTATISTICAS] Produtos com NCM original: {produtos_com_ncm}")
            print(f"[ESTATISTICAS] Produtos com CEST original: {produtos_com_cest}")
            
            return produtos
            
        except Exception as e:
            print(f"[ERRO] Erro ao carregar do banco de dados: {e}")
            print("[FALLBACK] Usando produtos de exemplo...")
            return _get_sample_produtos(args.limit or 10)
    
    elif args.from_file:
        print(f"[DIRETORIO] Carregando produtos do arquivo: {args.from_file}")
        try:
            with open(args.from_file, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
            
            if args.limit:
                produtos = produtos[:args.limit]
            
            return produtos
        except Exception as e:
            print(f"[ERRO] Erro ao carregar arquivo: {e}")
            return []
    
    else:
        # Produtos de exemplo
        return _get_sample_produtos(args.limit or 3)

def _get_sample_produtos(limit):
    """Retorna produtos de exemplo para teste"""
    produtos_exemplo = [
        {
            "produto_id": 10001,
            "descricao_produto": "Smartphone Samsung Galaxy S24 Ultra 512GB Preto",
            "codigo_produto": "SAM-S24U-512-BK",
            "descricao_completa": "Smartphone premium com processador Snapdragon, tela AMOLED 6.8 polegadas, câmera quádrupla 200MP"
        },
        {
            "produto_id": 10002,
            "descricao_produto": "Refrigerante Coca-Cola Zero Açúcar 350ml Lata",
            "codigo_produto": "COCA-ZERO-350",
            "descricao_completa": "Bebida gaseificada sem açúcar, sabor cola, embalagem de alumínio descartável"
        },
        {
            "produto_id": 10003,
            "descricao_produto": "Parafuso Phillips M8x25mm Aço Inoxidável",
            "codigo_produto": "PAR-PH-M8-25-INOX",
            "descricao_completa": "Fixador roscado com cabeça Phillips, material aço inoxidável 304, rosca métrica"
        },
        {
            "produto_id": 10004,
            "descricao_produto": "Notebook Dell Inspiron 15 Intel i7 16GB SSD 512GB",
            "codigo_produto": "DELL-INS15-I7-16-512",
            "descricao_completa": "Computador portátil para uso pessoal e profissional, processador Intel Core i7, memória RAM 16GB DDR4"
        },
        {
            "produto_id": 10005,
            "descricao_produto": "Tênis Nike Air Max 270 Masculino Preto Tamanho 42",
            "codigo_produto": "NIKE-AM270-M-BK-42",
            "descricao_completa": "Calçado esportivo masculino com tecnologia Air Max, parte superior em mesh e couro sintético"
        },
        {
            "produto_id": 10006,
            "descricao_produto": "Café Pilão Tradicional Torrado e Moído 500g",
            "codigo_produto": "PILAO-TRAD-500G",
            "descricao_completa": "Café torrado e moído tradicional, embalagem vácuo 500 gramas, origem Brasil"
        },
        {
            "produto_id": 10007,
            "descricao_produto": "Cabo USB-C para Lightning Apple Original 1m",
            "codigo_produto": "APPLE-USB-C-LIGHT-1M",
            "descricao_completa": "Cabo de dados e carregamento original Apple, conectores USB-C e Lightning, comprimento 1 metro"
        },
        {
            "produto_id": 10008,
            "descricao_produto": "Shampoo L'Oréal Elseve Hidra-Hialurônico 400ml",
            "codigo_produto": "LOREAL-HIDRA-HIAL-400",
            "descricao_completa": "Produto para higiene capilar com ácido hialurônico, cabelos ressecados, frasco 400ml"
        },
        {
            "produto_id": 10009,
            "descricao_produto": "Micro-ondas Brastemp 32L Branco BMS45CR",
            "codigo_produto": "BRASTEMP-MW-32L-BR",
            "descricao_completa": "Forno micro-ondas doméstico, capacidade 32 litros, cor branca, função descongelar e aquecer"
        },
        {
            "produto_id": 10010,
            "descricao_produto": "Bateria Automotiva Moura 60Ah 12V M60GD",
            "codigo_produto": "MOURA-BAT-60AH-M60GD",
            "descricao_completa": "Bateria para veículos automotores, capacidade 60 ampères-hora, tensão 12 volts, tecnologia chumbo-ácido"
        }
    ]
    
    return produtos_exemplo[:limit]

def _salvar_consulta_agente(unified_service, classificacao_id, produto_id, consulta_data):
    """Salva consulta de agente no SQLite para rastreamento"""
    try:
        # Preparar dados da consulta
        consulta_info = {
            'produto_id': produto_id,
            'classificacao_id': classificacao_id,
            'tipo_agente': consulta_data.get('tipo_consulta', 'unknown'),
            'query_original': consulta_data.get('query', ''),
            'resultado_consulta': str(consulta_data.get('resultado', '')),
            'metadados_consulta': json.dumps(consulta_data, ensure_ascii=False),
            'tempo_resposta_ms': consulta_data.get('tempo_ms', 0),
            'qualidade_resultado': 0.9,  # Score padrão alto para consultas do sistema
            'timestamp_consulta': consulta_data.get('timestamp', datetime.now().isoformat())
        }
        
        # Usar método do serviço unificado se disponível
        if hasattr(unified_service, 'salvar_consulta_agente'):
            return unified_service.salvar_consulta_agente(consulta_info)
        else:
            # Salvar diretamente na tabela se método não existir
            with unified_service.get_session() as session:
                from database.unified_sqlite_models import ConsultaAgente
                
                consulta_obj = ConsultaAgente(
                    produto_id=consulta_info['produto_id'],
                    agente_nome=consulta_info.get('tipo_agente', 'unknown'),
                    tipo_consulta=consulta_info.get('tipo_consulta', 'rag'),
                    query_original=consulta_info['query_original'],
                    total_resultados_encontrados=len(consulta_info.get('resultado_consulta', [])),
                    tempo_consulta_ms=consulta_info['tempo_resposta_ms'],
                    qualidade_resultados=consulta_info['qualidade_resultado']
                )
                
                session.add(consulta_obj)
                session.commit()
                return consulta_obj.id
                
    except Exception as e:
        logger.warning(f"Erro ao salvar consulta do agente: {e}")
        return None

def _classify_produto_unified(produto, unified_service):
    """Classifica um produto usando o sistema unificado com rastreamento completo"""
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
        
        return result
    
    start_time = time.time()
    consultas_realizadas = []
    
    # 1. Buscar NCM inteligente com rastreamento
    print(f"   [PROCESSANDO] Produto: {sanitize_text_for_windows(descricao[:60])}...")
    
    ncm_sugerido = _buscar_ncm_inteligente(descricao, unified_service)
    
    # Registrar consulta NCM
    consulta_ncm = {
        'tipo_consulta': 'ncm_inteligente',
        'query': descricao,
        'resultado': ncm_sugerido,
        'timestamp': datetime.now().isoformat(),
        'tempo_ms': int((time.time() - start_time) * 1000)
    }
    consultas_realizadas.append(consulta_ncm)
    
    # 2. Buscar CESTs para o NCM encontrado
    cest_sugerido = None
    if ncm_sugerido and ncm_sugerido != '99999999':
        cests = unified_service.buscar_cests_para_ncm(ncm_sugerido)
        if cests:
            # Escolher CEST com maior confiança
            cest_sugerido = max(cests, key=lambda x: x.get('confianca', 0))['codigo_cest']
            
            # Registrar consulta CEST
            consulta_cest = {
                'tipo_consulta': 'cest_mapping',
                'query': f"NCM {ncm_sugerido}",
                'resultado': f"{len(cests)} CESTs encontrados, selecionado: {cest_sugerido}",
                'cests_disponiveis': [c['codigo_cest'] for c in cests],
                'timestamp': datetime.now().isoformat(),
                'tempo_ms': int((time.time() - start_time) * 1000)
            }
            consultas_realizadas.append(consulta_cest)
    
    # 3. Verificar se é produto farmacêutico e usar ABC Farma
    if _is_pharmaceutical_product(descricao.lower()):
        try:
            abc_results = unified_service.search_abc_farma_by_text(descricao, limit=3)
            consulta_abc = {
                'tipo_consulta': 'abc_farma',
                'query': descricao,
                'resultado': f"{len(abc_results)} produtos similares encontrados" if abc_results else "Nenhum produto similar",
                'produtos_similares': [p['descricao'][:100] for p in abc_results[:3]] if abc_results else [],
                'timestamp': datetime.now().isoformat(),
                'tempo_ms': int((time.time() - start_time) * 1000)
            }
            consultas_realizadas.append(consulta_abc)
        except Exception as e:
            print(f"   [AVISO] Erro na consulta ABC Farma: {e}")
    
    # 4. Determinar confiança da classificação
    confianca = 0.95  # Alta confiança para sistema unificado
    if ncm_sugerido == '99999999':
        confianca = 0.1  # Baixa confiança para fallback
    elif _is_pharmaceutical_product(descricao.lower()) and len(consultas_realizadas) > 2:
        confianca = 0.98  # Muito alta para produtos farmacêuticos com ABC Farma
    
    # 5. Gerar justificativa detalhada
    justificativa_partes = [
        f"Produto analisado: {descricao[:100]}",
        f"NCM identificado: {ncm_sugerido}",
        f"CEST atribuído: {cest_sugerido or 'Nenhum'}",
        f"Consultas realizadas: {len(consultas_realizadas)}"
    ]
    
    if _is_pharmaceutical_product(descricao.lower()):
        justificativa_partes.append("Produto farmacêutico detectado - usado sistema ABC Farma")
    
    justificativa_sistema = ". ".join(justificativa_partes)
    
    tempo_total = int((time.time() - start_time) * 1000)
    
    return {
        'ncm_sugerido': ncm_sugerido,
        'cest_sugerido': cest_sugerido,
        'confianca_sugerida': confianca,
        'justificativa_sistema': justificativa_sistema,
        'consultas_realizadas': consultas_realizadas,
        'tempo_processamento': tempo_total,
        'sistema_origem': 'unified_sqlite_with_tracking'
    }
    
    # Buscar NCM baseado em palavras-chave na descrição
    ncm_sugerido = _buscar_ncm_inteligente(descricao, unified_service)
    
    # Buscar CEST baseado no NCM
    cest_sugerido = None
    confianca = 0.5
    
    if ncm_sugerido:
        cests = unified_service.buscar_cests_para_ncm(ncm_sugerido)
        if cests:
            cest_sugerido = cests[0]['codigo_cest']
            confianca = min(0.95, 0.7 + cests[0].get('confianca', 0.2))
    
    # Criar dados de classificação
    return {
        'produto_id': produto.get('produto_id'),
        'descricao_produto': descricao,
        'descricao_completa': produto.get('descricao_completa'),
        'codigo_produto': produto.get('codigo_produto'),
        'ncm_sugerido': ncm_sugerido or '00000000',
        'cest_sugerido': cest_sugerido,
        'confianca_sugerida': confianca,
        'justificativa_sistema': f'Classificação automática baseada em análise de texto: {descricao[:50]}...',
        'data_classificacao': datetime.now()
    }

def _buscar_ncm_inteligente(descricao, unified_service):
    """Busca NCM de forma inteligente baseada na descrição"""
    descricao_lower = descricao.lower()
    
    # Mapeamento de palavras-chave para NCMs comuns
    keyword_ncm_map = {
        # Eletrônicos
        'smartphone': '85171231',
        'celular': '85171231', 
        'telefone': '85171231',
        'notebook': '84713012',
        'computador': '84713012',
        'laptop': '84713012',
        
        # Bebidas
        'refrigerante': '22021000',
        'bebida': '22021000',
        'coca-cola': '22021000',
        'suco': '20099900',
        
        # Fixadores
        'parafuso': '73181500',
        'fixador': '73181500',
        'porca': '73181600',
        'prego': '73171010',
        
        # Calçados
        'tenis': '64041900',
        'calçado': '64041900',
        'sapato': '64041900',
        'sandalia': '64041900',
        
        # Alimentos
        'cafe': '09011119',
        'chocolate': '18069000',
        'biscoito': '19053200',
        'leite': '04011010',
        
        # Higiene e cosméticos
        'shampoo': '33051000',
        'sabonete': '34011900',
        'creme': '33049900',
        'perfume': '33030010',
        
        # Eletrodomésticos
        'micro-ondas': '85165000',
        'forno': '85165000',
        'geladeira': '84181000',
        'televisor': '85287200',
        
        # Automotivo
        'bateria': '85071000',
        'pneu': '40111000',
        'oleo': '27101259',
        
        # Cabos e eletrônicos
        'cabo': '85444200',
        'carregador': '85044090',
        'fonte': '85044090',
        
        # Medicamentos e farmacêuticos
        'mg': '30049099',  # Medicamentos em geral
        'ml': '30049099',  # Medicamentos líquidos
        'comp': '30049099',  # Comprimidos
        'cap': '30049099',  # Cápsulas
        'gts': '30049099',  # Gotas
        'xarope': '30049099',
        'pomada': '30049099',
        'medicamento': '30049099',
        'farmaco': '30049099',
        'vitamina': '30049099',
        'antibiotico': '30049099',
        'analgesico': '30049099',
        'antiinflamatorio': '30049099',
        'creme dental': '33061000',
        'pasta dental': '33061000',
        
        # Roupas e têxteis
        'camisa': '61051000',
        'calca': '62034200',
        'vestido': '62044200',
        'meia': '61159500',
        
        # Livros e papel
        'livro': '49019900',
        'caderno': '48201000',
        'papel': '48029200',
        
        # Brinquedos
        'boneca': '95030010',
        'carrinho': '95030090',
        'jogo': '95049000'
    }
    
    # Buscar palavra-chave na descrição
    for keyword, ncm in keyword_ncm_map.items():
        if keyword in descricao_lower:
            # Verificar se NCM existe na base
            ncm_data = unified_service.buscar_ncm(ncm)
            if ncm_data:
                return ncm
    
    # Busca específica para medicamentos usando ABC Farma
    if _is_pharmaceutical_product(descricao_lower):
        safe_desc = sanitize_text_for_windows(descricao[:50])
        print(f"   [FARMACEUTICO] Produto farmacêutico detectado: {safe_desc}...")
        try:
            # Buscar na base ABC Farma
            abc_results = unified_service.search_abc_farma_by_text(descricao, limit=3)
            if abc_results:
                print(f"   [OK] Encontrados {len(abc_results)} produtos similares no ABC Farma")
                # Usar o produto mais similar
                best_match = abc_results[0]
                safe_match = sanitize_text_for_windows(best_match['descricao'][:60])
                print(f"   [LISTA] Referência ABC Farma: {safe_match}...")
                return best_match['ncm']  # NCM farmacêutico (30049099)
            else:
                print(f"   [AVISO]  Nenhuma correspondência no ABC Farma, usando NCM padrão farmacêutico")
        except Exception as e:
            print(f"   [AVISO]  Erro na busca ABC Farma: {e}")
        
        return '30049099'  # NCM padrão para medicamentos
    
    # Fallback: buscar por padrão na base NCM
    try:
        # Extrair primeira palavra significativa
        palavras = [p for p in descricao.split() if len(p) > 3]
        if palavras:
            ncms = unified_service.buscar_ncms_por_padrao(palavras[0], 1)
            if ncms:
                return ncms[0]['codigo_ncm']
    except:
        pass
    
    # Último fallback: NCM genérico
    return '99999999'

def _is_pharmaceutical_product(descricao_lower):
    """Identifica se é um produto farmacêutico"""
    # Verificar primeiro se é produto de tecnologia ou eletrônico
    tech_indicators = [
        'smartphone', 'tablet', 'notebook', 'monitor', 'tv', 'eletrônico',
        'samsung', 'apple', 'sony', 'lg', 'motorola', 'xiaomi',
        'intel', 'amd', 'nvidia', 'processador', 'memoria', 'hd', 'ssd'
    ]
    
    for tech in tech_indicators:
        if tech in descricao_lower:
            return False
    
    pharmaceutical_indicators = [
        'medicamento', 'remedio', 'farmaco', 'comprimido', 'capsula',
        'ampola', 'frasco', 'blister', 'cartela', 'drágea',
        'xarope', 'solução', 'suspensão', 'pomada', 'gel', 'creme',
        'vitamina', 'antibiotico', 'analgesico', 'antiinflamatorio',
        'dipirona', 'paracetamol', 'ibuprofeno', 'amoxicilina',
        'simvastatina', 'enalapril', 'losartana', 'metformina'
    ]
    
    # Padrões de dosagem farmacêutica mais específicos
    import re
    dosage_patterns = [
        r'\b\d+\s*mg\b',  # 500 mg ou 500mg
        r'\b\d+\s*ml\b',  # 100 ml ou 100ml
        r'\b\d+\s*mcg\b', # 50 mcg ou 50mcg
        r'\b\d+\s*ui\b',  # 1000 ui ou 1000ui
        r'\b\d+\s*comp\b', # 30 comp
        r'\b\d+\s*caps?\b' # 20 cap ou caps
    ]
    
    # Verificar indicadores específicos
    for indicator in pharmaceutical_indicators:
        if indicator in descricao_lower:
            return True
    
    # Verificar padrões de dosagem
    for pattern in dosage_patterns:
        if re.search(pattern, descricao_lower):
            return True
    
    return False

def _save_classification_results(resultados, system_type):
    """Salva resultados da classificação no formato JSON/CSV e SQLite"""
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
            print(f"⚠️ Erro geral ao salvar no SQLite: {e}")
    
    # Determinar diretório de saída
    if system_type == 'unified':
        output_file = f"resultados_classificacao_unified_{timestamp}.json"
        csv_file = f"resultados_classificacao_unified_{timestamp}.csv"
    else:
        try:
            from config import Config
            config = Config()
            output_file = config.PROCESSED_DATA_DIR / f"classificacao_{timestamp}.json"
            csv_file = config.PROCESSED_DATA_DIR / f"classificacao_{timestamp}.csv"
            
            # Garantir que o diretório existe
            config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        except:
            output_file = f"resultados_classificacao_legacy_{timestamp}.json"
            csv_file = f"resultados_classificacao_legacy_{timestamp}.csv"
    
    # Salvar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'sistema': system_type,
            'total_produtos': len(resultados),
            'resultados': resultados
        }, f, indent=2, ensure_ascii=False, default=str)
    
    # Salvar CSV
    try:
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv(csv_file, index=False, encoding='utf-8')
    except Exception as e:
        logger.warning(f"Erro ao salvar CSV: {e}")
    
    print(f"\n[SALVANDO] Resultados salvos:")
    print(f"   - JSON: {output_file}")
    print(f"   - CSV: {csv_file}")

def _print_classification_stats(resultados):
    """Imprime estatísticas da classificação"""
    print(f"\n[DADOS] ESTATÍSTICAS DA CLASSIFICAÇÃO:")
    print("=" * 60)
    
    total = len(resultados)
    if total == 0:
        print("[ERRO] Nenhum resultado para analisar")
        return
    
    # Estatísticas básicas
    com_ncm = sum(1 for r in resultados if r.get('ncm_classificado', '00000000') not in ['00000000', '99999999', None])
    com_cest = sum(1 for r in resultados if r.get('cest_classificado'))
    
    # Converter confiança para float
    def get_confianca_float(resultado):
        confianca = resultado.get('confianca_consolidada', 0)
        try:
            return float(confianca) if confianca is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    confianca_alta = sum(1 for r in resultados if get_confianca_float(r) > 0.7)
    confianca_media = sum(get_confianca_float(r) for r in resultados) / total if total > 0 else 0
    
    print(f"[LISTA] Total de produtos: {total}")
    print(f"[COMANDO] Com NCM válido: {com_ncm} ({com_ncm/total*100:.1f}%)")
    print(f"[DADOS] Com CEST: {com_cest} ({com_cest/total*100:.1f}%)")
    print(f"[OK] Alta confiança (>0.7): {confianca_alta} ({confianca_alta/total*100:.1f}%)")
    print(f"[MEDIA] Confiança média: {confianca_media:.3f}")
    
    # Mostrar alguns exemplos
    print(f"\n[COMANDO] EXEMPLOS DE CLASSIFICAÇÃO:")
    print("=" * 60)
    
    for i, resultado in enumerate(resultados[:5], 1):
        descricao = sanitize_text_for_windows(resultado.get('descricao_produto', 'N/A')[:60] + "...")
        print(f"{i}. {descricao}")
        print(f"   NCM: {resultado.get('ncm_classificado', 'N/A')}")
        print(f"   CEST: {resultado.get('cest_classificado', 'Nenhum')}")
        print(f"   Confiança: {get_confianca_float(resultado):.3f}")
        sistema = resultado.get('sistema', 'legacy')
        tempo = resultado.get('tempo_processamento_ms', 'N/A')
        print(f"   Sistema: {sistema} | Tempo: {tempo}ms")
        print()
    
    return 0

def command_test_mapping(args):
    """Executa teste do banco de mapeamento."""
    print("[TESTE] COMANDO: TEST-MAPPING")
    print("=" * 60)
    
    # Importar e executar o teste
    try:
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        from test_mapping import MappingTester
        
        tester = MappingTester()
        success = tester.run_comprehensive_test()
        
        return 0 if success else 1
        
    except ImportError as e:
        print(f"[ERRO] Erro ao importar teste de mapeamento: {e}")
        return 1

def command_test_rag(args):
    """Executa teste do sistema RAG."""
    print("[TESTE] COMANDO: TEST-RAG")
    print("=" * 60)
    
    config = Config()
    
    # Verificar se os arquivos necessários existem
    if not config.FAISS_INDEX_FILE.exists():
        print("[ERRO] Índice FAISS não encontrado. Execute 'python main.py ingest' primeiro.")
        return 1
    
    if not config.METADATA_DB_FILE.exists():
        print("[ERRO] Base de metadados não encontrada. Execute 'python main.py ingest' primeiro.")
        return 1
    
    try:
        from vectorstore.faiss_store import FaissMetadataStore
        
        # Inicializar vector store
        print("📚 Inicializando sistema RAG...")
        vector_store = FaissMetadataStore(config.VECTOR_DIMENSION)
        vector_store.load_index(str(config.FAISS_INDEX_FILE))
        vector_store.initialize_metadata_db(str(config.METADATA_DB_FILE))
        
        print("[OK] Sistema RAG carregado com sucesso!")
        
        # ========================================================================
        # TESTE 1: BUSCA SEMÂNTICA GERAL
        # ========================================================================
        print(f"\n🔍 TESTE 1: BUSCA SEMÂNTICA GERAL")
        print("=" * 60)
        
        queries_teste = [
            "refrigerante de cola",
            "parafusos de metal",
            "smartphone celular",
            "água mineral",
            "café torrado"
        ]
        
        for query in queries_teste:
            print(f"\n[COMANDO] Busca: '{query}'")
            results = vector_store.search(query, k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    ncm = metadata.get('ncm', 'N/A')
                    score = result['score']
                    text = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                    
                    print(f"   {i}. NCM {ncm} | Score: {score:.3f}")
                    print(f"      {text}")
            else:
                print(f"   [ERRO] Nenhum resultado encontrado para '{query}'")
        
        # ========================================================================
        # TESTE 2: BUSCA HÍBRIDA FILTRADA
        # ========================================================================
        print(f"\n[COMANDO] TESTE 2: BUSCA HÍBRIDA FILTRADA")
        print("=" * 60)
        
        # Teste com filtro de NCM específico
        test_cases = [
            ("refrigerante", {"ncm": "22021000"}),  # Águas, incluindo águas minerais
            ("café", {"ncm": "09011100"}),  # Café não torrado, não descafeinado
            ("telefone", {"ncm": "85171200"}),  # Telefones para redes celulares
            ("parafuso", {"ncm": "73181500"})   # Parafusos de ferro ou aço
        ]
        
        for query, metadata_filter in test_cases:
            print(f"\n🔍 Busca: '{query}' | Filtro: {metadata_filter}")
            
            # Busca sem filtro
            results_sem_filtro = vector_store.search(query, k=5)
            
            # Busca com filtro
            results_com_filtro = vector_store.search(query, k=5, metadata_filter=metadata_filter)
            
            print(f"   [DADOS] Resultados sem filtro: {len(results_sem_filtro)}")
            print(f"   [DADOS] Resultados com filtro: {len(results_com_filtro)}")
            
            if results_com_filtro:
                print("   [COMANDO] Top 2 resultados filtrados:")
                for i, result in enumerate(results_com_filtro[:2], 1):
                    metadata = result['metadata']
                    score = result['score']
                    text = result['text'][:80] + "..." if len(result['text']) > 80 else result['text']
                    print(f"      {i}. Score: {score:.3f} | {text}")
            else:
                print(f"   [AVISO] Nenhum resultado encontrado com filtro {metadata_filter}")
        
        # ========================================================================
        # TESTE 3: ANÁLISE DE COBERTURA DO ÍNDICE
        # ========================================================================
        print(f"\n[DADOS] TESTE 3: ANÁLISE DE COBERTURA")
        print("=" * 60)
        
        # Buscar estatísticas do banco de metadados
        import sqlite3
        conn = sqlite3.connect(str(config.METADATA_DB_FILE))
        cursor = conn.cursor()
        
        # Total de chunks
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        
        # NCMs únicos
        cursor.execute("""
            SELECT COUNT(DISTINCT json_extract(metadata, '$.ncm')) 
            FROM chunks 
            WHERE json_extract(metadata, '$.ncm') IS NOT NULL
        """)
        ncms_unicos = cursor.fetchone()[0]
        
        # Produtos com GTIN
        cursor.execute("""
            SELECT COUNT(*) 
            FROM chunks 
            WHERE json_extract(metadata, '$.codigo_barra') IS NOT NULL 
            AND json_extract(metadata, '$.codigo_barra') != ''
        """)
        produtos_com_gtin = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   [PACOTE] Total de chunks indexados: {total_chunks:,}")
        print(f"   [COMANDO] NCMs únicos representados: {ncms_unicos:,}")
        print(f"   🏷️ Produtos com GTIN: {produtos_com_gtin:,}")
        print(f"   [DADOS] Cobertura GTIN: {produtos_com_gtin/total_chunks*100:.1f}%")
        
        print(f"\n[OK] TESTE RAG CONCLUÍDO COM SUCESSO!")
        return 0
        
    except Exception as e:
        print(f"[ERRO] ERRO no teste RAG: {e}")
        import traceback
        traceback.print_exc()
        return 1

def create_directory_structure():
    """Cria a estrutura de diretórios necessária."""
    config = Config()
    
    directories = [
        config.DATA_DIR,
        config.RAW_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.KNOWLEDGE_BASE_DIR,
        config.FEEDBACK_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("Estrutura de diretorios criada/verificada.")

def command_setup_review(args):
    """Configura o sistema de revisão humana (Fase 4)."""
    print("COMANDO: SETUP-REVIEW")
    print("=" * 60)
    
    # Verificar se deve reiniciar banco
    if hasattr(args, 'reset_database') and args.reset_database:
        empresa_id = getattr(args, 'empresa_id', None)
        if reset_database_for_new_company(empresa_id):
            print("✅ Banco de dados reiniciado com sucesso")
        else:
            print("❌ Erro ao reiniciar banco de dados")
            return
    
    try:
        # Determinar quais ações executar
        do_create = args.create_tables or args.force_recreate
        do_import = args.import_data
        do_start_api = args.start_api

        # Se nenhum argumento específico for fornecido, executar todas as ações
        is_default_run = not (do_create or do_import or do_start_api)
        
        if is_default_run:
            print("ℹ️ Nenhum argumento específico fornecido. Executando fluxo padrão: create-tables -> import-data -> start-api")
            do_create = True
            do_import = True
            do_start_api = True

        if do_create:
            from database.connection import create_tables, test_connection
            from database.models import Base
            from database.connection import engine
            
            if not test_connection():
                print("[ERRO] Erro: Não foi possível conectar ao banco de dados")
                return 1
            
            if args.force_recreate:
                print("[AVISO]  ATENÇÃO: Dropando todas as tabelas existentes...")
                print("   Isso irá apagar todos os dados existentes!")
                confirmacao = input("   Digite 'CONFIRMO' para continuar: ")
                
                if confirmacao != 'CONFIRMO':
                    print("[ERRO] Operação cancelada pelo usuário.")
                    return 1
                
                print("🗑️ Dropando tabelas existentes...")
                Base.metadata.drop_all(bind=engine)
                print("[OK] Tabelas dropadas com sucesso!")
            
            print("🔧 Criando tabelas do banco de dados...")
            create_tables()
            print("[OK] Tabelas criadas com sucesso!")
        
        if do_import:
            print("📥 Importando classificações existentes...")
            from database.connection import SessionLocal
            from feedback.review_service import ReviewService
            import glob
            
            # Buscar arquivos JSON de classificação
            # Determinar o diretório correto baseado na localização do script
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data" / "processed"
            pattern = str(data_dir / "classificacao_*.json")
            json_files = glob.glob(pattern)
            
            if json_files:
                arquivo_mais_recente = max(json_files, key=lambda f: Path(f).stat().st_mtime)
                print(f"📂 Importando: {Path(arquivo_mais_recente).name}")
                
                review_service = ReviewService()
                db = SessionLocal()
                
                try:
                    resultado = review_service.importar_classificacoes_json(
                        db=db,
                        caminho_arquivo=arquivo_mais_recente
                    )
                    
                    print(f"[OK] Importação concluída!")
                    print(f"   [DADOS] Total: {resultado['total']}")
                    print(f"   [OK] Importadas: {resultado['importadas']}")
                    print(f"   [ERRO] Erros: {resultado['erros']}")
                    
                finally:
                    db.close()
            else:
                print("[AVISO] Nenhum arquivo de classificação encontrado")
        
        if do_start_api:
            print("[COMANDO] Iniciando API de revisão...")
            try:
                import uvicorn
                
                logger.info("API iniciada em http://localhost:8000")
                logger.info("Documentação disponível em http://localhost:8000/api/docs")
                logger.info("Pressione Ctrl+C para parar")
                
                # Usar string de import sem reload para estabilidade em produção
                uvicorn.run("api.review_api:app", host="0.0.0.0", port=8000, reload=False)
                
            except KeyboardInterrupt:
                print("\n👋 API encerrada pelo usuário")
            except ImportError:
                print("[ERRO] Erro: FastAPI/Uvicorn não instalados")
                print("   Execute: pip install fastapi uvicorn")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"[ERRO] Erro na configuração de revisão: {e}")
        return 1

def command_golden_set(args):
    """Gerencia o Golden Set (Fase 5)."""
    print("🏆 COMANDO: GOLDEN-SET")
    print("=" * 60)
    
    try:
        from database.connection import SessionLocal, test_connection
        from feedback.continuous_learning import ContinuousLearningScheduler, GoldenSetManager
        from database.models import GoldenSetEntry
        
        if not test_connection():
            print("[ERRO] Erro: Não foi possível conectar ao banco de dados")
            return 1
        
        config = Config()
        
        if args.status or not any([args.update, args.force]):
            print("[DADOS] Status do Golden Set:")
            
            db = SessionLocal()
            try:
                total_entradas = db.query(GoldenSetEntry).count()
                nao_retreinadas = db.query(GoldenSetEntry).filter(
                    GoldenSetEntry.incluido_em_retreinamento == False
                ).count()
                
                print(f"   📈 Total de entradas: {total_entradas}")
                print(f"   🆕 Novas (não retreinadas): {nao_retreinadas}")
                
                # Verificar índices
                golden_manager = GoldenSetManager(config)
                if golden_manager.verificar_indice_existe():
                    print("   📂 Índice Golden Set: [OK]")
                else:
                    print("   📂 Índice Golden Set: [ERRO] (não encontrado)")
                
            finally:
                db.close()
        
        if args.update or args.force:
            print("[PROCESSANDO] Atualizando Golden Set...")
            
            scheduler = ContinuousLearningScheduler(config)
            db = SessionLocal()
            
            try:
                resultado = scheduler.executar_retreinamento(db, force=args.force)
                
                if resultado['status'] == 'sucesso':
                    print(f"[SUCESSO] Atualização concluída!")
                    print(f"   [DADOS] Total de entradas: {resultado['total_entradas']}")
                    print(f"   📂 Índice salvo em: {resultado['caminho_indice']}")
                else:
                    print(f"ℹ️ {resultado.get('message', 'Atualização não necessária')}")
                
            finally:
                db.close()
        
        return 0
        
    except Exception as e:
        print(f"[ERRO] Erro no Golden Set: {e}")
        return 1

def command_test_phases(args):
    """Testa as fases 4 e 5 completas."""
    print("[TESTE] COMANDO: TEST-PHASES")
    print("=" * 60)
    
    try:
        # Importar o script de teste
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from test_fases_4_5 import main as test_main
        
        success = test_main()
        
        if success:
            print("\n[SUCESSO] TODOS OS TESTES DAS FASES 4 E 5 PASSARAM!")
            return 0
        else:
            print("\n[AVISO] Alguns testes falharam")
            return 1
            
    except Exception as e:
        print(f"[ERRO] Erro nos testes: {e}")
        return 1



def reset_database_for_new_company(empresa_id: str = None):
    """Reinicia o banco de dados SQLite para nova empresa"""
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

def main():
    """Função principal com parser de argumentos."""
    parser = argparse.ArgumentParser(
        description="Sistema de Classificação Fiscal Agêntico",
        epilog="""
Exemplos de uso:
  python main.py ingest                            # Processar e vetorizar base de conhecimento
  python main.py classify --from-db --limit 100   # Classificar 100 produtos da BD (com fallback SQLite)
  python main.py classify --from-db-postgresql --limit 100  # Classificar 100 produtos diretamente do PostgreSQL
  python main.py classify --from-file produtos.json        # Classificar produtos de arquivo
  python main.py test-mapping                      # Testar banco de mapeamento NCM
  python main.py test-rag                          # Testar sistema de busca semântica
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando ingest
    parser_ingest = subparsers.add_parser('ingest', help='Processar e vetorizar base de conhecimento')
    
    # Comando classify
    parser_classify = subparsers.add_parser('classify', help='Classificar produtos com NCM/CEST')
    classify_group = parser_classify.add_mutually_exclusive_group()
    classify_group.add_argument('--from-db', action='store_true', 
                                help='Carregar produtos da base de dados (com fallback SQLite)')
    classify_group.add_argument('--from-db-postgresql', action='store_true', 
                                help='Carregar produtos diretamente do PostgreSQL (força conexão)')
    classify_group.add_argument('--from-file', type=str, metavar='ARQUIVO',
                                help='Carregar produtos de arquivo JSON')
    parser_classify.add_argument('--limit', type=int, metavar='N',
                                help='Limitar processamento a N produtos (apenas --from-db/--from-db-postgresql)')
    
    # Comando test-mapping
    parser_test_mapping = subparsers.add_parser('test-mapping', 
                                               help='Testar banco de mapeamento estruturado')
    
    # Comando test-rag
    parser_test_rag = subparsers.add_parser('test-rag', 
                                          help='Testar sistema de busca semântica')
    
    # Comandos das Fases 4 e 5
    parser_setup_review = subparsers.add_parser('setup-review', 
                                               help='Configurar sistema de revisão humana (Fase 4)')
    parser_setup_review.add_argument('--create-tables', action='store_true',
                                    help='Criar tabelas no banco de dados')
    parser_setup_review.add_argument('--force-recreate', action='store_true',
                                    help='Dropar e recriar todas as tabelas (cuidado: apaga dados!)')
    parser_setup_review.add_argument('--import-data', action='store_true',
                                    help='Importar classificações existentes')
    parser_setup_review.add_argument('--reset-database', action='store_true',
                                    help='Reiniciar banco de dados SQLite')
    parser_setup_review.add_argument('--empresa-id', type=str,
                                    help='ID da empresa para reiniciar banco específico')
    parser_setup_review.add_argument('--start-api', action='store_true',
                                    help='Iniciar API de revisão')
    
    parser_golden_set = subparsers.add_parser('golden-set',
                                            help='Gerenciar Golden Set (Fase 5)')
    parser_golden_set.add_argument('--update', action='store_true',
                                  help='Atualizar índice Golden Set')
    parser_golden_set.add_argument('--force', action='store_true',
                                  help='Forçar atualização mesmo com poucas entradas')
    parser_golden_set.add_argument('--status', action='store_true',
                                  help='Verificar status do Golden Set')
    
    parser_test_phases = subparsers.add_parser('test-phases',
                                             help='Testar fases 4 e 5 completas')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Criar estrutura de diretórios
    create_directory_structure()
    
    # Executar comando
    try:
        if args.command == 'ingest':
            return command_ingest(args)
        elif args.command == 'classify':
            return command_classify(args)
        elif args.command == 'test-mapping':
            return command_test_mapping(args)
        elif args.command == 'test-rag':
            return command_test_rag(args)
        elif args.command == 'setup-review':
            return command_setup_review(args)
        elif args.command == 'golden-set':
            return command_golden_set(args)
        elif args.command == 'test-phases':
            return command_test_phases(args)
        else:
            print(f"[ERRO] Comando desconhecido: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏸️ Operação interrompida pelo usuário.")
        return 1
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())