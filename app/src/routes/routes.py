from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from service.facade import FacadeSingletonController
from modules.users.user import User as UserSchema
from modules.users.user_model import User as UserModel
from database.db import get_db
from exceptions.domain_exceptions import UsuarioInvalidoError

router = APIRouter()

# Instanciar a Facade (vai devolver sempre a mesma instância devido ao Singleton)
facade = FacadeSingletonController.get_instance()

@router.get("/")
async def home():
    return {"message": "I'm alive message"}

@router.post("/users/")
async def create_user(user: UserSchema, auth_type: str = "API_KEY", db: Session = Depends(get_db)):
    try:
        # Devolve o usuário e o token
        user_criado, token = facade.gerarAcessoUsuario(user, db, auth_type)
        
        return {
            "message": "Usuário criado com sucesso", 
            "username": user_criado.username,
            "access_token": token,
            "auth_type": auth_type
        }
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except UsuarioInvalidoError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Mais tarde podemos mover isto para a Facade também (ex: facade.buscarUsuario(user_id, db))
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return {"id": db_user.id, "username": db_user.username}