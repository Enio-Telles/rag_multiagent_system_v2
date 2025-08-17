"""
API RESTful Multiempresa com Segurança Avançada
Implementação completa com autenticação JWT e autorização RBAC
"""

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import jwt
from datetime import datetime, timedelta
from enum import Enum
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums para papéis e permissões
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"      # Acesso a todas as empresas
    EMPRESA_ADMIN = "empresa_admin"   # Admin de uma empresa específica
    REVISOR = "revisor"              # Pode revisar classificações
    OPERADOR = "operador"            # Pode classificar produtos
    CONSULTOR = "consultor"          # Apenas leitura

class Permission(str, Enum):
    READ_EMPRESA = "read_empresa"
    WRITE_EMPRESA = "write_empresa"
    MANAGE_USERS = "manage_users"
    APPROVE_CLASSIFICATIONS = "approve_classifications"
    ACCESS_AUDIT = "access_audit"

# Modelos Pydantic para requests/responses
class EmpresaCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    cnpj: str = Field(..., regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    tipo_atividade: str
    descricao_atividade: Optional[str] = None
    canal_venda: str
    porte_empresa: Optional[str] = None
    regime_tributario: Optional[str] = None
    origem_db_config: Dict[str, Any]  # Configuração do PostgreSQL de origem

class EmpresaResponse(BaseModel):
    id: int
    nome: str
    cnpj: str
    tipo_atividade: str
    ativo: bool
    data_criacao: datetime
    
class IngestaoRequest(BaseModel):
    tabela_origem: str
    filtros: Optional[Dict[str, Any]] = None
    limite_registros: Optional[int] = None

class ClassificacaoRequest(BaseModel):
    produtos_ids: Optional[List[int]] = None  # Se None, classifica todos pendentes
    modo_batch: bool = True
    prioridade: str = "normal"  # alta, normal, baixa

class UserTokenData(BaseModel):
    user_id: str
    email: str
    roles: List[UserRole]
    empresa_permissions: Dict[int, List[Permission]]  # empresa_id -> permissões
    exp: datetime

# Segurança JWT
security = HTTPBearer()

class JWTManager:
    """Gerenciador de tokens JWT"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Cria um token de acesso"""
        to_encode = user_data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> UserTokenData:
        """Verifica e decodifica um token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return UserTokenData(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

jwt_manager = JWTManager("your-secret-key-here")  # Em produção, usar variável de ambiente

# Dependências de autenticação e autorização
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> UserTokenData:
    """Extrai e valida o usuário atual do token JWT"""
    token = credentials.credentials
    user_data = jwt_manager.verify_token(token)
    
    # Log de acesso
    logger.info(f"Usuário {user_data.user_id} acessou o sistema")
    
    return user_data

async def get_empresa_access(
    empresa_id: int,
    required_permission: Permission,
    current_user: UserTokenData = Depends(get_current_user)
) -> UserTokenData:
    """Valida acesso do usuário a uma empresa específica"""
    
    # Super admin tem acesso a tudo
    if UserRole.SUPER_ADMIN in current_user.roles:
        return current_user
    
    # Verificar permissões específicas da empresa
    empresa_permissions = current_user.empresa_permissions.get(empresa_id, [])
    
    if required_permission not in empresa_permissions:
        # Log de tentativa não autorizada
        logger.warning(f"Usuário {current_user.user_id} tentou acessar empresa {empresa_id} sem permissão {required_permission}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sem permissão para {required_permission} na empresa {empresa_id}"
        )
    
    return current_user

# Criação da aplicação FastAPI
app = FastAPI(
    title="Sistema de Classificação Fiscal Multiempresa",
    description="API para classificação automatizada de produtos com IA",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middlewares de segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

# =====================================
# ENDPOINTS DA API
# =====================================

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Endpoint de autenticação"""
    # Aqui seria validado com banco de usuários
    # Por simplicidade, exemplo básico
    
    if email == "admin@empresa.com" and password == "senha123":
        user_data = {
            "user_id": "user123",
            "email": email,
            "roles": [UserRole.SUPER_ADMIN],
            "empresa_permissions": {
                1: [Permission.READ_EMPRESA, Permission.WRITE_EMPRESA, Permission.APPROVE_CLASSIFICATIONS],
                2: [Permission.READ_EMPRESA]
            }
        }
        
        token = jwt_manager.create_access_token(user_data)
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.post("/api/empresas", response_model=EmpresaResponse)
async def criar_empresa(
    empresa_data: EmpresaCreateRequest,
    current_user: UserTokenData = Depends(get_current_user)
) -> EmpresaResponse:
    """
    Cria uma nova empresa no sistema
    Requer: Papel SUPER_ADMIN
    """
    
    # Validar permissões
    if UserRole.SUPER_ADMIN not in current_user.roles:
        raise HTTPException(status_code=403, detail="Apenas super admins podem criar empresas")
    
    try:
        # Usar o contexto manager e DI
        from src.core.empresa_context_manager import empresa_context_manager
        from src.services.empresa_classificacao_service import EmpresaClassificacaoService
        
        service = EmpresaClassificacaoService()
        resultado = service.inicializar_empresa(empresa_data.dict())
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=400, detail=resultado["erro"])
        
        # Log de auditoria
        logger.info(f"Empresa {resultado['empresa_id']} criada por {current_user.user_id}")
        
        return EmpresaResponse(
            id=resultado["empresa_id"],
            nome=empresa_data.nome,
            cnpj=empresa_data.cnpj,
            tipo_atividade=empresa_data.tipo_atividade,
            ativo=True,
            data_criacao=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar empresa: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/empresas", response_model=List[EmpresaResponse])
async def listar_empresas(
    current_user: UserTokenData = Depends(get_current_user)
) -> List[EmpresaResponse]:
    """
    Lista empresas acessíveis ao usuário
    """
    
    try:
        from src.services.empresa_classificacao_service import EmpresaClassificacaoService
        
        service = EmpresaClassificacaoService()
        empresas = service.listar_empresas()
        
        # Filtrar apenas empresas que o usuário tem acesso
        if UserRole.SUPER_ADMIN not in current_user.roles:
            empresas_acessiveis = [
                emp for emp in empresas 
                if emp["empresa_id"] in current_user.empresa_permissions
            ]
        else:
            empresas_acessiveis = empresas
        
        return [
            EmpresaResponse(
                id=emp["empresa_id"],
                nome=emp["info"]["nome"],
                cnpj=emp["info"].get("cnpj", ""),
                tipo_atividade=emp["info"]["tipo_atividade"],
                ativo=True,
                data_criacao=datetime.now()
            )
            for emp in empresas_acessiveis
        ]
        
    except Exception as e:
        logger.error(f"Erro ao listar empresas: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/empresas/{empresa_id}/ingestao")
async def iniciar_ingestao_dados(
    empresa_id: int,
    ingestao_data: IngestaoRequest,
    current_user: UserTokenData = Depends(
        lambda: get_empresa_access(empresa_id, Permission.WRITE_EMPRESA)
    )
):
    """
    Inicia processo de extração de dados do PostgreSQL de origem
    Requer: WRITE_EMPRESA permission
    """
    
    try:
        # Usar context manager para operação
        from src.core.empresa_context_manager import empresa_context_manager
        
        with empresa_context_manager.empresa_context(empresa_id, current_user.user_id) as ctx:
            # Implementar serviço de ingestão
            from src.services.ingestao_service import IngestaoService
            
            ingestao_service = IngestaoService(ctx)
            job_id = ingestao_service.iniciar_ingestao(
                tabela_origem=ingestao_data.tabela_origem,
                filtros=ingestao_data.filtros,
                limite_registros=ingestao_data.limite_registros
            )
            
            return {
                "job_id": job_id,
                "status": "iniciado",
                "empresa_id": empresa_id,
                "estimativa_tempo": "5-10 minutos"
            }
            
    except Exception as e:
        logger.error(f"Erro na ingestão para empresa {empresa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao iniciar ingestão")

@app.post("/api/empresas/{empresa_id}/classificacao")
async def iniciar_classificacao(
    empresa_id: int,
    classificacao_data: ClassificacaoRequest,
    current_user: UserTokenData = Depends(
        lambda: get_empresa_access(empresa_id, Permission.WRITE_EMPRESA)
    )
):
    """
    Inicia processo de classificação de produtos
    Requer: WRITE_EMPRESA permission
    """
    
    try:
        from src.core.empresa_context_manager import empresa_context_manager
        
        with empresa_context_manager.empresa_context(empresa_id, current_user.user_id) as ctx:
            from src.services.classificacao_batch_service import ClassificacaoBatchService
            
            batch_service = ClassificacaoBatchService(ctx)
            job_id = batch_service.iniciar_classificacao_batch(
                produtos_ids=classificacao_data.produtos_ids,
                modo_batch=classificacao_data.modo_batch,
                prioridade=classificacao_data.prioridade
            )
            
            return {
                "job_id": job_id,
                "status": "iniciado",
                "empresa_id": empresa_id,
                "modo": "batch" if classificacao_data.modo_batch else "individual"
            }
            
    except Exception as e:
        logger.error(f"Erro na classificação para empresa {empresa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao iniciar classificação")

@app.get("/api/empresas/{empresa_id}/revisao")
async def obter_dados_revisao(
    empresa_id: int,
    status: Optional[str] = "pendente",
    limit: int = 50,
    offset: int = 0,
    current_user: UserTokenData = Depends(
        lambda: get_empresa_access(empresa_id, Permission.READ_EMPRESA)
    )
):
    """
    Obtém dados para interface de revisão
    Requer: READ_EMPRESA permission
    """
    
    try:
        from src.core.empresa_context_manager import empresa_context_manager
        
        with empresa_context_manager.empresa_context(empresa_id, current_user.user_id) as ctx:
            from src.services.revisao_service import RevisaoService
            
            revisao_service = RevisaoService(ctx)
            dados_revisao = revisao_service.obter_classificacoes_revisao(
                status=status,
                limit=limit,
                offset=offset
            )
            
            return dados_revisao
            
    except Exception as e:
        logger.error(f"Erro ao obter dados de revisão para empresa {empresa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter dados de revisão")

@app.get("/api/empresas/{empresa_id}/auditoria")
async def obter_logs_auditoria(
    empresa_id: int,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    usuario_filtro: Optional[str] = None,
    acao_filtro: Optional[str] = None,
    current_user: UserTokenData = Depends(
        lambda: get_empresa_access(empresa_id, Permission.ACCESS_AUDIT)
    )
):
    """
    Obtém logs de auditoria da empresa
    Requer: ACCESS_AUDIT permission
    """
    
    try:
        from src.services.auditoria_service import AuditoriaService
        
        logs = AuditoriaService.obter_logs_empresa(
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            usuario_filtro=usuario_filtro,
            acao_filtro=acao_filtro
        )
        
        return {
            "empresa_id": empresa_id,
            "total_registros": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter auditoria para empresa {empresa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter logs de auditoria")

# Health check
@app.get("/api/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
