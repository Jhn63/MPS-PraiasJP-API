from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from schemas.user import User
from models.user_model import User as UserModel
from database.db import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
async def home():
    return {"message": "I'm alive message"}

@router.post("/users/")
async def create_user(user : User, db: Session = Depends(get_db)):
    db_user = UserModel(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "post successful", "id": db_user.id, "username": db_user.username}


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        return {"error": "User not found"}
    return {"id": db_user.id, "username": db_user.username}