"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # database_instances
    op.create_table('database_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_label', sa.String(), nullable=False),
        sa.Column('host', sa.String(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instance_label')
    )

    # sharepoint_connections
    op.create_table('sharepoint_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret', sa.String(), nullable=True),
        sa.Column('authority_host', sa.String(), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # sync_definitions
    op.create_table('sync_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('source_table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_list_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sync_mode', sa.String(), nullable=False),
        sa.Column('conflict_policy', sa.String(), nullable=False),
        sa.Column('key_strategy', sa.String(), nullable=False),
        sa.Column('key_constraint_name', sa.String(), nullable=True),
        sa.Column('target_strategy', sa.String(), nullable=False),
        sa.Column('cursor_strategy', sa.String(), nullable=False),
        sa.Column('cursor_column_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sharding_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # sync_sources
    op.create_table('sync_sources',
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('database_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['database_instance_id'], ['database_instances.id'], ),
        sa.ForeignKeyConstraint(['sync_def_id'], ['sync_definitions.id'], ),
        sa.PrimaryKeyConstraint('sync_def_id', 'database_instance_id')
    )

    # sync_targets
    op.create_table('sync_targets',
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['sync_def_id'], ['sync_definitions.id'], ),
        sa.PrimaryKeyConstraint('sync_def_id', 'target_list_id')
    )

    # sync_key_columns
    op.create_table('sync_key_columns',
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ordinal_position', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['sync_def_id'], ['sync_definitions.id'], ),
        sa.PrimaryKeyConstraint('sync_def_id', 'column_id')
    )

    # field_mappings
    op.create_table('field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('transform_rule', sa.String(), nullable=True),
        sa.Column('is_key', sa.Boolean(), nullable=False),
        sa.Column('is_readonly', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['sync_def_id'], ['sync_definitions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # sync_cursors
    op.create_table('sync_cursors',
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cursor_scope', sa.String(), nullable=False),
        sa.Column('cursor_type', sa.String(), nullable=False),
        sa.Column('cursor_value', sa.String(), nullable=False),
        sa.Column('source_instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sync_def_id'], ['sync_definitions.id'], ),
        sa.PrimaryKeyConstraint('sync_def_id', 'cursor_scope')
    )

    # sync_ledger
    op.create_table('sync_ledger',
        sa.Column('source_identity_hash', sa.String(), nullable=False),
        sa.Column('source_identity', sa.String(), nullable=False),
        sa.Column('source_key_strategy', sa.String(), nullable=False),
        sa.Column('source_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sp_list_id', sa.String(), nullable=False),
        sa.Column('sp_item_id', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('last_source_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('provenance', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('source_identity_hash')
    )

def downgrade() -> None:
    op.drop_table('sync_ledger')
    op.drop_table('sync_cursors')
    op.drop_table('field_mappings')
    op.drop_table('sync_key_columns')
    op.drop_table('sync_targets')
    op.drop_table('sync_sources')
    op.drop_table('sync_definitions')
    op.drop_table('sharepoint_connections')
    op.drop_table('database_instances')
