class DomainException(Exception):
    """Classe base para todas as exceções de domínio."""
    pass

class UsuarioInvalidoError(DomainException):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)

class EstacaoNaoEncontradaError(DomainException):
    def __init__(self, estacao_id: int):
        super().__init__(f"Estação com ID {estacao_id} não foi encontrada.")