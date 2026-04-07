import re
from sqlalchemy.orm import Session
from modules.users.user_model import User as UserModel
from models.estacao_model import EstacaoMonitoramento as EstacaoModel
from modules.users.user import User as UserSchema, UserCreate
from schemas.estacao import EstacaoMonitoramento as EstacaoSchema
from exceptions.domain_exceptions import UsuarioInvalidoError 
from modules.auth.auth_factory import AuthFactory

from modules.logger.logger_service import error_logger

password_pattern = re.compile(r"^(?=\S{8,128}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[!@#$%^&*()-+=]).*$")

class UsuarioController:
    def criarUsuario(self, user: UserCreate, db: Session):
        # 1. Validação (SRP: Garante que os dados de domínio são válidos)
        if not re.match(r"^\S{1,12}$", user.username):
            raise UsuarioInvalidoError("Formato de username inválido. Deve ter entre 1 e 12 caracteres sem espaços.")
        if not re.match(password_pattern, user.password):
            raise UsuarioInvalidoError("Formato de password inválido. Deve ser forte.")

        # 2. Persistência
        try:
            db_user = UserModel(username=user.username, password=user.password)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            error_logger.info(
                "User created successfully",
                username=user.username,
                user_id=db_user.id
            )
            return db_user
        except Exception as exc:
            db.rollback()
            error_logger.log_exception(
                exc,
                message="Failed to create user",
                username=user.username
            )
            raise
    
    def gerarTokenAcesso(self, user_id: int, auth_type: str) -> str:
        strategy = AuthFactory.get_strategy(auth_type)
        return strategy.gerar_chave(user_id)

    def autenticarUsuario(self, user: UserCreate, db: Session):
        """Autentica um usuário verificando username e password"""
        try:
            db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
            if db_user is None:
                raise UsuarioInvalidoError("Usuário não encontrado")
            
            if db_user.password != user.password:
                error_logger.warning(
                    "Failed login attempt - incorrect password",
                    username=user.username
                )
                raise UsuarioInvalidoError("Senha incorreta")
            
            error_logger.info(
                "User authenticated successfully",
                username=user.username,
                user_id=db_user.id
            )
            return db_user
        except UsuarioInvalidoError:
            raise
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Authentication failed",
                username=user.username
            )
            raise

    def count(self, db: Session) -> int:
        return db.query(UserModel).count()

class EstacaoController:
    def criarEstacao(self, estacao: EstacaoSchema, db: Session):
        try:
            db_estacao = EstacaoModel(
                nome=estacao.nome, 
                localizacao=estacao.localizacao, 
                status=estacao.status
            )
            db.add(db_estacao)
            db.commit()
            db.refresh(db_estacao)
            error_logger.info(
                "Estação created successfully",
                nome=estacao.nome,
                localizacao=estacao.localizacao,
                estacao_id=db_estacao.id
            )
            return db_estacao
        except Exception as exc:
            db.rollback()
            error_logger.log_exception(
                exc,
                message="Failed to create estação",
                nome=estacao.nome,
                localizacao=estacao.localizacao
            )
            raise

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
        try:
            result = self.estacaoController.criarEstacao(dados, db)
            error_logger.info(
                "New estação registered via facade",
                estacao_id=result.id,
                nome=dados.nome
            )
            return result
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Failed to register new estação via facade",
                nome=dados.nome
            )
            raise

    def gerarAcessoUsuario(self, dados: UserSchema, db: Session, auth_type: str = "API_KEY"):
        try:
            # 1. Cria o usuário
            db_user = self.usuarioController.criarUsuario(dados, db)
            
            # 2. Gera a chave de acesso usando o padrão selecionado
            token = self.usuarioController.gerarTokenAcesso(db_user.id, auth_type)
            
            error_logger.info(
                "User access generated successfully",
                user_id=db_user.id,
                username=dados.username,
                auth_type=auth_type
            )
            return db_user, token
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Failed to generate user access",
                username=dados.username,
                auth_type=auth_type
            )
            raise

    def realizarLogin(self, credenciais: UserSchema, db: Session, auth_type: str = "API_KEY"):
        try:
            # 1. Autentica o usuário
            db_user = self.usuarioController.autenticarUsuario(credenciais, db)
            
            # 2. Gera a chave de acesso usando o padrão selecionado
            token = self.usuarioController.gerarTokenAcesso(db_user.id, auth_type)
            
            error_logger.info(
                "User login successful",
                user_id=db_user.id,
                username=credenciais.username,
                auth_type=auth_type
            )
            return db_user, token
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Login failed",
                username=credenciais.username,
                auth_type=auth_type
            )
            raise

    def getQuantidadeTotalEntidades(self, db: Session) -> int:
        try:
            total_usuarios = self.usuarioController.count(db)
            total_estacoes = self.estacaoController.count(db)
            total = total_usuarios + total_estacoes
            error_logger.info(
                "Total entities counted",
                total_usuarios=total_usuarios,
                total_estacoes=total_estacoes,
                total=total
            )
            return total
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Failed to count total entidades"
            )
            raise