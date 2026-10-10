from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models.trail import Route, Checkpoint, Yatra
from app.models.group import Group, Member
from app.models.checkin import Checkin
from app.models.safety import RiskFlag, Incident
from app.schemas.group import GroupCreate, GroupRegisterResponse, GroupStatusResponse, ItineraryAdvisory
from app.services.code_gen import generate_group_code, make_pass_token
from app.rules.r10_itinerary import evaluate_r10_itinerary

router = APIRouter(prefix="/groups", tags=["Pilgrim Groups"])

@router.post("", response_model=GroupRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_group(payload: GroupCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new pilgrim group.
    Generates unambiguous 6-character code and evaluates R10 itinerary advisory.
    """
    # 1. Verify Route and Checkpoints
    route_stmt = (
        select(Route)
        .where(Route.id == payload.route_id)
        .options(selectinload(Route.checkpoints))
    )
    route_result = await db.execute(route_stmt)
    route = route_result.scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route ID {payload.route_id} does not exist."
        )

    yatra = await db.get(Yatra, route.yatra_id)
    if yatra.slug != 'manimahesh' or yatra.status != 'active':
        raise HTTPException(422, "Planned—route verification pending; registration unavailable")
    if len(payload.members) > payload.size:
        raise HTTPException(422, "Member details exceed declared group size")
    if payload.planned_return and payload.planned_return <= payload.planned_start:
        raise HTTPException(422, "Planned return must follow departure")
    if route.yatra_id != payload.yatra_id:
        raise HTTPException(422, "Route does not belong to selected yatra")
    if any(stop.checkpoint_id not in {cp.id for cp in route.checkpoints} for stop in payload.planned_stops):
        raise HTTPException(422, "Sleeping stop is not on this route")
    # 2. Evaluate R10 Itinerary Advisory
    checkpoints_by_id = {cp.id: cp for cp in route.checkpoints}
    advisories_data = []
    if payload.planned_stops:
        stops_dicts = [s.model_dump() for s in payload.planned_stops]
        advisories_data = evaluate_r10_itinerary(stops_dicts, checkpoints_by_id)

    # 3. Generate Unique Code
    for _ in range(10):
        candidate_code = generate_group_code(6)
        existing = await db.execute(select(Group).where(Group.code == candidate_code))
        if not existing.scalar_one_or_none():
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate unique group code. Please retry."
        )

    # 4. Create Group & Members
    new_group = Group(
        code=candidate_code,
        yatra_id=payload.yatra_id,
        route_id=payload.route_id,
        leader_name=payload.leader_name,
        leader_phone=payload.leader_phone,
        emergency_name=payload.emergency_name,
        emergency_phone=payload.emergency_phone,
        size=payload.size,
        planned_start=payload.planned_start,
        planned_return=payload.planned_return,
        status="planned",
        simulated=__import__("app.config", fromlist=["get_settings"]).get_settings().DEMO_MODE
    )
    db.add(new_group)
    await db.flush()

    for m in payload.members:
        member = Member(
            group_id=new_group.id,
            name=m.name,
            age_band=m.age_band,
            note=m.note
        )
        db.add(member)

    # Stable anonymous member slots preserve accounting without collecting excess PII.
    for index in range(len(payload.members), payload.size):
        db.add(Member(group_id=new_group.id, name=f"Member {index + 1}", age_band="unknown"))

    # Store any R10 advisory as an initial info risk_flag
    for adv in advisories_data:
        flag = RiskFlag(
            group_id=new_group.id,
            checkpoint_id=adv["details"].get("to_checkpoint_id"),
            rule_id="R10",
            severity="info",
            message_en=adv["message_en"],
            message_hi=adv["message_hi"],
            data=adv["details"],
            status="open"
        )
        db.add(flag)

    await db.commit()
    await db.refresh(new_group)

    return GroupRegisterResponse(
        id=new_group.id,
        code=new_group.code,
        pass_token=make_pass_token(new_group.code),
        yatra_id=new_group.yatra_id,
        route_id=new_group.route_id,
        leader_name=new_group.leader_name,
        size=new_group.size,
        status=new_group.status,
        advisories=[ItineraryAdvisory(**a) for a in advisories_data]
    )

@router.get("/{code}", response_model=GroupStatusResponse)
async def get_group_status(code: str, db: AsyncSession = Depends(get_db)):
    """Retrieve pilgrim group status, next checkpoint, and any active advice."""
    stmt = (
        select(Group)
        .where(Group.code == code)
        .options(
            selectinload(Group.checkins),
            selectinload(Group.flags), selectinload(Group.members)
        )
    )
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with code '{code}' not found."
        )

    # Get checkpoints for this route
    cp_stmt = select(Checkpoint).where(Checkpoint.route_id == group.route_id).order_by(Checkpoint.seq)
    cp_result = await db.execute(cp_stmt)
    checkpoints = cp_result.scalars().all()
    checkpoints_by_id = {cp.id: cp for cp in checkpoints}

    # Determine last checkpoint and next checkpoint
    last_cp_dict = None
    next_cp_dict = None
    eta_range = None

    valid_checkins = [c for c in group.checkins if c.valid and c.state_applied]
    if valid_checkins:
        valid_checkins.sort(key=lambda c: c.client_ts)
        last_checkin = valid_checkins[-1]
        last_cp = checkpoints_by_id.get(last_checkin.checkpoint_id)
        if last_cp:
            last_cp_dict = {
                "id": last_cp.id,
                "name_en": last_cp.name_en,
                "name_hi": last_cp.name_hi,
                "altitude_m": last_cp.altitude_m,
                "checked_in_at": last_checkin.client_ts.isoformat(),
                "headcount": last_checkin.headcount,
                "server_received_at": last_checkin.server_ts.isoformat(),
                "source": last_checkin.source, "direction": last_checkin.direction
            }
            # Find next checkpoint in sequence
            next_cps = ([cp for cp in reversed(checkpoints) if cp.seq < last_cp.seq] if last_checkin.direction == "returning" else [cp for cp in checkpoints if cp.seq > last_cp.seq])
            if group.status == "completed" or last_checkin.direction == "exit": next_cps = []
            if next_cps:
                next_cp = next_cps[0]
                next_cp_dict = {
                    "id": next_cp.id,
                    "seq": next_cp.seq,
                    "name_en": next_cp.name_en,
                    "name_hi": next_cp.name_hi,
                    "altitude_m": next_cp.altitude_m,
                    "dist_from_prev_km": next_cp.dist_from_prev_km,
                    "status": next_cp.status,
                    "cutoff_time": next_cp.cutoff_time
                }
                from app.rules.engine import calculate_median_eta
                scans=(await db.execute(select(Checkin).where(Checkin.valid==True,Checkin.checkpoint_id.in_([last_cp.id,next_cp.id])).order_by(Checkin.client_ts))).scalars().all()
                starts={};durations=[]
                for scan in scans:
                    if scan.checkpoint_id==last_cp.id: starts[scan.group_id]=scan.client_ts
                    elif scan.group_id in starts:
                        duration=(scan.client_ts-starts[scan.group_id]).total_seconds()/60
                        if duration>0:durations.append(duration)
                low,high=calculate_median_eta(last_cp.id,next_cp.id,durations,next_cp.min_minutes,next_cp.max_minutes)
                eta_range=f"{low} min – {high} min"
    else:
        # Not yet checked in: next is checkpoint 1
        if checkpoints:
            first_cp = checkpoints[0]
            next_cp_dict = {
                "id": first_cp.id,
                "seq": first_cp.seq,
                "name_en": first_cp.name_en,
                "name_hi": first_cp.name_hi,
                "altitude_m": first_cp.altitude_m,
                "cutoff_time": first_cp.cutoff_time
            }
            eta_range = "Trailhead Start"

    open_advice = [
        {
            "rule_id": f.rule_id,
            "severity": f.severity,
            "message_en": f.message_en,
            "message_hi": f.message_hi,
            "status": f.status,
            "created_at": f.created_at.isoformat()
        }
        for f in group.flags if f.status in ("open", "acked")
    ]

    return GroupStatusResponse(
        id=group.id,
        code=group.code,
        leader_name=group.leader_name,
        size=group.size,
        status=group.status,
        started_at=group.started_at,
        last_checkpoint=last_cp_dict,
        next_checkpoint=next_cp_dict,
        eta_range=eta_range,
        checkpoint_statuses=[{"id":cp.id,"name_en":cp.name_en,"name_hi":cp.name_hi,"status":cp.status,"facilities":cp.facilities} for cp in checkpoints],
        planned_return=group.planned_return,
        members=[{"id":m.id,"name":m.name,"age_band":m.age_band,"journey_state":m.journey_state,"last_checkpoint_id":m.last_checkpoint_id,"last_visit_at":m.last_visit_at.isoformat() if m.last_visit_at else None,"confirmation_source":m.confirmation_source} for m in group.members],
        journey_counts={state:sum(m.journey_state==state for m in group.members) for state in ('planned','outbound','returning','exit_pending','exited')},
        incidents=[{"id":i.id,"status":i.status,"type":i.type} for i in (await db.execute(select(Incident).where(Incident.group_id==group.id))).scalars()],
        open_advice=open_advice
    )
