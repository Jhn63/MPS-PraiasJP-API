import logging
from typing import Any, Protocol, runtime_checkable
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)

@runtime_checkable
class CommandProtocol(Protocol):
    """Interface mínima que todo Command deve satisfazer."""
 
    async def execute(self) -> Any:  # pragma: no cover
        ...



class HttpReceiver:
    """
    Receiver do padrão Command.
 
    Encapsula o httpx.AsyncClient e expõe métodos de baixo nível (get/post)
    que os Commands delegam na etapa `fetch`.
    """
 
    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url
        self._headers = headers or {}
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
 
    async def connect(self) -> None:
        """Abre (ou reabre) o cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=self._timeout,
            )
            logger.debug("HttpReceiver: cliente aberto para %s", self._base_url)
 
    async def disconnect(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("HttpReceiver: cliente fechado")
 
    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client, "Chame connect() antes de get()"
        return await self._client.get(url, **kwargs)
 
    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client, "Chame connect() antes de post()"
        return await self._client.post(url, **kwargs)
 
    # context-manager async para uso direto quando necessário
    async def __aenter__(self) -> "HttpReceiver":
        await self.connect()
        return self
 
    async def __aexit__(self, *_: Any) -> None:
        await self.disconnect()



class BaseCommand(ABC):
    """
    Classe base para todos os Commands do módulo.
 
    Implementa o padrão Template Method: `execute()` define o esqueleto
    do algoritmo e chama os hooks abstratos na ordem correta:
 
        execute()
          ├── connect()   ← hook: configura/conecta ao receiver
          ├── fetch()     ← hook: realiza a requisição HTTP
          ├── parse()     ← hook: transforma a resposta em domínio
          └── disconnect()← finalização garantida (finally)
 
    Subclasses DEVEM implementar `connect`, `fetch` e `parse`.
    O receiver (HttpReceiver) é injetado via construtor — isso permite
    mock em testes sem necessidade de monkeypatching.
    """
 
    def __init__(
        self,
        receiver: HttpReceiver | None = None,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        # Se nenhum receiver for passado, cria um interno (conveniente em produção)
        self._receiver = receiver or HttpReceiver(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
 
    # ── Template Method (final — não sobrescrever) ────────────────────────────
 
    async def execute(self) -> Any:
        """
        Orquestra o ciclo completo: connect → fetch → parse.
        Garante disconnect mesmo em caso de erro.
        """
        try:
            await self.connect()
            response = await self.fetch()
            return await self.parse(response)
        finally:
            await self._receiver.disconnect()
 
    # ── Hooks abstratos ───────────────────────────────────────────────────────
 
    @abstractmethod
    async def connect(self) -> None:
        """
        Abre a conexão / configura headers adicionais no receiver.
        Deve chamar `await self._receiver.connect()` ao final.
        """
 
    @abstractmethod
    async def fetch(self) -> httpx.Response:
        """Realiza a requisição HTTP via `self._receiver`."""
 
    @abstractmethod
    async def parse(self, response: httpx.Response) -> Any:
        """Transforma a resposta em dados de domínio (dict, dataclass, etc.)."""