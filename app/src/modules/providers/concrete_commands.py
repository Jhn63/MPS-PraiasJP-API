from datetime import datetime
from .commands import BaseCommand, HttpReceiver
import httpx


class TabuaMareCabedeloCommand(BaseCommand):
    """Command concreto para obter a tábua de marés do porto de Cabedelo do dia atual."""
    
    def __init__(self, receiver: HttpReceiver | None = None):
        super().__init__(
            receiver=receiver,
            base_url="https://tabuamare.devtu.qzz.io/api/v2",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10.0
        )
    
    async def connect(self) -> None:
        """Conecta ao receiver HttpReceiver."""
        await self._receiver.connect()

    async def fetch(self) -> httpx.Response:
        """Faz a requisição GET para obter a tábua de marés do dia atual."""
        now = datetime.now()
        response = await self._receiver.get(f"tabua-mare/pb01/{now.month}/{now.day}")
        response.raise_for_status()  # Levanta erro para status HTTP ruins
        return response
    
    async def parse(self, response: httpx.Response) -> list[dict]:
        """Extrai apenas o campo hours do JSON retornado."""
        data = response.json()
        # Navega na estrutura aninhada: data -> months -> days -> hours
        try:
            hours = data.get("data", [{}])[0].get("months", [{}])[0].get("days", [{}])[0].get("hours", [])
            return hours
        except (IndexError, TypeError, AttributeError):
            return []