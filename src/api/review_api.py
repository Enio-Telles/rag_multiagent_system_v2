"""
API REST para Interface de Revisão Humana - Versão Corrigida
Implementa endpoints para revisão, aprovação e correção de classificações
Com gestão completa de GTIN e Golden Set
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
import sys
import os
from pathlib import Path

# Adicionar src ao path para imports absolutos
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from database.models import ClassificacaoRevisao
from database.connection import get_db
from feedback.review_service import ReviewService
from feedback.metrics_service import MetricsService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar serviço de explicações
try:
    from feedback.explicacao_service import ExplicacaoService
    explicacao_service = ExplicacaoService()
    EXPLICACAO_SERVICE_AVAILABLE = True
except ImportError:
    EXPLICACAO_SERVICE_AVAILABLE = False
    logger.warning("Serviço de explicações não disponível")

app = FastAPI(
    title="Sistema de Classificação Fiscal - API de Revisão",
    description="API para revisão humana de classificações fiscais NCM/CEST com gestão de GTIN e Golden Set",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (interface web)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Modelos Pydantic para validação de dados
class ClassificacaoResponse(BaseModel):
    produto_id: int
    descricao_produto: str
    codigo_produto: str
    codigo_barra: Optional[str]
    ncm_original: Optional[str]
    cest_original: Optional[str]
    ncm_sugerido: Optional[str]
    cest_sugerido: Optional[str]
    confianca_sugerida: float
    status_revisao: str
    data_classificacao: datetime
    justificativa_sistema: Optional[str]

class ClassificacaoDetalhe(BaseModel):
    produto_id: int
    descricao_produto: str
    codigo_produto: Optional[str] = None
    codigo_barra: Optional[str] = None
    codigo_barra_status: Optional[str] = None
    ncm_original: Optional[str] = None
    cest_original: Optional[str] = None
    ncm_sugerido: Optional[str] = None
    cest_sugerido: Optional[str] = None
    confianca_sugerida: Optional[float] = None
    status_revisao: str
    justificativa_sistema: Optional[str] = None
    dados_trace_json: Optional[Dict[str, Any]] = None
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    codigo_barra_corrigido: Optional[str] = None
    codigo_barra_observacoes: Optional[str] = None
    justificativa_correcao: Optional[str] = None
    revisado_por: Optional[str] = None
    data_revisao: Optional[datetime] = None
    descricao_completa: Optional[str] = None

class RevisaoRequest(BaseModel):
    acao: str  # "APROVAR", "CORRIGIR"
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    codigo_barra_acao: str = "MANTER"  # "MANTER", "CORRIGIR", "REMOVER"
    codigo_barra_corrigido: Optional[str] = None
    codigo_barra_observacoes: Optional[str] = None
    descricao_completa: Optional[str] = None
    justificativa_correcao: Optional[str] = None
    revisado_por: str
    incluir_golden_set: bool = False

class GoldenSetRequest(BaseModel):
    produto_id: int
    justificativa: str
    revisado_por: str

class CodigoBarraValidacao(BaseModel):
    codigo_barra: str
    valido: bool
    tipo: Optional[str]
    detalhes: Optional[str]

class DashboardStats(BaseModel):
    total_classificacoes: int
    pendentes_revisao: int
    aprovadas: int
    corrigidas: int
    total_golden: int
    taxa_aprovacao: float
    confianca_media: float
    tempo_medio_revisao: Optional[float]
    distribuicao_confianca: Dict[str, int]

# Inicializar serviços
review_service = ReviewService()
metrics_service = MetricsService()

@app.get("/")
async def interface_principal():
    """Servir interface principal de revisão"""
    static_file = Path(__file__).parent / "static" / "interface_revisao.html"
    if static_file.exists():
        return FileResponse(static_file)
    else:
        return {"message": "Interface web em desenvolvimento. Acesse /api/docs para documentação da API."}

@app.get("/api/v1/health")
async def health_check():
    """Endpoint para verificação de saúde da API"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/v1/classificacoes", response_model=List[ClassificacaoResponse])
async def listar_classificacoes(
    status: Optional[str] = Query(None, description="Filtrar por status: PENDENTE_REVISAO, APROVADO, CORRIGIDO"),
    confianca_min: Optional[float] = Query(None, description="Confiança mínima"),
    page: int = Query(1, description="Número da página"),
    limit: int = Query(50, description="Itens por página"),
    db: Session = Depends(get_db)
):
    """Lista classificações para revisão com filtros opcionais"""
    try:
        classificacoes = review_service.listar_classificacoes(
            db=db,
            status=status,
            confianca_min=confianca_min,
            page=page,
            limit=limit
        )
        return classificacoes
    except Exception as e:
        logger.error(f"Erro ao listar classificações: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/classificacoes/proximo-pendente", response_model=ClassificacaoDetalhe)
async def obter_proximo_produto_pendente(
    produto_id_atual: Optional[int] = Query(None, description="ID do produto atual para evitar repetição"),
    db: Session = Depends(get_db)
):
    """Retorna o próximo produto pendente de revisão"""
    try:
        proximo_produto = review_service.obter_proximo_pendente(
            db=db, 
            produto_id_atual=produto_id_atual
        )
        if not proximo_produto:
            raise HTTPException(status_code=404, detail="Não há produtos pendentes de revisão")
        return proximo_produto
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter próximo produto: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/classificacoes/{produto_id}", response_model=ClassificacaoDetalhe)
async def obter_classificacao_detalhe(
    produto_id: int,
    db: Session = Depends(get_db)
):
    """Retorna todos os detalhes de uma classificação específica"""
    try:
        classificacao = review_service.obter_classificacao_detalhe(db=db, produto_id=produto_id)
        if not classificacao:
            raise HTTPException(status_code=404, detail="Classificação não encontrada")
        return classificacao
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter classificação {produto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.put("/api/v1/classificacoes/{produto_id}/revisar")
async def revisar_classificacao(
    produto_id: int,
    revisao: RevisaoRequest,
    db: Session = Depends(get_db)
):
    """Endpoint principal para revisão de classificações por especialistas"""
    try:
        # Validar dados de entrada
        if revisao.acao not in ["APROVAR", "CORRIGIR"]:
            raise HTTPException(status_code=400, detail="Ação deve ser 'APROVAR' ou 'CORRIGIR'")
        
        if revisao.acao == "CORRIGIR" and not (revisao.ncm_corrigido or revisao.cest_corrigido):
            raise HTTPException(
                status_code=400, 
                detail="Para corrigir, deve fornecer pelo menos NCM ou CEST corrigido"
            )
        
        # Processar revisão
        resultado = review_service.processar_revisao(
            db=db,
            produto_id=produto_id,
            acao=revisao.acao,
            ncm_corrigido=revisao.ncm_corrigido,
            cest_corrigido=revisao.cest_corrigido,
            justificativa_correcao=revisao.justificativa_correcao,
            descricao_completa=revisao.descricao_completa,
            codigo_barra_acao=revisao.codigo_barra_acao,
            codigo_barra_corrigido=revisao.codigo_barra_corrigido if revisao.codigo_barra_acao == "CORRIGIR" else None,
            codigo_barra_observacoes=revisao.codigo_barra_observacoes,
            revisado_por=revisao.revisado_por
        )
        
        return {"success": True, "message": "Revisão processada com sucesso", "data": resultado}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar revisão {produto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/dashboard/stats", response_model=DashboardStats)
async def obter_estatisticas_dashboard(
    periodo_dias: int = Query(30, description="Período em dias para calcular estatísticas"),
    db: Session = Depends(get_db)
):
    """Retorna estatísticas para o dashboard de monitoramento"""
    try:
        stats = metrics_service.calcular_estatisticas(db=db, periodo_dias=periodo_dias)
        return stats
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/golden-set/adicionar")
async def adicionar_ao_golden_set(
    request: GoldenSetRequest,
    db: Session = Depends(get_db)
):
    """Adiciona uma classificação aprovada ao Golden Set para aprendizagem contínua"""
    try:
        resultado = review_service.adicionar_ao_golden_set(
            db=db,
            produto_id=request.produto_id,
            justificativa=request.justificativa,
            revisado_por=request.revisado_por
        )
        return resultado
    except ValueError as e:
        logger.error(f"Erro de validação ao adicionar ao Golden Set: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao adicionar ao Golden Set: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/api/v1/golden-set/estatisticas")
async def estatisticas_golden_set(db: Session = Depends(get_db)):
    """Retorna estatísticas do Golden Set"""
    try:
        stats = review_service.obter_estatisticas_golden_set(db=db)
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/golden-set/listar")
async def listar_golden_set(
    page: int = Query(1, description="Número da página"),
    limit: int = Query(50, description="Itens por página"),
    db: Session = Depends(get_db)
):
    """Lista entradas do Golden Set com paginação"""
    try:
        entradas = review_service.listar_golden_set(db=db, page=page, limit=limit)
        return entradas
    except Exception as e:
        logger.error(f"Erro ao listar Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.delete("/api/v1/golden-set/{entrada_id}")
async def remover_entrada_golden_set(
    entrada_id: int,
    db: Session = Depends(get_db)
):
    """Remove uma entrada específica do Golden Set"""
    try:
        resultado = review_service.remover_entrada_golden_set(db=db, entrada_id=entrada_id)
        return resultado
    except ValueError as e:
        logger.error(f"Erro de validação ao remover entrada Golden Set: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao remover entrada Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.delete("/api/v1/golden-set/limpar")
async def limpar_golden_set(
    confirmar: bool = Query(False, description="Confirmação obrigatória para limpar todo o Golden Set"),
    db: Session = Depends(get_db)
):
    """Limpa todo o Golden Set (marca todas as entradas como inativas)"""
    try:
        if not confirmar:
            raise HTTPException(
                status_code=400, 
                detail="Parâmetro 'confirmar=true' é obrigatório para limpar o Golden Set"
            )
        
        resultado = review_service.limpar_golden_set(db=db)
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao limpar Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/golden-set/restaurar")
async def restaurar_golden_set(
    db: Session = Depends(get_db)
):
    """Restaura todas as entradas inativas do Golden Set"""
    try:
        resultado = review_service.restaurar_golden_set(db=db)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao restaurar Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# =============================================================================
# ENDPOINTS PARA EXPLICAÇÕES DOS AGENTES
# =============================================================================

@app.get("/api/v1/explicacoes/{produto_id}")
async def obter_explicacoes_produto(
    produto_id: int,
    agente: Optional[str] = Query(None, description="Nome do agente específico (expansion, ncm, cest, reconciler)")
):
    """Obtém explicações detalhadas dos agentes para um produto específico"""
    try:
        if not EXPLICACAO_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Serviço de explicações não disponível")
        
        if agente:
            # Explicação de um agente específico
            explicacao = explicacao_service.obter_explicacao_por_agente(produto_id, agente)
            if not explicacao:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Explicação do agente '{agente}' não encontrada para produto {produto_id}"
                )
            return explicacao
        else:
            # Todas as explicações do produto
            explicacoes = explicacao_service.obter_explicacoes_produto(produto_id)
            if not explicacoes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Nenhuma explicação encontrada para produto {produto_id}"
                )
            return {"produto_id": produto_id, "explicacoes": explicacoes}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter explicações do produto {produto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

class ClassificarComExplicacaoRequest(BaseModel):
    produto_id: int
    descricao_produto: str
    codigo_produto: Optional[str] = None
    salvar_explicacoes: bool = True

@app.post("/api/v1/classificar-com-explicacao")
async def classificar_produto_com_explicacao(
    request: ClassificarComExplicacaoRequest
):
    """Classifica um produto com explicações detalhadas de cada agente"""
    try:
        if not EXPLICACAO_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Serviço de explicações não disponível")
        
        # Importar o orquestrador
        from orchestrator.hybrid_router import HybridRouter
        
        # Criar instância do orquestrador
        router = HybridRouter()
        
        # Preparar dados do produto
        produto_data = {
            "id": request.produto_id,
            "produto_id": request.produto_id,
            "descricao_produto": request.descricao_produto,
            "codigo_produto": request.codigo_produto
        }
        
        # Classificar com explicações
        resultado = router.classify_product_with_explanations(
            produto_data, 
            salvar_explicacoes=request.salvar_explicacoes
        )
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao classificar produto com explicações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/api/v1/relatorio-agente/{agente_nome}")
async def obter_relatorio_agente(
    agente_nome: str,
    periodo_dias: int = Query(30, description="Período em dias para análise")
):
    """Gera relatório de performance de um agente específico"""
    try:
        if not EXPLICACAO_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Serviço de explicações não disponível")
        
        agentes_validos = ["expansion", "aggregation", "ncm", "cest", "reconciler"]
        if agente_nome not in agentes_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Agente '{agente_nome}' inválido. Agentes disponíveis: {', '.join(agentes_validos)}"
            )
        
        relatorio = explicacao_service.gerar_relatorio_agente(agente_nome, periodo_dias)
        
        if "erro" in relatorio:
            raise HTTPException(status_code=404, detail=relatorio["erro"])
        
        return relatorio
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório do agente {agente_nome}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.delete("/api/v1/explicacoes/limpar-antigas")
async def limpar_explicacoes_antigas(
    dias_manter: int = Query(90, description="Número de dias de explicações para manter"),
    confirmar: bool = Query(False, description="Confirmação obrigatória para limpar explicações")
):
    """Remove explicações antigas para otimizar o banco de dados"""
    try:
        if not EXPLICACAO_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Serviço de explicações não disponível")
        
        if not confirmar:
            raise HTTPException(
                status_code=400,
                detail="Parâmetro 'confirmar=true' é obrigatório para limpar explicações antigas"
            )
        
        if dias_manter < 7:
            raise HTTPException(
                status_code=400,
                detail="Período mínimo para manter explicações é de 7 dias"
            )
        
        removidos = explicacao_service.limpar_explicacoes_antigas(dias_manter)
        
        return {
            "sucesso": True,
            "explicacoes_removidas": removidos,
            "dias_mantidos": dias_manter,
            "data_limpeza": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao limpar explicações antigas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/consultas-metadados/{produto_id}")
async def obter_consultas_produto(produto_id: int):
    """
    Obtém todas as consultas realizadas pelos agentes para um produto específico
    """
    try:
        from feedback.consulta_metadados_service import consulta_tracker
        
        consultas = consulta_tracker.obter_consultas_produto(produto_id)
        
        if not consultas:
            # Tentar buscar consultas salvas no banco
            if EXPLICACAO_SERVICE_AVAILABLE:
                explicacoes = explicacao_service.obter_explicacoes_produto(produto_id)
                consultas_salvas = []
                
                for agente, lista_explicacoes in explicacoes.get("explicacoes_por_agente", {}).items():
                    for explicacao in lista_explicacoes:
                        if "consultas_detalhadas" in str(explicacao):
                            consultas_salvas.append({
                                "agente_nome": agente,
                                "fonte": "banco_permanente",
                                "timestamp": explicacao.get("timestamp"),
                                "dados": explicacao
                            })
                
                if consultas_salvas:
                    consultas = consultas_salvas
        
        return {
            "produto_id": produto_id,
            "total_consultas": len(consultas),
            "consultas": consultas,
            "agentes_com_consultas": list(set(c.get("agente_nome", "unknown") for c in consultas)),
            "timestamp_consulta": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter consultas do produto {produto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter consultas")

@app.get("/api/v1/consultas-metadados/{produto_id}/agente/{agente_nome}")
async def obter_consultas_agente(produto_id: int, agente_nome: str):
    """
    Obtém consultas específicas de um agente para um produto
    """
    try:
        from feedback.consulta_metadados_service import consulta_tracker
        
        consultas = consulta_tracker.obter_consultas_por_agente(produto_id, agente_nome)
        
        # Processar consultas para interface
        consultas_processadas = []
        for consulta in consultas:
            consulta_processada = {
                "id": consulta.get("id"),
                "tipo_consulta": consulta.get("tipo_consulta"),
                "banco_origem": consulta.get("banco_origem"),
                "query_original": consulta.get("query_original"),
                "timestamp": consulta.get("timestamp"),
                "metadados": consulta.get("metadados", {}),
                "resultados": consulta.get("resultados", {}),
                "metricas": consulta.get("metricas", {})
            }
            consultas_processadas.append(consulta_processada)
        
        return {
            "produto_id": produto_id,
            "agente_nome": agente_nome,
            "total_consultas": len(consultas_processadas),
            "consultas": consultas_processadas,
            "resumo": {
                "tipos_consulta": list(set(c.get("tipo_consulta") for c in consultas)),
                "bancos_consultados": list(set(c.get("banco_origem") for c in consultas)),
                "tempo_total_ms": sum(c.get("resultados", {}).get("tempo_execucao_ms", 0) for c in consultas)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter consultas do agente {agente_nome}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter consultas do agente")

@app.get("/api/v1/metadados-bancos")
async def obter_metadados_bancos():
    """
    Obtém informações sobre os bancos de dados disponíveis e suas características
    """
    try:
        metadados = {
            "bancos_disponiveis": {
                "faiss_vector": {
                    "nome": "Base Vetorial FAISS",
                    "tipo": "Busca Semântica",
                    "conteudo": "Embeddings de produtos e descrições NCM/CEST",
                    "total_chunks": "101.115 chunks indexados",
                    "modelo_embedding": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensoes": 384,
                    "algoritmo": "FAISS IndexFlatIP"
                },
                "ncm_base": {
                    "nome": "Base Hierárquica NCM",
                    "tipo": "Estrutura Hierárquica",
                    "conteudo": "Códigos NCM oficiais com hierarquia",
                    "total_codigos": "15.141 códigos NCM",
                    "estrutura": "8 dígitos hierárquicos (Capítulo→Posição→Subposição→Item)",
                    "fonte": "Receita Federal do Brasil"
                },
                "cest_base": {
                    "nome": "Base CEST",
                    "tipo": "Mapeamento Tributário",
                    "conteudo": "Códigos CEST e mapeamentos NCM→CEST",
                    "total_codigos": "1.174 mapeamentos CEST",
                    "estrutura": "Segmento.Item.SubItem (XX.XXX.XX)",
                    "fonte": "Convênios CONFAZ"
                },
                "golden_set": {
                    "nome": "Golden Set",
                    "tipo": "Exemplos Validados",
                    "conteudo": "Classificações validadas por humanos",
                    "total_exemplos": "Variável (crescimento contínuo)",
                    "qualidade": "Alta - Revisão humana",
                    "uso": "Aprendizagem e validação"
                },
                "medicamentos_farma": {
                    "nome": "Base ABC Farma",
                    "tipo": "Especializada - Medicamentos",
                    "conteudo": "Medicamentos com GTIN validados",
                    "total_produtos": "388.666 medicamentos",
                    "foco": "Capítulo 30 NCM / Segmento 13 CEST",
                    "validacao": "GTIN verificados"
                }
            },
            "tipos_consulta": {
                "rag": {
                    "descricao": "Busca semântica na base vetorial",
                    "entrada": "Texto livre (descrição do produto)",
                    "saida": "Produtos similares com scores de relevância",
                    "tempo_medio": "< 100ms"
                },
                "ncm_hierarchy": {
                    "descricao": "Navegação hierárquica NCM",
                    "entrada": "Código NCM parcial ou palavras-chave",
                    "saida": "Códigos NCM hierárquicos relacionados",
                    "tempo_medio": "< 50ms"
                },
                "cest_mapping": {
                    "descricao": "Mapeamento NCM para CEST",
                    "entrada": "Código NCM definido",
                    "saida": "CEST correspondente com regras",
                    "tempo_medio": "< 20ms"
                },
                "golden_set": {
                    "descricao": "Consulta a exemplos validados",
                    "entrada": "Descrição do produto ou NCM/CEST",
                    "saida": "Exemplos similares já validados",
                    "tempo_medio": "< 30ms"
                }
            },
            "metricas_qualidade": {
                "relevancia": "Score de similaridade (0.0 a 1.0)",
                "performance": "Tempo de resposta categorizado",
                "cobertura": "Percentual de consultas com resultados",
                "consistencia": "Variação entre consultas similares"
            }
        }
        
        return metadados
        
    except Exception as e:
        logger.error(f"Erro ao obter metadados dos bancos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter metadados")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)