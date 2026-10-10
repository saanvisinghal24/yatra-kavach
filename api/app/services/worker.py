import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete
from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models.receipt import Receipt
from app.models.group import Group, Member
from app.models.checkin import Checkin
from app.models.safety import RiskFlag, Incident, SymptomReport, ShareToken, NotificationLog
from app.models.trail import Yatra
from app.services.pipeline import evaluate_all

async def delete_groups(db, ids):
    for model in (Receipt, Incident, ShareToken, SymptomReport, Checkin, RiskFlag, Member):
        await db.execute(delete(model).where(model.group_id.in_(ids)))
    await db.execute(delete(Group).where(Group.id.in_(ids)))

async def retention(db):
    cutoff = datetime.now(timezone.utc)-timedelta(days=get_settings().RETENTION_DAYS)
    ids = (await db.execute(select(Group.id).join(Yatra,Group.yatra_id==Yatra.id).where(Group.created_at<cutoff,Yatra.season_end<cutoff.date()))).scalars().all()
    await db.execute(delete(NotificationLog).where(NotificationLog.sent_at < cutoff))
    await delete_groups(db,ids)
    await db.commit()

async def main():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await evaluate_all(db,weather=True)
                await retention(db)
                Path("/tmp/yatra-worker-heartbeat").touch()
        except Exception:
            logging.getLogger(__name__).error('Safety sweep failed; will retry')
        await asyncio.sleep(60)

if __name__ == '__main__': asyncio.run(main())
