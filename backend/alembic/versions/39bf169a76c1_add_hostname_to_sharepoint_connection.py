"""add_hostname_to_sharepoint_connection

Revision ID: 39bf169a76c1
Revises: 010_add_inventory_models
Create Date: 2026-01-03 14:05:01.073257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39bf169a76c1'
down_revision: Union[str, None] = '010_add_inventory_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sharepoint_connections', sa.Column('hostname', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('sharepoint_connections', 'hostname')