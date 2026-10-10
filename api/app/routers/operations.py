import csv
import io
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from statistics import median
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.config import get_settings
from app.models.group import Group
from app.models.trail import Checkpoint, Yatra
from app.models.checkin import Checkin
from app.models.safety import Incident, RiskFlag, SymptomReport
from app.services.auth import get_current_user, require_control_user, enforce_route
from app.services.qr_signer import make_checkpoint_qr_payload as sign_checkpoint_qr
from app.services.pipeline import utc, IST, evaluate_all
from app.services.worker import delete_groups

router = APIRouter(prefix='/ops', dependencies=[Depends(get_current_user)])
public = APIRouter()

@public.get('/config')
async def config():
    s=get_settings()
    root=Path(__file__).parents[1]
    facts=json.loads((root/'facts.yaml').read_text())
    return {'demo_mode':s.DEMO_MODE,'contact_email':s.CONTACT_EMAIL,'reviewed_by':s.REVIEWED_BY,'threshold_review':'Pending clinical and rescue review',
            'sms_number':s.SOS_FALLBACK_SMS_NUMBER,'rules':json.loads((root/'rules/rules.yaml').read_text()),
            'facts':[f for f in facts if f.get('value') is not None and all(f.get(k) for k in ('source','url','year'))]}

class CheckpointUpdate(BaseModel):
    status: Literal['open','congested','closed']
    medical: bool | None = None
    oxygen: bool | None = None

@router.patch('/checkpoints/{id}')
async def checkpoint_update(id:int, payload:CheckpointUpdate, db:AsyncSession=Depends(get_db), user=Depends(get_current_user)):
    if user.role not in ('admin','volunteer','rescue'): raise HTTPException(403,'Operational checkpoint role required')
    cp=await db.get(Checkpoint,id)
    if not cp: raise HTTPException(404,'Checkpoint not found')
    if user.route_scope and cp.route_id!=user.route_scope: raise HTTPException(403,'Outside route scope')
    cp.status=payload.status
    cp.facilities={**cp.facilities,**{k:v for k,v in payload.model_dump(exclude={'status'}).items() if v is not None}}
    await db.commit()
    return {'id':id,'status':cp.status,'facilities':cp.facilities}

class IncidentUpdate(BaseModel):
    status: Literal['open','assigned','resolved']
    assigned_to: str | None = Field(None,max_length=128)
    notes: str = Field('',max_length=4000)

@router.patch('/incidents/{id}', dependencies=[Depends(require_control_user)])
async def incident_update(id:int,payload:IncidentUpdate,db:AsyncSession=Depends(get_db),user=Depends(require_control_user)):
    inc=await db.get(Incident,id)
    if not inc: raise HTTPException(404,'Incident not found')
    enforce_route(user,(await db.get(Group,inc.group_id)).route_id)
    inc.status=payload.status; inc.assigned_to=payload.assigned_to; inc.notes=payload.notes
    inc.resolved_at=datetime.now(timezone.utc) if payload.status=='resolved' else None
    await db.commit()
    return {'id':id,'status':inc.status}

@router.get('/groups/{id}', dependencies=[Depends(require_control_user)])
async def group_detail(id:int,db:AsyncSession=Depends(get_db),user=Depends(require_control_user)):
    group=await db.get(Group,id)
    if not group: raise HTTPException(404,'Group not found')
    enforce_route(user,group.route_id)
    def fields(obj): return {c.name:getattr(obj,c.name) for c in obj.__table__.columns}
    result={'group':fields(group)}
    for name,model in [('checkins',Checkin),('flags',RiskFlag),('incidents',Incident),('health',SymptomReport)]:
        result[name]=[fields(v) for v in (await db.execute(select(model).where(model.group_id==id))).scalars()]
    return result

@router.get('/posters')
async def posters(db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    if user.role!='admin':raise HTTPException(403,'Admin required')
    origin=get_settings().PUBLIC_ORIGIN
    query=select(Checkpoint).order_by(Checkpoint.route_id,Checkpoint.seq)
    if user.route_scope is not None: query=query.where(Checkpoint.route_id==user.route_scope)
    return [{'id':c.id,'name':c.name_en,'name_hi':c.name_hi,'altitude':c.altitude_m,'token':sign_checkpoint_qr(c.id,c.qr_key_version),'url':origin+'/check-in?token='+sign_checkpoint_qr(c.id,c.qr_key_version)} for c in (await db.execute(query)).scalars()]

@router.get('/analytics', dependencies=[Depends(require_control_user)])
async def analytics(db:AsyncSession=Depends(get_db),user=Depends(require_control_user)):
    scan_query=select(Checkin).join(Group).where(Checkin.valid==True)
    if user.route_scope: scan_query=scan_query.where(Group.route_id==user.route_scope)
    scans=(await db.execute(scan_query.order_by(Checkin.client_ts))).scalars().all()
    flag_query=select(RiskFlag).join(Group)
    if user.route_scope: flag_query=flag_query.where(Group.route_id==user.route_scope)
    flags=(await db.execute(flag_query)).scalars().all()
    cps={c.id:c for c in (await db.execute(select(Checkpoint))).scalars()}
    hours=Counter(); segments=defaultdict(list); last={}; occupancy=Counter()
    for c in scans:
        hours[utc(c.client_ts).astimezone(IST).hour]+=1
        prev=last.get(c.group_id)
        if prev and cps[c.checkpoint_id].route_id==cps[prev.checkpoint_id].route_id and cps[c.checkpoint_id].seq==cps[prev.checkpoint_id].seq+1:
            segments[(prev.checkpoint_id,c.checkpoint_id)].append((utc(c.client_ts)-utc(prev.client_ts)).total_seconds()/60)
        last[c.group_id]=c
    for c in last.values():occupancy[c.checkpoint_id]+=c.headcount
    return {'peak_hours':[{'hour_ist':k,'checkins':v} for k,v in sorted(hours.items())],
        'segments':sorted([{'from':cps[a].name_en,'to':cps[b].name_en,'median_minutes':round(median(v),1),'samples':len(v)} for (a,b),v in segments.items()],key=lambda s:-s['median_minutes']),
        'alerts':[{'rule':r,'count':len(v),'resolved':sum(f.resolved_at is not None for f in v),'median_resolution_minutes':median([(utc(f.resolved_at)-utc(f.created_at)).total_seconds()/60 for f in v if f.resolved_at]) if any(f.resolved_at for f in v) else None} for r in sorted({f.rule_id for f in flags}) for v in [[f for f in flags if f.rule_id==r]]],
        'congestion':[{'after':cps[k].name_en,'people':v,'capacity':cps[k].capacity_hint} for k,v in occupancy.items()]}

@router.get('/analytics.csv', dependencies=[Depends(require_control_user)])
async def analytics_csv(db:AsyncSession=Depends(get_db),user=Depends(require_control_user)):
    data=await analytics(db,user);out=io.StringIO();w=csv.writer(out);w.writerow(['section','metric','values'])
    for name,rows in data.items():
        for row in rows:w.writerow([name, next(iter(row.values())),json.dumps(row)])
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=analytics.csv'})

class Scenario(BaseModel):
    name: Literal['fast-ascent','overdue-group','head-count-drop','thunderstorm','missing-group','delayed-sync','sos','split-return']

async def require_demo(user):
    if user.role!='admin' or not get_settings().DEMO_MODE:raise HTTPException(403,'Demo mode admin required')

@router.post('/demo/reset')
async def reset(db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    await require_demo(user)
    query=select(Group.id).where(Group.simulated==True)
    if user.route_scope is not None: query=query.where(Group.route_id==user.route_scope)
    ids=(await db.execute(query)).scalars().all()
    await delete_groups(db,ids);await db.commit()
    from app.seed.seed_trails import seed_data
    await seed_data()
    return {'deleted_simulated_groups':len(ids)}

@router.post('/demo/scenario')
async def scenario(payload:Scenario,db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    await require_demo(user)
    from uuid import uuid4
    codes={'fast-ascent':'DEMA22','overdue-group':'DEMB22','head-count-drop':'DEMC22','thunderstorm':'DEMD22','missing-group':'DEME22','delayed-sync':'DEMF22','sos':'DEMG22','split-return':'DEMH22'}
    code=codes[payload.name]
    old=(await db.execute(select(Group).where(Group.code==code))).scalar_one_or_none()
    if old:
        enforce_route(user, old.route_id)
        return {'code':old.code,'id':old.id,'already_loaded':True}
    y=(await db.execute(select(Yatra).where(Yatra.slug=='manimahesh').options(selectinload(Yatra.routes)))).scalar_one()
    route=y.routes[0]; cps=(await db.execute(select(Checkpoint).where(Checkpoint.route_id==route.id).order_by(Checkpoint.seq))).scalars().all()
    enforce_route(user, route.id)
    now=datetime.now(timezone.utc)
    g=Group(code=code,yatra_id=y.id,route_id=route.id,leader_name='Demo · '+payload.name,leader_phone='0000000000',emergency_name='Demo contact',emergency_phone='0000000000',size=5,planned_start=now,started_at=now,status='active',simulated=True)
    db.add(g);await db.flush()
    age={'fast-ascent':40,'overdue-group':220,'head-count-drop':180,'thunderstorm':30,'missing-group':440,'delayed-sync':120,'sos':30,'split-return':90}[payload.name]
    db.add(Checkin(id=str(uuid4()),group_id=g.id,checkpoint_id=cps[0].id,source='self',headcount=5,client_ts=now-timedelta(minutes=age),server_ts=now,clock_skew_s=0,valid=True))
    if payload.name in ('fast-ascent','head-count-drop'):
        db.add(Checkin(id=str(uuid4()),group_id=g.id,checkpoint_id=cps[1].id,source='self',headcount=3 if payload.name=='head-count-drop' else 5,client_ts=now-timedelta(minutes=5),server_ts=now,clock_skew_s=0,valid=True))
    if payload.name=='thunderstorm':
        from app.services.weather import evaluate_r5_weather
        f=evaluate_r5_weather({'weather_codes':[95]},cps[1].name_en)
        db.add(RiskFlag(group_id=g.id,checkpoint_id=cps[1].id,**f,status='open'))
    from app.services.journey import members_for, apply_event
    members = await members_for(db, g)
    await db.flush()
    for event in (await db.execute(select(Checkin).where(Checkin.group_id == g.id).order_by(Checkin.client_ts))).scalars():
        event.member_ids = [m.id for m in members[:event.headcount]]
        event.direction = 'outbound'
        await apply_event(db, g, event, members)
    if payload.name == 'split-return':
        for direction, cp, mins in [('returning', cps[1], 10), ('exit', cps[0], 2)]:
            event = Checkin(id=str(uuid4()), group_id=g.id, checkpoint_id=cp.id, source='volunteer', volunteer_id=user.id,
                headcount=2, member_ids=[m.id for m in members[:2]], direction=direction,
                client_ts=now-timedelta(minutes=mins), server_ts=now, clock_skew_s=0, valid=True)
            db.add(event)
            await apply_event(db, g, event, members)
    if payload.name == 'sos':
        flag = RiskFlag(group_id=g.id, checkpoint_id=cps[0].id, rule_id='SOS', severity='urgent',
            message_en='SIMULATED SOS: assistance requested. Dispatch not confirmed.',
            message_hi='अनुकरण एसओएस: सहायता का अनुरोध। सहायता भेजने की पुष्टि नहीं।', data={'simulated': True}, status='open')
        db.add(flag); await db.flush()
        db.add(Incident(group_id=g.id, flag_id=flag.id, type='emergency_sos', status='open', notes='SIMULATED demo SOS; no real call or dispatch.'))
    await db.commit();await evaluate_all(db)
    if payload.name=='missing-group':
        f=(await db.execute(select(RiskFlag).where(RiskFlag.group_id==g.id,RiskFlag.rule_id=='R8'))).scalar_one()
        db.add(Incident(group_id=g.id,flag_id=f.id,type='reporting_delay',status='open',notes='Demo mode: search window is in R8 evidence.'))
        await db.commit()
    return {'code':g.code,'id':g.id,'already_loaded':False}

class NewIncident(BaseModel):
    group_id:int
    type:str=Field('assistance',max_length=64)
    notes:str=Field('',max_length=4000)

@router.post('/incidents',dependencies=[Depends(require_control_user)])
async def create_incident(payload:NewIncident,db:AsyncSession=Depends(get_db),user=Depends(require_control_user)):
    if not await db.get(Group,payload.group_id):raise HTTPException(404,'Group not found')
    enforce_route(user,(await db.get(Group,payload.group_id)).route_id)
    inc=Incident(group_id=payload.group_id,type=payload.type,status='open',notes=payload.notes)
    db.add(inc);await db.commit()
    return {'id':inc.id,'status':inc.status}
