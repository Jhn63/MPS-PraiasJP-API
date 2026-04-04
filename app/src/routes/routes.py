# app/src/routes/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from service.facade import FacadeSingletonController
from schemas.user import User as UserSchema
from models.user_model import User as UserModel
from database.db import get_db
from exceptions.domain_exceptions import UsuarioInvalidoError

router = APIRouter()

# Instanciar a Facade (vai devolver sempre a mesma instância devido ao Singleton)
facade = FacadeSingletonController.get_instance()

@router.get("/")
async def home():
    return {"message": "I'm alive message"}

@router.post("/users/")
async def create_user(user: UserSchema, db: Session = Depends(get_db)):
    try:
        # A rota só conhece a Facade! Não chama o Controller ou Service diretamente.
        user_criado = facade.gerarAcessoUsuario(user, db)
        return {"message": "Utilizador criado com sucesso", "username": user_criado.username}
    except UsuarioInvalidoError as erro:
        # Levanta um erro HTTP 400 em vez de devolver um JSON normal com a chave "error"
        raise HTTPException(status_code=400, detail=str(erro))

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Mais tarde podemos mover isto para a Facade também (ex: facade.buscarUsuario(user_id, db))
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return {"id": db_user.id, "username": db_user.username}