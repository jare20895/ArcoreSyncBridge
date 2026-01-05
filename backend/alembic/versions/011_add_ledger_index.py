"""add_ledger_index

Revision ID: 011_add_ledger_index
Revises: 010_add_inventory_models
Create Date: 2026-01-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_add_ledger_index'
down_revision = 'a8d319b57d44'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create index for optimizing Ingress (Pull) lookups
    op.create_index(
        'idx_ledger_sp_lookup',
        'sync_ledger',
        ['sync_def_id', 'sp_list_id', 'sp_item_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_ledger_sp_lookup', table_name='sync_ledger')
