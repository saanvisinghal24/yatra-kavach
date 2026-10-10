from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models.trail import Yatra, Route, Checkpoint
from app.schemas.trail import YatraSchema, RouteSchema

router = APIRouter(prefix="/yatras", tags=["Yatras & Routes"])

@router.get("", response_model=List[YatraSchema])
async def list_yatras(db: AsyncSession = Depends(get_db)):
    """List all active pilgrimages with their routes and checkpoints."""
    stmt = (
        select(Yatra)
        .options(
            selectinload(Yatra.routes).selectinload(Route.checkpoints)
        )
        .order_by(Yatra.id)
    )
    result = await db.execute(stmt)
    yatras = result.scalars().all()
    return yatras

@router.get("/{slug}", response_model=YatraSchema)
async def get_yatra_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific pilgrimage by slug."""
    stmt = (
        select(Yatra)
        .where(Yatra.slug == slug)
        .options(
            selectinload(Yatra.routes).selectinload(Route.checkpoints)
        )
    )
    result = await db.execute(stmt)
    yatra = result.scalar_one_or_none()
    if not yatra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Yatra with slug '{slug}' not found."
        )
    return yatra
