from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from astral import Observer
from astral.sun import sun
from app.models.group import Group
from app.models.trail import Checkpoint, Route
from app.models.safety import RiskFlag
from app.rules.engine import *
from app.services.sweep import upsert_risk_flag
from app.services.weather import get_checkpoint_weather

IST = ZoneInfo('Asia/Kolkata')
def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
def cp_data(cp):
    return {c.name: getattr(cp,c.name) for c in cp.__table__.columns}
def scan_data(scan, cp):
    return {'client_ts': utc(scan.client_ts), 'checkpoint_id': cp.id, 'checkpoint_name': cp.name_en}

async def evaluate_all(db, weather=False):
    now = datetime.now(timezone.utc)
    groups = (await db.execute(select(Group).options(selectinload(Group.checkins)).where(Group.status.in_(['active','flagged','returning','split'])))).scalars().all()
    cps = (await db.execute(select(Checkpoint).order_by(Checkpoint.seq))).scalars().all()
    routes = {r.id:r for r in (await db.execute(select(Route))).scalars()}
    by_id = {c.id:c for c in cps}
    occupants = {}
    latest = {}
    for g in groups:
        scans = sorted([s for s in g.checkins if s.valid and (s.state_applied or not s.member_ids)], key=lambda s: utc(s.client_ts))
        if scans:
            latest[g.id] = scans
            occupants[scans[-1].checkpoint_id] = occupants.get(scans[-1].checkpoint_id,0) + scans[-1].headcount
    for g in groups:
        scans = latest.get(g.id)
        if not scans: continue
        last = scans[-1]; cp = by_id[last.checkpoint_id]; cur = cp_data(cp)
        if g.status == 'split':
            # Group-wide travel-time assumptions are invalid for separated members.
            # Member states and full audit remain visible for human reconciliation.
            continue
        if last.direction == 'exit': continue
        nxt = next((c for c in (list(reversed(cps)) if last.direction == 'returning' else cps) if c.route_id == g.route_id and (c.seq < cp.seq if last.direction == 'returning' else c.seq > cp.seq)), None)
        flags = []
        if routes[g.route_id].type == 'trek' and last.direction == 'outbound':
            if len(scans)>1 and by_id[scans[-2].checkpoint_id].seq == cp.seq-1:
                flags.append(evaluate_r1_fast_ascent(scan_data(last,cp), scan_data(scans[-2],by_id[scans[-2].checkpoint_id]),cur))
            local_scan = {**scan_data(last,cp),'client_ts':utc(last.client_ts).astimezone(IST)}
            flags.append(evaluate_r3_cutoff(local_scan,cur,cp_data(nxt) if nxt else None,now.astimezone(IST)))
            if nxt:
                nd = cp_data(nxt)
                flags.extend([evaluate_r2_slow_overdue(scan_data(last,cp),nd,now),evaluate_r8_missing(scan_data(last,cp),nd,now)])
                solar = sun(Observer(cp.lat,cp.lon),date=now.astimezone(IST).date(),tzinfo=IST)
                flags.append(evaluate_r4_night_on_trail(local_scan,nd,now.astimezone(IST),solar['sunset'].time()))
                if weather:
                    forecast = await get_checkpoint_weather(nxt.id,nxt.lat,nxt.lon,nxt.name_en)
                    w = forecast.get('r5_flag')
                    if w: flags.append(RuleFlag(**w,checkpoint_id=nxt.id))
        if nxt and cp.capacity_hint and occupants[cp.id]>cp.capacity_hint:
            flags.append(RuleFlag('R6','watch',f'Segment after {cp.name_en}: {occupants[cp.id]} people; indicative capacity {cp.capacity_hint}. Hold at checkpoint.',f'{cp.name_hi} के बाद {occupants[cp.id]} यात्री; क्षमता {cp.capacity_hint}। चौकी पर रुकें।',cp.id,{'people':occupants[cp.id],'capacity':cp.capacity_hint}))
        previous = scans[-2].headcount if len(scans)>1 else g.size
        prior = (await db.execute(select(RiskFlag).where(RiskFlag.group_id==g.id,RiskFlag.rule_id=='R9',RiskFlag.status.in_(['open','acked'])))).scalars().first()
        if prior: previous = max(previous,prior.data.get('previous_headcount',previous))
        duration = (now-utc(prior.created_at)).total_seconds()/60 if prior else 0
        flags.append(evaluate_r9_headcount_drop(last.headcount,previous,duration,cp.id))
        for flag in flags:
            if flag:
                resolved=(await db.execute(select(RiskFlag).where(RiskFlag.group_id==g.id,RiskFlag.rule_id==flag.rule_id,RiskFlag.status=='resolved').order_by(RiskFlag.resolved_at.desc()))).scalars().first()
                if resolved and resolved.resolved_at and utc(resolved.resolved_at)>=utc(last.server_ts):continue
                await upsert_risk_flag(db,g.id,flag)
    await db.commit()
