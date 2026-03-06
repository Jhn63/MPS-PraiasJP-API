from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EstacaoMonitoramento(BaseModel):
    id: Optional[int] = None
    nome: str
    localizacao: str
    dataInstall: Optional[datetime] = None
    status: str