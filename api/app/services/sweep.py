import asyncio
from datetime import datetime, timezone, time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import AsyncSessionLocal
from app.models.group import Group
from app.models.trail import Checkpoint
from app.models.checkin import Checkin
from app.models.safety import RiskFlag
from app.rules.engine import evaluate_r2_slow_overdue, evaluate_r8_missing, RuleFlag

async def upsert_risk_flag(db: AsyncSession, group_id: int, flag: RuleFlag) -> bool:
    """
    Upsert risk flag ensuring only one OPEN flag exists per (group_id, rule_id).
    Updates existing open flag if present; otherwise creates a new one.
    Returns True if a new flag was inserted.
    """
    if db.bind.dialect.name == 'postgresql':
        from sqlalchemy import text
        await db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':group_id})
    stmt = (
        select(RiskFlag)
        .where(
            RiskFlag.group_id == group_id,
            RiskFlag.rule_id == flag.rule_id,
            RiskFlag.status.in_(["open", "acked"])
        )
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.severity = flag.severity
        existing.message_en = flag.message_en
        existing.message_hi = flag.message_hi
        existing.checkpoint_id = flag.checkpoint_id
        existing.data = flag.data
        return False
    else:
        new_flag = RiskFlag(
            group_id=group_id,
            checkpoint_id=flag.checkpoint_id,
            rule_id=flag.rule_id,
            severity=flag.severity,
            message_en=flag.message_en,
            message_hi=flag.message_hi,
            data=flag.data,
            status="open"
        )
        db.add(new_flag)
        return True

async def run_safety_sweep_cycle(db: AsyncSession, now: datetime = None) -> int:
    """
    Single cycle of the 60s background safety sweep.
    Evaluates all active groups for R2 (slow/overdue) and R8 (missing).
    Returns count of updated/created flags.
    """
    current_time = now or datetime.now(timezone.utc)
    
    # 1. Fetch active groups with checkins
    stmt = (
        select(Group)
        .where(Group.status == "active")
        .options(
            selectinload(Group.checkins),
            selectinload(Group.flags)
        )
    )
    res = await db.execute(stmt)
    active_groups = res.scalars().all()

    # Pre-cache checkpoints
    cp_res = await db.execute(select(Checkpoint).order_by(Checkpoint.seq))
    all_checkpoints = cp_res.scalars().all()
    checkpoints_by_id = {cp.id: cp for cp in all_checkpoints}

    flags_modified = 0

    for grp in active_groups:
        valid_scans = [c for c in grp.checkins if c.valid]
        if not valid_scans:
            continue
        valid_scans.sort(key=lambda s: s.client_ts)
        last_scan = valid_scans[-1]

        curr_cp = checkpoints_by_id.get(last_scan.checkpoint_id)
        if not curr_cp:
            continue

        # Find next sequential checkpoint
        route_cps = [cp for cp in all_checkpoints if cp.route_id == grp.route_id and cp.seq > curr_cp.seq]
        if not route_cps:
            continue  # Reached final summit/destination
        next_cp = route_cps[0]

        last_checkin_dict = {
            "checkpoint_id": curr_cp.id,
            "checkpoint_name": curr_cp.name_en,
            "client_ts": last_scan.client_ts
        }
        next_cp_dict = {
            "id": next_cp.id,
            "seq": next_cp.seq,
            "name_en": next_cp.name_en,
            "name_hi": next_cp.name_hi,
            "max_minutes": next_cp.max_minutes,
            "cutoff_time": next_cp.cutoff_time
        }

        # Check R8: Missing
        r8_flag = evaluate_r8_missing(last_checkin_dict, next_cp_dict, current_time)
        if r8_flag:
            await upsert_risk_flag(db, grp.id, r8_flag)
            flags_modified += 1
        else:
            # Check R2: Slow / Overdue
            r2_flag = evaluate_r2_slow_overdue(last_checkin_dict, next_cp_dict, current_time)
            if r2_flag:
                await upsert_risk_flag(db, grp.id, r2_flag)
                flags_modified += 1

    await db.commit()
    return flags_modified
