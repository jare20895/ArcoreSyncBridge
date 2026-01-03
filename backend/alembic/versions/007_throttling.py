"""throttling

Revision ID: 007_throttling
Revises: 006_cdc_metadata
Create Date: 2026-01-02 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_throttling'
down_revision = '006_cdc_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sync_definitions', sa.Column('is_paused', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('sync_definitions', sa.Column('rate_limit_ms', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('sync_definitions', 'rate_limit_ms')
    op.drop_column('sync_definitions', 'is_paused')
