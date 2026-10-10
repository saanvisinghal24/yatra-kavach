#!/usr/bin/env python3
"""Two-phase deployed DB check. Run write, restart API, then read. Requires demo admin."""
import os,json,argparse,uuid
from pathlib import Path
from datetime import datetime,timezone
import httpx
p=argparse.ArgumentParser();p.add_argument('phase',choices=['write','read']);p.add_argument('--state',default='persistence-state.json');a=p.parse_args()
with httpx.Client(base_url=os.environ['PUBLIC_ORIGIN']+'/api/v1',timeout=30,trust_env=False) as c:
 r=c.post('/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']});r.raise_for_status()
 with c.stream('GET','/dashboard/stream') as stream:
  stream.raise_for_status()
  observed=set()
  for line in stream.iter_lines():
   if line.startswith('event:'):observed.add(line)
   if 'event: refresh' in observed:break
  assert 'event: connected' in observed
 if a.phase=='write':
  r=c.post('/ops/demo/scenario',json={'name':'head-count-drop'});r.raise_for_status();g=r.json()
  detail=c.get(f"/ops/groups/{g['id']}").json();flag=next(f for f in detail['flags'] if f['rule_id']=='R9')
  c.patch(f"/flags/{flag['id']}?action=ack").raise_for_status()
  r=c.post('/sos',json={'group_code':g['code']},headers={'Idempotency-Key':str(uuid.uuid4())});r.raise_for_status();inc=r.json()['incident_id']
  c.patch(f'/ops/incidents/{inc}',json={'status':'assigned','assigned_to':'Demo rescue desk','notes':'Restart persistence verification'}).raise_for_status()
  token=c.post('/share/generate/'+g['code']).json()['token']
  Path(a.state).write_text(json.dumps({**g,'token':token,'incident':inc}));Path(a.state).chmod(0o600)
  print('WRITE PASS. Restart API only; run read phase.')
 else:
  g=json.loads(Path(a.state).read_text());d=c.get(f"/ops/groups/{g['id']}");d.raise_for_status();d=d.json()
  assert d['checkins'] and any(f['rule_id']=='R9' and f['status']=='acked' for f in d['flags'])
  assert any(i['id']==g['incident'] and i['notes']=='Restart persistence verification' for i in d['incidents'])
  pilgrim=c.get('/groups/'+g['code']).json();assert any(i['assigned_to']=='Demo rescue desk' for i in pilgrim['incidents'])
  family=c.get('/share/'+g['token']).json();assert family['last_checkpoint']=='Dhancho' and 'leader_phone' not in family
  print('READ PASS. Check-in and staff assignment survived restart; pilgrim/family views reflect DB.')
