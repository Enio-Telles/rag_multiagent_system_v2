"""
Integração das APIs Existentes com SQLite Unificado
Atualiza todos os endpoints para usar o novo sistema unificado
"""

import os
import sys
from pathlib import Path

# Configurar path
sys.path.append('src')

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
import uuid
import time

# Imports do sistema unificado
from services.unified_sqlite_service import get_unified_service
from database.unified_sqlite_models import UnifiedBase

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aplicação FastAPI
app = FastAPI(
    title="Sistema de Classificação Fiscal - API Unificada",
    description="API completa integrada com SQLite unificado para classificação fiscal NCM/CEST",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serviço unificado
unified_service = get_unified_service("data/unified_rag_system.db")

# ==================
# MODELOS PYDANTIC
# ==================

class NCMBuscaRequest(BaseModel):
    """Request para busca de NCMs"""
    padrao: Optional[str] = None
    nivel: Optional[int] = None
    codigo_ncm: Optional[str] = None
    limite: int = 20

class NCMResponse(BaseModel):
    """Response para NCM"""
    codigo_ncm: str
    descricao_oficial: str
    descricao_curta: Optional[str]
    nivel_hierarquico: int
    codigo_pai: Optional[str]
    ativo: bool

class CESTProdutoRequest(BaseModel):
    """Request para buscar CEST de um produto"""
    codigo_ncm: str
    limite: int = 10

class CESTResponse(BaseModel):
    """Response para CEST"""
    codigo_cest: str
    descricao_cest: str
    descricao_resumida: Optional[str]
    categoria_produto: Optional[str]
    tipo_relacao: Optional[str]
    confianca: Optional[float]

class ProdutoClassificacaoRequest(BaseModel):
    """Request para classificação de produto"""
    produto_id: int
    descricao_produto: str
    descricao_completa: Optional[str] = None
    codigo_produto: Optional[str] = None
    codigo_barra: Optional[str] = None
    gtin_original: Optional[str] = None
    sessao_classificacao: Optional[str] = None

class ClassificacaoResponse(BaseModel):
    """Response para classificação"""
    id: int
    produto_id: int
    descricao_produto: str
    ncm_sugerido: Optional[str]
    cest_sugerido: Optional[str]
    confianca_sugerida: Optional[float]
    justificativa_sistema: Optional[str]
    status_revisao: str
    data_criacao: str

class RevisaoRequest(BaseModel):
    """Request para revisão humana"""
    classificacao_id: int
    status_revisao: str  # APROVADO, CORRIGIDO
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    justificativa_correcao: Optional[str] = None
    revisado_por: str
    tempo_revisao_segundos: Optional[int] = None

class GoldenSetRequest(BaseModel):
    """Request para adicionar ao Golden Set"""
    produto_id: int
    descricao_produto: str
    descricao_completa: Optional[str] = None
    codigo_produto: Optional[str] = None
    gtin_validado: Optional[str] = None
    ncm_final: str
    cest_final: Optional[str] = None
    fonte_validacao: str = "HUMANA"
    justificativa_inclusao: Optional[str] = None
    revisado_por: str
    qualidade_score: float = 1.0

class ExplicacaoAgenteRequest(BaseModel):
    """Request para salvar explicação de agente"""
    produto_id: int
    classificacao_id: Optional[int] = None
    agente_nome: str
    explicacao_detalhada: str
    nivel_confianca: float
    tempo_processamento_ms: Optional[int] = None
    rag_consultado: bool = False
    golden_set_utilizado: bool = False
    sessao_classificacao: Optional[str] = None

class ConsultaAgenteRequest(BaseModel):
    """Request para registrar consulta de agente"""
    agente_nome: str
    produto_id: int
    tipo_consulta: str
    query_original: str
    total_resultados_encontrados: int
    tempo_consulta_ms: int
    consulta_bem_sucedida: bool = True
    sessao_classificacao: Optional[str] = None

# ==================
# MODELOS EMPRESA CONTEXTO
# ==================

class InformacaoEmpresaRequest(BaseModel):
    """Request para cadastrar/atualizar informação da empresa"""
    tipo_atividade: str
    descricao_atividade: str
    segmento_mercado: Optional[str] = None
    canal_venda: Optional[str] = None  # ex: porta_a_porta, varejo, atacado
    regiao_atuacao: Optional[str] = None
    porte_empresa: Optional[str] = None  # MEI, ME, EPP, GRANDE
    regime_tributario: Optional[str] = None  # SIMPLES, LUCRO_PRESUMIDO, LUCRO_REAL
    observacoes: Optional[str] = None

class InformacaoEmpresaResponse(BaseModel):
    """Response para informação da empresa"""
    id: int
    tipo_atividade: str
    descricao_atividade: str
    segmento_mercado: Optional[str]
    canal_venda: Optional[str]
    regiao_atuacao: Optional[str]
    porte_empresa: Optional[str]
    regime_tributario: Optional[str]
    observacoes: Optional[str]
    data_criacao: str
    data_atualizacao: str
    ativo: bool

class ContextoClassificacaoResponse(BaseModel):
    """Response para contexto aplicado em classificação"""
    contexto_aplicado: Dict[str, Any]
    cest_especifico_aplicavel: Optional[str]
    justificativa_contexto: str

# ==================
# ENDPOINTS KNOWLEDGE BASE
# ==================

@app.get("/api/v1/ncm/buscar", response_model=List[NCMResponse])
async def buscar_ncms(
    padrao: Optional[str] = Query(None, description="Padrão para busca na descrição"),
    nivel: Optional[int] = Query(None, description="Nível hierárquico (2, 4, 6, 8)"),
    codigo_ncm: Optional[str] = Query(None, description="Código NCM específico"),
    limite: int = Query(20, description="Limite de resultados")
):
    """Busca NCMs por diferentes critérios"""
    try:
        start_time = time.time()
        
        if codigo_ncm:
            # Busca específica
            ncm = unified_service.buscar_ncm(codigo_ncm)
            resultados = [ncm] if ncm else []
        elif nivel:
            # Busca por nível
            resultados = unified_service.buscar_ncms_por_nivel(nivel, limite)
        elif padrao:
            # Busca por padrão
            resultados = unified_service.buscar_ncms_por_padrao(padrao, limite)
        else:
            # Busca geral (nível 2)
            resultados = unified_service.buscar_ncms_por_nivel(2, limite)
        
        # Registrar interação web
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'CONSULTA_NCM',
            'endpoint_acessado': '/api/v1/ncm/buscar',
            'metodo_http': 'GET',
            'dados_entrada': {'padrao': padrao, 'nivel': nivel, 'codigo_ncm': codigo_ncm},
            'dados_saida': {'total_resultados': len(resultados)},
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao buscar NCMs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cest/para-ncm/{codigo_ncm}", response_model=List[CESTResponse])
async def buscar_cests_para_ncm(codigo_ncm: str):
    """Busca CESTs relacionados a um NCM"""
    try:
        start_time = time.time()
        
        resultados = unified_service.buscar_cests_para_ncm(codigo_ncm)
        
        # Registrar interação
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'CONSULTA_CEST',
            'endpoint_acessado': f'/api/v1/cest/para-ncm/{codigo_ncm}',
            'metodo_http': 'GET',
            'dados_entrada': {'codigo_ncm': codigo_ncm},
            'dados_saida': {'total_resultados': len(resultados)},
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao buscar CESTs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ncm/{codigo_ncm}/exemplos")
async def buscar_exemplos_ncm(codigo_ncm: str, limite: int = Query(10, description="Limite de exemplos")):
    """Busca exemplos de produtos para um NCM"""
    try:
        resultados = unified_service.buscar_exemplos_ncm(codigo_ncm, limite)
        return {"codigo_ncm": codigo_ncm, "exemplos": resultados}
        
    except Exception as e:
        logger.error(f"Erro ao buscar exemplos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS CLASSIFICAÇÃO
# ==================

@app.post("/api/v1/classificar", response_model=ClassificacaoResponse)
async def classificar_produto(request: ProdutoClassificacaoRequest, background_tasks: BackgroundTasks):
    """Classifica um produto (endpoint principal)"""
    try:
        start_time = time.time()
        sessao_id = request.sessao_classificacao or str(uuid.uuid4())
        
        # Preparar dados para classificação
        produto_data = {
            'produto_id': request.produto_id,
            'descricao_produto': request.descricao_produto,
            'descricao_completa': request.descricao_completa,
            'codigo_produto': request.codigo_produto,
            'codigo_barra': request.codigo_barra,
            'gtin_original': request.gtin_original,
            'data_classificacao': datetime.now()
        }
        
        # Aqui você integraria com os agentes de IA para obter classificação
        # Por enquanto, vamos simular uma classificação
        produto_data.update({
            'ncm_sugerido': '85171231',  # Exemplo: smartphone
            'cest_sugerido': '2104700',
            'confianca_sugerida': 0.92,
            'justificativa_sistema': 'Classificação baseada em análise de IA multiagente'
        })
        
        # Criar classificação
        classificacao_id = unified_service.criar_classificacao(produto_data)
        
        # Registrar consultas dos agentes (simulado)
        background_tasks.add_task(
            registrar_consultas_agentes,
            request.produto_id,
            sessao_id
        )
        
        # Registrar interação web
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': sessao_id,
            'tipo_interacao': 'CLASSIFICACAO',
            'endpoint_acessado': '/api/v1/classificar',
            'metodo_http': 'POST',
            'dados_entrada': request.dict(),
            'dados_saida': {'classificacao_id': classificacao_id},
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        # Buscar e retornar classificação criada
        classificacoes = unified_service.buscar_classificacoes_pendentes(1)
        if classificacoes:
            return classificacoes[0]
        
        return {"id": classificacao_id, "status": "criada"}
        
    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/classificacoes/pendentes", response_model=List[ClassificacaoResponse])
async def listar_classificacoes_pendentes(limite: int = Query(50, description="Limite de resultados")):
    """Lista classificações pendentes de revisão"""
    try:
        resultados = unified_service.buscar_classificacoes_pendentes(limite)
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao buscar pendentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/classificacoes/{classificacao_id}/revisar")
async def revisar_classificacao(classificacao_id: int, request: RevisaoRequest):
    """Aplica revisão humana a uma classificação"""
    try:
        start_time = time.time()
        
        # Aplicar revisão
        sucesso = unified_service.revisar_classificacao(classificacao_id, request.dict())
        
        if not sucesso:
            raise HTTPException(status_code=404, detail="Classificação não encontrada")
        
        # Se foi aprovado, adicionar ao Golden Set
        if request.status_revisao == "APROVADO":
            # Buscar dados da classificação para Golden Set
            # (implementar lógica específica conforme necessário)
            pass
        
        # Registrar interação
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'REVISAO',
            'endpoint_acessado': f'/api/v1/classificacoes/{classificacao_id}/revisar',
            'metodo_http': 'PUT',
            'dados_entrada': request.dict(),
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return {"status": "revisao_aplicada", "classificacao_id": classificacao_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na revisão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS GOLDEN SET
# ==================

@app.post("/api/v1/golden-set")
async def adicionar_golden_set(request: GoldenSetRequest):
    """Adiciona entrada ao Golden Set"""
    try:
        golden_id = unified_service.adicionar_ao_golden_set(request.dict())
        return {"status": "adicionado", "golden_set_id": golden_id}
        
    except Exception as e:
        logger.error(f"Erro ao adicionar ao Golden Set: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/golden-set")
async def listar_golden_set(
    ncm: Optional[str] = Query(None, description="Filtrar por NCM"),
    limite: int = Query(50, description="Limite de resultados")
):
    """Lista entradas do Golden Set"""
    try:
        resultados = unified_service.buscar_golden_set(ncm=ncm, limite=limite)
        return {"total": len(resultados), "entradas": resultados}
        
    except Exception as e:
        logger.error(f"Erro ao buscar Golden Set: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS EXPLICAÇÕES
# ==================

@app.post("/api/v1/explicacoes")
async def salvar_explicacao_agente(request: ExplicacaoAgenteRequest):
    """Salva explicação de um agente"""
    try:
        explicacao_id = unified_service.salvar_explicacao_agente(request.dict())
        return {"status": "salva", "explicacao_id": explicacao_id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar explicação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/produtos/{produto_id}/explicacoes")
async def buscar_explicacoes_produto(produto_id: int):
    """Busca todas as explicações de um produto"""
    try:
        explicacoes = unified_service.buscar_explicacoes_produto(produto_id)
        return {"produto_id": produto_id, "explicacoes": explicacoes}
        
    except Exception as e:
        logger.error(f"Erro ao buscar explicações: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS CONSULTAS
# ==================

@app.post("/api/v1/consultas")
async def registrar_consulta_agente(request: ConsultaAgenteRequest):
    """Registra consulta realizada por um agente"""
    try:
        consulta_id = unified_service.registrar_consulta_agente(request.dict())
        return {"status": "registrada", "consulta_id": consulta_id}
        
    except Exception as e:
        logger.error(f"Erro ao registrar consulta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS DASHBOARD
# ==================

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats():
    """Obtém estatísticas para o dashboard"""
    try:
        start_time = time.time()
        
        stats = unified_service.get_dashboard_stats()
        
        # Adicionar métricas de performance
        stats['performance'] = {
            'tempo_resposta_ms': int((time.time() - start_time) * 1000),
            'timestamp': datetime.now().isoformat()
        }
        
        # Registrar acesso ao dashboard
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'DASHBOARD',
            'endpoint_acessado': '/api/v1/dashboard/stats',
            'metodo_http': 'GET',
            'dados_saida': stats,
            'tempo_processamento_ms': stats['performance']['tempo_resposta_ms'],
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/metricas")
async def dashboard_metricas():
    """Obtém métricas de qualidade"""
    try:
        from datetime import timedelta
        
        # Calcular métricas dos últimos 30 dias
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=30)
        
        metricas = unified_service.calcular_metricas_periodo(data_inicio, data_fim)
        
        return {
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            },
            'metricas': metricas
        }
        
    except Exception as e:
        logger.error(f"Erro nas métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS SISTEMA
# ==================

@app.get("/api/v1/sistema/status")
async def sistema_status():
    """Verifica status do sistema"""
    try:
        # Verificar conectividade do banco
        counts = unified_service.contar_registros()
        
        status = {
            'status': 'operacional',
            'versao': '3.0.0',
            'banco_sqlite': 'data/unified_rag_system.db',
            'registros': counts,
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return {
            'status': 'erro',
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/sistema/health")
async def health_check():
    """Health check simples"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================
# FUNÇÕES AUXILIARES
# ==================

async def registrar_consultas_agentes(produto_id: int, sessao_id: str):
    """Registra consultas simuladas dos agentes (background task)"""
    try:
        agentes_consultas = [
            {
                'agente_nome': 'expansion',
                'tipo_consulta': 'RAG_VECTORSTORE',
                'query_original': 'expansão de produto',
                'total_resultados_encontrados': 10,
                'tempo_consulta_ms': 45
            },
            {
                'agente_nome': 'ncm_agent',
                'tipo_consulta': 'NCM_HIERARCHY',
                'query_original': 'classificação NCM',
                'total_resultados_encontrados': 5,
                'tempo_consulta_ms': 25
            },
            {
                'agente_nome': 'cest_agent',
                'tipo_consulta': 'CEST_MAPPING',
                'query_original': 'mapeamento CEST',
                'total_resultados_encontrados': 3,
                'tempo_consulta_ms': 18
            }
        ]
        
        for consulta in agentes_consultas:
            consulta.update({
                'produto_id': produto_id,
                'sessao_classificacao': sessao_id,
                'consulta_bem_sucedida': True
            })
            unified_service.registrar_consulta_agente(consulta)
            
    except Exception as e:
        logger.error(f"Erro ao registrar consultas dos agentes: {e}")

# ==================
# ENDPOINTS EMPRESA CONTEXTO
# ==================

@app.post("/api/v1/empresa/configurar", response_model=InformacaoEmpresaResponse)
async def configurar_empresa(request: InformacaoEmpresaRequest):
    """
    Configura ou atualiza as informações da empresa para contexto de classificação
    """
    try:
        # Verificar se já existe uma empresa cadastrada
        empresa_existente = unified_service.obter_informacao_empresa()
        
        dados_empresa = {
            'tipo_atividade': request.tipo_atividade,
            'descricao_atividade': request.descricao_atividade,
            'segmento_mercado': request.segmento_mercado,
            'canal_venda': request.canal_venda,
            'regiao_atuacao': request.regiao_atuacao,
            'porte_empresa': request.porte_empresa,
            'regime_tributario': request.regime_tributario,
            'observacoes': request.observacoes,
            'ativo': True
        }
        
        if empresa_existente:
            # Atualizar empresa existente
            empresa_id = empresa_existente['id']
            unified_service.atualizar_informacao_empresa(empresa_id, dados_empresa)
            logger.info(f"Empresa atualizada: ID {empresa_id}")
        else:
            # Criar nova empresa
            empresa_id = unified_service.cadastrar_informacao_empresa(dados_empresa)
            logger.info(f"Nova empresa cadastrada: ID {empresa_id}")
        
        # Retornar dados atualizados
        empresa_atualizada = unified_service.obter_informacao_empresa()
        
        return InformacaoEmpresaResponse(
            id=empresa_atualizada['id'],
            tipo_atividade=empresa_atualizada['tipo_atividade'],
            descricao_atividade=empresa_atualizada['descricao_atividade'],
            segmento_mercado=empresa_atualizada.get('segmento_mercado'),
            canal_venda=empresa_atualizada.get('canal_venda'),
            regiao_atuacao=empresa_atualizada.get('regiao_atuacao'),
            porte_empresa=empresa_atualizada.get('porte_empresa'),
            regime_tributario=empresa_atualizada.get('regime_tributario'),
            observacoes=empresa_atualizada.get('observacoes'),
            data_criacao=empresa_atualizada['data_criacao'],
            data_atualizacao=empresa_atualizada['data_atualizacao'],
            ativo=empresa_atualizada['ativo']
        )
        
    except Exception as e:
        logger.error(f"Erro ao configurar empresa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v1/empresa", response_model=Optional[InformacaoEmpresaResponse])
async def obter_empresa():
    """
    Obtém as informações atuais da empresa
    """
    try:
        empresa = unified_service.obter_informacao_empresa()
        
        if not empresa:
            return None
            
        return InformacaoEmpresaResponse(
            id=empresa['id'],
            tipo_atividade=empresa['tipo_atividade'],
            descricao_atividade=empresa['descricao_atividade'],
            segmento_mercado=empresa.get('segmento_mercado'),
            canal_venda=empresa.get('canal_venda'),
            regiao_atuacao=empresa.get('regiao_atuacao'),
            porte_empresa=empresa.get('porte_empresa'),
            regime_tributario=empresa.get('regime_tributario'),
            observacoes=empresa.get('observacoes'),
            data_criacao=empresa['data_criacao'],
            data_atualizacao=empresa['data_atualizacao'],
            ativo=empresa['ativo']
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter empresa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v1/empresa/contexto", response_model=Optional[ContextoClassificacaoResponse])
async def obter_contexto_empresa():
    """
    Obtém o contexto de classificação baseado na empresa configurada
    """
    try:
        empresa = unified_service.obter_informacao_empresa()
        
        if not empresa:
            return None
        
        # Simular o serviço de contexto (similar ao que fizemos)
        contexto_aplicado = {
            "tipo_atividade": empresa['tipo_atividade'],
            "canal_venda": empresa.get('canal_venda'),
            "porte_empresa": empresa.get('porte_empresa')
        }
        
        # Determinar CEST específico se aplicável
        cest_especifico = None
        justificativa = f"Contexto baseado na atividade: {empresa['tipo_atividade']}"
        
        # Regra específica para porta a porta -> CEST 28
        if empresa.get('canal_venda') == 'porta_a_porta':
            cest_especifico = "28.%"  # Segmento 28
            justificativa = "Empresa realiza venda porta a porta - aplicável ao segmento 28 do CEST"
        
        return ContextoClassificacaoResponse(
            contexto_aplicado=contexto_aplicado,
            cest_especifico_aplicavel=cest_especifico,
            justificativa_contexto=justificativa
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter contexto empresa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.delete("/api/v1/empresa")
async def remover_empresa():
    """
    Remove as informações da empresa (desativa)
    """
    try:
        empresa = unified_service.obter_informacao_empresa()
        
        if not empresa:
            raise HTTPException(status_code=404, detail="Nenhuma empresa configurada")
        
        # Desativar empresa
        unified_service.atualizar_informacao_empresa(empresa['id'], {'ativo': False})
        
        return {"message": "Informações da empresa removidas com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover empresa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ==================
# ARQUIVOS ESTÁTICOS E ROOT
# ==================

# Servir arquivos estáticos (se houver frontend)
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root():
    """Página inicial da API"""
    return {
        "sistema": "Classificação Fiscal - API Unificada",
        "versao": "3.0.0",
        "status": "operacional",
        "documentacao": "/api/docs",
        "endpoints_principais": [
            "/api/v1/ncm/buscar",
            "/api/v1/classificar",
            "/api/v1/dashboard/stats"
        ]
    }

# ==================
# INICIALIZAÇÃO
# ==================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando API Unificada com SQLite")
    logger.info("📊 Documentação disponível em: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "api_unified:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
