import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Dieta(Base):
    """Dieta de um lote. O custo/cab/dia e o consumo de MS saem dos itens."""

    __tablename__ = "dieta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lote.id", ondelete="SET NULL"), index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    itens: Mapped[list["ItemDieta"]] = relationship(
        back_populates="dieta", cascade="all, delete-orphan"
    )


class ItemDieta(Base):
    """Ingrediente da dieta: inclusão (kg MN/cab/dia), preço (R$/kg MN), MS (%)."""

    __tablename__ = "item_dieta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    dieta_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dieta.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingrediente: Mapped[str] = mapped_column(String(120), nullable=False)
    inclusao_kg: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)  # kg MN/cab/dia
    preco_kg: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)     # R$/kg MN
    ms_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)        # 0..1

    dieta: Mapped["Dieta"] = relationship(back_populates="itens")
