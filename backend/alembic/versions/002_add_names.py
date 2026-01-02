"""add_names

Revision ID: 002_add_names
Revises: 70043344a3d8
Create Date: 2026-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_names'
down_revision = '70043344a3d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sync_definitions
    op.add_column('sync_definitions', sa.Column('source_schema', sa.String(), nullable=True))
    op.add_column('sync_definitions', sa.Column('source_table_name', sa.String(), nullable=True))

    # field_mappings
    op.add_column('field_mappings', sa.Column('source_column_name', sa.String(), nullable=True))
    op.add_column('field_mappings', sa.Column('target_column_name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('field_mappings', 'target_column_name')
    op.drop_column('field_mappings', 'source_column_name')
    op.drop_column('sync_definitions', 'source_table_name')
    op.drop_column('sync_definitions', 'source_schema')
