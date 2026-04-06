from abc import ABC, abstractmethod
from fastapi import HTTPException, Header
from modules.auth.auth_factory import AuthFactory
from middlewares.permissoes_composite import ComponentePermissao, PermissaoSimples

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
            raise HTTPException(status_code=401, detail="Acesso Negado: Token não fornecido.")
        
        strategy = AuthFactory.get_strategy("API_KEY")
        if not strategy.validar_chave(token):
            raise HTTPException(status_code=401, detail="Acesso Negado: Token inválido.")
        
        return super().manipular(request_data)

class AutorizacaoHandler(Handler):
    """Etapa 2: Verifica as permissões usando o Composite."""
    def __init__(self, permissao_necessaria: str, cargo_usuario: ComponentePermissao):
        super().__init__()
        self.permissao_necessaria = permissao_necessaria
        self.cargo_usuario = cargo_usuario

    def manipular(self, request_data: dict) -> bool:
        if not self.cargo_usuario.tem_permissao(self.permissao_necessaria):
            raise HTTPException(status_code=403, detail=f"Acesso Negado: Faltam privilégios para '{self.permissao_necessaria}'.")
        
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
    etapa_1_token.manipular({"token": x_token})