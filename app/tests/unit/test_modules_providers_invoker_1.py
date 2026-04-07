import pytest
from unittest.mock import AsyncMock
from app.src.modules.providers.invoker import Invoker
from app.src.modules.providers.commands import CommandProtocol


class MockCommand(CommandProtocol):
    def __init__(self, result=None, should_fail=False):
        self.result = result
        self.should_fail = should_fail

    async def execute(self):
        if self.should_fail:
            raise ValueError("Mock command failed")
        return self.result


class TestInvoker:
    def test_init(self):
        invoker = Invoker()
        assert isinstance(invoker._commands, dict)
        assert len(invoker._commands) == 0

    def test_register(self):
        invoker = Invoker()
        command = MockCommand(result="success")
        result = invoker.register("test_key", command)
        assert "test_key" in invoker._commands
        assert invoker._commands["test_key"] is command
        assert result is invoker  # Check fluent interface

    def test_register_invalid_command(self):
        invoker = Invoker()
        with pytest.raises(TypeError):
            invoker.register("test_key", "not a command")

    def test_unregister(self):
        invoker = Invoker()
        command = MockCommand()
        invoker.register("test_key", command)
        assert "test_key" in invoker._commands
        invoker.unregister("test_key")
        assert "test_key" not in invoker._commands

    def test_registered_keys(self):
        invoker = Invoker()
        assert invoker.registered_keys == []
        invoker.register("key1", MockCommand())
        invoker.register("key2", MockCommand())
        assert set(invoker.registered_keys) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_execute(self):
        invoker = Invoker()
        command = MockCommand(result="executed")
        invoker.register("test_key", command)
        result = await invoker.execute("test_key")
        assert result == "executed"

    @pytest.mark.asyncio
    async def test_execute_unknown_key(self):
        invoker = Invoker()
        with pytest.raises(KeyError):
            await invoker.execute("unknown")

    @pytest.mark.asyncio
    async def test_execute_all(self):
        invoker = Invoker()
        command1 = MockCommand(result="result1")
        command2 = MockCommand(result="result2")
        command3 = MockCommand(should_fail=True)
        invoker.register("cmd1", command1)
        invoker.register("cmd2", command2)
        invoker.register("cmd3", command3)
        results = await invoker.execute_all()
        assert results["cmd1"] == "result1"
        assert results["cmd2"] == "result2"
        assert "error" in results["cmd3"]
        assert "Mock command failed" in results["cmd3"]["error"]