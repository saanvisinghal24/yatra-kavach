import asyncio
import io
import csv
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models.group import Group
from app.models.trail import Checkpoint, Route
from app.models.checkin import Checkin
from app.models.safety import RiskFlag, Incident
from app.models.user import User
from app.services.auth import get_current_user, require_control_user, enforce_route
from app.services.sse import sse_hub

router = APIRouter(tags=["Control Room Operations"], dependencies=[Depends(require_control_user)])

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    route: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """KPI summary strip for control room overview."""
    if route: enforce_route(scoped_user, route)
    route = scoped_user.route_scope or route
    query = select(Group).where(Group.status.in_(["active", "flagged", "returning", "split"]))
    if route:
        query = query.where(Group.route_id == route)
    groups = (await db.execute(query)).scalars().all()

    active_groups_count = len(groups)
    total_pilgrims = sum(g.size for g in groups)

    # Count urgent flags
    flag_stmt = select(func.count(RiskFlag.id)).where(RiskFlag.status == "open", RiskFlag.severity == "urgent")
    if route: flag_stmt = flag_stmt.join(Group).where(Group.route_id == route)
    urgent_flags_count = (await db.execute(flag_stmt)).scalar() or 0

    # Count watch flags
    watch_stmt = select(func.count(RiskFlag.id)).where(RiskFlag.status == "open", RiskFlag.severity == "watch")
    if route: watch_stmt = watch_stmt.join(Group).where(Group.route_id == route)
    watch_flags_count = (await db.execute(watch_stmt)).scalar() or 0

    # Overdue count (flags with rule R2 or R8)
    overdue_stmt = select(func.count(RiskFlag.id)).where(
        RiskFlag.status == "open",
        RiskFlag.rule_id.in_(["R2", "R8"])
    )
    if route: overdue_stmt = overdue_stmt.join(Group).where(Group.route_id == route)
    overdue_count = (await db.execute(overdue_stmt)).scalar() or 0

    return {
        "active_groups": active_groups_count,
        "total_pilgrims_on_trail": total_pilgrims,
        "urgent_alerts": urgent_flags_count,
        "watch_alerts": watch_flags_count,
        "overdue_groups": overdue_count,
        "control_status": "NORMAL" if urgent_flags_count == 0 else "HEIGHTENED_ALERT"
    }

@router.get("/dashboard/groups")
async def get_dashboard_groups(
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """Retrieve list of groups with current coordinates, last checkpoint, and flags."""
    stmt = (
        select(Group)
        .options(
            selectinload(Group.checkins),
            selectinload(Group.flags)
        )
        .order_by(Group.created_at.desc())
    )
    if scoped_user.route_scope: stmt = stmt.where(Group.route_id == scoped_user.route_scope)
    if state:
        stmt = stmt.where(Group.status == state)
    groups = (await db.execute(stmt)).scalars().all()

    response = []
    for g in groups:
        valid_scans = [c for c in g.checkins if c.valid]
        last_cp_id = None
        last_scan_time = None
        current_headcount = 0 if g.status == "cancelled" else g.size
        if valid_scans:
            valid_scans.sort(key=lambda s: s.client_ts)
            last_cp_id = valid_scans[-1].checkpoint_id
            last_scan_time = valid_scans[-1].client_ts.isoformat()
            current_headcount = valid_scans[-1].headcount

        open_flags = [
            {
                "id": f.id,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "message_en": f.message_en,
                "created_at": f.created_at.isoformat()
            }
            for f in g.flags if f.status == "open"
        ]

        response.append({
            "id": g.id,
            "code": g.code,
            "leader_name": g.leader_name,
            "leader_phone": g.leader_phone,
            "emergency_phone": g.emergency_phone,
            "size": g.size,
            "current_headcount": current_headcount,
            "status": g.status,
            "last_checkpoint_id": last_cp_id,
            "last_scan_time": last_scan_time,
            "last_server_received_at": valid_scans[-1].server_ts.isoformat() if valid_scans else None,
            "confirmation_source": valid_scans[-1].source if valid_scans else None,
            "open_flags": open_flags
        })
    return response

@router.get("/dashboard/stream")
async def stream_dashboard_events():
    """SSE real-time event stream for the Control Room dashboard."""
    async def event_generator():
        queue = await sse_hub.subscribe()
        try:
            # Send initial keep-alive
            yield f"event: connected\ndata: {{\"time\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=1)
                    # Payloads contain group codes; broadcast refresh only across route scopes.
                    yield 'event: refresh\ndata: {}\n\n'
                except asyncio.TimeoutError:
                    yield 'event: refresh\ndata: {}\n\n'
        finally:
            sse_hub.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

@router.get("/flags")
async def list_risk_flags(
    status: Optional[str] = "open",
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """Retrieve audit list of risk flags."""
    stmt = select(RiskFlag).order_by(RiskFlag.created_at.desc())
    if scoped_user.route_scope: stmt = stmt.join(Group).where(Group.route_id == scoped_user.route_scope)
    if status:
        stmt = stmt.where(RiskFlag.status == status)
    if severity:
        stmt = stmt.where(RiskFlag.severity == severity)
    flags = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": f.id,
            "group_id": f.group_id,
            "checkpoint_id": f.checkpoint_id,
            "rule_id": f.rule_id,
            "severity": f.severity,
            "message_en": f.message_en,
            "message_hi": f.message_hi,
            "data": f.data,
            "status": f.status,
            "created_at": f.created_at.isoformat(),
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None
        }
        for f in flags
    ]

@router.patch("/flags/{id}")
async def update_risk_flag_status(
    id: int,
    action: str = Query(..., pattern="^(ack|resolve)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """Acknowledge or resolve an active safety flag."""
    res = await db.execute(select(RiskFlag).where(RiskFlag.id == id))
    flag = res.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Risk flag not found.")

    enforce_route(user, (await db.get(Group, flag.group_id)).route_id)
    now = datetime.now(timezone.utc)
    if action == "ack":
        flag.status = "acked"
    elif action == "resolve":
        flag.status = "resolved"
        flag.resolved_at = now
        flag.resolved_by = user.id

    await db.commit()
    # Broadcast to SSE
    await sse_hub.broadcast("flag_update", {"flag_id": id, "status": flag.status, "action": action})
    return {"id": id, "status": flag.status}

@router.get("/incidents")
async def list_incidents(db: AsyncSession = Depends(get_db), scoped_user: User = Depends(require_control_user)):
    """List all rescue incidents."""
    stmt = select(Incident).order_by(Incident.created_at.desc())
    if scoped_user.route_scope: stmt = stmt.join(Group).where(Group.route_id == scoped_user.route_scope)
    incidents = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": inc.id,
            "group_id": inc.group_id,
            "flag_id": inc.flag_id,
            "type": inc.type,
            "status": inc.status,
            "assigned_to": inc.assigned_to,
            "notes": inc.notes,
            "created_at": inc.created_at.isoformat()
        }
        for inc in incidents
    ]

@router.post("/admin/checkpoints/{id}/verify")
async def verify_checkpoint(
    id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """Admin endpoint to officially verify physical survey coordinates."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required to verify survey coordinates.")
    cp = await db.get(Checkpoint, id)
    if not cp: raise HTTPException(404, "Checkpoint not found")
    enforce_route(user, cp.route_id)
    stmt = update(Checkpoint).where(Checkpoint.id == id).values(verified=True)
    await db.execute(stmt)
    await db.commit()
    return {"checkpoint_id": id, "verified": True}

@router.get("/admin/report.csv")
async def export_report_csv(
    route: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    scoped_user: User = Depends(require_control_user)
):
    """Generate CSV audit report of all checkins and flags."""
    if route: enforce_route(scoped_user, route)
    route = scoped_user.route_scope or route
    stmt = select(Checkin).order_by(Checkin.server_ts.desc())
    if route:
        stmt=stmt.join(Group,Checkin.group_id==Group.id).where(Group.route_id==route)
    checkins = (await db.execute(stmt)).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Checkin_UUID", "Group_ID", "Checkpoint_ID", "Headcount", "Client_TS", "Server_TS", "Valid", "Invalid_Reason"])
    for c in checkins:
        writer.writerow([c.id, c.group_id, c.checkpoint_id, c.headcount, c.client_ts, c.server_ts, c.valid, c.invalid_reason])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=yatra_kavach_report.csv"}
    )
