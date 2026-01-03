"""run_history

Revision ID: 008_run_history
Revises: 007_throttling
Create Date: 2026-01-02 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_run_history'
down_revision = '007_throttling'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('sync_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_type', sa.String(), nullable=False), # PUSH, INGRESS, CDC
        sa.Column('status', sa.String(), nullable=False), # RUNNING, COMPLETED, FAILED
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('items_processed', sa.Integer(), default=0),
        sa.Column('items_failed', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('ix_sync_runs_sync_def_id', 'sync_runs', ['sync_def_id'])
    op.create_index('ix_sync_runs_start_time', 'sync_runs', ['start_time'])


def downgrade() -> None:
    op.drop_table('sync_runs')
