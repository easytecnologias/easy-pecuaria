"""audit log

Revision ID: e5c7f9a1d246
Revises: d4b6e8a0c135
Create Date: 2026-07-16 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5c7f9a1d246'
down_revision: Union[str, None] = 'd4b6e8a0c135'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=True),
        sa.Column('usuario_id', sa.Uuid(), nullable=True),
        sa.Column('usuario_email', sa.String(length=180), nullable=False),
        sa.Column('acao', sa.String(length=80), nullable=False),
        sa.Column('entidade', sa.String(length=40), nullable=True),
        sa.Column('entidade_id', sa.Uuid(), nullable=True),
        sa.Column('detalhe', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizacao.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_log_org_id'), 'audit_log', ['org_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_log_org_id'), table_name='audit_log')
    op.drop_table('audit_log')
