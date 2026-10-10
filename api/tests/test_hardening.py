import os
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import Settings
from app.services.qr_signer import make_checkpoint_qr_payload
from app.db import AsyncSessionLocal
from app.models.safety import Incident

@pytest.mark.asyncio
async def test_persistence_both_directions_and_event_replay():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test', headers={'Origin':'http://localhost:5173'}) as c:
        assert (await c.get('/api/v1/dashboard/groups')).status_code==401
        reg=await c.post('/api/v1/groups',json={'consent': True, 'yatra_id':1,'route_id':1,'leader_name':'Demo persistence','leader_phone':'0000000000','emergency_name':'Demo contact','emergency_phone':'0000000000','size':3,'planned_start':datetime.now(timezone.utc).isoformat()})
        assert reg.status_code==201
        group=reg.json(); code=group['code']
        token=(await c.post('/api/v1/share/generate/'+code)).json()['token']
        now=datetime.now(timezone.utc)
        members=(await c.get('/api/v1/groups/'+code)).json()['members']
        events=[{'id':str(uuid4()),'group_code':code,'checkpoint_id':cp,'signed_qr':make_checkpoint_qr_payload(cp,1),'headcount':count,'member_ids':[m['id'] for m in members[:count]],'client_ts':(now-timedelta(minutes=minutes)).isoformat()} for cp,count,minutes in [(1,3,30),(2,2,1)]]
        first=await c.post('/api/v1/checkins/batch',json={'events':events});assert first.json()['accepted_count']==2,first.text
        again=await c.post('/api/v1/checkins/batch',json={'events':events});assert again.json()['duplicate_count']==2
        share=(await c.get('/api/v1/share/'+token)).json();assert share['last_checkpoint']=='Dhancho';assert 'leader_phone' not in share
        key=str(uuid4());body={'group_code':code,'headache':3,'stomach':3,'fatigue':3,'dizziness':3,'red_flags':[]}
        a=await c.post('/api/v1/symptom-reports',json=body,headers={'Idempotency-Key':key});b=await c.post('/api/v1/symptom-reports',json=body,headers={'Idempotency-Key':key});assert a.json()==b.json()
        key=str(uuid4());a=await c.post('/api/v1/sos',json={'group_code':code},headers={'Idempotency-Key':key});b=await c.post('/api/v1/sos',json={'group_code':code},headers={'Idempotency-Key':key});assert a.json()==b.json()
        assert (await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']})).status_code==200
        detail=(await c.get(f"/api/v1/ops/groups/{group['id']}")).json();assert len(detail['checkins'])==2 and len(detail['health'])==1 and len(detail['incidents'])==1
        assert {'R1','R9','R7','SOS'}.issubset({f['rule_id'] for f in detail['flags']})
        inc=detail['incidents'][0]
        assert (await c.patch(f"/api/v1/ops/incidents/{inc['id']}",json={'status':'assigned','assigned_to':'Rescue desk','notes':'Demo search team allocated'})).status_code==200
        assert (await c.patch('/api/v1/ops/checkpoints/2',json={'status':'closed','oxygen':True})).status_code==200
        flag=next(f for f in detail['flags'] if f['rule_id']=='R9')
        assert (await c.patch(f"/api/v1/flags/{flag['id']}?action=ack")).status_code==200
        status=(await c.get('/api/v1/groups/'+code)).json()
        assert 'assigned_to' not in status['incidents'][0]
        detail=(await c.get(f"/api/v1/ops/groups/{group['id']}")).json()
        assert detail['incidents'][0]['assigned_to']=='Rescue desk'
        assert any(cp['id']==2 and cp['status']=='closed' for cp in status['checkpoint_statuses'])
        assert any(f['rule_id']=='R9' and f['status']=='acked' for f in status['open_advice'])
        async with AsyncSessionLocal() as db:
            saved=await db.get(Incident,inc['id']);assert saved.notes=='Demo search team allocated'
        assert (await c.get('/api/v1/ops/analytics')).json()['peak_hours']
        assert (await c.get('/api/v1/ops/analytics.csv')).status_code==200
        assert (await c.get('/api/v1/ops/posters')).status_code==200

def test_production_rejects_default_secrets():
    with pytest.raises(ValueError):Settings(ENVIRONMENT='production',SECRET_KEY='default',JWT_SECRET='short',QR_HMAC_SECRET='short')

@pytest.mark.asyncio
async def test_unauthenticated_volunteer_rejected():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test', headers={'Origin':'http://localhost:5173'}) as c:
        r=await c.post('/api/v1/checkins/batch',json={'events':[{'id':str(uuid4()),'group_code':'TEST01','checkpoint_id':1,'signed_qr':make_checkpoint_qr_payload(1,1),'headcount':2,'client_ts':datetime.now(timezone.utc).isoformat(),'source':'volunteer'}]})
        assert r.status_code==401

@pytest.mark.asyncio
async def test_retention_deletes_linked_personal_records():
    from app.services.worker import retention
    from app.models.group import Group
    from app.models.trail import Yatra
    from app.models.safety import ShareToken
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        y=await db.get(Yatra,1);previous=y.season_end;y.season_end=(datetime.now(timezone.utc)-timedelta(days=60)).date()
        g=Group(code='OLD234',yatra_id=1,route_id=1,leader_name='Expired demo',leader_phone='0000000000',emergency_name='Expired contact',emergency_phone='0000000000',size=1,planned_start=datetime.now(timezone.utc)-timedelta(days=60),created_at=datetime.now(timezone.utc)-timedelta(days=60),status='completed')
        db.add(g);await db.flush();id=g.id
        db.add(ShareToken(group_id=id,token=uuid4().hex,expires_at=datetime.now(timezone.utc)))
        await db.commit();await retention(db)
        assert (await db.execute(select(Group).where(Group.id==id))).scalar_one_or_none() is None
        assert not (await db.execute(select(ShareToken).where(ShareToken.group_id==id))).scalars().all()
        y.season_end=previous;await db.commit()

@pytest.mark.asyncio
async def test_rate_limit_and_secure_headers():
    from app.config import get_settings
    from sqlalchemy import text
    settings=get_settings();old=settings.ENVIRONMENT
    async with AsyncSessionLocal() as db:
        await db.execute(text('CREATE TABLE IF NOT EXISTS rate_bucket (key VARCHAR(64), bucket BIGINT, count INTEGER NOT NULL, PRIMARY KEY (key,bucket))'))
        await db.execute(text('DELETE FROM rate_bucket'));await db.commit()
    settings.ENVIRONMENT='production'
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url='https://test') as c:
            for _ in range(10):
                response=await c.post('/api/v1/auth/login',json={'email':'invalid@test.invalid','password':'invalid'})
                assert response.status_code==401
            assert (await c.post('/api/v1/auth/login',json={'email':'invalid@test.invalid','password':'invalid'})).status_code==429
            response=await c.get('/health');assert response.headers['strict-transport-security'].startswith('max-age=')
            assert response.headers['x-content-type-options']=='nosniff'
            denied=await c.post('/api/v1/groups',headers={'Origin':'https://untrusted.invalid'},json={});assert denied.status_code==403
    finally:settings.ENVIRONMENT=old
