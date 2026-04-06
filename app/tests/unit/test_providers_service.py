import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.src.modules.providers.service import ProvidersService
from app.src.modules.providers.concrete_commands import TabuaMareCabedeloCommand
from app.src.modules.providers.commands import HttpReceiver
import httpx


class TestTabuaMareCabedeloCommand:
    """Testes unitários para TabuaMareCabedeloCommand."""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Testa inicialização do TabuaMareCabedeloCommand."""
        cmd = TabuaMareCabedeloCommand()
        assert cmd is not None
        assert hasattr(cmd, '_receiver')
    
    @pytest.mark.asyncio
    async def test_init_with_custom_receiver(self):
        """Testa inicialização com receiver customizado."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        assert cmd._receiver is mock_receiver
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Testa conexão ao receiver."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        
        await cmd.connect()
        
        mock_receiver.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Testa requisição HTTP bem-sucedida."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_receiver.get.return_value = mock_response
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        result = await cmd.fetch()
        
        assert result is mock_response
        mock_response.raise_for_status.assert_called_once()
        # Verifica que o endpoint foi chamado com formato correto (mês/dia)
        call_args = mock_receiver.get.call_args[0][0]
        assert "tabua-mare/pb01/" in call_args
    
    @pytest.mark.asyncio
    async def test_fetch_with_http_error(self):
        """Testa erro HTTP durante fetch."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )
        mock_receiver.get.return_value = mock_response
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        
        with pytest.raises(httpx.HTTPStatusError):
            await cmd.fetch()
    
    @pytest.mark.asyncio
    async def test_parse_success(self):
        """Testa parsing bem-sucedido da resposta."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        
        expected_data = {
            "data": [
                {
                    "months": [
                        {
                            "days": [
                                {
                                    "hours": [
                                        {"hour": "00:38:00", "level": 0.76},
                                        {"hour": "06:59:00", "level": 2.10},
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_response.json.return_value = expected_data
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        result = await cmd.parse(mock_response)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["hour"] == "00:38:00"
        assert result[0]["level"] == 0.76
    
    @pytest.mark.asyncio
    async def test_parse_empty_data(self):
        """Testa parsing com dados vazios."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {}
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        result = await cmd.parse(mock_response)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_parse_malformed_data(self):
        """Testa parsing com dados malformados."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"invalid": "structure"}
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        result = await cmd.parse(mock_response)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Testa execução completa do comando."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_response = MagicMock(spec=httpx.Response)
        
        expected_data = {
            "data": [
                {
                    "months": [
                        {
                            "days": [
                                {
                                    "hours": [
                                        {"hour": "00:38:00", "level": 0.76},
                                        {"hour": "06:59:00", "level": 2.10},
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_response.json.return_value = expected_data
        mock_receiver.get.return_value = mock_response
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        result = await cmd.execute()
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_receiver.connect.assert_called_once()
        mock_receiver.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_disconnect_on_error(self):
        """Testa que disconnect é chamado mesmo com erro."""
        mock_receiver = AsyncMock(spec=HttpReceiver)
        mock_receiver.get.side_effect = ValueError("Connection failed")
        
        cmd = TabuaMareCabedeloCommand(receiver=mock_receiver)
        
        with pytest.raises(ValueError):
            await cmd.execute()
        
        mock_receiver.disconnect.assert_called_once()


class TestProvidersService:
    """Testes unitários para ProvidersService."""
    
    def test_init(self):
        """Testa inicialização do ProvidersService."""
        service = ProvidersService()
        assert service is not None
        assert hasattr(service, 'invoker')
        assert "tabua_mare_cabedelo" in service.invoker.registered_keys
    
    def test_init_registers_command(self):
        """Testa que o comando está registrado na inicialização."""
        service = ProvidersService()
        registered_keys = service.invoker.registered_keys
        assert "tabua_mare_cabedelo" in registered_keys
        assert len(registered_keys) == 1
    
    @pytest.mark.asyncio
    async def test_fetch_tabua_mare_cabedelo_success(self):
        """Testa busca bem-sucedida da tábua de marés."""
        service = ProvidersService()
        
        # Mock do comando registrado
        expected_result = [
            {"hour": "00:38:00", "level": 0.76},
            {"hour": "06:59:00", "level": 2.10},
        ]
        
        mock_command = AsyncMock()
        mock_command.execute.return_value = expected_result
        service.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        result = await service.fetch_tabua_mare_cabedelo()
        
        assert result == expected_result
        mock_command.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_tabua_mare_cabedelo_error(self):
        """Testa comportamento em caso de erro."""
        service = ProvidersService()
        
        # Mock do comando que falha
        mock_command = AsyncMock()
        mock_command.execute.side_effect = Exception("API Error")
        service.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        with pytest.raises(Exception, match="API Error"):
            await service.fetch_tabua_mare_cabedelo()
    
    @pytest.mark.asyncio
    async def test_fetch_tabua_mare_cabedelo_logs_success(self):
        """Testa logging de sucesso."""
        service = ProvidersService()
        
        expected_result = [
            {"hour": "00:38:00", "level": 0.76},
            {"hour": "06:59:00", "level": 2.10},
        ]
        
        mock_command = AsyncMock()
        mock_command.execute.return_value = expected_result
        service.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        with patch('app.src.modules.providers.service.logger') as mock_logger:
            result = await service.fetch_tabua_mare_cabedelo()
            
            mock_logger.info.assert_called_once()
            assert "sucesso" in mock_logger.info.call_args[0][0].lower()
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_fetch_tabua_mare_cabedelo_logs_error(self):
        """Testa logging de erro."""
        service = ProvidersService()
        
        error_message = "Connection timeout"
        mock_command = AsyncMock()
        mock_command.execute.side_effect = Exception(error_message)
        service.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        with patch('app.src.modules.providers.service.logger') as mock_logger:
            with pytest.raises(Exception):
                await service.fetch_tabua_mare_cabedelo()
            
            mock_logger.error.assert_called_once()
            assert error_message in mock_logger.error.call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_multiple_services_independent(self):
        """Testa que múltiplas instâncias de serviço são independentes."""
        service1 = ProvidersService()
        service2 = ProvidersService()
        
        # Cada serviço tem seu próprio invoker
        assert service1.invoker is not service2.invoker
        
        # Modificar um não afeta o outro
        mock_command = AsyncMock()
        service1.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        assert service2.invoker._commands["tabua_mare_cabedelo"] != mock_command


class TestProvidersServiceIntegration:
    """Testes de integração do ProvidersService com Invoker."""
    
    @pytest.mark.asyncio
    async def test_service_with_real_command_structure(self):
        """Testa estrutura real do comando no serviço."""
        service = ProvidersService()
        
        # Verifica que o comando está registrado corretamente
        assert "tabua_mare_cabedelo" in service.invoker.registered_keys
        
        # Verifica que é uma instância de TabuaMareCabedeloCommand
        cmd = service.invoker._commands["tabua_mare_cabedelo"]
        assert isinstance(cmd, TabuaMareCabedeloCommand)
    
    @pytest.mark.asyncio
    async def test_service_invoker_execute_all(self):
        """Testa execução de todos os comandos via invoker."""
        service = ProvidersService()
        
        # Mock do comando
        expected_result = [{"hour": "00:38:00", "level": 0.76}]
        mock_command = AsyncMock()
        mock_command.execute.return_value = expected_result
        service.invoker._commands["tabua_mare_cabedelo"] = mock_command
        
        # Executa todos os comandos
        results = await service.invoker.execute_all()
        
        assert "tabua_mare_cabedelo" in results
        assert results["tabua_mare_cabedelo"] == expected_result
