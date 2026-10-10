"""Regression checks for safety-relevant pilot boundaries; no live services."""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from app.main import app
from app.db import AsyncSessionLocal
from app.models.trail import Route, Yatra
from app.models.safety import ShareToken
from app.services.qr_signer import make_checkpoint_qr_payload


def registration(route_id=1, yatra_id=1):
    return dict(consent=True, yatra_id=yatra_id, route_id=route_id,
                leader_name='Simulated QA leader', leader_phone='0000000000',
                emergency_name='Simulated QA contact', emergency_phone='0000000000',
                size=2, planned_start=datetime.now(timezone.utc).isoformat())


@pytest.mark.asyncio
async def test_planned_routes_cannot_register():
    async with AsyncSessionLocal() as db:
        rows=(await db.execute(select(Route.id,Yatra.id).join(Yatra).where(Yatra.slug!='manimahesh'))).all()
    assert rows, 'Seed must retain visible planned routes'
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        for route_id,yatra_id in rows:
            response=await client.post('/api/v1/groups',json=registration(route_id,yatra_id))
            assert response.status_code==422, response.text


@pytest.mark.asyncio
async def test_expired_family_link_is_not_accessible():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        group=(await client.post('/api/v1/groups',json=registration())).json()
        response=await client.post('/api/v1/share/generate/'+group['code'])
        assert response.status_code==200,response.text
        token=response.json()['token']
        async with AsyncSessionLocal() as db:
            share=(await db.execute(select(ShareToken).where(ShareToken.token==token))).scalar_one()
            share.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)
            await db.commit()
        response=await client.get('/api/v1/share/'+token)
        assert response.status_code==404


@pytest.mark.asyncio
async def test_mixed_invalid_valid_batch_preserves_valid_event_and_replay_id():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        group=(await client.post('/api/v1/groups',json=registration())).json()
        valid=dict(id=str(uuid.uuid4()),group_code=group['code'],checkpoint_id=1,
                   signed_qr=make_checkpoint_qr_payload(1,1),headcount=2,
                   client_ts=datetime.now(timezone.utc).isoformat())
        invalid={**valid,'id':str(uuid.uuid4()),'signed_qr':'YK1:CP:1:forged'}
        first=await client.post('/api/v1/checkins/batch',json={'events':[invalid,valid]})
        assert first.status_code==200,first.text
        assert first.json()['accepted_count']==1
        assert first.json()['invalid_count']==1
        replay=await client.post('/api/v1/checkins/batch',json={'events':[valid]})
        assert replay.json()['duplicate_count']==1
