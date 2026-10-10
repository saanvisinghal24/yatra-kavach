import os
import asyncio
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.user import User
from app.services.auth import hash_password

async def seed_staff():
    async with AsyncSessionLocal() as db:
        for role in ("admin", "health", "police", "rescue", "volunteer"):
            email = os.environ.get(f"STAFF_{role.upper()}_EMAIL", "")
            password = os.environ.get(f"STAFF_{role.upper()}_PASSWORD", "")
            if not email or len(password) < 16:
                raise ValueError(f"Set STAFF_{role.upper()}_EMAIL and a random password of at least 16 characters")
            user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not user:
                db.add(User(email=email, password_hash=hash_password(password), role=role))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_staff())
