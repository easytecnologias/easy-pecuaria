import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# audio 8: "vai ter varios tipos de silagem"
TIPOS_SILAGEM = ("milho", "sorgo", "capim", "cana", "outro")


class Silagem(Base):
    """Um silo/lote de silagem. O cliente quer cada tipo com seus proprios
    dados de qualidade (materia seca alvo, umidade, temperatura) e os dados
    da colheita (maquinario usado, para qual curral/confinamento).
    """

    __tablename__ = "silagem"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)   # "Silagem 1", "Silo capim"
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    data_ensilagem: Mapped[date | None] = mapped_column(Date)

    # qualidade
    ms_meta: Mapped[float | None] = mapped_column(Numeric(5, 4))     # materia seca alvo (%)
    ms_real: Mapped[float | None] = mapped_column(Numeric(5, 4))     # materia seca medida (%)
    umidade: Mapped[float | None] = mapped_column(Numeric(5, 4))     # taxa de umidade (%)
    temperatura: Mapped[float | None] = mapped_column(Numeric(5, 2))  # graus C

    # volume
    quantidade_t: Mapped[float | None] = mapped_column(Numeric(12, 3))   # produzido
    consumo_diario_t: Mapped[float | None] = mapped_column(Numeric(12, 3))

    # colheita (subtopico pedido no audio 8)
    maquinario: Mapped[str | None] = mapped_column(String(160))      # colhedora, vagao, trator
    destino: Mapped[str | None] = mapped_column(String(120))         # curral / confinamento
    responsavel: Mapped[str | None] = mapped_column(String(120))
    observacao: Mapped[str | None] = mapped_column(String(255))
    situacao: Mapped[str] = mapped_column(String(20), default="aberto", nullable=False)  # aberto|fechado|consumido
