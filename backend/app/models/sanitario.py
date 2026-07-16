import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EventoSanitario(Base):
    """Aplicação sanitária num animal (vacina, vermífugo, tratamento, exame...).
    Aplicar num lote gera um evento por animal (fica na ficha de cada um).
    proxima_aplicacao alimenta o calendário/alerta de vencimento.
    """

    __tablename__ = "evento_sanitario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lote.id", ondelete="SET NULL")
    )  # marca que foi aplicação de lote
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # vacina|vermifugo|tratamento|exame|carrapaticida|hormonio
    produto: Mapped[str] = mapped_column(String(120), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    proxima_aplicacao: Mapped[date | None] = mapped_column(Date, index=True)
    dose: Mapped[str | None] = mapped_column(String(40))
    observacao: Mapped[str | None] = mapped_column(String(200))
