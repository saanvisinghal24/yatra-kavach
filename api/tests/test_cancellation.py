import hashlib
import uuid
from datetime import datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from app.main import app
from app.db import AsyncSessionLocal
from app.models.group import Group
from app.services.qr_signer import make_checkpoint_qr_payload

async def register(client):
    r = await client.post('/api/v1/groups', json=dict(consent=True, yatra_id=1, route_id=1,
        leader_name='Test Leader', leader_phone='9000000000', emergency_name='Test Contact',
        emergency_phone='9000000001', size=2, planned_start='2027-08-01T06:00:00Z'))
    assert r.status_code == 201, r.text
    return r.json()

def scan(code):
    import os
    return dict(id=str(uuid.uuid4()), group_code=code, checkpoint_id=1,
        signed_qr=make_checkpoint_qr_payload(1, 1, os.environ['QR_HMAC_SECRET']),
        source='self', headcount=2, client_ts=datetime.now(timezone.utc).isoformat(), clock_skew_s=0)

@pytest.mark.asyncio
async def test_private_cancellation_idempotency_and_scan_block():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        data=await register(client);code=data['code'];token=data['cancellation_token']
        async with AsyncSessionLocal() as db:
            g=(await db.execute(select(Group).where(Group.code==code))).scalar_one()
            assert g.cancellation_token_hash==hashlib.sha256(token.encode()).hexdigest()
        public=await client.get('/api/v1/groups/'+code)
        assert token not in public.text and 'cancellation_token' not in public.text
        assert (await client.post(f'/api/v1/groups/{code}/cancel',json={'cancellation_token':'wrong'})).status_code==403
        for _ in range(2):
            r=await client.post(f'/api/v1/groups/{code}/cancel',json={'cancellation_token':token,'reason':'Plans changed'})
            assert r.status_code==200, r.text
        public=(await client.get('/api/v1/groups/'+code)).json()
        assert public['status']=='cancelled' and public['next_checkpoint'] is None
        assert public['journey_counts']['cancelled']==2
        r=await client.post('/api/v1/checkins/batch',json={'events':[scan(code)]})
        assert r.status_code==200, r.text
        assert r.json()['invalid_count']==1 and r.json()['accepted_count']==0
        assert (await client.get('/api/v1/groups/'+code)).json()['status']=='cancelled'

@pytest.mark.asyncio
async def test_cannot_cancel_after_checkin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        data=await register(client);code=data['code']
        r=await client.post('/api/v1/checkins/batch',json={'events':[scan(code)]})
        assert r.status_code==200 and r.json()['accepted_count']==1, r.text
        r=await client.post(f'/api/v1/groups/{code}/cancel',json={'cancellation_token':data['cancellation_token']})
        assert r.status_code==409, r.text
        assert (await client.get('/api/v1/groups/'+code)).json()['status']!='cancelled'

@pytest.mark.asyncio
async def test_missing_key_old_pass_and_reason_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        assert (await client.post('/api/v1/groups/TEST01/cancel',json={'cancellation_token':'YK1:TEST01'})).status_code==403
        data=await register(client);url=f"/api/v1/groups/{data['code']}/cancel"
        assert (await client.post(url,json={})).status_code==422
        assert (await client.post(url,json={'cancellation_token':data['cancellation_token'],'reason':'x'*301})).status_code==422
