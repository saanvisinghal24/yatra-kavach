"""Auditable member-level return accounting. Historical destination scans do not prove exit."""
from alembic import op
import sqlalchemy as sa
revision = '003_journey'
down_revision = '002_security'
branch_labels = depends_on = None

def upgrade():
    op.add_column('group', sa.Column('planned_return', sa.DateTime(timezone=True)))
    op.add_column('member', sa.Column('journey_state', sa.String(24), nullable=False, server_default='planned'))
    op.add_column('member', sa.Column('last_visit_at', sa.DateTime(timezone=True)))
    op.add_column('member', sa.Column('last_checkpoint_id', sa.Integer()))
    op.add_column('member', sa.Column('confirmation_source', sa.String(16)))
    op.add_column('checkin', sa.Column('direction', sa.String(16), nullable=False, server_default='outbound'))
    op.add_column('checkin', sa.Column('member_ids', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('checkin', sa.Column('state_applied', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE yatra SET status='planned' WHERE slug <> 'manimahesh'")
    op.execute("UPDATE \"group\" SET status='active' WHERE status='completed'")

def downgrade():
    for col in ('state_applied','member_ids','direction'): op.drop_column('checkin',col)
    for col in ('confirmation_source','last_checkpoint_id','last_visit_at','journey_state'): op.drop_column('member',col)
    op.drop_column('group','planned_return')
