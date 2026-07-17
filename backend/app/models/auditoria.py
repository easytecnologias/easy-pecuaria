import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditLog(Base):
    """Trilha de auditoria: quem fez o quê, quando, em qual organização.
    Registra ações sensíveis (usuários, organizações, exclusões, login).
    O email fica desnormalizado para sobreviver à exclusão do usuário.
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizacao.id", ondelete="SET NULL"), index=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )
    usuario_email: Mapped[str] = mapped_column(String(180), nullable=False)
    acao: Mapped[str] = mapped_column(String(80), nullable=False)
    entidade: Mapped[str | None] = mapped_column(String(40))
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    detalhe: Mapped[str | None] = mapped_column(String(300))
