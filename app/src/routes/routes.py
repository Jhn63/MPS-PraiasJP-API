from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from service.facade import FacadeSingletonController
from modules.users.user import UserCreate
from modules.users.user_model import User as UserModel
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