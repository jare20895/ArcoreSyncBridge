"""add_source_table_id_to_sharepoint_list

Revision ID: 1e5342dd39e1
Revises: 39bf169a76c1
Create Date: 2026-01-03 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1e5342dd39e1'
down_revision: Union[str, None] = '39bf169a76c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sharepoint_lists', sa.Column('source_table_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_sharepoint_lists_source_table_id',
        'sharepoint_lists', 'database_tables',
        ['source_table_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_sharepoint_lists_source_table_id', 'sharepoint_lists', type_='foreignkey')
    op.drop_column('sharepoint_lists', 'source_table_id')