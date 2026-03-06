import re
from sqlalchemy.orm import Session

from schemas.user import User
from models.user_model import User as UserModel

# Substitua o password_pattern gigante por este aqui:
password_pattern = re.compile(r"^(?=\S{8,128}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[!@#$%^&*()-+=]).*$")

def create_user(user: User, db: Session):
    if not re.match(r"^\S{1,12}$", user.username):
        raise ValueError("Invalid username format")
    if not re.match(password_pattern, user.password):
        raise ValueError("Invalid password format")

    db_user = UserModel(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)