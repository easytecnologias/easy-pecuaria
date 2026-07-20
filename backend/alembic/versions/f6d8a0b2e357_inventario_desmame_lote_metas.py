"""inventario, desmame/matriz, metas por lote e rastreabilidade de movimento

Pedidos do cliente (audios 1, 7, 10, 11 e 12).

Revision ID: f6d8a0b2e357
Revises: e5c7f9a1d246
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6d8a0b2e357"
down_revision: Union[str, None] = "e5c7f9a1d246"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- audio 1: metas por lote ---------------------------------------------
    op.add_column("lote", sa.Column("capacidade", sa.Integer(), nullable=True))
    op.add_column("lote", sa.Column("dias_cocho", sa.Integer(), nullable=True))
    op.add_column("lote", sa.Column("gmd_meta", sa.Numeric(6, 3), nullable=True))
    op.add_column("lote", sa.Column("rendimento_carcaca", sa.Numeric(5, 4), nullable=True))

    # --- audio 7: tipo de matriz e desmame -----------------------------------
    op.add_column("animal", sa.Column("tipo_matriz", sa.String(40), nullable=True))
    op.add_column("animal", sa.Column("desmama_data", sa.Date(), nullable=True))
    op.add_column("animal", sa.Column("desmama_peso", sa.Numeric(8, 2), nullable=True))

    # --- audio 12: quem movimentou o animal ----------------------------------
    op.add_column("movimento_animal", sa.Column("usuario_id", sa.Uuid(), nullable=True))
    op.add_column("movimento_animal", sa.Column("usuario_nome", sa.String(160), nullable=True))
    op.create_foreign_key(
        "fk_movimento_animal_usuario", "movimento_animal", "usuario",
        ["usuario_id"], ["id"], ondelete="SET NULL",
    )

    # --- audios 10 e 11: inventario / patrimonio -----------------------------
    op.create_table(
        "item_inventario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fazenda_id", sa.Uuid(), nullable=False),
        sa.Column("categoria", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("identificacao", sa.String(80), nullable=True),
        sa.Column("localizacao", sa.String(120), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=True),
        sa.Column("unidade", sa.String(20), nullable=True),
        sa.Column("valor", sa.Numeric(12, 2), nullable=True),
        sa.Column("situacao", sa.String(20), nullable=False, server_default="ativo"),
        sa.Column("data_aquisicao", sa.Date(), nullable=True),
        sa.Column("observacao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_item_inventario_fazenda_id", "item_inventario", ["fazenda_id"])
    op.create_index("ix_item_inventario_categoria", "item_inventario", ["categoria"])

    op.create_table(
        "movimento_inventario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("fazenda_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=True),
        sa.Column("origem", sa.String(120), nullable=True),
        sa.Column("destino", sa.String(120), nullable=True),
        sa.Column("fazenda_destino_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_nome", sa.String(160), nullable=True),
        sa.Column("observacao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item_inventario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fazenda_destino_id"], ["fazenda.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_movimento_inventario_item_id", "movimento_inventario", ["item_id"])
    op.create_index("ix_movimento_inventario_fazenda_id", "movimento_inventario", ["fazenda_id"])
    op.create_index("ix_movimento_inventario_data", "movimento_inventario", ["data"])

    # --- audio 1: ajusta as metas das fazendas QUE JA EXISTEM --------------
    # (PREMISSAS_PADRAO so vale para fazenda nova; aqui alcanca as antigas)
    op.execute("DELETE FROM parametro WHERE grupo = 'Clima'")
    op.execute("""
        INSERT INTO parametro (id, fazenda_id, grupo, chave, rotulo, valor, unidade, created_at, updated_at)
        SELECT gen_random_uuid(), f.id, 'Confinamento', v.chave, v.rotulo, v.valor, v.unidade, now(), now()
        FROM fazenda f
        CROSS JOIN (VALUES
            ('quantidade_lotes', 'Quantidade de lotes', 4, 'lotes'),
            ('espaco_por_lote',  'Espaco por lote',    75, 'cab/lote')
        ) AS v(chave, rotulo, valor, unidade)
        WHERE NOT EXISTS (
            SELECT 1 FROM parametro p WHERE p.fazenda_id = f.id AND p.chave = v.chave
        )
    """)
    # rotulos passam a indicar que sao o padrao (cada lote pode sobrescrever)
    op.execute("""
        UPDATE parametro SET rotulo = rotulo || ' (padrao)'
        WHERE chave IN ('dias_cocho', 'gmd_meta', 'rendimento_carcaca')
          AND rotulo NOT LIKE '%(padrao)'
    """)


def downgrade() -> None:
    op.drop_table("movimento_inventario")
    op.drop_table("item_inventario")
    op.drop_constraint("fk_movimento_animal_usuario", "movimento_animal", type_="foreignkey")
    op.drop_column("movimento_animal", "usuario_nome")
    op.drop_column("movimento_animal", "usuario_id")
    op.drop_column("animal", "desmama_peso")
    op.drop_column("animal", "desmama_data")
    op.drop_column("animal", "tipo_matriz")
    op.drop_column("lote", "rendimento_carcaca")
    op.drop_column("lote", "gmd_meta")
    op.drop_column("lote", "dias_cocho")
    op.drop_column("lote", "capacidade")
