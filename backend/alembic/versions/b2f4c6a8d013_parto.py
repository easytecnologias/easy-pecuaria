"""parto

Revision ID: b2f4c6a8d013
Revises: 073a1ad95aa3
Create Date: 2026-07-16 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f4c6a8d013'
down_revision: Union[str, None] = '073a1ad95aa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'parto',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fazenda_id', sa.Uuid(), nullable=False),
        sa.Column('mae_id', sa.Uuid(), nullable=False),
        sa.Column('bezerro_id', sa.Uuid(), nullable=True),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('resultado', sa.String(length=14), nullable=False),
        sa.Column('sexo_bezerro', sa.String(length=1), nullable=True),
        sa.Column('brinco_bezerro', sa.String(length=40), nullable=True),
        sa.Column('peso_nascimento', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('observacao', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['fazenda_id'], ['fazenda.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mae_id'], ['animal.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bezerro_id'], ['animal.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_parto_fazenda_id'), 'parto', ['fazenda_id'], unique=False)
    op.create_index(op.f('ix_parto_mae_id'), 'parto', ['mae_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_parto_mae_id'), table_name='parto')
    op.drop_index(op.f('ix_parto_fazenda_id'), table_name='parto')
    op.drop_table('parto')
