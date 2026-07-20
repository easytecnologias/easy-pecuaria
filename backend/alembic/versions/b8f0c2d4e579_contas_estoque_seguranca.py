"""contas a pagar/receber e estoque de seguranca da silagem

Pedidos do cliente (audios 3 e 9).

Revision ID: b8f0c2d4e579
Revises: a7e9b1c3d468
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8f0c2d4e579"
down_revision: Union[str, None] = "a7e9b1c3d468"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# todas as tabelas herdam created_at/updated_at do Base declarativo
TS = dict(server_default=sa.text("now()"), nullable=False)


def upgrade() -> None:
    # --- audio 3: estoque de seguranca da silagem ----------------------------
    op.add_column(
        "silagem", sa.Column("estoque_seguranca_t", sa.Numeric(12, 3), nullable=True)
    )

    # --- audio 9: contas a pagar e a receber ---------------------------------
    op.create_table(
        "conta_financeira",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "fazenda_id", sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(60), nullable=False),
        sa.Column("contraparte", sa.String(160)),
        sa.Column("documento", sa.String(15), nullable=False, server_default="outro"),
        sa.Column("numero_documento", sa.String(60)),
        sa.Column("valor", sa.Numeric(14, 2), nullable=False),
        sa.Column("emissao", sa.Date()),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="aberto"),
        sa.Column("data_baixa", sa.Date()),
        sa.Column("valor_pago", sa.Numeric(14, 2)),
        sa.Column(
            "lancamento_id", sa.Uuid(),
            sa.ForeignKey("lancamento_financeiro.id", ondelete="SET NULL"),
        ),
        sa.Column("observacao", sa.String(255)),
        sa.Column("criado_por_nome", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), **TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), **TS),
    )
    op.create_index("ix_conta_financeira_fazenda_id", "conta_financeira", ["fazenda_id"])
    op.create_index("ix_conta_financeira_tipo", "conta_financeira", ["tipo"])
    op.create_index("ix_conta_financeira_status", "conta_financeira", ["status"])
    # o filtro mais usado da tela: o que vence primeiro
    op.create_index("ix_conta_financeira_vencimento", "conta_financeira", ["vencimento"])


def downgrade() -> None:
    op.drop_index("ix_conta_financeira_vencimento", table_name="conta_financeira")
    op.drop_index("ix_conta_financeira_status", table_name="conta_financeira")
    op.drop_index("ix_conta_financeira_tipo", table_name="conta_financeira")
    op.drop_index("ix_conta_financeira_fazenda_id", table_name="conta_financeira")
    op.drop_table("conta_financeira")
    op.drop_column("silagem", "estoque_seguranca_t")
