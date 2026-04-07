
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Memento — snapshot imutável
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EstacaoMemento:
    """
    Snapshot imutável de uma EstacaoMonitoramento.

    frozen=True garante que nenhum campo pode ser alterado após criação,
    preservando a integridade do histórico.
    """
    estacao_id: int
    nome: str
    localizacao: str
    status: str
    nivel_mare: Optional[str]       # pode ser None se ainda não foi sincronizado
    salvo_em: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return (
            f"[Memento #{self.estacao_id}] "
            f"nome='{self.nome}' | "
            f"nivel_mare='{self.nivel_mare}' | "
            f"status='{self.status}' | "
            f"salvo_em={self.salvo_em.strftime('%Y-%m-%d %H:%M:%S')}"
        )


# ---------------------------------------------------------------------------
# Originator — cria e restaura a partir do modelo SQLAlchemy
# ---------------------------------------------------------------------------

class EstacaoOriginator:
    """
    Originator do padrão Memento.

    É o único que sabe quais campos salvar e como restaurá-los.
    O Caretaker nunca acessa o conteúdo do Memento diretamente.

    Uso:
        originator = EstacaoOriginator(db_estacao)
        snapshot = originator.salvar()          # antes de alterar
        ...alterações no db_estacao...
        originator.restaurar(snapshot)          # se precisar reverter
        db.commit()                             # persistir o rollback
    """

    def __init__(self, estacao) -> None:
        self._estacao = estacao

    def salvar(self) -> EstacaoMemento:
        """Cria um snapshot do estado atual da estação."""
        print(
            f"[Memento] Salvando snapshot de '{self._estacao.nome}' "
            f"(nivel_mare='{self._estacao.nivel_mare}', status='{self._estacao.status}')"
        )
        return EstacaoMemento(
            estacao_id=self._estacao.id,
            nome=self._estacao.nome,
            localizacao=self._estacao.localizacao,
            status=self._estacao.status,
            nivel_mare=self._estacao.nivel_mare,
        )

    def restaurar(self, memento: EstacaoMemento) -> None:
        """
        Restaura os dados da estação a partir de um snapshot.
        Após chamar este método, execute db.commit() para persistir.
        """
        if memento.estacao_id != self._estacao.id:
            raise ValueError(
                f"Memento pertence à estação #{memento.estacao_id}, "
                f"mas Originator opera na estação #{self._estacao.id}."
            )
        print(
            f"[Memento] Restaurando '{self._estacao.nome}' "
            f"para snapshot de {memento.salvo_em.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self._estacao.nome = memento.nome
        self._estacao.localizacao = memento.localizacao
        self._estacao.status = memento.status
        self._estacao.nivel_mare = memento.nivel_mare


# ---------------------------------------------------------------------------
# Caretaker — gerencia o histórico sem conhecer o conteúdo
# ---------------------------------------------------------------------------

class EstacaoCaretaker:
    """
    Caretaker do padrão Memento.

    Armazena e recupera Mementos sem conhecer seu conteúdo interno.
    Um Caretaker por estação (identificado pelo estacao_id).

    Uso:
        caretaker = EstacaoCaretaker(estacao_id=1)
        caretaker.adicionar(originator.salvar())    # salva snapshot
        ultimo = caretaker.get_ultimo()             # consulta
        originator.restaurar(ultimo)                # rollback
    """

    def __init__(self, estacao_id: int) -> None:
        self._estacao_id = estacao_id
        self._historico: list[EstacaoMemento] = []

    def adicionar(self, memento: EstacaoMemento) -> None:
        if memento.estacao_id != self._estacao_id:
            raise ValueError(
                f"Caretaker gerencia estação #{self._estacao_id}, "
                f"mas Memento é da estação #{memento.estacao_id}."
            )
        self._historico.append(memento)
        print(f"[Caretaker] Snapshot salvo. Total no histórico: {len(self._historico)}")

    def get_ultimo(self) -> Optional[EstacaoMemento]:
        """Retorna o snapshot mais recente sem removê-lo."""
        if not self._historico:
            print(f"[Caretaker] Histórico da estação #{self._estacao_id} está vazio.")
            return None
        return self._historico[-1]

    def desfazer(self) -> Optional[EstacaoMemento]:
        """Remove e retorna o snapshot mais recente (rollback destrutivo)."""
        if not self._historico:
            print(f"[Caretaker] Nada para desfazer na estação #{self._estacao_id}.")
            return None
        memento = self._historico.pop()
        print(f"[Caretaker] Snapshot removido. Restam: {len(self._historico)}")
        return memento

    def get_historico(self) -> list[EstacaoMemento]:
        return list(self._historico)

    def exibir_historico(self) -> None:
        print(f"\n{'='*60}")
        print(f"  Histórico — Estação #{self._estacao_id} ({len(self._historico)} snapshots)")
        print(f"{'='*60}")
        if not self._historico:
            print("  (vazio)")
        for i, m in enumerate(self._historico, start=1):
            print(f"  [{i}] {m}")
        print(f"{'='*60}\n")