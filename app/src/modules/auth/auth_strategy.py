from abc import ABC, abstractmethod
import secrets
from modules.logger.error_logger import error_logger

class AuthStrategy(ABC):
    """Interface abstrata para as estratégias de autenticação."""
    
    @abstractmethod
    def gerar_chave(self, user_id: int) -> str:
        pass

    @abstractmethod
    def validar_chave(self, chave: str) -> bool:
        pass

class ApiKeyStrategy(AuthStrategy):
    """Implementação concreta de autenticação baseada em API Key."""
    
    def gerar_chave(self, user_id: int) -> str:
        # Gera uma chave segura combinando o ID do usuário e um hash aleatório
        token = secrets.token_urlsafe(32)
        chave = f"ak_{user_id}_{token}"
        error_logger.info(
            "API Key generated",
            user_id=user_id
        )
        return chave

    def validar_chave(self, chave: str) -> bool:
        # A validação real na Feature 2 pode checar no banco, 
        # mas aqui fazemos a validação primária de formato.
        is_valid = chave.startswith("ak_") and len(chave) > 10
        if not is_valid:
            error_logger.warning(
                "API Key validation failed",
                reason="Invalid format or length"
            )
        else:
            error_logger.info("API Key validated successfully")
        return is_valid

class JWTStrategy(AuthStrategy):
    """Implementação concreta de autenticação baseada em JWT (Exemplo para extensibilidade)."""
    
    def gerar_chave(self, user_id: int) -> str:
        # Aqui entraria a lógica de codificação JWT (ex: usando PyJWT)
        chave = f"eyJhbGciOiJIUzI1Ni.user_{user_id}.simulacao_assinatura"
        error_logger.info(
            "JWT generated",
            user_id=user_id
        )
        return chave

    def validar_chave(self, chave: str) -> bool:
        is_valid = chave.startswith("eyJ")
        if not is_valid:
            error_logger.warning(
                "JWT validation failed",
                reason="Invalid format"
            )
        else:
            error_logger.info("JWT validated successfully")
        return is_valid