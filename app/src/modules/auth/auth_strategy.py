from abc import ABC, abstractmethod
import secrets

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
        return f"ak_{user_id}_{token}"

    def validar_chave(self, chave: str) -> bool:
        # A validação real na Feature 2 pode checar no banco, 
        # mas aqui fazemos a validação primária de formato.
        return chave.startswith("ak_") and len(chave) > 10

class JWTStrategy(AuthStrategy):
    """Implementação concreta de autenticação baseada em JWT (Exemplo para extensibilidade)."""
    
    def gerar_chave(self, user_id: int) -> str:
        # Aqui entraria a lógica de codificação JWT (ex: usando PyJWT)
        return f"eyJhbGciOiJIUzI1Ni.user_{user_id}.simulacao_assinatura"

    def validar_chave(self, chave: str) -> bool:
        return chave.startswith("eyJ")