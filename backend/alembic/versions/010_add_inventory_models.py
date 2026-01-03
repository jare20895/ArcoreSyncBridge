"""add_inventory_models_complete_data_model

Revision ID: 010_add_inventory_models
Revises: 009_cascade_deletes
Create Date: 2026-01-02 00:00:00.000000

Adds the complete DATA_MODEL specification including:
- Application and Database inventory models
- DatabaseTable, TableColumn, TableConstraint, TableIndex
- SharePointSite, SharePointList, SharePointColumn
- Metrics and monitoring tables
- Updates DatabaseInstance with new fields

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_inventory_models'
down_revision = '009_cascade_deletes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================================
    # Create Application table
    # ============================================================================
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_team', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ============================================================================
    # Create Database table
    # ============================================================================
    op.create_table(
        'databases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('db_type', sa.String(), server_default='POSTGRES', nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('database_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('application_id', 'database_name', 'environment', name='uq_database_app_name_env')
    )
    op.create_index('ix_databases_app_status', 'databases', ['application_id', 'status'])

    # ============================================================================
    # Update DatabaseInstance table with new fields
    # ============================================================================
    op.add_column('database_instances', sa.Column('database_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('database_instances', sa.Column('database_name_override', sa.String(), nullable=True))
    op.add_column('database_instances', sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('database_instances', sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True))
    op.add_column('database_instances', sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True))
    op.add_column('database_instances', sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_database_instances_database_id',
        'database_instances', 'databases',
        ['database_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_database_instances_database_status', 'database_instances', ['database_id', 'status', 'priority'])

    # ============================================================================
    # Create DatabaseTable table
    # ============================================================================
    op.create_table(
        'database_tables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('database_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schema_name', sa.String(), server_default='public', nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('table_type', sa.String(), server_default='BASE', nullable=False),
        sa.Column('primary_key', sa.String(), nullable=True),
        sa.Column('row_estimate', sa.BigInteger(), nullable=True),
        sa.Column('last_introspected_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('database_id', 'schema_name', 'table_name', name='uq_table_database_schema_name')
    )

    # ============================================================================
    # Create TableColumn table
    # ============================================================================
    op.create_table(
        'table_columns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ordinal_position', sa.Integer(), nullable=False),
        sa.Column('column_name', sa.String(), nullable=False),
        sa.Column('data_type', sa.String(), nullable=False),
        sa.Column('is_nullable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('is_identity', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_primary_key', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_unique', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['table_id'], ['database_tables.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('table_id', 'column_name', name='uq_column_table_name')
    )

    # ============================================================================
    # Create TableConstraint table
    # ============================================================================
    op.create_table(
        'table_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('constraint_name', sa.String(), nullable=False),
        sa.Column('constraint_type', sa.String(), nullable=False),
        sa.Column('columns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('referenced_table', sa.String(), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['database_tables.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_table_constraints_table_type', 'table_constraints', ['table_id', 'constraint_type'])

    # ============================================================================
    # Create TableIndex table
    # ============================================================================
    op.create_table(
        'table_indexes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('index_name', sa.String(), nullable=False),
        sa.Column('is_unique', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('index_method', sa.String(), nullable=True),
        sa.Column('columns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['database_tables.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_table_indexes_table_unique', 'table_indexes', ['table_id', 'is_unique'])

    # ============================================================================
    # Create SourceTableMetric table
    # ============================================================================
    op.create_table(
        'source_table_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('database_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('row_count', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('max_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['database_tables.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['database_instance_id'], ['database_instances.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_source_table_metrics_table_instance_time', 'source_table_metrics', ['table_id', 'database_instance_id', 'captured_at'])

    # ============================================================================
    # Create SharePointSite table
    # ============================================================================
    op.create_table(
        'sharepoint_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('hostname', sa.String(), nullable=False),
        sa.Column('site_path', sa.String(), nullable=False),
        sa.Column('site_id', sa.String(), nullable=False),
        sa.Column('web_url', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='ACTIVE', nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['sharepoint_connections.id'], ondelete='CASCADE'),
    )

    # ============================================================================
    # Create SharePointList table
    # ============================================================================
    op.create_table(
        'sharepoint_lists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('list_id', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template', sa.String(), nullable=True),
        sa.Column('is_provisioned', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_provisioned_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('site_id', 'list_id', name='uq_list_site_list_id')
    )

    # ============================================================================
    # Create SharePointColumn table
    # ============================================================================
    op.create_table(
        'sharepoint_columns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('column_name', sa.String(), nullable=False),
        sa.Column('column_type', sa.String(), nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_readonly', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['sharepoint_lists.id'], ondelete='CASCADE'),
    )

    # ============================================================================
    # Create TargetListMetric table
    # ============================================================================
    op.create_table(
        'target_list_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('target_list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('item_count', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_modified_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['target_list_id'], ['sharepoint_lists.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_target_list_metrics_list_time', 'target_list_metrics', ['target_list_id', 'captured_at'])

    # ============================================================================
    # Create IntrospectionRun table
    # ============================================================================
    op.create_table(
        'introspection_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('database_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), server_default='RUNNING', nullable=False),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['database_instance_id'], ['database_instances.id'], ondelete='CASCADE'),
    )

    # ============================================================================
    # Create SchemaSnapshot table
    # ============================================================================
    op.create_table(
        'schema_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('database_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('columns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('indexes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['database_tables.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['database_instance_id'], ['database_instances.id'], ondelete='CASCADE'),
    )

    # ============================================================================
    # Create SyncMetric table
    # ============================================================================
    op.create_table(
        'sync_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_list_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_sync_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_rows_synced', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_reconcile_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_row_count', sa.BigInteger(), nullable=True),
        sa.Column('target_row_count', sa.BigInteger(), nullable=True),
        sa.Column('reconcile_delta', sa.BigInteger(), nullable=True),
        sa.Column('reconcile_status', sa.String(), server_default='UNKNOWN', nullable=False),
        sa.UniqueConstraint('sync_def_id', 'source_instance_id', 'target_list_id', name='uq_sync_metric_def_source_target')
    )

    # ============================================================================
    # Create SyncEvent table
    # ============================================================================
    op.create_table(
        'sync_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_sync_events_run_time', 'sync_events', ['sync_run_id', 'created_at'])


def downgrade() -> None:
    # Drop all new tables in reverse order
    op.drop_table('sync_events')
    op.drop_table('sync_metrics')
    op.drop_table('schema_snapshots')
    op.drop_table('introspection_runs')
    op.drop_table('target_list_metrics')
    op.drop_table('sharepoint_columns')
    op.drop_table('sharepoint_lists')
    op.drop_table('sharepoint_sites')
    op.drop_table('source_table_metrics')
    op.drop_table('table_indexes')
    op.drop_table('table_constraints')
    op.drop_table('table_columns')
    op.drop_table('database_tables')

    # Remove added columns from database_instances
    op.drop_constraint('fk_database_instances_database_id', 'database_instances', type_='foreignkey')
    op.drop_column('database_instances', 'last_verified_at')
    op.drop_column('database_instances', 'valid_to')
    op.drop_column('database_instances', 'valid_from')
    op.drop_column('database_instances', 'config')
    op.drop_column('database_instances', 'database_name_override')
    op.drop_column('database_instances', 'database_id')

    op.drop_table('databases')
    op.drop_table('applications')
