import re
from sqlalchemy.orm import Session

from schemas.user import User
from models.user_model import User as UserModel

password_pattern = re.compile(
    '''
    ^(?=\S{8,128}$)          # length between 8 and 128 characters
    (?=.*?\d)                # at least 1 digits
    (?=.*?[a-z])             # at least 1 lowercase letter
    (?=.*?[A-Z])             # at least 1 uppercase letter
    (?=.*?[!@#$%^&*()-+=])   # at least 1 special character
    ''')

def create_user(user: User, db: Session):
    if not re.match(r"^\S{1,12}$", user.username):
        raise ValueError("Invalid username format")
    if not re.match(password_pattern, user.password):
        raise ValueError("Invalid password format")

    db_user = UserModel(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)