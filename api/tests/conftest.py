import os
import pytest
import secrets
for key in ("SECRET_KEY", "JWT_SECRET", "QR_HMAC_SECRET"):
    os.environ[key] = secrets.token_urlsafe(48)

# Ensure testing uses SQLite in-memory or local test file
import tempfile
_test_db = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///" + _test_db)
os.environ["SYNC_DATABASE_URL"] = os.environ.get("TEST_SYNC_DATABASE_URL", "sqlite:///" + _test_db)
os.environ["ENVIRONMENT"] = "testing"

from app.config import get_settings
get_settings.cache_clear()

import pytest_asyncio
for role in ('admin','health','police','rescue','volunteer'):
    os.environ[f'STAFF_{role.upper()}_EMAIL'] = f'{role}@test.invalid'
    os.environ[f'STAFF_{role.upper()}_PASSWORD'] = secrets.token_urlsafe(24)

@pytest_asyncio.fixture(autouse=True)
async def setup_domain():
    from app.seed.seed_trails import seed_data
    from app.seed.staff import seed_staff
    from app.db import AsyncSessionLocal
    from app.models.group import Group
    from sqlalchemy import select
    from datetime import datetime, timezone
    await seed_data()
    await seed_staff()
    async with AsyncSessionLocal() as db:
        if not (await db.execute(select(Group).where(Group.code=='TEST01'))).scalar_one_or_none():
            db.add(Group(code='TEST01',yatra_id=1,route_id=1,leader_name='Test Group',leader_phone='0000000000',emergency_name='Test Contact',emergency_phone='0000000000',size=2,planned_start=datetime.now(timezone.utc),status='planned'))
            await db.commit()
