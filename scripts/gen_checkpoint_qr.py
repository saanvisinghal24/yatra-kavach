#!/usr/bin/env python3
"""Generate A4 PNG/PDF posters from the deployed DB and environment secrets."""
import sys, asyncio, argparse, json, io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from runtime import load_environment
import os
os.environ.update(load_environment())
from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models.trail import Yatra
from app.models.group import Group
from app.services.qr_signer import make_checkpoint_qr_payload
from app.services.posters import poster,pdf_bytes

async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='qr');parser.add_argument('--route',default='manimahesh');parser.add_argument('--allow-local',action='store_true');args=parser.parse_args()
    settings=get_settings();origin=settings.PUBLIC_ORIGIN.rstrip('/')
    if not settings.QR_HMAC_SECRET or (not origin.startswith('https://') and not args.allow_local):raise SystemExit('Set PUBLIC_ORIGIN to your HTTPS domain and QR_HMAC_SECRET before printing.')
    dest=Path(args.output);dest.mkdir(parents=True,exist_ok=True);manifest=[]
    label='LOCAL DEMO — localhost only' if args.allow_local else 'SIMULATED DEMO'
    async with AsyncSessionLocal() as db:
        y=(await db.execute(select(Yatra).where(Yatra.slug==args.route).options(selectinload(Yatra.routes)))).scalar_one()
        from app.models.trail import Checkpoint
        cps=(await db.execute(select(Checkpoint).where(Checkpoint.route_id==y.routes[0].id).order_by(Checkpoint.seq))).scalars().all()
        for cp in cps:
            token=make_checkpoint_qr_payload(cp.id,cp.qr_key_version);url=origin+'/check-in?token='+token
            img=poster(cp.name_en,cp.name_hi,f'{label} · {cp.altitude_m} m · Indicative',url)
            base=dest/f'checkpoint-{cp.id}';buffer=io.BytesIO();img.save(buffer,format='PNG',dpi=(300,300));base.with_suffix('.png').write_bytes(buffer.getvalue());base.with_suffix('.pdf').write_bytes(pdf_bytes(img));manifest.append({'png':base.name+'.png','payload':url,'key_version':cp.qr_key_version})
        groups=(await db.execute(select(Group).where(Group.simulated==True).order_by(Group.id).limit(5))).scalars().all()
        for g in groups:
            token=f'{origin}/pass/{g.code}?token=YK1:{g.code}';img=poster('Demo group pass','डेमो दल पास',f'{label} · {g.code} · {g.size} people',token)
            base=dest/f'pass-{g.code}';buffer=io.BytesIO();img.save(buffer,format='PNG',dpi=(300,300));base.with_suffix('.png').write_bytes(buffer.getvalue());base.with_suffix('.pdf').write_bytes(pdf_bytes(img));manifest.append({'png':base.name+'.png','payload':token})
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Generated {len(cps)} checkpoint posters and {len(groups)} sample passes in {dest}')
if __name__=='__main__':asyncio.run(main())
