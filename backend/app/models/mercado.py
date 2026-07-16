import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CotacaoArroba(Base):
    """Cotação da arroba do boi gordo (R$/@) por fazenda/data. Alimenta o
    indicador arroba_recebida. origem = manual | integracao.
    """

    __tablename__ = "cotacao_arroba"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # R$/@
    origem: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    fonte: Mapped[str | None] = mapped_column(String(120))


class CotacaoInsumo(Base):
    """Cotação de insumo entregue: preço origem + frete + outros; MS% -> custo/kg MS."""

    __tablename__ = "cotacao_insumo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    insumo: Mapped[str] = mapped_column(String(120), nullable=False)
    praca: Mapped[str | None] = mapped_column(String(120))
    unidade: Mapped[str] = mapped_column(String(10), default="kg")  # kg | t
    preco_origem: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    frete: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    outros: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    ms_pct: Mapped[float] = mapped_column(Numeric(5, 4), default=1)  # 0..1
