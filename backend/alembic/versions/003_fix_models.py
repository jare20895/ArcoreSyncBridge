"""fix_models

Revision ID: 003_fix_models
Revises: 002_add_names
Create Date: 2026-01-02 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_fix_models'
down_revision = '002_add_names'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # database_instances
    op.add_column('database_instances', sa.Column('db_name', sa.String(), nullable=True))
    op.add_column('database_instances', sa.Column('username', sa.String(), nullable=True))
    op.add_column('database_instances', sa.Column('password', sa.String(), nullable=True)) # TODO: Encrypt

    # sync_cursors
    # 1. Add target_list_id
    op.add_column('sync_cursors', sa.Column('target_list_id', postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Update Primary Key / Constraints
    # Dropping old PK constraint might depend on its name.
    # Usually 'sync_cursors_pkey'.
    try:
        op.drop_constraint('sync_cursors_pkey', 'sync_cursors', type_='primary')
    except Exception:
        pass # Might not exist or different name
    
    # We want a composite unique constraint that allows NULLs (so distinct source vs target cursors)
    # But for a PK, we need non-nulls.
    # Strategy: Use a surrogate PK (id) OR keep composite PK if we ensure no nulls (which is hard here).
    # Better: Use (sync_def_id, cursor_scope, source_instance_id, target_list_id) as Unique Index,
    # and maybe just a surrogate ID for PK, OR simple composite PK if we force values.
    # Let's try adding a surrogate ID for simplicity in management, 
    # OR stick to the existing pattern but relax the PK to a Unique Constraint.
    
    # Let's go with: PK = (sync_def_id, cursor_scope, source_instance_id, target_list_id) -> Wait, if nulls allowed, can't be PK.
    # Revert to: PK = (sync_def_id, cursor_scope) IS NOT ENOUGH.
    
    # DECISION: Add a surrogate ID to SyncCursor to be clean.
    # But that changes the model significantly.
    
    # Alternative:
    # Make a unique index on (sync_def_id, cursor_scope, source_instance_id, target_list_id).
    # And maybe no PK? SQLAlchemy needs a PK.
    
    # Let's add a surrogate 'id' column.
    op.add_column('sync_cursors', sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.create_primary_key('sync_cursors_pkey', 'sync_cursors', ['id'])

    # Add Unique Index for logic
    # Note: Postgres treats NULLs as distinct in Unique constraints usually, but for "one cursor per scope/target", we want uniqueness.
    # We might need partial indexes.
    # "unique_target_cursor" WHERE cursor_scope='TARGET'
    # "unique_source_cursor" WHERE cursor_scope='SOURCE'
    
    op.create_index('ix_sync_cursors_target', 'sync_cursors', ['sync_def_id', 'target_list_id'], unique=True, postgresql_where=sa.text("cursor_scope = 'TARGET'"))
    op.create_index('ix_sync_cursors_source', 'sync_cursors', ['sync_def_id', 'source_instance_id'], unique=True, postgresql_where=sa.text("cursor_scope = 'SOURCE'"))


def downgrade() -> None:
    # sync_cursors
    op.drop_index('ix_sync_cursors_source', table_name='sync_cursors')
    op.drop_index('ix_sync_cursors_target', table_name='sync_cursors')
    op.drop_constraint('sync_cursors_pkey', 'sync_cursors', type_='primary')
    op.drop_column('sync_cursors', 'id')
    op.drop_column('sync_cursors', 'target_list_id')
    
    # restore old PK (approximate)
    op.create_primary_key('sync_cursors_pkey', 'sync_cursors', ['sync_def_id', 'cursor_scope'])

    # database_instances
    op.drop_column('database_instances', 'password')
    op.drop_column('database_instances', 'username')
    op.drop_column('database_instances', 'db_name')
