import uuid

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Parametro(Base):
    """Premissas/metas por fazenda (aba 'Premissas' da planilha).

    Modelo chave-valor tipado. Ex: chave='custo_max_dieta', valor=13.5, unidade='R$/cab/dia'.
    Uma regra de gatilho pode referenciar 'chave' para resolver o limite da fazenda.
    """

    __tablename__ = "parametro"
    __table_args__ = (UniqueConstraint("fazenda_id", "chave", name="uq_parametro_fazenda_chave"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grupo: Mapped[str | None] = mapped_column(String(60))         # Rebanho, Confinamento, Dieta...
    chave: Mapped[str] = mapped_column(String(60), nullable=False)  # identificador estavel
    rotulo: Mapped[str] = mapped_column(String(160), nullable=False)  # texto amigavel
    valor: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(40))
    observacao: Mapped[str | None] = mapped_column(String(255))
