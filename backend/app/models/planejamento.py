import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# audio 13: "planejamento semanal, mensal, anual"
PERIODOS = ("semanal", "mensal", "anual")
STATUS_ATIVIDADE = ("pendente", "em_andamento", "concluida", "cancelada")
# tipos citados pelo cliente
TIPOS_ATIVIDADE = (
    "manejo_rebanho", "manejo_sanitario", "pesagem", "reproducao",
    "nutricao", "manutencao", "administrativo", "outro",
)


class Atividade(Base):
    """Atividade planejada, com responsavel e acompanhamento de conclusao.

    O cliente lanca a atividade, define quem executa, a pessoa ve o que tem
    para fazer e marca como concluida — e ele acompanha os numeros.
    """

    __tablename__ = "atividade"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="outro", index=True)
    periodo: Mapped[str] = mapped_column(String(10), nullable=False, default="semanal", index=True)

    data_prevista: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="pendente", index=True)

    # quem deve executar (a pessoa ve na propria tela o que tem para fazer)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), index=True
    )
    responsavel_nome: Mapped[str | None] = mapped_column(String(160))  # desnormalizado

    # quem criou e quem concluiu — rastreabilidade igual a das movimentacoes
    criado_por_nome: Mapped[str | None] = mapped_column(String(160))
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    concluida_por_nome: Mapped[str | None] = mapped_column(String(160))
    observacao_conclusao: Mapped[str | None] = mapped_column(String(255))
