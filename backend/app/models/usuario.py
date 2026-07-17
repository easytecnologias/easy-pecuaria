import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import PapelUsuario


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizacao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuario] = mapped_column(
        Enum(PapelUsuario, name="papel_usuario"), default=PapelUsuario.gerente, nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # super-admin da plataforma: cria/gerencia organizações (distinto do admin do cliente)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UsuarioFazenda(Base):
    """Escopo de acesso: quais fazendas cada usuario enxerga.

    Direcao/admin normalmente veem todas; gerente/campo podem ver so uma.
    """

    __tablename__ = "usuario_fazenda"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), primary_key=True
    )
