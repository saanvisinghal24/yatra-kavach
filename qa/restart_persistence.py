"""Real process restart check against disposable local SQLite. No secrets printed."""
import sys,os,time,subprocess,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from runtime import ROOT,VENV_PYTHON,load_environment
import httpx
from datetime import datetime,timezone
ENV=load_environment(); BASE='http://127.0.0.1:8002'
assert ENV['ENVIRONMENT']!='production'
def start():
 p=subprocess.Popen([str(VENV_PYTHON),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8002'],cwd=ROOT/'api',env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:
   if httpx.get(BASE+'/health',trust_env=False).status_code==200:return p
  except httpx.HTTPError:pass
  time.sleep(.1)
 p.terminate();raise RuntimeError('API failed to start')
def stop(p):p.terminate();p.wait(timeout=10)
def login(c):
 r=c.post('/auth/login',json={'email':ENV['STAFF_ADMIN_EMAIL'],'password':ENV['STAFF_ADMIN_PASSWORD']});r.raise_for_status()
p=start()
try:
 with httpx.Client(base_url=BASE+'/api/v1',headers={'Origin':ENV['PUBLIC_ORIGIN']},trust_env=False,timeout=20) as c:
  r=c.post('/groups',json={'consent':True,'yatra_id':1,'route_id':1,'leader_name':'Simulated restart leader','leader_phone':'0000000000','emergency_name':'Simulated contact','emergency_phone':'0000000000','size':2,'planned_start':datetime.now(timezone.utc).isoformat()});r.raise_for_status();g=r.json();code=g['code']
  login(c);posters=c.get('/ops/posters').json();qr=posters[0]['url']
  event={'id':str(uuid.uuid4()),'group_code':code,'checkpoint_id':1,'signed_qr':qr.split('token=')[-1],'headcount':2,'client_ts':datetime.now(timezone.utc).isoformat()}
  from urllib.parse import unquote
  event['signed_qr']=unquote(event['signed_qr'])
  r=c.post('/checkins/batch',json={'events':[event]});r.raise_for_status();assert r.json()['accepted_count']==1,r.text
  r=c.post('/sos',json={'group_code':code},headers={'Idempotency-Key':str(uuid.uuid4())});r.raise_for_status();incident=r.json()['incident_id']
  c.patch(f'/ops/incidents/{incident}',json={'status':'assigned','assigned_to':'Simulated rescue desk','notes':'Restart persisted private note'}).raise_for_status()
  r=c.post('/share/generate/'+code);r.raise_for_status();token=r.json()['token']
 stop(p);p=start()
 with httpx.Client(base_url=BASE+'/api/v1',headers={'Origin':ENV['PUBLIC_ORIGIN']},trust_env=False,timeout=20) as c:
  pilgrim=c.get('/groups/'+code);pilgrim.raise_for_status();d=pilgrim.json();assert d['last_checkpoint']['id']==1
  assert any(i['id']==incident for i in d['incidents'])
  assert all('notes' not in i and 'assigned_to' not in i for i in d['incidents'])
  family=c.get('/share/'+token);family.raise_for_status();assert family.json()['last_checkpoint']=='Hadsar';assert 'leader_phone' not in family.json()
  login(c);detail=c.get('/ops/groups/'+str(g['id']));detail.raise_for_status();detail=detail.json()
  assert any(i['id']==incident and i['notes']=='Restart persisted private note' for i in detail['incidents'])
  replay=c.post('/checkins/batch',json={'events':[event]});assert replay.json()['duplicate_count']==1
  print('PASS: actual API stop/start; registration, check-in, SOS, staff assignment/note, family view and replay idempotency persisted in SQLite. Not PostgreSQL evidence.')
finally:
 if p.poll() is None:stop(p)
