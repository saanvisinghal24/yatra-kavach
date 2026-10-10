"""Publication is staff-authored information, never an automated safety guarantee."""
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.advisory import Advisory
from app.models.trail import Route, Checkpoint
from app.services.auth import get_current_user

router = APIRouter(prefix='/advisories', tags=['Advisories'])
CONTROL = {'admin', 'health', 'police', 'rescue'}
STAFF = CONTROL | {'volunteer'}


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def scope(user, route_id):
    if user.role not in STAFF:
        raise HTTPException(403, 'Staff role required')
    if user.route_scope is not None and user.route_scope != route_id:
        raise HTTPException(403, 'Outside route scope')


class Publication(BaseModel):
    route_id: int = Field(gt=0)
    checkpoint_id: int | None = Field(None, gt=0)
    kind: Literal['staff_advisory', 'volunteer_observation', 'official_advisory']
    title: str = Field(min_length=1, max_length=160)
    title_hi: str = Field('', max_length=160)
    body: str = Field(min_length=1, max_length=4000)
    body_hi: str = Field('', max_length=4000)
    source_url: HttpUrl | None = None
    checkpoint_status: Literal['open', 'congested', 'closed'] | None = None
    observed_at: datetime
    expires_at: datetime
    simulated: bool = False

    @field_validator('title', 'body')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Publication text cannot be blank')
        return value.strip()

    @field_validator('observed_at', 'expires_at')
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Timezone is required')
        return value.astimezone(timezone.utc)

    @model_validator(mode='after')
    def consistency(self):
        if self.kind == 'official_advisory' and self.source_url is None:
            raise ValueError('Official advisories require a source URL; publication is not source authentication')
        if self.checkpoint_status is not None and self.checkpoint_id is None:
            raise ValueError('Checkpoint status requires a checkpoint')
        if self.expires_at <= self.observed_at:
            raise ValueError('Expiry must follow observation time')
        return self


def public_item(item):
    fields = ('id', 'route_id', 'checkpoint_id', 'kind', 'title', 'title_hi', 'body', 'body_hi',
              'source_url', 'checkpoint_status', 'observed_at', 'received_at', 'expires_at', 'withdrawn_at', 'simulated')
    return {name: utc(value).isoformat() if isinstance(value := getattr(item, name), datetime) else value for name in fields}


@router.get('')
async def active(response: Response, route_id: int = Query(..., gt=0), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    rows = (await db.execute(select(Advisory).where(Advisory.route_id == route_id,
        Advisory.expires_at > now, Advisory.withdrawn_at.is_(None)).order_by(Advisory.observed_at.desc(), Advisory.id.desc()))).scalars().all()
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Retrieved-At'] = now.isoformat()
    return [public_item(item) for item in rows]


@router.get('/history')
async def history(route_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    scope(user, route_id)
    rows = (await db.execute(select(Advisory).where(Advisory.route_id == route_id).order_by(Advisory.id.desc()).limit(limit))).scalars().all()
    return [public_item(item) for item in rows]


@router.post('', status_code=201)
async def publish(payload: Publication, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    scope(user, payload.route_id)
    if user.role == 'volunteer' and (payload.kind != 'volunteer_observation' or payload.checkpoint_status is not None):
        raise HTTPException(403, 'Volunteers may publish observations only')
    if not await db.get(Route, payload.route_id):
        raise HTTPException(404, 'Route not found')
    if payload.checkpoint_id is not None:
        checkpoint = await db.get(Checkpoint, payload.checkpoint_id)
        if not checkpoint or checkpoint.route_id != payload.route_id:
            raise HTTPException(422, 'Checkpoint does not belong to route')
    now = datetime.now(timezone.utc)
    if payload.observed_at > now + timedelta(minutes=5):
        raise HTTPException(422, 'Observation time is in the future; check device clock')
    if payload.expires_at <= now or payload.expires_at > now + timedelta(days=30):
        raise HTTPException(422, 'Expiry must be in the next 30 days')
    data = payload.model_dump(exclude={'source_url'})
    item = Advisory(**data, source_url=str(payload.source_url) if payload.source_url else None,
                    author_id=user.id, received_at=now)
    db.add(item)
    await db.commit()
    return public_item(item)


@router.post('/{advisory_id}/withdraw')
async def withdraw(advisory_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    item = await db.get(Advisory, advisory_id)
    if not item:
        raise HTTPException(404, 'Advisory not found')
    scope(user, item.route_id)
    if user.role not in CONTROL:
        raise HTTPException(403, 'Control-room role required')
    if item.withdrawn_at is None:
        item.withdrawn_at = datetime.now(timezone.utc)
        item.withdrawn_by = user.id
        await db.commit()
    return public_item(item)
