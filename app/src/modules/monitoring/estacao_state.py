
from abc import ABC, abstractmethod


class EstacaoState(ABC):

    @abstractmethod
    def verificar(self, context: "EstacaoContext", nivel_provider: str) -> None:
        """Compara o nivel do Provider com o estado atual e decide a transição."""

    @abstractmethod
    def sincronizar(self, context: "EstacaoContext") -> None:
        """Inicia o processo de sincronização."""

    @abstractmethod
    def concluir(self, context: "EstacaoContext") -> None:
        """Conclui a sincronização."""

    @abstractmethod
    def get_status_nome(self) -> str:
        """Retorna o nome do status para persistência no banco."""

    def __str__(self) -> str:
        return self.get_status_nome()


# ---------------------------------------------------------------------------
# ATUALIZADO
# ---------------------------------------------------------------------------

class EstadoAtualizado(EstacaoState):

    def verificar(self, context: "EstacaoContext", nivel_provider: str) -> None:
        if context.nivel_mare != nivel_provider:
            print(
                f"[State] '{context.nome}': Divergência detectada "
                f"(banco='{context.nivel_mare}' | provider='{nivel_provider}'). "
                f"→ DESATUALIZADO"
            )
            context.set_state(EstadoDesatualizado())
        else:
            print(f"[State] '{context.nome}': Nível de maré em dia. Nenhuma ação necessária.")

    def sincronizar(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Já está ATUALIZADO.")

    def concluir(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Já está ATUALIZADO. Nenhuma ação necessária.")

    def get_status_nome(self) -> str:
        return "ATUALIZADO"


# ---------------------------------------------------------------------------
# DESATUALIZADO
# ---------------------------------------------------------------------------

class EstadoDesatualizado(EstacaoState):

    def verificar(self, context: "EstacaoContext", nivel_provider: str) -> None:
        print(f"[State] '{context.nome}': Já DESATUALIZADO. Inicie a sincronização.")

    def sincronizar(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Iniciando sincronização → EM_SINCRONIZACAO")
        context.set_state(EstadoEmSincronizacao())

    def concluir(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Erro — sincronização não foi iniciada.")

    def get_status_nome(self) -> str:
        return "DESATUALIZADO"


# ---------------------------------------------------------------------------
# EM_SINCRONIZACAO
# ---------------------------------------------------------------------------

class EstadoEmSincronizacao(EstacaoState):

    def verificar(self, context: "EstacaoContext", nivel_provider: str) -> None:
        print(f"[State] '{context.nome}': Sincronização em andamento. Aguarde.")

    def sincronizar(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Já está EM_SINCRONIZACAO.")

    def concluir(self, context: "EstacaoContext") -> None:
        print(f"[State] '{context.nome}': Sincronização concluída → ATUALIZADO")
        context.set_state(EstadoAtualizado())

    def get_status_nome(self) -> str:
        return "EM_SINCRONIZACAO"


# ---------------------------------------------------------------------------
# Mapa: string do banco → objeto de estado
# ---------------------------------------------------------------------------

_ESTADOS_MAP: dict[str, EstacaoState] = {
    "ATUALIZADO":        EstadoAtualizado(),
    "DESATUALIZADO":     EstadoDesatualizado(),
    "EM_SINCRONIZACAO":  EstadoEmSincronizacao(),
}

def estado_from_string(status: str) -> EstacaoState:
    estado = _ESTADOS_MAP.get(status.upper())
    if estado is None:
        raise ValueError(
            f"Status '{status}' inválido. Aceitos: {list(_ESTADOS_MAP.keys())}"
        )
    return estado


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

class EstacaoContext:
    """
    Contexto do padrão State.

    Representa uma EstacaoMonitoramento em memória.
    Mantém o estado atual e delega todas as ações a ele.

    Uso:
        ctx = EstacaoContext(db_estacao.nome, db_estacao.nivel_mare, estado_from_string(db_estacao.status))
        ctx.verificar(nivel_do_provider)   # compara e transiciona se necessário
        ctx.sincronizar()                  # inicia sync se DESATUALIZADO
        ctx.concluir()                     # conclui sync
        
        # Salvar de volta no banco:
        db_estacao.status     = ctx.status
        db_estacao.nivel_mare = ctx.nivel_mare
    """

    def __init__(self, nome: str, nivel_mare: str, estado_inicial: EstacaoState):
        self.nome = nome
        self.nivel_mare = nivel_mare  # valor atual no banco
        self._state = estado_inicial

    def set_state(self, novo_estado: EstacaoState) -> None:
        print(f"[State] Transição: {self._state.get_status_nome()} → {novo_estado.get_status_nome()}")
        self._state = novo_estado

    @property
    def status(self) -> str:
        return self._state.get_status_nome()

    def verificar(self, nivel_provider: str) -> None:
        self._state.verificar(self, nivel_provider)

    def sincronizar(self) -> None:
        self._state.sincronizar(self)

    def concluir(self) -> None:
        self._state.concluir(self)