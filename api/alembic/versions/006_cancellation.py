"""Private pre-departure group cancellation."""
from alembic import op
import sqlalchemy as sa
revision = "006_cancellation"
down_revision = "005_pilot_labels"
branch_labels = depends_on = None

def upgrade():
    op.add_column("group", sa.Column("cancellation_token_hash", sa.String(64), nullable=True))
    op.add_column("group", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("group", sa.Column("cancellation_reason", sa.String(300), nullable=True))

def downgrade():
    for name in ("cancellation_reason", "cancelled_at", "cancellation_token_hash"):
        op.drop_column("group", name)
