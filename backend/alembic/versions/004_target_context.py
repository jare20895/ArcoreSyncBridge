"""target_context

Revision ID: 004_target_context
Revises: 003_fix_models
Create Date: 2026-01-02 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_target_context'
down_revision = '003_fix_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sync_targets
    op.add_column('sync_targets', sa.Column('sharepoint_connection_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('sync_targets', sa.Column('site_id', sa.String(), nullable=True))
    
    # Ideally FK to sharepoint_connections, but connection_id might be nullable if using default? 
    # Spec says "Store SharePoint context per target".
    op.create_foreign_key('fk_sync_targets_connection', 'sync_targets', 'sharepoint_connections', ['sharepoint_connection_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_sync_targets_connection', 'sync_targets', type_='foreignkey')
    op.drop_column('sync_targets', 'site_id')
    op.drop_column('sync_targets', 'sharepoint_connection_id')
