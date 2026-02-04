from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import service.user_service as UserService
from schemas.user import User
from models.user_model import User as UserModel
from database.db import get_db

router = APIRouter()

@router.get("/")
async def home():
    return {"message": "I'm alive message"}

@router.post("/users/")
async def create_user(user : User, db: Session = Depends(get_db)):
    try:
        UserService.create_user(user, db)
    except ValueError as ve:
        return {"error": str(ve)}

    return {"message": "post successful"}

#beta version
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        return {"error": "User not found"}
    return {"id": db_user.id, "username": db_user.username}