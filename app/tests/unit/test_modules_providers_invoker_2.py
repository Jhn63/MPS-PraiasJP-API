import pytest
from unittest.mock import AsyncMock, MagicMock
from app.src.modules.providers.invoker import Invoker
from app.src.modules.providers.commands import BaseCommand, HttpReceiver
import httpx


class JSONCommand(BaseCommand):
    """Implementação concreta de BaseCommand para testes com JSON."""
    
    def __init__(self, endpoint: str = "/users", should_fail: bool = False, receiver: HttpReceiver | None = None):
        super().__init__(
            receiver=receiver,
            base_url="https://jsonplaceholder.typicode.com",
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        self.endpoint = endpoint
        self.should_fail = should_fail
    
    async def connect(self) -> None:
        """Conecta ao receiver HttpReceiver."""
        await self._receiver.connect()
    
    async def fetch(self) -> httpx.Response:
        """Faz a requisição GET ao endpoint."""
        if self.should_fail:
            raise ValueError("Simulated fetch error")
        return await self._receiver.get(self.endpoint)
    
    async def parse(self, response: httpx.Response) -> list[dict]:
        """Converte a resposta JSON em lista de dicionários."""
        return response.json()


class TestJSONCommand:
    """Testes unitários para a classe JSONCommand."""
    
    @pytest.mark.asyncio
    async def test_json_command_init(self):
        """Testa inicialização do JSONCommand."""
        cmd = JSONCommand(endpoint="/users", should_fail=False)
        assert cmd.endpoint == "/users"
        assert cmd.should_fail is False
    
    @pytest.mark.asyncio
    async def test_json_command_connect(self):
        """Testa conectar ao receiver."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        cmd = JSONCommand(receiver=mock_receiver)
        
        await cmd.connect()
        mock_receiver.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_json_command_fetch_success(self):
        """Testa requisição HTTP bem-sucedida."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_receiver.get.return_value = mock_response
        
        cmd = JSONCommand(endpoint="/users", receiver=mock_receiver)
        result = await cmd.fetch()
        
        assert result is mock_response
        mock_receiver.get.assert_called_once_with("/users")
    
    @pytest.mark.asyncio
    async def test_json_command_fetch_error(self):
        """Testa error durante fetch."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        cmd = JSONCommand(endpoint="/users", should_fail=True, receiver=mock_receiver)
        
        with pytest.raises(ValueError, match="Simulated fetch error"):
            await cmd.fetch()
    
    @pytest.mark.asyncio
    async def test_json_command_parse(self):
        """Testa parsing da resposta JSON."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        expected_users = [
            {"id": 1, "name": "Leanne Graham", "username": "Bret", "email": "Sincere@april.biz"},
            {"id": 2, "name": "Ervin Howell", "username": "Antonette", "email": "Shanna@melissa.tv"}
        ]
        mock_response.json.return_value = expected_users
        
        cmd = JSONCommand(receiver=mock_receiver)
        result = await cmd.parse(mock_response)
        
        assert result == expected_users
        assert isinstance(result, list)
        assert len(result) == 2
        mock_response.json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_json_command_execute_success(self):
        """Testa o ciclo completo execute() com sucesso."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        expected_users = [
            {"id": 1, "name": "Leanne Graham", "username": "Bret", "email": "Sincere@april.biz"},
            {"id": 2, "name": "Ervin Howell", "username": "Antonette", "email": "Shanna@melissa.tv"}
        ]
        mock_response.json.return_value = expected_users
        mock_receiver.get.return_value = mock_response
        
        cmd = JSONCommand(endpoint="/users", receiver=mock_receiver)
        result = await cmd.execute()
        
        assert result == expected_users
        assert isinstance(result, list)
        assert len(result) == 2
        mock_receiver.connect.assert_called_once()
        mock_receiver.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_json_command_execute_error_still_disconnects(self):
        """Testa que disconnect é chamado mesmo com erro."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_receiver.get.side_effect = ValueError("Connection failed")
        
        cmd = JSONCommand(endpoint="/users", receiver=mock_receiver)
        
        with pytest.raises(ValueError, match="Connection failed"):
            await cmd.execute()
        
        # Verifica que disconnect foi chamado mesmo com erro
        mock_receiver.disconnect.assert_called_once()


class TestInvokerWithJSONCommand:
    """Testes integrando Invoker com JSONCommand."""
    
    @pytest.mark.asyncio
    async def test_invoker_with_json_command(self):
        """Testa registar e executar JSONCommand via Invoker."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"id": 1, "title": "Test Post"}
        mock_receiver.get.return_value = mock_response
        
        cmd = JSONCommand(endpoint="/users/", receiver=mock_receiver)
        invoker = Invoker()
        invoker.register("fetch_post", cmd)
        
        result = await invoker.execute("fetch_post")
        
        assert result == {"id": 1, "title": "Test Post"}
    
    @pytest.mark.asyncio
    async def test_invoker_execute_all_with_json_commands(self):
        """Testa executar múltiplos JSONCommands via Invoker."""
        mock_receiver1 = AsyncMock(spec=HttpReceiver)
        mock_response1 = MagicMock(spec=httpx.Response)
        mock_response1.json.return_value = {"id": 1, "title": "Post 1"}
        mock_receiver1.get.return_value = mock_response1
        
        mock_receiver2 = AsyncMock(spec=HttpReceiver)
        mock_response2 = MagicMock(spec=httpx.Response)
        mock_response2.json.return_value = {"id": 2, "title": "Post 2"}
        mock_receiver2.get.return_value = mock_response2
        
        cmd1 = JSONCommand(endpoint="/users/", receiver=mock_receiver1)
        cmd2 = JSONCommand(endpoint="/posts/2", receiver=mock_receiver2)
        
        invoker = Invoker()
        invoker.register("post1", cmd1)
        invoker.register("post2", cmd2)
        
        results = await invoker.execute_all()
        
        assert results["post1"] == {"id": 1, "title": "Post 1"}
        assert results["post2"] == {"id": 2, "title": "Post 2"}