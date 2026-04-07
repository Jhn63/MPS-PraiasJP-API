from abc import ABC, abstractmethod
from fastapi import HTTPException, Header
from modules.auth.auth_factory import AuthFactory
from middlewares.permissoes_composite import ComponentePermissao, PermissaoSimples
from modules.logger.error_logger import error_logger

class Handler(ABC):
    """Classe base para os elos da cadeia."""
    def __init__(self):
        self.proximo_handler: 'Handler' = None

    def set_proximo(self, handler: 'Handler') -> 'Handler':
        self.proximo_handler = handler
        return handler

    @abstractmethod
    def manipular(self, request_data: dict) -> bool:
        if self.proximo_handler:
            return self.proximo_handler.manipular(request_data)
        return True

class ValidacaoTokenHandler(Handler):
    """Etapa 1: Verifica se o token é válido usando a Factory."""
    def manipular(self, request_data: dict) -> bool:
        token = request_data.get("token")
        if not token:
            error_logger.warning("Token validation failed", reason="Token not provided")
            raise HTTPException(status_code=401, detail="Acesso Negado: Token não fornecido.")
        
        strategy = AuthFactory.get_strategy("API_KEY")
        if not strategy.validar_chave(token):
            error_logger.warning("Token validation failed", reason="Invalid token", token=token[:10] + "...")
            raise HTTPException(status_code=401, detail="Acesso Negado: Token inválido.")
        
        error_logger.info("Token validated successfully", token=token[:10] + "...")
        return super().manipular(request_data)

class AutorizacaoHandler(Handler):
    """Etapa 2: Verifica as permissões usando o Composite."""
    def __init__(self, permissao_necessaria: str, cargo_usuario: ComponentePermissao):
        super().__init__()
        self.permissao_necessaria = permissao_necessaria
        self.cargo_usuario = cargo_usuario

    def manipular(self, request_data: dict) -> bool:
        if not self.cargo_usuario.tem_permissao(self.permissao_necessaria):
            error_logger.warning(
                "Authorization failed",
                required_permission=self.permissao_necessaria,
                reason="Insufficient privileges"
            )
            raise HTTPException(status_code=403, detail=f"Acesso Negado: Faltam privilégios para '{self.permissao_necessaria}'.")
        
        error_logger.info(
            "Authorization granted",
            required_permission=self.permissao_necessaria
        )
        return super().manipular(request_data)

def verificar_acesso(x_token: str = Header(default=None)):
    """Função injetável do FastAPI para blindar as rotas."""
    # Simulando um usuário com permissão básica para fins de teste
    permissao_usuario = PermissaoSimples("ler:usuarios")
    
    # 1. Monta a cadeia
    etapa_1_token = ValidacaoTokenHandler()
    etapa_2_permissao = AutorizacaoHandler("ler:usuarios", permissao_usuario)
    etapa_1_token.set_proximo(etapa_2_permissao)
    
    # 2. Executa a cadeia
    error_logger.info(
        "Access verification initiated",
        has_token=x_token is not None
    )
    return etapa_1_token.manipular({"token": x_token})