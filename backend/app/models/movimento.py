import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MovimentoAnimal(Base):
    """Movimentação de um animal: compra, venda, morte, descarte, transferência.
    Muda o status/lote do animal e alimenta os KPIs (vendas/mortes) do painel.
    """

    __tablename__ = "movimento_animal"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # compra|venda|morte|descarte|transferencia
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valor: Mapped[float | None] = mapped_column(Numeric(12, 2))  # compra/venda (R$)
    motivo: Mapped[str | None] = mapped_column(String(120))       # descarte/morte
    lote_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lote.id", ondelete="SET NULL")
    )  # transferência
    observacao: Mapped[str | None] = mapped_column(String(200))
