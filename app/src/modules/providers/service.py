import logging
from .invoker import Invoker
from .concrete_commands import TabuaMareCabedeloCommand

logger = logging.getLogger(__name__)


class ProvidersService:
    """
    Serviço de alto nível que utiliza Invoker para gerenciar e executar comandos.
    Pode ser estendido para incluir lógica de negócios, validação, etc.
    """
    
    def __init__(self) -> None:
        self.invoker = Invoker()
        # Registra comandos padrão
        self.invoker.register("tabua_mare_cabedelo", TabuaMareCabedeloCommand())

    async def fetch_tabua_mare_cabedelo(self) -> list[dict]:
        """Executa e retorna a tábua de marés de Cabedelo."""
        try:
            result = await self.invoker.execute("tabua_mare_cabedelo")
            logger.info("Tábua de marés obtida com sucesso: %d horas", len(result))
            return result
        except Exception as e:
            logger.error("Erro ao obter tábua de marés: %s", str(e))
            raise
