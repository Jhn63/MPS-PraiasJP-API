from abc import ABC, abstractmethod
from typing import List

class ComponentePermissao(ABC):
    """Interface comum para Permissões simples e Cargos compostos."""
    @abstractmethod
    def tem_permissao(self, permissao: str) -> bool:
        pass

class PermissaoSimples(ComponentePermissao):
    """Folha (Leaf): Representa uma permissão individual."""
    def __init__(self, nome: str):
        self.nome = nome

    def tem_permissao(self, permissao: str) -> bool:
        return self.nome == permissao

class Cargo(ComponentePermissao):
    """Nó Composto (Composite): Representa um cargo que contém várias permissões."""
    def __init__(self, nome: str):
        self.nome = nome
        self._permissoes: List[ComponentePermissao] = []

    def adicionar(self, permissao: ComponentePermissao):
        self._permissoes.append(permissao)

    def tem_permissao(self, permissao: str) -> bool:
        return any(p.tem_permissao(permissao) for p in self._permissoes)