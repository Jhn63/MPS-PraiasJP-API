import re
from sqlalchemy.orm import Session
from modules.users.user_model import User as UserModel
from models.estacao_model import EstacaoMonitoramento as EstacaoModel
from modules.users.user import User as UserSchema
from schemas.estacao import EstacaoMonitoramento as EstacaoSchema
from exceptions.domain_exceptions import UsuarioInvalidoError 
from modules.auth.auth_factory import AuthFactory

password_pattern = re.compile(r"^(?=\S{8,128}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[!@#$%^&*()-+=]).*$")

class UsuarioController:
    def criarUsuario(self, user: UserSchema, db: Session):
        # 1. Validação (SRP: Garante que os dados de domínio são válidos)
        if not re.match(r"^\S{1,12}$", user.username):
            raise UsuarioInvalidoError("Formato de username inválido. Deve ter entre 1 e 12 caracteres sem espaços.")
        if not re.match(password_pattern, user.password):
            raise UsuarioInvalidoError("Formato de password inválido. Deve ser forte.")

        # 2. Persistência
        db_user = UserModel(username=user.username, password=user.password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def gerarTokenAcesso(self, user_id: int, auth_type: str) -> str:
        strategy = AuthFactory.get_strategy(auth_type)
        return strategy.gerar_chave(user_id)

    def count(self, db: Session) -> int:
        return db.query(UserModel).count()

class EstacaoController:
    def criarEstacao(self, estacao: EstacaoSchema, db: Session):
        db_estacao = EstacaoModel(
            nome=estacao.nome, 
            localizacao=estacao.localizacao, 
            status=estacao.status
        )
        db.add(db_estacao)
        db.commit()
        db.refresh(db_estacao)
        return db_estacao

    def count(self, db: Session) -> int:
        return db.query(EstacaoModel).count()

class FacadeSingletonController:
    _instancia = None

    def __new__(cls):
        # Implementação de Singleton no Python
        if cls._instancia is None:
            cls._instancia = super(FacadeSingletonController, cls).__new__(cls)
            # Inicialização interna dos subsistemas
            cls._instancia.usuarioController = UsuarioController()
            cls._instancia.estacaoController = EstacaoController()
        return cls._instancia

    @classmethod
    def get_instance(cls):
        return cls()

    # --- Delegação de Chamadas ---
    def cadastrarNovaEstacao(self, dados: EstacaoSchema, db: Session):
        return self.estacaoController.criarEstacao(dados, db)

    def gerarAcessoUsuario(self, dados: UserSchema, db: Session, auth_type: str = "API_KEY"):
        # 1. Cria o usuário
        db_user = self.usuarioController.criarUsuario(dados, db)
        
        # 2. Gera a chave de acesso usando o padrão selecionado
        token = self.usuarioController.gerarTokenAcesso(db_user.id, auth_type)
        
        return db_user, token

    def getQuantidadeTotalEntidades(self, db: Session) -> int:
        total_usuarios = self.usuarioController.count(db)
        total_estacoes = self.estacaoController.count(db)
        return total_usuarios + total_estacoes