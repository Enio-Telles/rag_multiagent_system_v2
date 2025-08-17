"""
API REST para Interface de Revisão Humana - Versão Integrada com SQLite Unificado
Atualiza endpoints para usar o sistema SQLite unificado
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
import sys
import os
from pathlib import Path
import uuid
import time

# Adicionar src ao path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Imports do sistema unificado
from services.unified_sqlite_service import get_unified_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Classificação Fiscal - API de Revisão Unificada",
    description="API integrada com SQLite unificado para revisão humana de classificações fiscais NCM/CEST",
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

# Inicializar serviço unificado
unified_service = get_unified_service("data/unified_rag_system.db")

# Servir arquivos estáticos
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ==================
# MODELOS PYDANTIC
# ==================

class ClassificacaoResponse(BaseModel):
    """Response para classificação na interface de revisão"""
    id: int
    produto_id: int
    descricao_produto: str
    codigo_produto: Optional[str]
    codigo_barra: Optional[str]
    gtin_original: Optional[str]
    ncm_sugerido: Optional[str]
    cest_sugerido: Optional[str]
    confianca_sugerida: Optional[float]
    status_revisao: str
    data_criacao: str
    justificativa_sistema: Optional[str]
    descricao_completa: Optional[str]

class ClassificacaoDetalhe(BaseModel):
    """Detalhe completo da classificação"""
    id: int
    produto_id: int
    descricao_produto: str
    codigo_produto: Optional[str] = None
    codigo_barra: Optional[str] = None
    gtin_original: Optional[str] = None
    ncm_sugerido: Optional[str] = None
    cest_sugerido: Optional[str] = None
    confianca_sugerida: Optional[float] = None
    status_revisao: str
    justificativa_sistema: Optional[str] = None
    descricao_completa: Optional[str] = None
    # Dados de revisão
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    justificativa_correcao: Optional[str] = None
    revisado_por: Optional[str] = None
    data_revisao: Optional[str] = None
    tempo_revisao_segundos: Optional[int] = None
    # Explicações e traces
    explicacoes_agentes: List[Dict[str, Any]] = []
    consultas_realizadas: List[Dict[str, Any]] = []

class RevisaoRequest(BaseModel):
    """Request para revisão humana"""
    status_revisao: str  # APROVADO, CORRIGIDO, REJEITADO
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    justificativa_correcao: Optional[str] = None
    revisado_por: str
    tempo_revisao_segundos: Optional[int] = None
    adicionar_golden_set: bool = False

class CodigoBarraCorrecaoRequest(BaseModel):
    """Request para correção de código de barras"""
    codigo_barra_corrigido: str
    observacoes: Optional[str] = None
    revisado_por: str

class ExportacaoRequest(BaseModel):
    """Request para exportação de dados"""
    formato: str = "json"  # json, csv, excel
    filtros: Optional[Dict[str, Any]] = None
    incluir_explicacoes: bool = True
    incluir_consultas: bool = True

# ==================
# ENDPOINTS PRINCIPAIS
# ==================

@app.get("/", response_class=FileResponse)
async def serve_index():
    """Serve a página inicial da interface de revisão"""
    try:
        static_path = Path(__file__).parent / "static" / "index.html"
        if static_path.exists():
            return FileResponse(str(static_path))
        else:
            return JSONResponse({
                "sistema": "Interface de Revisão - SQLite Unificado",
                "versao": "3.0.0",
                "documentacao": "/api/docs",
                "status": "operacional"
            })
    except Exception as e:
        logger.error(f"Erro ao servir index: {e}")
        return JSONResponse({"erro": str(e)}, status_code=500)

@app.get("/api/classificacoes/pendentes", response_model=List[ClassificacaoResponse])
async def listar_classificacoes_pendentes(
    limite: int = Query(50, description="Número máximo de registros"),
    offset: int = Query(0, description="Deslocamento para paginação"),
    filtro_status: Optional[str] = Query(None, description="Filtrar por status")
):
    """Lista classificações pendentes de revisão"""
    try:
        start_time = time.time()
        
        # Buscar classificações pendentes
        resultados = unified_service.buscar_classificacoes_pendentes(limite, offset)
        
        # Aplicar filtro de status se especificado
        if filtro_status:
            resultados = [r for r in resultados if r['status_revisao'] == filtro_status]
        
        # Registrar interação
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'LISTA_PENDENTES',
            'endpoint_acessado': '/api/classificacoes/pendentes',
            'metodo_http': 'GET',
            'dados_entrada': {'limite': limite, 'offset': offset, 'filtro_status': filtro_status},
            'dados_saida': {'total_resultados': len(resultados)},
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao listar pendentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classificacoes/{classificacao_id}", response_model=ClassificacaoDetalhe)
async def obter_classificacao_detalhe(classificacao_id: int):
    """Obtém detalhes completos de uma classificação"""
    try:
        start_time = time.time()
        
        # Buscar classificação
        classificacao = unified_service.buscar_classificacao_por_id(classificacao_id)
        if not classificacao:
            raise HTTPException(status_code=404, detail="Classificação não encontrada")
        
        # Buscar explicações dos agentes
        explicacoes = unified_service.buscar_explicacoes_produto(classificacao['produto_id'])
        
        # Buscar consultas realizadas
        consultas = unified_service.buscar_consultas_produto(classificacao['produto_id'])
        
        # Montar resposta completa
        detalhe = {
            **classificacao,
            'explicacoes_agentes': explicacoes,
            'consultas_realizadas': consultas
        }
        
        # Registrar interação
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'DETALHE_CLASSIFICACAO',
            'endpoint_acessado': f'/api/classificacoes/{classificacao_id}',
            'metodo_http': 'GET',
            'dados_entrada': {'classificacao_id': classificacao_id},
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return detalhe
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/classificacoes/{classificacao_id}/revisar")
async def revisar_classificacao(classificacao_id: int, request: RevisaoRequest):
    """Aplica revisão humana a uma classificação"""
    try:
        start_time = time.time()
        
        # Preparar dados de revisão
        dados_revisao = {
            'status_revisao': request.status_revisao,
            'ncm_corrigido': request.ncm_corrigido,
            'cest_corrigido': request.cest_corrigido,
            'justificativa_correcao': request.justificativa_correcao,
            'revisado_por': request.revisado_por,
            'tempo_revisao_segundos': request.tempo_revisao_segundos,
            'data_revisao': datetime.now()
        }
        
        # Aplicar revisão
        sucesso = unified_service.revisar_classificacao(classificacao_id, dados_revisao)
        
        if not sucesso:
            raise HTTPException(status_code=404, detail="Classificação não encontrada")
        
        # Se aprovado e solicitado, adicionar ao Golden Set
        if request.status_revisao == "APROVADO" and request.adicionar_golden_set:
            classificacao = unified_service.buscar_classificacao_por_id(classificacao_id)
            if classificacao:
                golden_data = {
                    'produto_id': classificacao['produto_id'],
                    'descricao_produto': classificacao['descricao_produto'],
                    'descricao_completa': classificacao.get('descricao_completa'),
                    'codigo_produto': classificacao.get('codigo_produto'),
                    'gtin_validado': classificacao.get('gtin_original'),
                    'ncm_final': request.ncm_corrigido or classificacao['ncm_sugerido'],
                    'cest_final': request.cest_corrigido or classificacao['cest_sugerido'],
                    'fonte_validacao': 'REVISAO_HUMANA',
                    'justificativa_inclusao': f"Aprovado na revisão por {request.revisado_por}",
                    'revisado_por': request.revisado_por,
                    'qualidade_score': 1.0,
                    'data_validacao': datetime.now()
                }
                unified_service.adicionar_ao_golden_set(golden_data)
        
        # Registrar métrica de qualidade
        unified_service.registrar_metrica_qualidade({
            'produto_id': classificacao_id,
            'tipo_metrica': 'REVISAO_HUMANA',
            'valor_metrica': 1.0 if request.status_revisao == "APROVADO" else 0.5,
            'detalhes_metrica': {
                'status_revisao': request.status_revisao,
                'tempo_revisao': request.tempo_revisao_segundos,
                'revisado_por': request.revisado_por
            },
            'data_calculo': datetime.now()
        })
        
        # Registrar interação
        tempo_ms = int((time.time() - start_time) * 1000)
        unified_service.registrar_interacao_web({
            'sessao_usuario': str(uuid.uuid4()),
            'tipo_interacao': 'REVISAO_APLICADA',
            'endpoint_acessado': f'/api/classificacoes/{classificacao_id}/revisar',
            'metodo_http': 'POST',
            'dados_entrada': request.dict(),
            'tempo_processamento_ms': tempo_ms,
            'sucesso': True,
            'codigo_resposta': 200
        })
        
        return {
            "status": "revisao_aplicada",
            "classificacao_id": classificacao_id,
            "adicionado_golden_set": request.adicionar_golden_set and request.status_revisao == "APROVADO"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na revisão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/classificacoes/{classificacao_id}/corrigir-codigo-barra")
async def corrigir_codigo_barra(classificacao_id: int, request: CodigoBarraCorrecaoRequest):
    """Corrige código de barras de uma classificação"""
    try:
        # Buscar classificação atual
        classificacao = unified_service.buscar_classificacao_por_id(classificacao_id)
        if not classificacao:
            raise HTTPException(status_code=404, detail="Classificação não encontrada")
        
        # Preparar dados de atualização
        dados_atualizacao = {
            'codigo_barra': request.codigo_barra_corrigido,
            'gtin_original': request.codigo_barra_corrigido,
            'codigo_barra_observacoes': request.observacoes,
            'codigo_barra_corrigido_por': request.revisado_por,
            'data_correcao_codigo_barra': datetime.now()
        }
        
        # Atualizar classificação
        sucesso = unified_service.atualizar_classificacao(classificacao_id, dados_atualizacao)
        
        if not sucesso:
            raise HTTPException(status_code=500, detail="Erro ao corrigir código de barras")
        
        return {
            "status": "codigo_barra_corrigido",
            "classificacao_id": classificacao_id,
            "codigo_barra_novo": request.codigo_barra_corrigido
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao corrigir código de barras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS ESTATÍSTICAS
# ==================

@app.get("/api/estatisticas/dashboard")
async def estatisticas_dashboard():
    """Obtém estatísticas para o dashboard de revisão"""
    try:
        start_time = time.time()
        
        # Buscar estatísticas básicas
        stats = unified_service.get_dashboard_stats()
        
        # Calcular métricas específicas de revisão
        from datetime import timedelta
        
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=30)
        
        metricas_revisao = unified_service.calcular_metricas_periodo(data_inicio, data_fim)
        
        # Consolidar dados
        dashboard_data = {
            'contadores_gerais': stats,
            'metricas_30_dias': metricas_revisao,
            'performance': {
                'tempo_resposta_ms': int((time.time() - start_time) * 1000),
                'status_sistema': 'operacional'
            },
            'ultima_atualizacao': datetime.now().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Erro nas estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/estatisticas/revisao")
async def estatisticas_revisao():
    """Obtém estatísticas específicas do processo de revisão"""
    try:
        # Buscar métricas de revisão
        stats_revisao = unified_service.get_revision_stats()
        
        return {
            'estatisticas_revisao': stats_revisao,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro nas estatísticas de revisão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS BUSCA E FILTROS
# ==================

@app.get("/api/buscar/produtos")
async def buscar_produtos(
    termo: str = Query(..., description="Termo de busca"),
    campo: str = Query("descricao", description="Campo de busca: descricao, codigo, codigo_barra"),
    limite: int = Query(20, description="Limite de resultados")
):
    """Busca produtos por diferentes critérios"""
    try:
        # Implementar busca baseada no campo
        if campo == "descricao":
            resultados = unified_service.buscar_produtos_por_descricao(termo, limite)
        elif campo == "codigo":
            resultados = unified_service.buscar_produtos_por_codigo(termo, limite)
        elif campo == "codigo_barra":
            resultados = unified_service.buscar_produtos_por_codigo_barra(termo, limite)
        else:
            raise HTTPException(status_code=400, detail="Campo de busca inválido")
        
        return {
            'termo_busca': termo,
            'campo_busca': campo,
            'total_encontrados': len(resultados),
            'resultados': resultados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS EXPORTAÇÃO
# ==================

@app.post("/api/exportar/classificacoes")
async def exportar_classificacoes(request: ExportacaoRequest):
    """Exporta classificações em diferentes formatos"""
    try:
        # Buscar classificações para exportação
        classificacoes = unified_service.buscar_classificacoes_para_exportacao(
            filtros=request.filtros,
            incluir_explicacoes=request.incluir_explicacoes,
            incluir_consultas=request.incluir_consultas
        )
        
        if request.formato == "json":
            return JSONResponse({
                'dados': classificacoes,
                'total_registros': len(classificacoes),
                'data_exportacao': datetime.now().isoformat()
            })
        else:
            # Para CSV/Excel, implementar lógica específica
            raise HTTPException(status_code=501, detail=f"Formato {request.formato} não implementado ainda")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na exportação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# ENDPOINTS SISTEMA
# ==================

@app.get("/api/sistema/status")
async def status_sistema():
    """Verifica status do sistema de revisão"""
    try:
        # Verificar conectividade
        counts = unified_service.contar_registros()
        
        return {
            'status': 'operacional',
            'versao': '3.0.0',
            'sistema': 'Interface de Revisão - SQLite Unificado',
            'banco_dados': 'data/unified_rag_system.db',
            'registros': counts,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return {
            'status': 'erro',
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/health")
async def health_check():
    """Health check simples"""
    return {
        "status": "healthy",
        "service": "review_api_unified",
        "timestamp": datetime.now().isoformat()
    }

# ==================
# INICIALIZAÇÃO
# ==================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando API de Revisão Unificada")
    logger.info("📊 Interface disponível em: http://localhost:8001")
    logger.info("📚 Documentação em: http://localhost:8001/api/docs")
    
    uvicorn.run(
        "review_api_unified:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
