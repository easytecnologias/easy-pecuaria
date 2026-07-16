import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import Operador, Severidade, StatusAlerta, TipoReferencia


class RegraGatilho(Base):
    """Regra de decisao (aba 'Dashboard' da planilha: colunas Regra/Acao).

    Pertence a organizacao e aplica a todas as fazendas dela. O limite pode ser
    um valor fixo OU a chave de um Parametro — resolvido por fazenda na avaliacao.
    """

    __tablename__ = "regra_gatilho"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizacao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicador_definicao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    operador: Mapped[Operador] = mapped_column(Enum(Operador, name="operador"), nullable=False)

    tipo_referencia: Mapped[TipoReferencia] = mapped_column(
        Enum(TipoReferencia, name="tipo_referencia"), nullable=False
    )
    valor_referencia: Mapped[float | None] = mapped_column(Numeric(16, 4))  # se valor_fixo
    parametro_chave: Mapped[str | None] = mapped_column(String(60))         # se parametro
    tolerancia: Mapped[float | None] = mapped_column(Numeric(16, 4))        # para abs_diff>

    severidade: Mapped[Severidade] = mapped_column(
        Enum(Severidade, name="severidade"), nullable=False
    )
    acao: Mapped[str] = mapped_column(Text, nullable=False)  # o que fazer quando dispara
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Alerta(Base):
    """Resultado da avaliacao de uma regra para uma fazenda num momento."""

    __tablename__ = "alerta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    regra_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regra_gatilho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicador_definicao.id", ondelete="CASCADE"), nullable=False
    )
    severidade: Mapped[Severidade] = mapped_column(
        Enum(Severidade, name="severidade", create_type=False), nullable=False
    )
    status: Mapped[StatusAlerta] = mapped_column(
        Enum(StatusAlerta, name="status_alerta"), default=StatusAlerta.aberto, nullable=False
    )
    valor_observado: Mapped[float | None] = mapped_column(Numeric(16, 4))
    valor_referencia: Mapped[float | None] = mapped_column(Numeric(16, 4))
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    acao: Mapped[str | None] = mapped_column(Text)
    avaliado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
