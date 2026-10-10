import os
import pytest
from httpx import ASGITransport,AsyncClient
from app.main import app
from app.config import get_settings

@pytest.mark.asyncio
async def test_demo_scenarios_idempotent_and_reset():
 s=get_settings();old=s.DEMO_MODE;s.DEMO_MODE=True
 try:
  async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test', headers={'Origin':'http://localhost:5173'}) as c:
   await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']})
   for name,rule in [('fast-ascent','R1'),('overdue-group','R2'),('head-count-drop','R9'),('thunderstorm','R5'),('missing-group','R8')]:
    first=await c.post('/api/v1/ops/demo/scenario',json={'name':name});assert first.status_code==200,first.text
    second=await c.post('/api/v1/ops/demo/scenario',json={'name':name});assert second.json()['already_loaded']
    details=(await c.get(f"/api/v1/ops/groups/{first.json()['id']}")).json();assert any(f['rule_id']==rule for f in details['flags'])
   result=await c.post('/api/v1/ops/demo/reset');assert result.status_code==200 and result.json()['deleted_simulated_groups']>=5
   assert (await c.post('/api/v1/ops/demo/reset')).json()['deleted_simulated_groups']==0
 finally:s.DEMO_MODE=old

@pytest.mark.asyncio
async def test_new_demo_sos_delay_and_split_scenarios():
 s=get_settings();old=s.DEMO_MODE;s.DEMO_MODE=True
 try:
  async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test',headers={'Origin':s.PUBLIC_ORIGIN}) as c:
   await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']})
   for name in ['delayed-sync','sos','split-return']:
    result=await c.post('/api/v1/ops/demo/scenario',json={'name':name})
    assert result.status_code==200,result.text
    assert (await c.post('/api/v1/ops/demo/scenario',json={'name':name})).json()['already_loaded']
    group=(await c.get('/api/v1/groups/'+result.json()['code'])).json()
    if name=='split-return':
     assert group['status']=='split'
     assert sum(m['journey_state']=='exited' for m in group['members'])==2
    if name=='sos':
     assert len(group['incidents'])==1
    if name=='delayed-sync':
     from datetime import datetime
     cp=group['last_checkpoint']
     assert (datetime.fromisoformat(cp['server_received_at'])-datetime.fromisoformat(cp['checked_in_at'])).total_seconds()>=7200
   await c.post('/api/v1/ops/demo/reset')
 finally:s.DEMO_MODE=old
