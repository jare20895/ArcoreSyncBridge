"""add_inventory_integrity_indexes

Revision ID: b7c3d1e4f2a9
Revises: 011_add_ledger_index
Create Date: 2026-03-18 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b7c3d1e4f2a9'
down_revision = '011_add_ledger_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_sharepoint_connections_tenant_client',
        'sharepoint_connections',
        ['tenant_id', 'client_id'],
    )
    op.create_unique_constraint(
        'uq_databases_app_name_env',
        'databases',
        ['application_id', 'name', 'environment'],
    )
    op.create_unique_constraint(
        'uq_database_tables_db_schema_table',
        'database_tables',
        ['database_id', 'schema_name', 'table_name'],
    )
    op.create_index('ix_database_tables_database_id', 'database_tables', ['database_id'])
    op.create_unique_constraint(
        'uq_table_columns_table_column',
        'table_columns',
        ['table_id', 'column_name'],
    )
    op.create_index('ix_table_columns_table_id', 'table_columns', ['table_id'])
    op.create_unique_constraint(
        'uq_sharepoint_sites_connection_site',
        'sharepoint_sites',
        ['connection_id', 'site_id'],
    )
    op.create_unique_constraint(
        'uq_sharepoint_lists_site_list',
        'sharepoint_lists',
        ['site_id', 'list_id'],
    )
    op.create_index('ix_sharepoint_lists_source_table_id', 'sharepoint_lists', ['source_table_id'])
    op.create_unique_constraint(
        'uq_sharepoint_columns_list_column',
        'sharepoint_columns',
        ['list_id', 'column_name'],
    )
    op.create_index('ix_sharepoint_columns_list_id', 'sharepoint_columns', ['list_id'])
    op.create_unique_constraint(
        'uq_field_mappings_sync_source_target',
        'field_mappings',
        ['sync_def_id', 'source_column_id', 'target_column_id'],
    )
    op.create_index('ix_field_mappings_sync_def_id', 'field_mappings', ['sync_def_id'])
    op.create_index(
        'ix_sync_cursors_sync_scope_updated',
        'sync_cursors',
        ['sync_def_id', 'cursor_scope', 'updated_at'],
    )
    op.create_index(
        'ix_sync_ledger_sync_source_instance',
        'sync_ledger',
        ['sync_def_id', 'source_instance_id'],
    )
    op.create_index(
        'ix_source_table_metrics_table_instance',
        'source_table_metrics',
        ['table_id', 'database_instance_id'],
    )
    op.create_index('ix_target_list_metrics_target_list_id', 'target_list_metrics', ['target_list_id'])
    op.create_index(
        'ix_introspection_runs_instance_started',
        'introspection_runs',
        ['database_instance_id', 'started_at'],
    )
    op.create_index(
        'ix_schema_snapshots_table_instance',
        'schema_snapshots',
        ['table_id', 'database_instance_id'],
    )
    op.create_index('ix_sync_metrics_sync_def_id', 'sync_metrics', ['sync_def_id'])
    op.create_index('ix_sync_metrics_reconcile_status', 'sync_metrics', ['reconcile_status'])
    op.create_index('ix_sync_events_sync_run_id', 'sync_events', ['sync_run_id'])
    op.create_index('ix_sync_events_severity_created', 'sync_events', ['severity', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_sync_events_severity_created', table_name='sync_events')
    op.drop_index('ix_sync_events_sync_run_id', table_name='sync_events')
    op.drop_index('ix_sync_metrics_reconcile_status', table_name='sync_metrics')
    op.drop_index('ix_sync_metrics_sync_def_id', table_name='sync_metrics')
    op.drop_index('ix_schema_snapshots_table_instance', table_name='schema_snapshots')
    op.drop_index('ix_introspection_runs_instance_started', table_name='introspection_runs')
    op.drop_index('ix_target_list_metrics_target_list_id', table_name='target_list_metrics')
    op.drop_index('ix_source_table_metrics_table_instance', table_name='source_table_metrics')
    op.drop_index('ix_sync_ledger_sync_source_instance', table_name='sync_ledger')
    op.drop_index('ix_sync_cursors_sync_scope_updated', table_name='sync_cursors')
    op.drop_index('ix_field_mappings_sync_def_id', table_name='field_mappings')
    op.drop_constraint('uq_field_mappings_sync_source_target', 'field_mappings', type_='unique')
    op.drop_index('ix_sharepoint_columns_list_id', table_name='sharepoint_columns')
    op.drop_constraint('uq_sharepoint_columns_list_column', 'sharepoint_columns', type_='unique')
    op.drop_index('ix_sharepoint_lists_source_table_id', table_name='sharepoint_lists')
    op.drop_constraint('uq_sharepoint_lists_site_list', 'sharepoint_lists', type_='unique')
    op.drop_constraint('uq_sharepoint_sites_connection_site', 'sharepoint_sites', type_='unique')
    op.drop_index('ix_table_columns_table_id', table_name='table_columns')
    op.drop_constraint('uq_table_columns_table_column', 'table_columns', type_='unique')
    op.drop_index('ix_database_tables_database_id', table_name='database_tables')
    op.drop_constraint('uq_database_tables_db_schema_table', 'database_tables', type_='unique')
    op.drop_constraint('uq_databases_app_name_env', 'databases', type_='unique')
    op.drop_constraint('uq_sharepoint_connections_tenant_client', 'sharepoint_connections', type_='unique')
