import os
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.qr_signer import make_checkpoint_qr_payload

@pytest.mark.asyncio
async def test_split_exit_and_delayed_outbound_never_complete_others():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test',headers={'Origin':'http://localhost:5173'}) as c:
        now=datetime.now(timezone.utc)
        g=(await c.post('/api/v1/groups',json={'consent':True,'yatra_id':1,'route_id':1,'leader_name':'Simulated split test','leader_phone':'0000000000','emergency_name':'Test','emergency_phone':'0000000000','size':2,'planned_start':now.isoformat()})).json()
        members=(await c.get('/api/v1/groups/'+g['code'])).json()['members']
        ids=[m['id'] for m in members]
        async def scan(direction,selected,minutes,source='self',cp=1):
            response=await c.post('/api/v1/checkins/batch',json={'events':[{'id':str(uuid4()),'group_code':g['code'],'checkpoint_id':cp,'signed_qr':make_checkpoint_qr_payload(cp,1),'headcount':len(selected),'member_ids':selected,'direction':direction,'source':source,'client_ts':(now-timedelta(minutes=minutes)).isoformat()}]})
            assert response.status_code==200,response.text
            assert response.json()['accepted_count']==1,response.text
        await scan('outbound',ids,60)
        await scan('exit',ids[:1],20)
        status=(await c.get('/api/v1/groups/'+g['code'])).json()
        assert status['status']=='split' and status['members'][0]['journey_state']=='exit_pending'
        await c.post('/api/v1/auth/login',json={'email':os.environ['STAFF_VOLUNTEER_EMAIL'],'password':os.environ['STAFF_VOLUNTEER_PASSWORD']})
        await scan('exit',ids[:1],10,'volunteer')
        await scan('outbound',ids[:1],1,cp=2)
        status=(await c.get('/api/v1/groups/'+g['code'])).json()
        assert status['status']=='split'
        assert status['members'][0]['journey_state']=='exited'
        assert status['members'][1]['journey_state']=='outbound'
        assert status['last_checkpoint']['direction']=='exit'
        await scan('exit',ids[1:],5,'volunteer')
        assert (await c.get('/api/v1/groups/'+g['code'])).json()['status']=='completed'
