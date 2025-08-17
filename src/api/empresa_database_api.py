"""
API Endpoints para Gerenciamento de Bancos de Dados por Empresa
Expõe funcionalidades do sistema de classificação com bancos segregados
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.services.empresa_classificacao_service import EmpresaClassificacaoService
from src.orchestrator.hybrid_router import HybridRouter

# Modelos Pydantic
class ProdutoRequest(BaseModel):
    gtin: Optional[str] = None
    nome_produto: str
    descricao_original: Optional[str] = None
    descricao_enriquecida: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    peso: Optional[float] = None
    unidade_medida: Optional[str] = None
    preco: Optional[float] = None
    usuario: Optional[str] = "api"

class ClassificacaoAprovacaoRequest(BaseModel):
    usuario: str
    observacoes: Optional[str] = ""

class ClassificacaoRejeicaoRequest(BaseModel):
    usuario: str
    motivo: str

class EmpresaInicializacaoRequest(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    tipo_atividade: str
    descricao_atividade: Optional[str] = None
    canal_venda: str
    porte_empresa: Optional[str] = None
    regime_tributario: Optional[str] = None

# Router
router = APIRouter(prefix="/api/v1/empresa-db", tags=["Empresa Database"])

# Instância do serviço
classificacao_service = EmpresaClassificacaoService()

# Dependência para o HybridRouter
async def get_hybrid_router():
    """Dependency para obter instância do HybridRouter"""
    try:
        from src.orchestrator.hybrid_router import HybridRouter
        return HybridRouter()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar HybridRouter: {str(e)}")

@router.post("/inicializar")
async def inicializar_empresa(empresa_data: EmpresaInicializacaoRequest) -> Dict[str, Any]:
    """
    Inicializa uma nova empresa no sistema com banco de dados próprio
    """
    try:
        resultado = classificacao_service.inicializar_empresa(empresa_data.dict())
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas")
async def listar_empresas() -> List[Dict[str, Any]]:
    """
    Lista todas as empresas com seus bancos de dados
    """
    try:
        return classificacao_service.listar_empresas()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas/{empresa_id}/stats")
async def obter_estatisticas_empresa(empresa_id: int) -> Dict[str, Any]:
    """
    Obtém estatísticas de uma empresa específica
    """
    try:
        stats = classificacao_service.db_manager.get_empresa_stats(empresa_id)
        
        if "erro" in stats:
            raise HTTPException(status_code=404, detail=stats["erro"])
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas/{empresa_id}/relatorio")
async def obter_relatorio_empresa(empresa_id: int) -> Dict[str, Any]:
    """
    Gera relatório completo de uma empresa
    """
    try:
        relatorio = classificacao_service.get_relatorio_empresa(empresa_id)
        
        if "erro" in relatorio:
            raise HTTPException(status_code=404, detail=relatorio["erro"])
        
        return relatorio
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/empresas/{empresa_id}/produtos")
async def classificar_produto(
    empresa_id: int, 
    produto_data: ProdutoRequest,
    hybrid_router: HybridRouter = Depends(get_hybrid_router)
) -> Dict[str, Any]:
    """
    Classifica um produto para uma empresa específica
    """
    try:
        resultado = classificacao_service.classificar_produto_empresa(
            empresa_id, produto_data.dict(), hybrid_router
        )
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas/{empresa_id}/produtos/{produto_id}")
async def obter_produto_detalhado(empresa_id: int, produto_id: int) -> Dict[str, Any]:
    """
    Obtém detalhes completos de um produto incluindo histórico de agentes
    """
    try:
        detalhes = classificacao_service.db_manager.get_produto_detalhado(empresa_id, produto_id)
        
        if "erro" in detalhes:
            raise HTTPException(status_code=404, detail=detalhes["erro"])
        
        return detalhes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/empresas/{empresa_id}/classificacoes/{classificacao_id}/aprovar")
async def aprovar_classificacao(
    empresa_id: int, 
    classificacao_id: int,
    aprovacao_data: ClassificacaoAprovacaoRequest
) -> Dict[str, Any]:
    """
    Aprova uma classificação específica
    """
    try:
        resultado = classificacao_service.aprovar_classificacao(
            empresa_id, classificacao_id, aprovacao_data.usuario, aprovacao_data.observacoes
        )
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/empresas/{empresa_id}/classificacoes/{classificacao_id}/rejeitar")
async def rejeitar_classificacao(
    empresa_id: int, 
    classificacao_id: int,
    rejeicao_data: ClassificacaoRejeicaoRequest
) -> Dict[str, Any]:
    """
    Rejeita uma classificação específica
    """
    try:
        resultado = classificacao_service.rejeitar_classificacao(
            empresa_id, classificacao_id, rejeicao_data.usuario, rejeicao_data.motivo
        )
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/empresas/{empresa_id}/produtos/{produto_id}/golden-set")
async def adicionar_ao_golden_set(
    empresa_id: int, 
    produto_id: int,
    usuario: Optional[str] = "api"
) -> Dict[str, Any]:
    """
    Adiciona um produto aprovado ao Golden Set compartilhado
    """
    try:
        resultado = classificacao_service.adicionar_ao_golden_set(
            empresa_id, produto_id, usuario
        )
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/golden-set")
async def listar_golden_set(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Lista produtos do Golden Set compartilhado
    """
    try:
        import sqlite3
        
        with sqlite3.connect(classificacao_service.db_manager.golden_set_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Contar total
            cursor.execute("SELECT COUNT(*) FROM golden_set_produtos WHERE ativo = 1")
            total = cursor.fetchone()[0]
            
            # Buscar produtos
            cursor.execute("""
                SELECT * FROM golden_set_produtos 
                WHERE ativo = 1 
                ORDER BY data_atualizacao DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            produtos = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "produtos": produtos
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/golden-set/{golden_id}/validacoes")
async def obter_validacoes_golden_set(golden_id: int) -> List[Dict[str, Any]]:
    """
    Obtém validações de um produto do Golden Set
    """
    try:
        import sqlite3
        
        with sqlite3.connect(classificacao_service.db_manager.golden_set_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM golden_set_validacoes 
                WHERE produto_golden_id = ? 
                ORDER BY data_validacao DESC
            """, (golden_id,))
            
            validacoes = [dict(row) for row in cursor.fetchall()]
            
            return validacoes
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas/{empresa_id}/produtos")
async def listar_produtos_empresa(
    empresa_id: int, 
    limit: int = 50, 
    offset: int = 0,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista produtos de uma empresa com paginação
    """
    try:
        import sqlite3
        
        db_path = classificacao_service.db_manager.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Construir query com filtros
            where_clause = "WHERE p.ativo = 1"
            params = []
            
            if status:
                where_clause += " AND c.status = ?"
                params.append(status)
            
            # Contar total
            count_query = f"""
                SELECT COUNT(DISTINCT p.id) 
                FROM produtos_empresa p 
                LEFT JOIN classificacoes c ON p.id = c.produto_id 
                {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Buscar produtos
            params.extend([limit, offset])
            query = f"""
                SELECT p.*, c.ncm_codigo, c.cest_codigo, c.status as status_classificacao,
                       c.confianca_ncm, c.confianca_cest, c.data_classificacao
                FROM produtos_empresa p 
                LEFT JOIN classificacoes c ON p.id = c.produto_id 
                {where_clause}
                ORDER BY p.data_cadastro DESC 
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, params)
            produtos = [dict(row) for row in cursor.fetchall()]
            
            return {
                "empresa_id": empresa_id,
                "total": total,
                "limit": limit,
                "offset": offset,
                "produtos": produtos
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/empresas/{empresa_id}/agentes/performance")
async def obter_performance_agentes(empresa_id: int) -> Dict[str, Any]:
    """
    Obtém métricas de performance dos agentes para uma empresa
    """
    try:
        import sqlite3
        
        db_path = classificacao_service.db_manager.get_empresa_db_path(empresa_id)
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Performance geral por agente
            cursor.execute("""
                SELECT 
                    agente_nome,
                    COUNT(*) as total_acoes,
                    AVG(tempo_execucao) as tempo_medio,
                    SUM(CASE WHEN sucesso = 1 THEN 1 ELSE 0 END) as sucessos,
                    AVG(confianca) as confianca_media,
                    COUNT(DISTINCT produto_id) as produtos_processados
                FROM agente_acoes
                GROUP BY agente_nome
                ORDER BY total_acoes DESC
            """)
            
            performance = [dict(row) for row in cursor.fetchall()]
            
            # Consultas por agente
            cursor.execute("""
                SELECT 
                    agente_nome,
                    tipo_consulta,
                    COUNT(*) as total_consultas,
                    AVG(resultados_encontrados) as media_resultados,
                    AVG(relevancia_score) as relevancia_media,
                    AVG(tempo_resposta) as tempo_medio_resposta
                FROM agente_consultas
                GROUP BY agente_nome, tipo_consulta
                ORDER BY total_consultas DESC
            """)
            
            consultas = [dict(row) for row in cursor.fetchall()]
            
            return {
                "empresa_id": empresa_id,
                "performance_agentes": performance,
                "consultas_agentes": consultas
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
