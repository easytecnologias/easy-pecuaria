import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Lote(Base):
    """Grupo de manejo. A maior parte da operacao e lancada por lote."""

    __tablename__ = "lote"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(40))  # Matrizes, Engorda, Bezerros, Novilhas
    local: Mapped[str | None] = mapped_column(String(80))       # Pasto 3, Curral 1
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Metas por lote (None = usa o padrao da fazenda em Parametro)
    capacidade: Mapped[int | None] = mapped_column(Integer)          # espaco do lote (cabecas)
    dias_cocho: Mapped[int | None] = mapped_column(Integer)
    gmd_meta: Mapped[float | None] = mapped_column(Numeric(6, 3))
    rendimento_carcaca: Mapped[float | None] = mapped_column(Numeric(5, 4))


class Animal(Base):
    """Animal individual. Pode ou nao ter brinco; sempre pertence a uma fazenda."""

    __tablename__ = "animal"
    __table_args__ = (UniqueConstraint("fazenda_id", "brinco", name="uq_animal_fazenda_brinco"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lote.id", ondelete="SET NULL"), index=True
    )
    brinco: Mapped[str] = mapped_column(String(40), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(40))  # Matriz, Garrote, Bezerro, Novilha, Touro, Boi
    raca: Mapped[str | None] = mapped_column(String(60))
    sexo: Mapped[str | None] = mapped_column(String(1))  # M / F
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    mae_brinco: Mapped[str | None] = mapped_column(String(40))
    pai: Mapped[str | None] = mapped_column(String(80))
    origem: Mapped[str | None] = mapped_column(String(20))  # nascido / comprado
    status: Mapped[str] = mapped_column(String(20), default="ativo", nullable=False)
    # Matriz: composicao genetica (Nelore puro, F1, T-Cross, ...)
    tipo_matriz: Mapped[str | None] = mapped_column(String(40))
    # Desmame do bezerro (peso medio de desmama sai daqui)
    desmama_data: Mapped[date | None] = mapped_column(Date)
    desmama_peso: Mapped[float | None] = mapped_column(Numeric(8, 2))


class Pesagem(Base):
    """Evento de pesagem. GMD e calculado contra a pesagem anterior do mesmo animal."""

    __tablename__ = "pesagem"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    peso: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    gmd: Mapped[float | None] = mapped_column(Numeric(6, 3))  # calculado no registro
    observacao: Mapped[str | None] = mapped_column(String(255))
