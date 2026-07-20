import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LancamentoFinanceiro(Base):
    """Despesa ou receita da fazenda. O saldo, a margem por cabeça e o capital
    de giro (em dias) saem do conjunto de lançamentos.
    """

    __tablename__ = "lancamento_financeiro"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # despesa | receita
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # R$
    descricao: Mapped[str | None] = mapped_column(String(200))


# audio 9: "contas a pagar e a receber, lancamentos de notas, acompanhamentos,
# quando as duplicatas e os boletos estiverem vencendo"
TIPOS_CONTA = ("pagar", "receber")
TIPOS_DOCUMENTO = ("duplicata", "boleto", "nota", "recibo", "outro")
STATUS_CONTA = ("aberto", "baixado", "cancelado")


class ContaFinanceira(Base):
    """Compromisso com data de vencimento — a pagar ou a receber.

    Diferente do LancamentoFinanceiro, que e o dinheiro que JA entrou ou saiu,
    a conta e o que esta previsto. Quando ela e baixada (paga/recebida), o
    sistema gera o lancamento correspondente para o saldo continuar certo.
    """

    __tablename__ = "conta_financeira"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # pagar | receber
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    # quem recebe (fornecedor) ou quem paga (cliente)
    contraparte: Mapped[str | None] = mapped_column(String(160))

    documento: Mapped[str] = mapped_column(String(15), default="outro", nullable=False)
    numero_documento: Mapped[str | None] = mapped_column(String(60))

    valor: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    emissao: Mapped[date | None] = mapped_column(Date)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(12), default="aberto", nullable=False, index=True)
    data_baixa: Mapped[date | None] = mapped_column(Date)
    valor_pago: Mapped[float | None] = mapped_column(Numeric(14, 2))
    # lancamento gerado na baixa — permite desfazer sem duplicar no caixa
    lancamento_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lancamento_financeiro.id", ondelete="SET NULL")
    )

    observacao: Mapped[str | None] = mapped_column(String(255))
    criado_por_nome: Mapped[str | None] = mapped_column(String(160))
