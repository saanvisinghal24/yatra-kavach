#!/usr/bin/env python3
"""Load reproducible, idempotent Demo mode scenarios through the real API."""
import argparse,os
import httpx
p=argparse.ArgumentParser();p.add_argument('--url',default=os.environ.get('PUBLIC_ORIGIN'));p.add_argument('--reset',action='store_true');args=p.parse_args()
if not args.url:raise SystemExit('Set PUBLIC_ORIGIN or --url')
with httpx.Client(base_url=args.url.rstrip('/')+'/api/v1',timeout=30,trust_env=False) as client:
    r=client.post('/auth/login',json={'email':os.environ['STAFF_ADMIN_EMAIL'],'password':os.environ['STAFF_ADMIN_PASSWORD']});r.raise_for_status()
    if args.reset:client.post('/ops/demo/reset').raise_for_status()
    for name in ['fast-ascent','overdue-group','head-count-drop','thunderstorm','missing-group']:
        r=client.post('/ops/demo/scenario',json={'name':name});r.raise_for_status()
        print('Demo mode:',name,r.json()['code'])
