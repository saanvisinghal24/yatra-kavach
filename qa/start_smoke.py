"""Launch exact PWA command and inspect endpoints in the same process lifetime."""
import os,signal,subprocess,time,sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
log=ROOT/'qa/start-smoke.log'
with log.open('w') as output:
 p=subprocess.Popen([sys.executable,'scripts/start.py','--preview'],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  with httpx.Client(trust_env=False,timeout=2) as c:
   urls=['http://127.0.0.1:8000/health','http://127.0.0.1:5173/','http://127.0.0.1:5173/sw.js','http://127.0.0.1:5173/api/v1/yatras','http://127.0.0.1:5173/api/v1/advisories?route_id=1']
   for i in range(120):
    if p.poll() is not None:raise RuntimeError('Launcher exited; inspect local start-smoke.log')
    try:
     results=[c.get(url) for url in urls]
     if all(r.status_code==200 for r in results):break
    except httpx.HTTPError:pass
    time.sleep(.25)
   else:raise RuntimeError('Endpoints did not become ready')
   for url,r in zip(urls,results):print(url,r.status_code)
 finally:
  os.killpg(p.pid,signal.SIGINT)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM)
