"""escore corporal

Revision ID: c3a5e7f9b024
Revises: b2f4c6a8d013
Create Date: 2026-07-16 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a5e7f9b024'
down_revision: Union[str, None] = 'b2f4c6a8d013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'escore_corporal',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fazenda_id', sa.Uuid(), nullable=False),
        sa.Column('animal_id', sa.Uuid(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('escore', sa.Numeric(precision=2, scale=1), nullable=False),
        sa.Column('observacao', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['fazenda_id'], ['fazenda.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['animal_id'], ['animal.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_escore_corporal_fazenda_id'), 'escore_corporal', ['fazenda_id'], unique=False)
    op.create_index(op.f('ix_escore_corporal_animal_id'), 'escore_corporal', ['animal_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_escore_corporal_animal_id'), table_name='escore_corporal')
    op.drop_index(op.f('ix_escore_corporal_fazenda_id'), table_name='escore_corporal')
    op.drop_table('escore_corporal')
