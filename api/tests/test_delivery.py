import os
from datetime import datetime,timedelta,timezone
import pytest
from httpx import AsyncClient,ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_pilot_names_and_no_invented_facilities():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as c:
        yatras=(await c.get('/api/v1/yatras')).json()
        pilot=next(y for y in yatras if y['slug']=='manimahesh')
        cps=pilot['routes'][0]['checkpoints']
        assert [p['name_en'] for p in cps]==['Hadsar','Dhancho','Sundrasi','Gauri Kund','Manimahesh Lake']
        assert all(not cp['facilities'] for cp in cps)

@pytest.mark.asyncio
async def test_advisory_publication_withdraw_and_volunteer_boundary():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test',headers={'Origin':'http://localhost:5173'}) as c:
        now=datetime.now(timezone.utc)
        payload=dict(route_id=1,checkpoint_id=1,kind='staff_advisory',title='Simulated test',title_hi='काल्पनिक परीक्षण',body='Test only',body_hi='केवल परीक्षण',observed_at=now.isoformat(),expires_at=(now+timedelta(hours=1)).isoformat(),simulated=True)
        assert (await c.post('/api/v1/advisories',json=payload)).status_code==401
        await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_VOLUNTEER_EMAIL'],'password':os.environ['STAFF_VOLUNTEER_PASSWORD']})
        assert (await c.post('/api/v1/advisories',json=payload)).status_code==403
        observation=await c.post('/api/v1/advisories',json={**payload,'kind':'volunteer_observation'})
        assert observation.status_code==201,observation.text
        await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']})
        assert (await c.post('/api/v1/advisories',json={**payload,'kind':'official_advisory'})).status_code==422
        published=await c.post('/api/v1/advisories',json=payload)
        assert published.status_code==201,published.text
        item=published.json();assert 'author_id' not in item
        assert item['id'] in [a['id'] for a in (await c.get('/api/v1/advisories?route_id=1')).json()]
        assert (await c.post('/api/v1/advisories/'+str(item['id'])+'/withdraw')).status_code==200
        assert item['id'] not in [a['id'] for a in (await c.get('/api/v1/advisories?route_id=1')).json()]
        assert (await c.post('/api/v1/advisories',json={**payload,'expires_at':(now-timedelta(seconds=1)).isoformat()})).status_code==422

@pytest.mark.asyncio
async def test_cookie_mutation_rejects_missing_origin():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as c:
        login=await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']})
        assert login.status_code==200
        assert (await c.post('/api/v1/auth/logout')).status_code==403
        assert (await c.post('/api/v1/auth/logout',headers={'Origin':'http://localhost:5173'})).status_code==200
