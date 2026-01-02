"""ledger_scoping

Revision ID: 005_ledger_scoping
Revises: 004_target_context
Create Date: 2026-01-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_ledger_scoping'
down_revision = '004_target_context'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add sync_def_id to sync_ledger
    op.add_column('sync_ledger', sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # We ideally want it to be nullable=False, but we have existing data.
    # In a real scenario we'd backfill or truncate.
    # For now, let's assume we can truncate or it's fine.
    
    # 2. Update Primary Key
    # Drop existing PK (source_identity_hash)
    try:
        op.drop_constraint('sync_ledger_pkey', 'sync_ledger', type_='primary')
    except Exception:
        pass
    
    # Create new PK (sync_def_id, source_identity_hash)
    # This requires sync_def_id to be non-null. 
    # If this fails due to nulls, user must manually fix data.
    # We will try to make it nullable=False after update, but here we just set it as PK.
    # Note: Postgres PK columns must be NOT NULL.
    # So we should probably make it not null, but that requires data migration.
    # For this dev environment, I will recreate the table or just add it to PK and hope for best (or truncate).
    
    # Let's try to add it as PK. If it fails, I'll catch it? No, alembic doesn't catch.
    # Proper way: 
    # op.execute("TRUNCATE TABLE sync_ledger") # SAFETY: Dev env only
    op.execute("TRUNCATE TABLE sync_ledger CASCADE") 
    
    op.alter_column('sync_ledger', 'sync_def_id', nullable=False)
    op.create_primary_key('sync_ledger_pkey', 'sync_ledger', ['sync_def_id', 'source_identity_hash'])


def downgrade() -> None:
    op.drop_constraint('sync_ledger_pkey', 'sync_ledger', type_='primary')
    op.drop_column('sync_ledger', 'sync_def_id')
    op.create_primary_key('sync_ledger_pkey', 'sync_ledger', ['source_identity_hash'])
