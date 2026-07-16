import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LancamentoFinanceiro(Base):
    """Despesa ou receita da fazenda. O saldo, a margem por cabeça e o capital
    de giro (em dias) saem do conjunto de lançamentos.
    """

    __tablename__ = "lancamento_financeiro"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # despesa | receita
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # R$
    descricao: Mapped[str | None] = mapped_column(String(200))
