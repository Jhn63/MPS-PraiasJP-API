from sqlalchemy import Integer, String, Column, DateTime
import datetime
from database.db import Base

class EstacaoMonitoramento(Base):
    __tablename__ = "EstacaoMonitoramento"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    nome = Column(String, index=True)
    localizacao = Column(String)
    dataInstall = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)