import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EscoreCorporal(Base):
    """Avaliação de escore de condição corporal (ECC) de um animal, escala 1–5.
    O último escore por animal alimenta a distribuição (magras/ideais/gordas) —
    chave pra manejo nutricional e reprodutivo das matrizes.
    """

    __tablename__ = "escore_corporal"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    escore: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)  # 1.0 – 5.0
    observacao: Mapped[str | None] = mapped_column(String(200))
