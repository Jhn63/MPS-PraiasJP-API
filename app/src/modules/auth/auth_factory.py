from modules.auth.auth_strategy import AuthStrategy, ApiKeyStrategy, JWTStrategy
from modules.logger.error_logger import error_logger

class AuthFactory:
    """Factory Method para instanciar a estratégia de autenticação correta."""
    
    @staticmethod
    def get_strategy(auth_type: str) -> AuthStrategy:
        tipo = auth_type.upper()
        
        if tipo == "API_KEY":
            error_logger.info("Auth strategy requested", auth_type="API_KEY")
            return ApiKeyStrategy()
        elif tipo == "JWT":
            error_logger.info("Auth strategy requested", auth_type="JWT")
            return JWTStrategy()
        else:
            error_logger.warning(
                "Unsupported authentication type",
                auth_type=auth_type
            )
            raise ValueError(f"Tipo de autenticação não suportado: {auth_type}")