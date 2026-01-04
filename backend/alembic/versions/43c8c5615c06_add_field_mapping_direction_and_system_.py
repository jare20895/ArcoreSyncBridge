"""add_field_mapping_direction_and_system_fields

Revision ID: 43c8c5615c06
Revises: 98dd8cac8c98
Create Date: 2026-01-03 22:08:47.299411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43c8c5615c06'
down_revision: Union[str, None] = '98dd8cac8c98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sync_direction column to field_mappings table
    op.add_column('field_mappings',
        sa.Column('sync_direction', sa.String(), nullable=False, server_default='BIDIRECTIONAL')
    )

    # Add is_system_field column to field_mappings table
    op.add_column('field_mappings',
        sa.Column('is_system_field', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('field_mappings', 'is_system_field')
    op.drop_column('field_mappings', 'sync_direction')
