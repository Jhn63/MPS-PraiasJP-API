from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id       : Optional[int] = None
    username : str
    password : str

class UserCreate(BaseModel):
    username : str
    password : str

class UserRead(BaseModel):
    id       : int
    username : str