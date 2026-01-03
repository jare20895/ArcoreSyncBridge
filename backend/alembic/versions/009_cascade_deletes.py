"""cascade_deletes

Revision ID: 009_cascade_deletes
Revises: 008_run_history
Create Date: 2026-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_cascade_deletes'
down_revision = '008_run_history'
branch_labels = None
depends_on = None


def _drop_fk(conn, table: str, column: str, ref_table: str) -> None:
    rows = conn.execute(
        sa.text(
            """
            SELECT con.conname
            FROM pg_constraint con
            JOIN pg_attribute att
              ON att.attrelid = con.conrelid
             AND att.attnum = ANY(con.conkey)
            WHERE con.contype = 'f'
              AND con.conrelid = CAST(:table AS regclass)
              AND con.confrelid = CAST(:ref_table AS regclass)
              AND att.attname = :column
            """
        ),
        {"table": table, "ref_table": ref_table, "column": column},
    ).fetchall()
    for (name,) in rows:
        op.drop_constraint(name, table, type_='foreignkey')


def upgrade() -> None:
    conn = op.get_bind()

    _drop_fk(conn, 'sync_sources', 'sync_def_id', 'sync_definitions')
    _drop_fk(conn, 'sync_sources', 'database_instance_id', 'database_instances')
    _drop_fk(conn, 'sync_targets', 'sync_def_id', 'sync_definitions')
    _drop_fk(conn, 'sync_targets', 'sharepoint_connection_id', 'sharepoint_connections')
    _drop_fk(conn, 'sync_key_columns', 'sync_def_id', 'sync_definitions')
    _drop_fk(conn, 'field_mappings', 'sync_def_id', 'sync_definitions')
    _drop_fk(conn, 'sync_cursors', 'sync_def_id', 'sync_definitions')

    op.create_foreign_key(
        'fk_sync_sources_sync_def_id',
        'sync_sources',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_sync_sources_database_instance_id',
        'sync_sources',
        'database_instances',
        ['database_instance_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_sync_targets_sync_def_id',
        'sync_targets',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_sync_targets_sharepoint_connection_id',
        'sync_targets',
        'sharepoint_connections',
        ['sharepoint_connection_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_sync_key_columns_sync_def_id',
        'sync_key_columns',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_field_mappings_sync_def_id',
        'field_mappings',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_sync_cursors_sync_def_id',
        'sync_cursors',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_sync_cursors_sync_def_id', 'sync_cursors', type_='foreignkey')
    op.drop_constraint('fk_field_mappings_sync_def_id', 'field_mappings', type_='foreignkey')
    op.drop_constraint('fk_sync_key_columns_sync_def_id', 'sync_key_columns', type_='foreignkey')
    op.drop_constraint('fk_sync_targets_sharepoint_connection_id', 'sync_targets', type_='foreignkey')
    op.drop_constraint('fk_sync_targets_sync_def_id', 'sync_targets', type_='foreignkey')
    op.drop_constraint('fk_sync_sources_database_instance_id', 'sync_sources', type_='foreignkey')
    op.drop_constraint('fk_sync_sources_sync_def_id', 'sync_sources', type_='foreignkey')

    op.create_foreign_key(
        'fk_sync_sources_sync_def_id',
        'sync_sources',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_sync_sources_database_instance_id',
        'sync_sources',
        'database_instances',
        ['database_instance_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_sync_targets_sync_def_id',
        'sync_targets',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_sync_targets_sharepoint_connection_id',
        'sync_targets',
        'sharepoint_connections',
        ['sharepoint_connection_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_sync_key_columns_sync_def_id',
        'sync_key_columns',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_field_mappings_sync_def_id',
        'field_mappings',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_sync_cursors_sync_def_id',
        'sync_cursors',
        'sync_definitions',
        ['sync_def_id'],
        ['id'],
    )
