"""add_status_to_sharepoint_list

Revision ID: 98dd8cac8c98
Revises: 1e5342dd39e1
Create Date: 2026-01-03 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98dd8cac8c98'
down_revision: Union[str, None] = '1e5342dd39e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sharepoint_lists', sa.Column('status', sa.String(), server_default='ACTIVE', nullable=False))


def downgrade() -> None:
    op.drop_column('sharepoint_lists', 'status')