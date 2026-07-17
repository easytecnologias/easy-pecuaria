"""usuario superadmin (multi-org)

Revision ID: d4b6e8a0c135
Revises: c3a5e7f9b024
Create Date: 2026-07-16 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b6e8a0c135'
down_revision: Union[str, None] = 'c3a5e7f9b024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'usuario',
        sa.Column('is_superadmin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    # promove o admin inicial a super-admin da plataforma
    op.execute("UPDATE usuario SET is_superadmin = true WHERE email = 'admin@pecuaria.local'")


def downgrade() -> None:
    op.drop_column('usuario', 'is_superadmin')
