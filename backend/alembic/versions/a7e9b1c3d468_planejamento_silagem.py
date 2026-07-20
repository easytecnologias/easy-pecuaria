"""planejamento de atividades e silagem como modulo proprio

Pedidos do cliente (audios 8 e 13).

Revision ID: a7e9b1c3d468
Revises: f6d8a0b2e357
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7e9b1c3d468"
down_revision: Union[str, None] = "f6d8a0b2e357"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TS = dict(server_default=sa.text("now()"), nullable=False)


def upgrade() -> None:
    # --- audio 13: planejamento de atividades --------------------------------
    op.create_table(
        "atividade",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fazenda_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(160), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False, server_default="outro"),
        sa.Column("periodo", sa.String(10), nullable=False, server_default="semanal"),
        sa.Column("data_prevista", sa.Date(), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="pendente"),
        sa.Column("responsavel_id", sa.Uuid(), nullable=True),
        sa.Column("responsavel_nome", sa.String(160), nullable=True),
        sa.Column("criado_por_nome", sa.String(160), nullable=True),
        sa.Column("concluida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("concluida_por_nome", sa.String(160), nullable=True),
        sa.Column("observacao_conclusao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), **TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), **TS),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responsavel_id"], ["usuario.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_atividade_fazenda_id", "atividade", ["fazenda_id"])
    op.create_index("ix_atividade_data_prevista", "atividade", ["data_prevista"])
    op.create_index("ix_atividade_status", "atividade", ["status"])
    op.create_index("ix_atividade_periodo", "atividade", ["periodo"])
    op.create_index("ix_atividade_tipo", "atividade", ["tipo"])
    op.create_index("ix_atividade_responsavel_id", "atividade", ["responsavel_id"])

    # --- audio 8: silagem como modulo proprio --------------------------------
    op.create_table(
        "silagem",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fazenda_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("data_ensilagem", sa.Date(), nullable=True),
        sa.Column("ms_meta", sa.Numeric(5, 4), nullable=True),
        sa.Column("ms_real", sa.Numeric(5, 4), nullable=True),
        sa.Column("umidade", sa.Numeric(5, 4), nullable=True),
        sa.Column("temperatura", sa.Numeric(5, 2), nullable=True),
        sa.Column("quantidade_t", sa.Numeric(12, 3), nullable=True),
        sa.Column("consumo_diario_t", sa.Numeric(12, 3), nullable=True),
        sa.Column("maquinario", sa.String(160), nullable=True),
        sa.Column("destino", sa.String(120), nullable=True),
        sa.Column("responsavel", sa.String(120), nullable=True),
        sa.Column("observacao", sa.String(255), nullable=True),
        sa.Column("situacao", sa.String(20), nullable=False, server_default="aberto"),
        sa.Column("created_at", sa.DateTime(timezone=True), **TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), **TS),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_silagem_fazenda_id", "silagem", ["fazenda_id"])
    op.create_index("ix_silagem_tipo", "silagem", ["tipo"])


def downgrade() -> None:
    op.drop_table("silagem")
    op.drop_table("atividade")
