import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import FormatoIndicador, OrigemValor


class IndicadorDefinicao(Base):
    """Catalogo de indicadores (KPIs). Global — compartilhado entre fazendas."""

    __tablename__ = "indicador_definicao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)  # ex: custo_dieta_cab_dia
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(60))  # Dieta, Reproducao, Confinamento...
    unidade: Mapped[str | None] = mapped_column(String(40))
    formato: Mapped[FormatoIndicador] = mapped_column(
        Enum(FormatoIndicador, name="formato_indicador"),
        default=FormatoIndicador.numero,
        nullable=False,
    )
    casas_decimais: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255))


class IndicadorValor(Base):
    """Serie temporal: valor de um indicador para uma fazenda numa data."""

    __tablename__ = "indicador_valor"
    __table_args__ = (
        UniqueConstraint("fazenda_id", "indicador_id", "data_ref", name="uq_indicador_valor"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicador_definicao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valor: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    data_ref: Mapped[date] = mapped_column(Date, nullable=False)
    origem: Mapped[OrigemValor] = mapped_column(
        Enum(OrigemValor, name="origem_valor"), default=OrigemValor.manual, nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(String(255))
