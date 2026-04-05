from sqlalchemy import Integer, String, Column
from database.db import Base

class User(Base):
    __tablename__ = "User"

    id       = Column(Integer, autoincrement=True, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)