from sqlalchemy.orm import Session
from models.user_model import User as UserModel
from models.estacao_model import EstacaoMonitoramento as EstacaoModel
from schemas.user import User as UserSchema
from schemas.estacao import EstacaoMonitoramento as EstacaoSchema

class UsuarioController:
    def criarUsuario(self, user: UserSchema, db: Session):
        db_user = UserModel(username=user.username, password=user.password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

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

    def __init__(self):
        if FacadeSingletonController._instancia is not None:
            raise Exception("Esta classe é um Singleton! Utilize FacadeSingletonController.get_instance()")
        else:
            self.usuarioController = UsuarioController()
            self.estacaoController = EstacaoController()
            FacadeSingletonController._instancia = self

    @staticmethod
    def get_instance():
        if FacadeSingletonController._instancia is None:
            FacadeSingletonController()
        return FacadeSingletonController._instancia

    def cadastrarNovaEstacao(self, dados: EstacaoSchema, db: Session):
        return self.estacaoController.criarEstacao(dados, db)

    def gerarAcessoUsuario(self, dados: UserSchema, db: Session):
        return self.usuarioController.criarUsuario(dados, db)

    def getQuantidadeTotalEntidades(self, db: Session) -> int:
        total_usuarios = self.usuarioController.count(db)
        total_estacoes = self.estacaoController.count(db)
        return total_usuarios + total_estacoes