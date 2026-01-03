"""cdc_metadata

Revision ID: 006_cdc_metadata
Revises: 005_ledger_scoping
Create Date: 2026-01-02 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_cdc_metadata'
down_revision = '005_ledger_scoping'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # database_instances
    op.add_column('database_instances', sa.Column('replication_slot_name', sa.String(), nullable=True))
    op.add_column('database_instances', sa.Column('last_wal_lsn', sa.String(), nullable=True))
    
    # sync_definitions
    op.add_column('sync_definitions', sa.Column('cdc_enabled', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('sync_definitions', 'cdc_enabled')
    op.drop_column('database_instances', 'last_wal_lsn')
    op.drop_column('database_instances', 'replication_slot_name')
