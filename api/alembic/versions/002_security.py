"""Shared request limits and simulated group marker."""
from alembic import op
import sqlalchemy as sa
revision = '002_security'
down_revision = '001_initial_schema'
branch_labels = depends_on = None

def upgrade():
    op.create_table('event_receipt',sa.Column('id',sa.String(64),primary_key=True),sa.Column('group_id',sa.Integer(),sa.ForeignKey('group.id',ondelete='CASCADE'),nullable=False),sa.Column('response',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table('rate_bucket', sa.Column('key', sa.String(64), primary_key=True), sa.Column('bucket', sa.BigInteger(), primary_key=True), sa.Column('count', sa.Integer(), nullable=False))
    op.add_column('group', sa.Column('consent_version', sa.String(16), nullable=False, server_default='demo-v1'))
    op.add_column('group', sa.Column('simulated', sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    op.drop_table("event_receipt")
    op.drop_column("group", "consent_version")
    op.drop_column('group', 'simulated')
    op.drop_table('rate_bucket')
