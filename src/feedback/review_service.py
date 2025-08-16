"""
Serviço para gerenciar revisões de classificações
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging
import sys
import os
from pathlib import Path

# Adicionar src ao path para imports absolutos
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from database.models import ClassificacaoRevisao, GoldenSetEntry, EstadoOrdenacao
from config import Config

logger = logging.getLogger(__name__)

class ReviewService:
    """
    Serviço responsável por gerenciar o ciclo de revisão humana
    """
    
    def __init__(self):
        self.config = Config()
    
    def listar_classificacoes(
        self,
        db: Session,
        status: Optional[str] = None,
        confianca_min: Optional[float] = None,
        page: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista classificações com filtros opcionais
        """
        query = db.query(ClassificacaoRevisao)
        
        # Aplicar filtros
        if status:
            query = query.filter(ClassificacaoRevisao.status_revisao == status)
        
        if confianca_min is not None:
            query = query.filter(ClassificacaoRevisao.confianca_sugerida >= confianca_min)
        
        # Ordenação e paginação
        query = query.order_by(desc(ClassificacaoRevisao.data_classificacao))
        offset = (page - 1) * limit
        classificacoes = query.offset(offset).limit(limit).all()
        
        # Converter para dict
        resultado = []
        for c in classificacoes:
            resultado.append({
                "produto_id": c.produto_id,
                "descricao_produto": c.descricao_produto,
                "codigo_produto": c.codigo_produto,
                "codigo_barra": c.codigo_barra,  # Incluir código de barras
                "ncm_original": c.ncm_original,  # Incluir NCM original
                "cest_original": c.cest_original,  # Incluir CEST original
                "ncm_sugerido": c.ncm_sugerido,
                "cest_sugerido": c.cest_sugerido,
                "confianca_sugerida": c.confianca_sugerida,
                "status_revisao": c.status_revisao,
                "data_classificacao": c.data_classificacao,
                "justificativa_sistema": c.justificativa_sistema or "Nenhuma justificativa fornecida pelo sistema"
            })
        
        return resultado
    
    def obter_proximo_pendente(self, db: Session, produto_id_atual: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retorna o próximo produto pendente de revisão, ordenado alfabeticamente 
        e sempre começando com uma letra diferente da anterior
        """
        import string
        import unicodedata
        
        def remover_acentos(texto):
            """Remove acentos e caracteres especiais para ordenação"""
            if not texto:
                return ""
            # Normalizar e remover acentos
            texto_norm = unicodedata.normalize('NFD', texto.upper())
            texto_sem_acento = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
            return texto_sem_acento
        
        def primeira_letra_valida(texto):
            """Retorna a primeira letra válida (A-Z) da descrição"""
            texto_limpo = remover_acentos(texto)
            for char in texto_limpo:
                if char in string.ascii_uppercase:
                    return char
            return 'Z'  # Fallback para produtos que não começam com letra
        
        # Obter estado atual da ordenação
        estado = db.query(EstadoOrdenacao).first()
        if not estado:
            # Criar estado inicial
            estado = EstadoOrdenacao(ultima_letra_usada="", ultimo_produto_id=None)
            db.add(estado)
            db.commit()
            db.refresh(estado)
        
        ultima_letra = estado.ultima_letra_usada or ""
        
        # Buscar todos os produtos pendentes
        query = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.status_revisao == "PENDENTE_REVISAO"
        )
        
        # Excluir produto atual se especificado
        if produto_id_atual:
            query = query.filter(ClassificacaoRevisao.produto_id != produto_id_atual)
        
        produtos_pendentes = query.all()
        
        if not produtos_pendentes:
            return None
        
        # Organizar produtos por primeira letra
        produtos_por_letra = {}
        for produto in produtos_pendentes:
            primeira_letra = primeira_letra_valida(produto.descricao_produto)
            if primeira_letra not in produtos_por_letra:
                produtos_por_letra[primeira_letra] = []
            produtos_por_letra[primeira_letra].append(produto)
        
        # Ordenar produtos dentro de cada letra alfabeticamente
        for letra in produtos_por_letra:
            produtos_por_letra[letra].sort(
                key=lambda p: remover_acentos(p.descricao_produto or "")
            )
        
        # Encontrar próxima letra disponível (diferente da última usada)
        letras_disponiveis = sorted(produtos_por_letra.keys())
        
        classificacao_escolhida = None
        nova_letra = None
        
        # Se há mais de uma letra disponível, escolher uma diferente da última
        if len(letras_disponiveis) > 1 and ultima_letra in letras_disponiveis:
            # Encontrar próxima letra na ordem alfabética
            try:
                indice_atual = letras_disponiveis.index(ultima_letra)
                # Próxima letra (circular)
                proximo_indice = (indice_atual + 1) % len(letras_disponiveis)
                nova_letra = letras_disponiveis[proximo_indice]
            except ValueError:
                # Se última letra não está na lista, usar a primeira
                nova_letra = letras_disponiveis[0]
        else:
            # Usar primeira letra disponível
            nova_letra = letras_disponiveis[0]
        
        # Pegar primeiro produto da letra escolhida
        if nova_letra and nova_letra in produtos_por_letra:
            classificacao_escolhida = produtos_por_letra[nova_letra][0]
        
        if not classificacao_escolhida:
            # Fallback: usar qualquer produto disponível
            classificacao_escolhida = produtos_pendentes[0]
            nova_letra = primeira_letra_valida(classificacao_escolhida.descricao_produto)
        
        # Atualizar estado da ordenação
        estado.ultima_letra_usada = nova_letra
        estado.ultimo_produto_id = classificacao_escolhida.produto_id
        estado.data_atualizacao = datetime.now()
        db.commit()
        
        # Log para debug
        logger.info(f"Ordenação alfabética: {ultima_letra} → {nova_letra}, Produto: {classificacao_escolhida.descricao_produto[:50]}")
        
        return {
            "produto_id": classificacao_escolhida.produto_id,
            "descricao_produto": classificacao_escolhida.descricao_produto,
            "descricao_completa": classificacao_escolhida.descricao_completa,
            "codigo_produto": classificacao_escolhida.codigo_produto,
            "codigo_barra": classificacao_escolhida.codigo_barra,
            "codigo_barra_status": classificacao_escolhida.codigo_barra_status,
            "codigo_barra_corrigido": classificacao_escolhida.codigo_barra_corrigido,
            "codigo_barra_observacoes": classificacao_escolhida.codigo_barra_observacoes,
            "ncm_original": classificacao_escolhida.ncm_original,
            "cest_original": classificacao_escolhida.cest_original,
            "ncm_sugerido": classificacao_escolhida.ncm_sugerido,
            "cest_sugerido": classificacao_escolhida.cest_sugerido,
            "confianca_sugerida": classificacao_escolhida.confianca_sugerida,
            "status_revisao": classificacao_escolhida.status_revisao,
            "justificativa_sistema": self._extrair_justificativa_completa(classificacao_escolhida),
            "dados_trace_json": classificacao_escolhida.dados_trace_json,
            "ncm_corrigido": classificacao_escolhida.ncm_corrigido,
            "cest_corrigido": classificacao_escolhida.cest_corrigido,
            "justificativa_correcao": classificacao_escolhida.justificativa_correcao,
            "revisado_por": classificacao_escolhida.revisado_por,
            "data_revisao": classificacao_escolhida.data_revisao,
            "_ordenacao_info": {
                "letra_anterior": ultima_letra,
                "letra_atual": nova_letra,
                "primeira_letra_produto": primeira_letra_valida(classificacao_escolhida.descricao_produto)
            }
        }
    
    def obter_classificacao_detalhe(self, db: Session, produto_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna todos os detalhes de uma classificação específica
        """
        classificacao = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.produto_id == produto_id
        ).first()
        
        if not classificacao:
            return None
        
        return {
            "produto_id": classificacao.produto_id,
            "descricao_produto": classificacao.descricao_produto,
            "descricao_completa": classificacao.descricao_completa,  # Descrição mais detalhada
            "codigo_produto": classificacao.codigo_produto,
            "codigo_barra": classificacao.codigo_barra,  # Código de barras extraído do PostgreSQL
            "codigo_barra_status": classificacao.codigo_barra_status,
            "codigo_barra_corrigido": classificacao.codigo_barra_corrigido,
            "codigo_barra_observacoes": classificacao.codigo_barra_observacoes,
            "ncm_original": classificacao.ncm_original,  # NCM original do banco
            "cest_original": classificacao.cest_original,  # CEST original do banco
            "ncm_sugerido": classificacao.ncm_sugerido,
            "cest_sugerido": classificacao.cest_sugerido,
            "confianca_sugerida": classificacao.confianca_sugerida,
            "status_revisao": classificacao.status_revisao,
            "justificativa_sistema": self._extrair_justificativa_completa(classificacao),
            "dados_trace_json": classificacao.dados_trace_json,
            "ncm_corrigido": classificacao.ncm_corrigido,
            "cest_corrigido": classificacao.cest_corrigido,
            "justificativa_correcao": classificacao.justificativa_correcao,
            "revisado_por": classificacao.revisado_por,
            "data_revisao": classificacao.data_revisao
        }
    
    def processar_revisao(
        self,
        db: Session,
        produto_id: int,
        acao: str,
        ncm_corrigido: Optional[str] = None,
        cest_corrigido: Optional[str] = None,
        justificativa_correcao: Optional[str] = None,
        descricao_completa: Optional[str] = None,
        codigo_barra_acao: str = "MANTER",
        codigo_barra_corrigido: Optional[str] = None,
        codigo_barra_observacoes: Optional[str] = None,
        revisado_por: str = "sistema"
    ) -> Dict[str, Any]:
        """
        Processa a revisão de uma classificação por um especialista
        """
        # Buscar classificação existente
        classificacao = db.query(ClassificacaoRevisao).filter(
            ClassificacaoRevisao.produto_id == produto_id
        ).first()
        
        if not classificacao:
            raise ValueError(f"Classificação não encontrada para produto_id {produto_id}")
        
        # Registrar tempo de revisão
        if classificacao.data_classificacao:
            tempo_revisao = (datetime.now() - classificacao.data_classificacao).total_seconds()
            classificacao.tempo_revisao_segundos = int(tempo_revisao)
        
        # Atualizar descrição completa se fornecida
        if descricao_completa:
            classificacao.descricao_completa = descricao_completa
        
        # Atualizar código de barras baseado na ação escolhida pelo revisor
        if codigo_barra_acao == "CORRIGIR" and codigo_barra_corrigido:
            classificacao.codigo_barra_corrigido = codigo_barra_corrigido
            classificacao.codigo_barra_status = "CORRETO"
        elif codigo_barra_acao == "REMOVER":
            classificacao.codigo_barra_corrigido = None
            classificacao.codigo_barra_status = "NAO_APLICAVEL"
        elif codigo_barra_acao == "MANTER":
            # Marcar como correto se o revisor escolheu manter
            classificacao.codigo_barra_status = "CORRETO"
        
        if codigo_barra_observacoes:
            classificacao.codigo_barra_observacoes = codigo_barra_observacoes
        
        # Atualizar campos baseado na ação
        if acao == "APROVAR":
            classificacao.status_revisao = "APROVADO"
            # Manter as classificações sugeridas como finais
            classificacao.ncm_corrigido = classificacao.ncm_sugerido
            classificacao.cest_corrigido = classificacao.cest_sugerido
        elif acao == "CORRIGIR":
            classificacao.status_revisao = "CORRIGIDO"
            classificacao.ncm_corrigido = ncm_corrigido or classificacao.ncm_sugerido
            classificacao.cest_corrigido = cest_corrigido or classificacao.cest_sugerido
            classificacao.justificativa_correcao = justificativa_correcao
        
        # Dados da revisão
        classificacao.revisado_por = revisado_por
        classificacao.data_revisao = datetime.now()
        
        # Salvar no banco
        try:
            db.commit()
            
            # Adicionar ao Golden Set se aprovado ou corrigido
            self._adicionar_ao_golden_set(db, classificacao)
            
            logger.info(f"Revisão processada: produto_id={produto_id}, acao={acao}, revisado_por={revisado_por}")
            
            return {
                "produto_id": produto_id,
                "status_revisao": classificacao.status_revisao,
                "ncm_final": classificacao.ncm_corrigido,
                "cest_final": classificacao.cest_corrigido
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao processar revisão: {e}")
            raise
    
    def _adicionar_ao_golden_set(self, db: Session, classificacao: ClassificacaoRevisao):
        """
        Adiciona uma classificação validada ao Golden Set
        """
        try:
            # Verificar se já existe no Golden Set
            existing = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.classificacao_revisao_id == classificacao.id
            ).first()
            
            if existing:
                # Atualizar entrada existente
                existing.ncm_final = classificacao.ncm_corrigido
                existing.cest_final = classificacao.cest_corrigido
                existing.fonte_validacao = classificacao.status_revisao
                existing.data_validacao = datetime.now()
            else:
                # Criar nova entrada
                golden_entry = GoldenSetEntry(
                    classificacao_revisao_id=classificacao.id,
                    descricao_produto=classificacao.descricao_produto,
                    codigo_produto=classificacao.codigo_produto,
                    ncm_final=classificacao.ncm_corrigido,
                    cest_final=classificacao.cest_corrigido,
                    fonte_validacao=classificacao.status_revisao,
                    confianca_original=classificacao.confianca_sugerida,
                    revisado_por=classificacao.revisado_por,
                    data_validacao=datetime.now()
                )
                db.add(golden_entry)
            
            db.commit()
            logger.info(f"Entrada adicionada ao Golden Set: produto_id={classificacao.produto_id}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar ao Golden Set: {e}")
            # Não fazer rollback aqui pois pode afetar a transação principal
    
    def importar_classificacoes_json(self, db: Session, caminho_arquivo: str) -> Dict[str, int]:
        """
        Importa classificações de um arquivo JSON para o banco de dados
        """
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                classificacoes = json.load(f)
            
            importadas = 0
            erros = 0
            
            for c in classificacoes:
                produto_id = None
                try:
                    # Usar transação individual para cada produto
                    produto_id = c.get('produto_id')
                    
                    if not produto_id:
                        logger.warning("Produto sem ID encontrado, pulando...")
                        erros += 1
                        continue
                    
                    # Verificar se já existe
                    existing = db.query(ClassificacaoRevisao).filter(
                        ClassificacaoRevisao.produto_id == produto_id
                    ).first()
                    
                    if existing:
                        # Atualizar registro existente
                        existing.ncm_sugerido = c.get('ncm_classificado')
                        existing.cest_sugerido = c.get('cest_classificado')
                        existing.confianca_sugerida = c.get('confianca_consolidada', 0.0)
                        existing.justificativa_sistema = c.get('justificativa_final', '')
                        existing.dados_trace_json = json.dumps(c.get('traces', {})) if c.get('traces') else None
                        existing.data_classificacao = datetime.now()
                    else:
                        # Criar novo registro
                        nova_classificacao = ClassificacaoRevisao(
                            produto_id=produto_id,
                            descricao_produto=c.get('descricao_produto', ''),
                            codigo_produto=c.get('codigo_produto', ''),
                            codigo_barra=c.get('codigo_barra'),  # Código de barras extraído do PostgreSQL
                            codigo_barra_status="PENDENTE_VERIFICACAO",  # Sempre pendente para revisão humana
                            ncm_original=c.get('ncm'),
                            cest_original=c.get('cest'),
                            ncm_sugerido=c.get('ncm_classificado'),
                            cest_sugerido=c.get('cest_classificado'),
                            confianca_sugerida=c.get('confianca_consolidada', 0.0),
                            justificativa_sistema=c.get('justificativa_final', ''),
                            status_revisao="PENDENTE_REVISAO",
                            dados_trace_json=json.dumps(c.get('traces', {})) if c.get('traces') else None,
                            data_classificacao=datetime.now()
                        )
                        db.add(nova_classificacao)
                    
                    # Commit individual para cada produto
                    db.commit()
                    importadas += 1
                    
                except Exception as e:
                    logger.warning(f"Erro ao importar produto {produto_id or 'N/A'}: {e}")
                    # Rollback individual para este produto
                    try:
                        db.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Erro no rollback para produto {produto_id or 'N/A'}: {rollback_error}")
                    erros += 1
                    continue
            
            logger.info(f"Importação concluída: {importadas} classificações importadas, {erros} erros")
            
            return {
                "importadas": importadas,
                "erros": erros,
                "total": len(classificacoes)
            }
            
        except Exception as e:
            logger.error(f"Erro na importação: {e}")
            # Se houve erro no carregamento do arquivo, fazer rollback geral
            try:
                db.rollback()
            except:
                pass
            raise

    def adicionar_ao_golden_set(
        self, 
        db: Session, 
        produto_id: int, 
        justificativa: str, 
        revisado_por: str
    ) -> Dict[str, Any]:
        """
        Adiciona uma classificação ao Golden Set com dados enriquecidos
        Se estiver pendente, aprova automaticamente antes de adicionar
        Inclui descrição completa, dados corrigidos e explicações dos agentes
        """
        try:
            # Buscar classificação
            classificacao = db.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.produto_id == produto_id
            ).first()
            
            if not classificacao:
                raise ValueError(f"Classificação {produto_id} não encontrada")
            
            # Se estiver pendente, aprovar automaticamente
            if classificacao.status_revisao == "PENDENTE_REVISAO":
                classificacao.status_revisao = "APROVADO"
                classificacao.revisado_por = revisado_por
                classificacao.data_revisao = datetime.now()
                db.commit()
                logger.info(f"Produto {produto_id} aprovado automaticamente para Golden Set")
            
            elif classificacao.status_revisao not in ["APROVADO", "CORRIGIDO"]:
                raise ValueError(f"Produto deve estar aprovado ou corrigido para ser adicionado ao Golden Set. Status atual: {classificacao.status_revisao}")
            
            # Verificar se já existe no Golden Set
            entrada_existente = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.produto_id == produto_id
            ).first()
            
            if entrada_existente:
                return {
                    "success": False,
                    "message": "Produto já existe no Golden Set",
                    "produto_id": produto_id
                }
            
            # Determinar dados finais (priorizando correções humanas)
            ncm_final = classificacao.ncm_corrigido or classificacao.ncm_sugerido
            cest_final = classificacao.cest_corrigido or classificacao.cest_sugerido
            gtin_final = classificacao.codigo_barra_corrigido or classificacao.codigo_barra
            descricao_completa = classificacao.descricao_completa or classificacao.descricao_produto
            
            # Extrair palavras-chave fiscais da descrição
            palavras_chave = self._extrair_palavras_chave_fiscais(descricao_completa)
            
            # Identificar categoria e material do produto
            categoria_produto = self._identificar_categoria_produto(descricao_completa, ncm_final)
            material_predominante = self._identificar_material_predominante(descricao_completa)
            
            # Criar entrada no Golden Set com dados enriquecidos
            golden_entry = GoldenSetEntry(
                produto_id=classificacao.produto_id,
                descricao_produto=classificacao.descricao_produto,  # Descrição original
                descricao_completa=descricao_completa,  # Descrição enriquecida pelo revisor
                codigo_produto=classificacao.codigo_produto,
                gtin_validado=gtin_final,  # GTIN final revisado por humanos
                ncm_final=ncm_final,  # NCM final revisado por humanos
                cest_final=cest_final,  # CEST final revisado por humanos
                confianca_original=classificacao.confianca_sugerida,
                fonte_validacao="HUMANA",
                justificativa_inclusao=justificativa,
                revisado_por=revisado_por,
                data_adicao=datetime.now(),
                ativo=True,
                
                # Dados enriquecidos para uso pelos agentes
                palavras_chave_fiscais=palavras_chave,
                categoria_produto=categoria_produto,
                material_predominante=material_predominante,
                aplicacoes_uso=self._extrair_aplicacoes_uso(descricao_completa),
                caracteristicas_tecnicas=self._extrair_caracteristicas_tecnicas(descricao_completa),
                contexto_uso=self._determinar_contexto_uso(ncm_final, cest_final)
            )
            
            db.add(golden_entry)
            db.commit()
            
            # Buscar e incluir explicações dos agentes se disponíveis
            try:
                from feedback.explicacao_service import ExplicacaoService
                explicacao_service = ExplicacaoService()
                explicacao_service.atualizar_golden_set_com_explicacoes(produto_id, golden_entry.id)
            except ImportError:
                logger.warning("Serviço de explicações não disponível para atualizar Golden Set")
            except Exception as e:
                logger.warning(f"Erro ao adicionar explicações ao Golden Set: {e}")
            
            logger.info(f"Produto {produto_id} adicionado ao Golden Set por {revisado_por} com dados enriquecidos")
            
            return {
                "success": True,
                "message": "Produto adicionado ao Golden Set com dados enriquecidos",
                "produto_id": produto_id,
                "golden_set_id": golden_entry.id,
                "dados_incluidos": {
                    "descricao_original": classificacao.descricao_produto,
                    "descricao_completa": descricao_completa,
                    "ncm_final": ncm_final,
                    "cest_final": cest_final,
                    "gtin_validado": gtin_final,
                    "palavras_chave": palavras_chave,
                    "categoria": categoria_produto,
                    "material": material_predominante
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao adicionar ao Golden Set: {e}")
            raise
    
    def _extrair_palavras_chave_fiscais(self, descricao: str) -> str:
        """Extrai palavras-chave relevantes para classificação fiscal"""
        if not descricao:
            return ""
        
        # Palavras-chave comuns em classificação fiscal
        palavras_relevantes = [
            'aço', 'ferro', 'aluminio', 'plastico', 'metal', 'vidro', 'madeira', 'papel',
            'textil', 'couro', 'borracha', 'ceramica', 'eletronico', 'eletrico', 'digital',
            'medicamento', 'alimento', 'bebida', 'cosmético', 'higiene', 'limpeza',
            'industrial', 'domestico', 'automotivo', 'informatica', 'telecomunicacao',
            'maquina', 'equipamento', 'ferramenta', 'instrumento', 'dispositivo'
        ]
        
        descricao_lower = descricao.lower()
        palavras_encontradas = []
        
        for palavra in palavras_relevantes:
            if palavra in descricao_lower:
                palavras_encontradas.append(palavra)
        
        return ", ".join(palavras_encontradas[:10])  # Limitar a 10 palavras-chave
    
    def _identificar_categoria_produto(self, descricao: str, ncm: str) -> str:
        """Identifica a categoria do produto baseada na descrição e NCM"""
        if not descricao:
            return "Categoria não identificada"
        
        descricao_lower = descricao.lower()
        
        # Categorias baseadas em NCM (primeiros 2 dígitos)
        if ncm and len(ncm) >= 2:
            capitulo = ncm[:2]
            categorias_ncm = {
                '30': 'Medicamentos',
                '22': 'Bebidas',
                '84': 'Máquinas e equipamentos',
                '85': 'Equipamentos elétricos e eletrônicos',
                '87': 'Veículos e partes',
                '90': 'Instrumentos de precisão',
                '73': 'Produtos de ferro ou aço',
                '39': 'Plásticos e suas obras',
                '33': 'Óleos essenciais e cosméticos',
                '34': 'Sabões e produtos de limpeza'
            }
            
            if capitulo in categorias_ncm:
                return categorias_ncm[capitulo]
        
        # Identificação por palavras-chave
        if any(palavra in descricao_lower for palavra in ['medicamento', 'remedio', 'farmaco']):
            return 'Medicamentos'
        elif any(palavra in descricao_lower for palavra in ['bebida', 'refrigerante', 'suco']):
            return 'Bebidas'
        elif any(palavra in descricao_lower for palavra in ['maquina', 'equipamento', 'motor']):
            return 'Máquinas e equipamentos'
        elif any(palavra in descricao_lower for palavra in ['eletronico', 'celular', 'computador']):
            return 'Eletrônicos'
        elif any(palavra in descricao_lower for palavra in ['cosmetico', 'perfume', 'shampoo']):
            return 'Cosméticos e higiene'
        else:
            return 'Produto geral'
    
    def _identificar_material_predominante(self, descricao: str) -> str:
        """Identifica o material predominante do produto"""
        if not descricao:
            return "Material não identificado"
        
        descricao_lower = descricao.lower()
        
        materiais = {
            'aço': ['aço', 'ferro', 'metal ferroso'],
            'aluminio': ['aluminio', 'alumínio'],
            'plastico': ['plastico', 'plástico', 'pvc', 'polietileno'],
            'vidro': ['vidro', 'cristal'],
            'madeira': ['madeira', 'madeirado'],
            'papel': ['papel', 'papelão', 'cartão'],
            'textil': ['tecido', 'algodão', 'poliester'],
            'metal': ['metal', 'metálico', 'liga'],
            'borracha': ['borracha', 'elastomero'],
            'ceramica': ['ceramica', 'cerâmica', 'porcelana']
        }
        
        for material, palavras in materiais.items():
            if any(palavra in descricao_lower for palavra in palavras):
                return material.title()
        
        return "Material misto"
    
    def _extrair_aplicacoes_uso(self, descricao: str) -> str:
        """Extrai aplicações e usos do produto"""
        if not descricao:
            return ""
        
        descricao_lower = descricao.lower()
        aplicacoes = []
        
        # Contextos de uso comuns
        contextos = {
            'domestico': ['domestico', 'casa', 'residencial', 'lar'],
            'industrial': ['industrial', 'industria', 'fabrica'],
            'comercial': ['comercial', 'loja', 'escritorio'],
            'medico': ['medico', 'hospitalar', 'clinico', 'saude'],
            'automotivo': ['automotivo', 'carro', 'veiculo'],
            'informatica': ['informatica', 'computador', 'digital'],
            'alimenticio': ['alimenticio', 'cozinha', 'culinario']
        }
        
        for contexto, palavras in contextos.items():
            if any(palavra in descricao_lower for palavra in palavras):
                aplicacoes.append(contexto)
        
        return ", ".join(aplicacoes) if aplicacoes else "Uso geral"
    
    def _extrair_caracteristicas_tecnicas(self, descricao: str) -> str:
        """Extrai características técnicas relevantes"""
        if not descricao:
            return ""
        
        import re
        caracteristicas = []
        
        # Buscar dimensões
        dimensoes = re.findall(r'\d+(?:\.\d+)?\s*(?:mm|cm|m|pol|polegada)', descricao.lower())
        if dimensoes:
            caracteristicas.extend([f"Dimensão: {dim}" for dim in dimensoes[:3]])
        
        # Buscar voltagem
        voltagem = re.findall(r'\d+\s*v(?:olts?)?|\d+\s*vac', descricao.lower())
        if voltagem:
            caracteristicas.extend([f"Voltagem: {volt}" for volt in voltagem[:2]])
        
        # Buscar peso
        peso = re.findall(r'\d+(?:\.\d+)?\s*(?:kg|g|gramas?)', descricao.lower())
        if peso:
            caracteristicas.extend([f"Peso: {p}" for p in peso[:2]])
        
        return "; ".join(caracteristicas[:5]) if caracteristicas else "Características não especificadas"
    
    def _determinar_contexto_uso(self, ncm: str, cest: str) -> str:
        """Determina o contexto de uso baseado nas classificações"""
        contextos = []
        
        if ncm:
            capitulo = ncm[:2] if len(ncm) >= 2 else ""
            if capitulo in ['30', '33', '34']:
                contextos.append("Consumo pessoal")
            elif capitulo in ['84', '85', '90']:
                contextos.append("Uso profissional/industrial")
            elif capitulo in ['87']:
                contextos.append("Automotivo")
            elif capitulo in ['22']:
                contextos.append("Consumo alimentar")
        
        if cest:
            if cest.startswith('13'):
                contextos.append("Medicamentos - farmácia")
            elif cest.startswith('03'):
                contextos.append("Bebidas - varejo")
            elif cest.startswith('21'):
                contextos.append("Eletrônicos - substituição tributária")
        
        return "; ".join(contextos) if contextos else "Contexto geral"

    def obter_estatisticas_golden_set(self, db: Session) -> Dict[str, Any]:
        """
        Retorna estatísticas do Golden Set
        """
        try:
            # Contagens básicas
            total_entradas = db.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == True).count()
            
            # Entradas por fonte
            por_fonte = db.query(
                GoldenSetEntry.fonte_validacao,
                func.count(GoldenSetEntry.id)
            ).filter(GoldenSetEntry.ativo == True).group_by(GoldenSetEntry.fonte_validacao).all()
            
            # Entradas recentes (últimos 30 dias)
            data_limite = datetime.utcnow() - timedelta(days=30)
            recentes = db.query(GoldenSetEntry).filter(
                and_(
                    GoldenSetEntry.ativo == True,
                    GoldenSetEntry.data_adicao >= data_limite
                )
            ).count()
            
            # Top revisores
            top_revisores = db.query(
                GoldenSetEntry.revisado_por,
                func.count(GoldenSetEntry.id).label('total')
            ).filter(GoldenSetEntry.ativo == True).group_by(
                GoldenSetEntry.revisado_por
            ).order_by(desc('total')).limit(10).all()
            
            # Distribuição de confiança
            confianca_stats = db.query(
                func.avg(GoldenSetEntry.confianca_original),
                func.min(GoldenSetEntry.confianca_original),
                func.max(GoldenSetEntry.confianca_original),
                func.count(GoldenSetEntry.id)
            ).filter(GoldenSetEntry.ativo == True).first()
            
            return {
                "total_entradas": total_entradas,
                "distribuicao_por_fonte": {fonte: count for fonte, count in por_fonte},
                "entradas_recentes_30_dias": recentes,
                "top_revisores": [{"revisor": revisor, "total": total} for revisor, total in top_revisores],
                "estatisticas_confianca": {
                    "media": float(confianca_stats[0]) if confianca_stats[0] else 0,
                    "minima": float(confianca_stats[1]) if confianca_stats[1] else 0,
                    "maxima": float(confianca_stats[2]) if confianca_stats[2] else 0,
                    "total_com_confianca": confianca_stats[3]
                },
                "ultima_atualizacao": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas Golden Set: {e}")
            raise

    def _extrair_justificativa_completa(self, classificacao: ClassificacaoRevisao) -> str:
        """
        Extrai a justificativa completa dos dados de trace dos agentes de IA
        """
        try:
            # Se há justificativa direta, usar ela
            if classificacao.justificativa_sistema and classificacao.justificativa_sistema.strip():
                return classificacao.justificativa_sistema
            
            # Tentar extrair dos dados de trace JSON
            if classificacao.dados_trace_json:
                try:
                    if isinstance(classificacao.dados_trace_json, str):
                        traces = json.loads(classificacao.dados_trace_json)
                    else:
                        traces = classificacao.dados_trace_json
                    
                    # Buscar justificativas nos traces dos agentes
                    justificativas = []
                    
                    # Verificar diferentes estruturas possíveis
                    if isinstance(traces, dict):
                        # Buscar por chaves comuns de justificativa
                        for key in ['justificativa_final', 'reasoning', 'explanation', 'justification', 'rationale']:
                            if key in traces and traces[key]:
                                justificativas.append(f"**{key.title()}**: {traces[key]}")
                        
                        # Buscar em agentes específicos
                        for agent_key in ['classification_agent', 'validation_agent', 'consensus_agent']:
                            if agent_key in traces and isinstance(traces[agent_key], dict):
                                agent_data = traces[agent_key]
                                if 'reasoning' in agent_data:
                                    justificativas.append(f"**{agent_key.replace('_', ' ').title()}**: {agent_data['reasoning']}")
                                elif 'explanation' in agent_data:
                                    justificativas.append(f"**{agent_key.replace('_', ' ').title()}**: {agent_data['explanation']}")
                    
                    if justificativas:
                        return " | ".join(justificativas)
                        
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.warning(f"Erro ao extrair justificativa dos traces: {e}")
            
            # Fallback baseado nas classificações sugeridas
            ncm = classificacao.ncm_sugerido or "não classificado"
            cest = classificacao.cest_sugerido or "não aplicável"
            confianca = (classificacao.confianca_sugerida or 0) * 100
            
            return f"Classificação automática: NCM {ncm}, CEST {cest} (confiança: {confianca:.1f}%). Baseada em análise semântica e comparação com produtos similares no banco de dados."
            
        except Exception as e:
            logger.error(f"Erro ao extrair justificativa completa: {e}")
            return "Sistema em aprendizado - classificação baseada em análise semântica e comparação com produtos similares"

    def atualizar_gtin_produto(
        self, 
        db: Session, 
        produto_id: int, 
        acao: str, 
        gtin_novo: Optional[str] = None,
        observacoes: Optional[str] = None,
        revisado_por: str = "sistema"
    ) -> Dict[str, Any]:
        """
        Atualiza informações de GTIN de um produto
        Ações: 'MANTER', 'CORRIGIR', 'REMOVER', 'MARCAR_INCORRETO'
        """
        try:
            classificacao = db.query(ClassificacaoRevisao).filter(
                ClassificacaoRevisao.produto_id == produto_id
            ).first()
            
            if not classificacao:
                raise ValueError(f"Classificação {produto_id} não encontrada")
            
            if acao == "MANTER":
                classificacao.gtin_status = "CORRETO"
                
            elif acao == "CORRIGIR":
                if not gtin_novo:
                    raise ValueError("GTIN novo é obrigatório para ação CORRIGIR")
                classificacao.gtin_corrigido = gtin_novo
                classificacao.gtin_status = "CORRIGIDO"
                
            elif acao == "REMOVER":
                classificacao.gtin_corrigido = None
                classificacao.gtin_status = "NAO_APLICAVEL"
                
            elif acao == "MARCAR_INCORRETO":
                classificacao.gtin_status = "INCORRETO"
            
            else:
                raise ValueError(f"Ação inválida: {acao}")
            
            if observacoes:
                classificacao.gtin_observacoes = observacoes
            
            classificacao.data_revisao = datetime.utcnow()
            classificacao.revisado_por = revisado_por
            
            db.commit()
            
            return {
                "success": True,
                "produto_id": produto_id,
                "acao": acao,
                "gtin_final": classificacao.gtin_corrigido or classificacao.gtin_original,
                "status": classificacao.gtin_status
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao atualizar GTIN: {e}")
            raise

    def listar_golden_set(
        self, 
        db: Session, 
        page: int = 1, 
        limit: int = 50,
        ativo_apenas: bool = True
    ) -> Dict[str, Any]:
        """
        Lista entradas do Golden Set com paginação
        """
        try:
            query = db.query(GoldenSetEntry)
            
            if ativo_apenas:
                query = query.filter(GoldenSetEntry.ativo == True)
            
            # Contar total
            total = query.count()
            
            # Aplicar paginação
            offset = (page - 1) * limit
            entradas = query.order_by(desc(GoldenSetEntry.data_adicao)).offset(offset).limit(limit).all()
            
            # Converter para dict
            resultado = []
            for entrada in entradas:
                resultado.append({
                    "id": entrada.id,
                    "produto_id": entrada.produto_id,
                    "descricao_produto": entrada.descricao_produto,
                    "codigo_produto": entrada.codigo_produto,
                    "gtin_validado": entrada.gtin_validado,
                    "ncm_final": entrada.ncm_final,
                    "cest_final": entrada.cest_final,
                    "confianca_original": entrada.confianca_original,
                    "fonte_validacao": entrada.fonte_validacao,
                    "justificativa_inclusao": entrada.justificativa_inclusao,
                    "revisado_por": entrada.revisado_por,
                    "data_adicao": entrada.data_adicao,
                    "ativo": entrada.ativo,
                    "qualidade_score": entrada.qualidade_score,
                    "vezes_usado": entrada.vezes_usado,
                    "ultima_utilizacao": entrada.ultima_utilizacao
                })
            
            return {
                "entradas": resultado,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar Golden Set: {e}")
            raise

    def remover_entrada_golden_set(self, db: Session, entrada_id: int) -> Dict[str, Any]:
        """
        Remove (marca como inativa) uma entrada específica do Golden Set
        """
        try:
            entrada = db.query(GoldenSetEntry).filter(GoldenSetEntry.id == entrada_id).first()
            
            if not entrada:
                raise ValueError(f"Entrada {entrada_id} não encontrada no Golden Set")
            
            if not entrada.ativo:
                return {
                    "success": False,
                    "message": "Entrada já está inativa",
                    "entrada_id": entrada_id
                }
            
            # Marcar como inativa em vez de deletar
            entrada.ativo = False
            db.commit()
            
            logger.info(f"Entrada {entrada_id} removida do Golden Set")
            
            return {
                "success": True,
                "message": "Entrada removida do Golden Set com sucesso",
                "entrada_id": entrada_id,
                "produto_id": entrada.produto_id
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao remover entrada Golden Set: {e}")
            raise

    def limpar_golden_set(self, db: Session) -> Dict[str, Any]:
        """
        Limpa todo o Golden Set (marca todas as entradas como inativas)
        """
        try:
            # Contar entradas ativas antes da limpeza
            total_ativas = db.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == True).count()
            
            if total_ativas == 0:
                return {
                    "success": True,
                    "message": "Golden Set já está vazio",
                    "entradas_removidas": 0
                }
            
            # Marcar todas as entradas como inativas
            entradas_atualizadas = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.ativo == True
            ).update({"ativo": False})
            
            db.commit()
            
            logger.warning(f"Golden Set limpo: {entradas_atualizadas} entradas marcadas como inativas")
            
            return {
                "success": True,
                "message": f"Golden Set limpo com sucesso. {entradas_atualizadas} entradas removidas.",
                "entradas_removidas": entradas_atualizadas,
                "data_limpeza": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao limpar Golden Set: {e}")
            raise

    def restaurar_golden_set(self, db: Session) -> Dict[str, Any]:
        """
        Restaura todas as entradas inativas do Golden Set
        """
        try:
            # Contar entradas inativas
            total_inativas = db.query(GoldenSetEntry).filter(GoldenSetEntry.ativo == False).count()
            
            if total_inativas == 0:
                return {
                    "success": True,
                    "message": "Não há entradas inativas para restaurar",
                    "entradas_restauradas": 0
                }
            
            # Reativar todas as entradas inativas
            entradas_restauradas = db.query(GoldenSetEntry).filter(
                GoldenSetEntry.ativo == False
            ).update({"ativo": True})
            
            db.commit()
            
            logger.info(f"Golden Set restaurado: {entradas_restauradas} entradas reativadas")
            
            return {
                "success": True,
                "message": f"Golden Set restaurado com sucesso. {entradas_restauradas} entradas reativadas.",
                "entradas_restauradas": entradas_restauradas,
                "data_restauracao": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao restaurar Golden Set: {e}")
            raise

    def obter_backup_golden_set(self, db: Session) -> Dict[str, Any]:
        """
        Cria um backup completo do Golden Set em formato JSON
        """
        try:
            # Buscar todas as entradas (ativas e inativas)
            entradas = db.query(GoldenSetEntry).order_by(GoldenSetEntry.data_adicao).all()
            
            backup_data = []
            for entrada in entradas:
                backup_data.append({
                    "id": entrada.id,
                    "produto_id": entrada.produto_id,
                    "descricao_produto": entrada.descricao_produto,
                    "codigo_produto": entrada.codigo_produto,
                    "gtin_validado": entrada.gtin_validado,
                    "ncm_final": entrada.ncm_final,
                    "cest_final": entrada.cest_final,
                    "confianca_original": entrada.confianca_original,
                    "fonte_validacao": entrada.fonte_validacao,
                    "justificativa_inclusao": entrada.justificativa_inclusao,
                    "revisado_por": entrada.revisado_por,
                    "data_adicao": entrada.data_adicao.isoformat() if entrada.data_adicao else None,
                    "ativo": entrada.ativo,
                    "qualidade_score": entrada.qualidade_score,
                    "vezes_usado": entrada.vezes_usado,
                    "ultima_utilizacao": entrada.ultima_utilizacao.isoformat() if entrada.ultima_utilizacao else None,
                    "embedding_atualizado": entrada.embedding_atualizado
                })
            
            return {
                "success": True,
                "total_entradas": len(backup_data),
                "entradas_ativas": len([e for e in backup_data if e["ativo"]]),
                "entradas_inativas": len([e for e in backup_data if not e["ativo"]]),
                "data_backup": datetime.now().isoformat(),
                "dados": backup_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar backup Golden Set: {e}")
            raise
