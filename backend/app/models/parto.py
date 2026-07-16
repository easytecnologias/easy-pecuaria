import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Parto(Base):
    """Nascimento (parto) de uma matriz. Quando nasce vivo, cria o bezerro no
    rebanho (Animal) já ligado à mãe. Alimenta a evolução do rebanho e a natalidade.
    """

    __tablename__ = "parto"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mae_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bezerro_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("animal.id", ondelete="SET NULL")
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    resultado: Mapped[str] = mapped_column(String(14), nullable=False)  # nascido_vivo | natimorto
    sexo_bezerro: Mapped[str | None] = mapped_column(String(1))  # M | F
    brinco_bezerro: Mapped[str | None] = mapped_column(String(40))
    peso_nascimento: Mapped[float | None] = mapped_column(Numeric(6, 2))  # kg
    observacao: Mapped[str | None] = mapped_column(String(200))
