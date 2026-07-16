import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Organizacao(Base):
    __tablename__ = "organizacao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)

    fazendas: Mapped[list["Fazenda"]] = relationship(
        back_populates="organizacao", cascade="all, delete-orphan"
    )


class Fazenda(Base):
    __tablename__ = "fazenda"
    __table_args__ = (UniqueConstraint("org_id", "nome", name="uq_fazenda_org_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizacao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    municipio: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[str | None] = mapped_column(String(2))
    area_ha: Mapped[float | None] = mapped_column(Numeric(12, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organizacao: Mapped["Organizacao"] = relationship(back_populates="fazendas")
