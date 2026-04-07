
from datetime import datetime
from sqlalchemy.orm import Session

from models.estacao_model import EstacaoMonitoramento as EstacaoModel
from modules.monitoring.estacao_state import EstacaoContext, estado_from_string
from modules.monitoring.estacao_memento import EstacaoOriginator, EstacaoCaretaker
from modules.providers.service import ProvidersService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nivel_mais_proximo(tabua: list[dict]) -> str:
    """
    Recebe a tábua de marés do dia e retorna o nível (como string)
    cujo horário é o mais próximo do momento atual.

    Formato esperado de cada item:
        {"hour": "06:59:00", "level": 2.0999999046325684}

    Retorna:
        String do nível, ex: "2.1"
    """
    agora = datetime.now().time()

    def diferenca_segundos(item: dict) -> int:
        hora_item = datetime.strptime(item["hour"], "%H:%M:%S").time()
        delta = abs(
            datetime.combine(datetime.today(), agora) -
            datetime.combine(datetime.today(), hora_item)
        )
        return int(delta.total_seconds())

    mais_proximo = min(tabua, key=diferenca_segundos)
    nivel = round(mais_proximo["level"], 2)

    print(
        f"[Monitoramento] Horário atual: {agora.strftime('%H:%M:%S')} | "
        f"Entrada mais próxima: {mais_proximo['hour']} | "
        f"Nível: {nivel}"
    )

    return str(nivel)


# ---------------------------------------------------------------------------
# Módulo principal
# ---------------------------------------------------------------------------

class MonitoramentoService:
    """
    Serviço de monitoramento das estações.

    Orquestra o fluxo completo:
        Provider → comparação (State) → persistência → histórico (Memento)

    O _caretakers mantém o histórico de snapshots em memória
    enquanto a aplicação estiver rodando.
    """

    def __init__(self) -> None:
        self._providers_service = ProvidersService()
        self._caretakers: dict[int, EstacaoCaretaker] = {}

    # ------------------------------------------------------------------ #
    #  Ponto de entrada principal                                         #
    # ------------------------------------------------------------------ #

    async def monitorar_estacao(self, estacao_id: int, db: Session) -> EstacaoModel:
        """
        Roda o ciclo completo de monitoramento para uma estação.

        Fluxo:
            1. Busca dado atual do Provider
            2. Encontra nível mais próximo do horário atual
            3. Carrega a estação do banco
            4. Salva Memento (snapshot antes de qualquer mudança)
            5. Usa State para comparar e decidir se atualiza
            6. Se necessário: atualiza banco e conclui State

        Args:
            estacao_id: ID da EstacaoMonitoramento no banco
            db: Sessão SQLAlchemy

        Returns:
            EstacaoMonitoramento atualizada (ou inalterada se já estava em dia)
        """
        # 1. Busca dados do Provider
        print(f"\n[Monitoramento] Iniciando monitoramento da estação #{estacao_id}")
        tabua = await self._providers_service.fetch_tabua_mare_cabedelo()

        # 2. Nível mais próximo do horário atual
        nivel_provider = _nivel_mais_proximo(tabua)

        # 3. Carrega estação do banco
        db_estacao = db.query(EstacaoModel).filter(EstacaoModel.id == estacao_id).first()
        if not db_estacao:
            raise ValueError(f"Estação #{estacao_id} não encontrada no banco.")

        # Garante status inicial válido
        if not db_estacao.status:
            db_estacao.status = "DESATUALIZADO"

        # 4. Salva Memento ANTES de qualquer alteração
        originator = EstacaoOriginator(db_estacao)
        snapshot = originator.salvar()
        self._get_caretaker(estacao_id).adicionar(snapshot)

        # 5. State: compara nivel do banco com nivel do Provider
        ctx = EstacaoContext(
            nome=db_estacao.nome,
            nivel_mare=db_estacao.nivel_mare or "",
            estado_inicial=estado_from_string(db_estacao.status),
        )
        ctx.verificar(nivel_provider)

        # 6. Se State detectou divergência → sincroniza e atualiza banco
        if ctx.status == "DESATUALIZADO":
            ctx.sincronizar()                          # → EM_SINCRONIZACAO
            db_estacao.nivel_mare = nivel_provider     # atualiza o dado
            ctx.concluir()                             # → ATUALIZADO

        # Persiste o status final no banco
        db_estacao.status = ctx.status
        db.commit()
        db.refresh(db_estacao)

        print(
            f"[Monitoramento] Estação '{db_estacao.nome}' finalizada. "
            f"Status: {db_estacao.status} | nivel_mare: {db_estacao.nivel_mare}"
        )
        return db_estacao

    # ------------------------------------------------------------------ #
    #  Operações de Memento                                               #
    # ------------------------------------------------------------------ #

    def rollback_estacao(self, estacao_id: int, db: Session) -> EstacaoModel:
        """
        Restaura a estação ao último snapshot salvo.
        Útil se uma atualização corrompeu os dados.
        """
        db_estacao = db.query(EstacaoModel).filter(EstacaoModel.id == estacao_id).first()
        if not db_estacao:
            raise ValueError(f"Estação #{estacao_id} não encontrada.")

        ultimo = self._get_caretaker(estacao_id).desfazer()
        if ultimo is None:
            print(f"[Monitoramento] Nenhum snapshot para restaurar na estação #{estacao_id}.")
            return db_estacao

        EstacaoOriginator(db_estacao).restaurar(ultimo)
        db.commit()
        db.refresh(db_estacao)
        return db_estacao

    def exibir_historico(self, estacao_id: int) -> None:
        """Exibe o histórico de snapshots da estação (auditoria)."""
        self._get_caretaker(estacao_id).exibir_historico()

    # ------------------------------------------------------------------ #
    #  Helper                                                             #
    # ------------------------------------------------------------------ #

    def _get_caretaker(self, estacao_id: int) -> EstacaoCaretaker:
        if estacao_id not in self._caretakers:
            self._caretakers[estacao_id] = EstacaoCaretaker(estacao_id)
        return self._caretakers[estacao_id]