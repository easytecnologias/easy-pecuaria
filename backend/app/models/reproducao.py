import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Inseminacao(Base):
    """Evento de inseminação (IATF) de uma matriz, com o resultado do diagnóstico
    de gestação (DG). Um registro por tentativa; o DG atualiza o resultado depois.
    """

    __tablename__ = "inseminacao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    touro: Mapped[str] = mapped_column(String(120), nullable=False)  # touro/sêmen
    inseminador: Mapped[str | None] = mapped_column(String(120))
    protocolo: Mapped[str | None] = mapped_column(String(120))
    # pendente (ainda sem DG) | prenhe | vazia
    resultado: Mapped[str] = mapped_column(String(12), default="pendente", nullable=False)
    dg_data: Mapped[date | None] = mapped_column(Date)
