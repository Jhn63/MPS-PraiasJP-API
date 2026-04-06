
import logging
from typing import Any
from .commands import CommandProtocol


logger = logging.getLogger(__name__)

class Invoker:
    """
    Invoker do padrão Command.
 
    Mantém um registry de Commands indexados por chave string.
    Não conhece nenhuma implementação concreta — só o protocolo.
 
    Uso:
        invoker = Invoker()
        invoker.register("users", UsersFetchCommand(...))
        result  = await invoker.execute("users")
        results = await invoker.execute_all()
    """
 
    def __init__(self) -> None:
        self._commands: dict[str, CommandProtocol] = {}
 
    # ── registro ──────────────────────────────────────────────────────────────
 
    def register(self, key: str, command: CommandProtocol) -> "Invoker":
        """Registra um command. Retorna `self` para encadeamento fluente."""
        if not isinstance(command, CommandProtocol):
            raise TypeError(f"{command!r} não implementa CommandProtocol")
        self._commands[key] = command
        logger.debug("Invoker: comando '%s' registrado", key)
        return self
 
    def unregister(self, key: str) -> None:
        self._commands.pop(key, None)
 
    @property
    def registered_keys(self) -> list[str]:
        return list(self._commands.keys())
 
    # ── execução ──────────────────────────────────────────────────────────────
 
    async def execute(self, key: str) -> Any:
        """Executa um único comando pelo nome."""
        if key not in self._commands:
            raise KeyError(f"Comando '{key}' não encontrado. Registrados: {self.registered_keys}")
        logger.info("Invoker: executando '%s'", key)
        return await self._commands[key].execute()
 
    async def execute_all(self) -> dict[str, Any]:
        """
        Executa todos os comandos registrados sequencialmente.
        Erros individuais são capturados e retornados como exceção no dict
        para não interromper os demais.
        """
        results: dict[str, Any] = {}
        for key, command in self._commands.items():
            try:
                results[key] = await command.execute()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Invoker: erro ao executar '%s'", key)
                results[key] = {"error": str(exc)}
        return results