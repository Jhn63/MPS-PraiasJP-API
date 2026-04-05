from modules.auth.auth_strategy import AuthStrategy, ApiKeyStrategy, JWTStrategy

class AuthFactory:
    """Factory Method para instanciar a estratégia de autenticação correta."""
    
    @staticmethod
    def get_strategy(auth_type: str) -> AuthStrategy:
        tipo = auth_type.upper()
        
        if tipo == "API_KEY":
            return ApiKeyStrategy()
        elif tipo == "JWT":
            return JWTStrategy()
        else:
            raise ValueError(f"Tipo de autenticação não suportado: {auth_type}")