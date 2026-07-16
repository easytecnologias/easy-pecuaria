import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MovimentoVolumoso(Base):
    """Entrada (ensilagem/compra) ou saída (consumo) de volumoso, em toneladas.
    O saldo e os dias de estoque saem dos movimentos.
    """

    __tablename__ = "movimento_volumoso"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # entrada | saida
    quantidade_t: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)  # toneladas
    descricao: Mapped[str | None] = mapped_column(String(160))
