"""Scoped expiring advisories, observations and operational status publications."""
from alembic import op
import sqlalchemy as sa
revision = '004_advisories'
down_revision = '003_journey'
branch_labels = depends_on = None


def upgrade():
    op.create_table('advisory',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('route.id', ondelete='CASCADE'), nullable=False),
        sa.Column('checkpoint_id', sa.Integer(), sa.ForeignKey('checkpoint.id', ondelete='CASCADE')),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='SET NULL')),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('title_hi', sa.String(160), nullable=False, server_default=''),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('body_hi', sa.Text(), nullable=False, server_default=''),
        sa.Column('source_url', sa.String(2000)),
        sa.Column('checkpoint_status', sa.String(16)),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True)),
        sa.Column('withdrawn_by', sa.Integer(), sa.ForeignKey('user.id', ondelete='SET NULL')),
        sa.Column('simulated', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index('ix_advisory_route_id', 'advisory', ['route_id'])
    op.create_index('ix_advisory_expires_at', 'advisory', ['expires_at'])


def downgrade():
    op.drop_table('advisory')
