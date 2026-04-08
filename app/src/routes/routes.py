from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from service.facade import FacadeSingletonController
from modules.users.user import UserCreate
from modules.users.user_model import User as UserModel
from schemas.estacao import EstacaoMonitoramento as EstacaoSchema
from database.db import get_db
from exceptions.domain_exceptions import UsuarioInvalidoError
from middlewares.auth_chain import verificar_acesso

from modules.logger.error_logger import error_logger

router = APIRouter()

# Instanciar a Facade (vai devolver sempre a mesma instância devido ao Singleton)
facade = FacadeSingletonController.get_instance()

@router.get("/")
async def home():
    return {"message": "I'm alive message"}

@router.post("/users/")
async def register_user(user: UserCreate, auth_type: str = "API_KEY", db: Session = Depends(get_db)):
    try:
        # Devolve o usuário e o token
        user_criado, token = facade.gerarAcessoUsuario(user, db, auth_type)
        
        error_logger.info(
            "User registration endpoint accessed",
            username=user.username,
            auth_type=auth_type
        )
        return {
            "message": "Usuário criado com sucesso", 
            "username": user_criado.username,
            "access_token": token,
            "auth_type": auth_type
        }
    except ValueError as erro:
        error_logger.warning(
            "Registration failed - ValueError",
            username=user.username,
            error=str(erro)
        )
        raise HTTPException(status_code=400, detail=str(erro))
    except UsuarioInvalidoError as erro:
        error_logger.warning(
            "Registration failed - UsuarioInvalidoError",
            username=user.username,
            error=str(erro)
        )
        raise HTTPException(status_code=400, detail=str(erro))

@router.post("/login/")
async def login_user(user: UserCreate, auth_type: str = "API_KEY", db: Session = Depends(get_db)):
    try:
        # Autentica o usuário e gera o token
        user_autenticado, token = facade.realizarLogin(user, db, auth_type)
        
        error_logger.info(
            "User login endpoint accessed",
            username=user.username,
            auth_type=auth_type
        )
        return {
            "message": "Login realizado com sucesso",
            "username": user_autenticado.username,
            "access_token": token,
            "auth_type": auth_type
        }
    except ValueError as erro:
        error_logger.warning(
            "Login failed - ValueError",
            username=user.username,
            error=str(erro)
        )
        raise HTTPException(status_code=400, detail=str(erro))
    except UsuarioInvalidoError as erro:
        error_logger.warning(
            "Login failed - UsuarioInvalidoError",
            username=user.username,
            error=str(erro)
        )
        raise HTTPException(status_code=400, detail=str(erro))


# ==================== ESTAÇÃO ROUTES ====================

@router.get("/estacoes/nome/{nome}")
async def get_estacao_by_nome(nome: str, db: Session = Depends(get_db), _: str = Depends(verificar_acesso)):
    try:
        estacao = facade.obterEstacaoPorNome(nome, db)
        
        error_logger.info(
            "Estação retrieved by nome endpoint",
            nome=nome,
            estacao_id=estacao.id
        )
        return {
            "message": "Estação encontrada com sucesso",
            "estacao": {
                "id": estacao.id,
                "nome": estacao.nome,
                "localizacao": estacao.localizacao,
                "status": estacao.status,
                "dataInstall": estacao.dataInstall,
                "nivel_mare": estacao.nivel_mare,
                "baneabilidade": estacao.baneabilidade
            }
        }
    except ValueError as erro:
        error_logger.warning(
            "Get estação by nome - ValueError",
            nome=nome,
            error=str(erro)
        )
        raise HTTPException(status_code=404, detail=str(erro))
    except Exception as erro:
        error_logger.log_exception(
            erro,
            message="Get estação by nome - Unexpected error",
            nome=nome
        )
        raise HTTPException(status_code=500, detail="Erro ao buscar estação")


@router.get("/estacoes/localizacao/{localizacao}")
async def get_estacao_by_localizacao(localizacao: str, db: Session = Depends(get_db), _: str = Depends(verificar_acesso)):
    try:
        estacao = facade.obterEstacaoPorLocalizacao(localizacao, db)
        
        error_logger.info(
            "Estação retrieved by localizacao endpoint",
            localizacao=localizacao,
            estacao_id=estacao.id
        )
        return {
            "message": "Estação encontrada com sucesso",
            "estacao": {
                "id": estacao.id,
                "nome": estacao.nome,
                "localizacao": estacao.localizacao,
                "status": estacao.status,
                "dataInstall": estacao.dataInstall,
                "nivel_mare": estacao.nivel_mare,
                "baneabilidade": estacao.baneabilidade
            }
        }
    except ValueError as erro:
        error_logger.warning(
            "Get estação by localizacao - ValueError",
            localizacao=localizacao,
            error=str(erro)
        )
        raise HTTPException(status_code=404, detail=str(erro))
    except Exception as erro:
        error_logger.log_exception(
            erro,
            message="Get estação by localizacao - Unexpected error",
            localizacao=localizacao
        )
        raise HTTPException(status_code=500, detail="Erro ao buscar estação")


@router.get("/estacoes/status/{status}")
async def list_estacoes_by_status(status: str, db: Session = Depends(get_db), _: str = Depends(verificar_acesso)):
    try:
        estacoes = facade.listarEstacoesPorStatus(status, db)
        
        error_logger.info(
            "Estações listed by status endpoint",
            status=status,
            total=len(estacoes)
        )
        
        estacoes_data = [
            {
                "id": estacao.id,
                "nome": estacao.nome,
                "localizacao": estacao.localizacao,
                "status": estacao.status,
                "dataInstall": estacao.dataInstall,
                "nivel_mare": estacao.nivel_mare,
                "baneabilidade": estacao.baneabilidade
            }
            for estacao in estacoes
        ]
        
        return {
            "message": f"Encontradas {len(estacoes)} estação(ões) com status '{status}'",
            "total": len(estacoes),
            "estacoes": estacoes_data
        }
    except Exception as erro:
        error_logger.log_exception(
            erro,
            message="List estações by status - Unexpected error",
            status=status
        )
        raise HTTPException(status_code=500, detail="Erro ao listar estações")


@router.get("/estacoes/baneabilidade/{baneabilidade}")
async def list_estacoes_by_baneabilidade(baneabilidade: str, db: Session = Depends(get_db), _: str = Depends(verificar_acesso)):
    try:
        estacoes = facade.listarEstacoesPorBaneabilidade(baneabilidade, db)
        
        error_logger.info(
            "Estações listed by baneabilidade endpoint",
            baneabilidade=baneabilidade,
            total=len(estacoes)
        )
        
        estacoes_data = [
            {
                "id": estacao.id,
                "nome": estacao.nome,
                "localizacao": estacao.localizacao,
                "status": estacao.status,
                "dataInstall": estacao.dataInstall,
                "nivel_mare": estacao.nivel_mare,
                "baneabilidade": estacao.baneabilidade
            }
            for estacao in estacoes
        ]
        
        return {
            "message": f"Encontradas {len(estacoes)} estação(ões) com baneabilidade '{baneabilidade}'",
            "total": len(estacoes),
            "estacoes": estacoes_data
        }
    except Exception as erro:
        error_logger.log_exception(
            erro,
            message="List estações by baneabilidade - Unexpected error",
            baneabilidade=baneabilidade
        )
        raise HTTPException(status_code=500, detail="Erro ao listar estações")