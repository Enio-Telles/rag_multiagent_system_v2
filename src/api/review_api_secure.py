"""
API REST para Interface de Revisão Humana - Fase 4 (Versão Segura)
Implementa endpoints para revisão, aprovação e correção de classificações
Com gestão completa de GTIN, Golden Set e segurança aprimorada
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
import sys
import os
from pathlib import Path
import secrets
import hashlib
import re
from html import escape
import jwt

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

# Configurações de segurança
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Sistema de autenticação
security = HTTPBearer()

# Usuários válidos do sistema (em produção, usar banco de dados)
VALID_USERS = {
    "ana.silva@empresa.com": {
        "name": "Ana Silva",
        "email": "ana.silva@empresa.com",
        "role": "revisor",
        "password_hash": hashlib.sha256("senha123".encode()).hexdigest()  # Em produção, usar bcrypt
    },
    "admin@empresa.com": {
        "name": "Administrador",
        "email": "admin@empresa.com", 
        "role": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest()
    }
}

app = FastAPI(
    title="Sistema de Classificação Fiscal - API de Revisão Segura",
    description="API para revisão humana de classificações fiscais NCM/CEST com gestão de GTIN, Golden Set e segurança aprimorada",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Domínios específicos em produção
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    codigo_barra: Optional[str]  # Código de barras
    ncm_original: Optional[str]  # NCM original do banco
    cest_original: Optional[str]  # CEST original do banco  
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
    codigo_barra: Optional[str] = None  # Código de barras extraído do PostgreSQL
    codigo_barra_status: Optional[str] = None  # "PENDENTE_VERIFICACAO", "CORRETO", "INCORRETO", "NAO_APLICAVEL"
    ncm_original: Optional[str] = None  # NCM original do banco
    cest_original: Optional[str] = None  # CEST original do banco
    ncm_sugerido: Optional[str] = None
    cest_sugerido: Optional[str] = None
    confianca_sugerida: Optional[float] = None
    status_revisao: str
    justificativa_sistema: Optional[str] = None
    dados_trace_json: Optional[Dict[str, Any]] = None
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    codigo_barra_corrigido: Optional[str] = None  # Código de barras corrigido pelo revisor
    codigo_barra_observacoes: Optional[str] = None  # Observações sobre correções
    justificativa_correcao: Optional[str] = None
    revisado_por: Optional[str] = None
    data_revisao: Optional[datetime] = None
    descricao_completa: Optional[str] = None

class RevisaoRequest(BaseModel):
    acao: str  # "APROVAR", "CORRIGIR" ou "GOLDEN_SET"
    ncm_corrigido: Optional[str] = None
    cest_corrigido: Optional[str] = None
    codigo_barra_acao: str = "MANTER"  # "MANTER", "CORRIGIR", "REMOVER"
    codigo_barra_corrigido: Optional[str] = None  # Novo código de barras se acao = "CORRIGIR"
    codigo_barra_observacoes: Optional[str] = None  # Observações sobre o código de barras
    descricao_completa: Optional[str] = None  # Descrição mais detalhada do produto
    justificativa_correcao: Optional[str] = None
    revisado_por: str
    incluir_golden_set: bool = False  # Se deve incluir no Golden Set
    
    @validator('acao')
    def validate_acao(cls, v):
        if v not in ["APROVAR", "CORRIGIR", "GOLDEN_SET"]:
            raise ValueError('Ação deve ser APROVAR, CORRIGIR ou GOLDEN_SET')
        return v
    
    @validator('ncm_corrigido')
    def validate_ncm(cls, v):
        if v and not validate_ncm_cest(v):
            raise ValueError('NCM deve ter 8 dígitos')
        return v
    
    @validator('cest_corrigido')
    def validate_cest(cls, v):
        if v and not validate_ncm_cest(v):
            raise ValueError('CEST deve ter formato XX.XXX.XX')
        return v

class CodigoBarraValidacao(BaseModel):
    codigo_barra: str
    valido: bool
    tipo: Optional[str]  # "EAN13", "UPC", "EAN8", etc.
    detalhes: Optional[str]

class DashboardStats(BaseModel):
    total_classificacoes: int
    pendentes_revisao: int
    aprovadas: int
    corrigidas: int
    taxa_aprovacao: float
    confianca_media: float
    tempo_medio_revisao: Optional[float]
    distribuicao_confianca: Dict[str, int]

class LoginRequest(BaseModel):
    email: str
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v.lower()

class UserResponse(BaseModel):
    name: str
    email: str
    role: str
    token: str

# Funções de segurança
def sanitize_input(text: str) -> str:
    """Sanitiza entrada do usuário para prevenir XSS"""
    if not text:
        return ""
    # Escapar HTML
    sanitized = escape(text)
    # Remover caracteres perigosos
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    return sanitized.strip()

def validate_ncm_cest(code: str) -> bool:
    """Valida formato de códigos NCM/CEST"""
    if not code:
        return True  # Opcional
    # NCM: 8 dígitos, CEST: formato XX.XXX.XX
    ncm_pattern = r'^\d{8}$'
    cest_pattern = r'^\d{2}\.\d{3}\.\d{2}$'
    return bool(re.match(ncm_pattern, code) or re.match(cest_pattern, code))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        if email not in VALID_USERS:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return VALID_USERS[email]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Inicializar serviços
review_service = ReviewService()
metrics_service = MetricsService()

# Endpoints de autenticação
@app.post("/api/v1/auth/login", response_model=UserResponse)
async def login(login_data: LoginRequest):
    """Endpoint de login com autenticação JWT"""
    try:
        email = login_data.email.lower()
        password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
        
        if email not in VALID_USERS:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        user = VALID_USERS[email]
        if user["password_hash"] != password_hash:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Criar token
        access_token = create_access_token(data={"sub": email})
        
        return UserResponse(
            name=user["name"],
            email=user["email"],
            role=user["role"],
            token=access_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/auth/me")
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Retorna informações do usuário atual"""
    return {
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }

@app.get("/")
async def interface_principal():
    """Servir interface principal de revisão"""
    static_file = Path(__file__).parent / "static" / "interface_revisao_secure.html"
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Lista classificações para revisão com filtros opcionais
    """
    try:
        # Sanitizar parâmetros de entrada
        if status:
            status = sanitize_input(status)
        
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retorna o próximo produto pendente de revisão
    """
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retorna todos os detalhes de uma classificação específica
    """
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Endpoint principal para revisão de classificações por especialistas
    """
    try:
        # Sanitizar dados de entrada
        if revisao.justificativa_correcao:
            revisao.justificativa_correcao = sanitize_input(revisao.justificativa_correcao)
        if revisao.descricao_completa:
            revisao.descricao_completa = sanitize_input(revisao.descricao_completa)
        if revisao.codigo_barra_observacoes:
            revisao.codigo_barra_observacoes = sanitize_input(revisao.codigo_barra_observacoes)
        
        # Validar dados de entrada
        if revisao.acao not in ["APROVAR", "CORRIGIR"]:
            raise HTTPException(status_code=400, detail="Ação deve ser 'APROVAR' ou 'CORRIGIR'")
        
        if revisao.acao == "CORRIGIR" and not (revisao.ncm_corrigido or revisao.cest_corrigido):
            raise HTTPException(
                status_code=400, 
                detail="Para corrigir, deve fornecer pelo menos NCM ou CEST corrigido"
            )
        
        # Usar email do usuário autenticado
        revisao.revisado_por = current_user["email"]
        
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retorna estatísticas para o dashboard de monitoramento
    """
    try:
        stats = metrics_service.calcular_estatisticas(db=db, periodo_dias=periodo_dias)
        return stats
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/codigo-barra/validar", response_model=CodigoBarraValidacao)
async def validar_codigo_barra(
    codigo_barra: str,
    current_user: dict = Depends(verify_token)
):
    """
    Valida um código de barras (EAN, UPC, etc.)
    NOTA: Esta validação é apenas técnica. A verificação se o código está correto
    para o produto deve ser feita por humanos no sistema de revisão.
    """
    try:
        # Sanitizar entrada
        codigo_barra = sanitize_input(codigo_barra)
        validacao = _validar_codigo_barra_formato(codigo_barra)
        return validacao
    except Exception as e:
        logger.error(f"Erro ao validar código de barras {codigo_barra}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/golden-set/adicionar")
async def adicionar_ao_golden_set(
    produto_id: int,
    justificativa: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Adiciona uma classificação aprovada ao Golden Set para aprendizagem contínua
    """
    try:
        # Sanitizar entrada
        justificativa = sanitize_input(justificativa)
        
        resultado = review_service.adicionar_ao_golden_set(
            db=db,
            produto_id=produto_id,
            justificativa=justificativa,
            revisado_por=current_user["email"]
        )
        return resultado
    except Exception as e:
        logger.error(f"Erro ao adicionar ao Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/golden-set/estatisticas")
async def estatisticas_golden_set(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retorna estatísticas do Golden Set
    """
    try:
        stats = review_service.obter_estatisticas_golden_set(db=db)
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas Golden Set: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# Funções auxiliares para código de barras
def _validar_codigo_barra_formato(codigo_barra: str) -> CodigoBarraValidacao:
    """
    Valida formato de código de barras usando algoritmo de checksum
    NOTA: Esta é apenas uma validação de formato. A verificação se o código
    está correto para o produto deve ser feita por humanos no sistema de revisão.
    """
    if not codigo_barra:
        return CodigoBarraValidacao(
            codigo_barra="",
            valido=False,
            tipo=None,
            detalhes="Código vazio"
        )
    
    # Remover espaços e caracteres especiais
    codigo_limpo = re.sub(r'[^0-9]', '', codigo_barra)
    
    if not codigo_limpo:
        return CodigoBarraValidacao(
            codigo_barra=codigo_barra,
            valido=False,
            tipo=None,
            detalhes="Código não contém dígitos válidos"
        )
    
    # Identificar tipo de código de barras
    comprimento = len(codigo_limpo)
    tipo_codigo = None
    
    if comprimento == 8:
        tipo_codigo = "EAN8"
    elif comprimento == 12:
        tipo_codigo = "UPC"
    elif comprimento == 13:
        tipo_codigo = "EAN13"
    elif comprimento == 14:
        tipo_codigo = "EAN14"
    else:
        return CodigoBarraValidacao(
            codigo_barra=codigo_barra,
            valido=False,
            tipo=None,
            detalhes=f"Comprimento inválido: {comprimento} dígitos"
        )
    
    # Validar checksum (algoritmo padrão EAN/UPC)
    try:
        digitos = [int(d) for d in codigo_limpo]
        if len(digitos) == 0:
            raise ValueError("Lista de dígitos vazia")
            
        checksum_calculado = _calcular_checksum_codigo_barra(digitos[:-1])
        checksum_original = digitos[-1]
        
        valido = checksum_calculado == checksum_original
        
        return CodigoBarraValidacao(
            codigo_barra=codigo_limpo,
            valido=valido,
            tipo=tipo_codigo,
            detalhes="Checksum válido" if valido else f"Checksum inválido (esperado: {checksum_calculado})"
        )
    except (ValueError, IndexError) as e:
        return CodigoBarraValidacao(
            codigo_barra=codigo_barra,
            valido=False,
            tipo=tipo_codigo,
            detalhes=f"Erro na validação: {str(e)}"
        )

def _calcular_checksum_codigo_barra(digitos: List[int]) -> int:
    """
    Calcula o dígito verificador para código de barras (EAN/UPC)
    """
    if not digitos:
        raise ValueError("Lista de dígitos não pode estar vazia")
    
    soma = 0
    for i, digito in enumerate(reversed(digitos)):
        peso = 3 if i % 2 == 0 else 1
        soma += digito * peso
    
    resto = soma % 10
    return (10 - resto) % 10

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)