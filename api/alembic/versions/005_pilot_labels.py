"""Correct proposed pilot labels; remove unverified facility claims."""
from alembic import op
import sqlalchemy as sa
revision = '005_pilot_labels'
down_revision = '004_advisories'
branch_labels = depends_on = None

def upgrade():
    conn = op.get_bind()
    route_ids = "SELECT route.id FROM route JOIN yatra ON yatra.id=route.yatra_id WHERE yatra.slug='manimahesh'"
    for seq,en,hi in [(1,'Hadsar','हड़सर'),(2,'Dhancho','धंचो'),(3,'Sundrasi','सुंदरासी'),(4,'Gauri Kund','गौरी कुंड'),(5,'Manimahesh Lake','मणिमहेश झील')]:
        conn.execute(sa.text(f'UPDATE checkpoint SET name_en=:en,name_hi=:hi WHERE route_id IN ({route_ids}) AND seq=:seq'),dict(en=en,hi=hi,seq=seq))
    conn.execute(sa.text("UPDATE checkpoint SET facilities='{}' WHERE verified=false"))

def downgrade():
    # Metadata correction must not reintroduce unverified facility claims.
    pass
