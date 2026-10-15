from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, Response, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models.group import Group
from app.models.trail import Checkpoint
from app.models.checkin import Checkin
from app.schemas.checkin import CheckinBatchRequest, CheckinBatchResponse, CheckinResultItem
from app.services.qr_signer import verify_checkpoint_qr

router = APIRouter(prefix="/checkins", tags=["Check-in Ingest Pipeline"])

@router.post("/batch", response_model=CheckinBatchResponse)
async def ingest_checkin_batch(
    payload: CheckinBatchRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a batch of checkpoint scans (up to 50 items).
    Strictly idempotent by client-generated UUID PK.
    Verifies HMAC-SHA256 signature on physical checkpoint QRs.
    Sets standard Date header for client clock-skew calibration.
    """
    user = None
    if any(e.source == "volunteer" for e in payload.events):
        from app.services.auth import get_current_user, security
        user = await get_current_user(request, await security(request), db)
    now = datetime.now(timezone.utc)
    # Add standard HTTP Date header for client synchronization
    response.headers["Date"] = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    results: List[CheckinResultItem] = []
    accepted = 0
    duplicates = 0
    invalids = 0

    for item in payload.events:
        if db.bind.dialect.name == 'postgresql':
            from sqlalchemy import text
            # Cross-worker idempotency and group-level serialization.
            await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {'key': item.group_code})
        await db.flush()
        # 1. Idempotency Check
        existing_check = await db.execute(select(Checkin).where(Checkin.id == item.id))
        existing = existing_check.scalar_one_or_none()
        if existing:
            results.append(CheckinResultItem(
                id=item.id,
                status="duplicate" if existing.valid else "invalid",
                valid=existing.valid,
                invalid_reason=existing.invalid_reason,
                server_ts=existing.server_ts
            ))
            if existing.valid:duplicates += 1
            else:invalids += 1
            continue

        # 2. Group Verification
        group_stmt = select(Group).where(Group.code == item.group_code)
        group_res = await db.execute(group_stmt)
        group = group_res.scalar_one_or_none()
        if not group:
            results.append(CheckinResultItem(
                id=item.id,
                status="invalid",
                valid=False,
                invalid_reason=f"Group code '{item.group_code}' not found.",
                server_ts=now
            ))
            invalids += 1
            continue

        if group.status == "cancelled":
            results.append(CheckinResultItem(id=item.id, status="invalid", valid=False,
                invalid_reason="This trip has been cancelled. Contact checkpoint staff if already on the trail.", server_ts=now))
            invalids += 1
            continue

        # 3. Checkpoint Verification
        cp_stmt = select(Checkpoint).where(Checkpoint.id == item.checkpoint_id)
        cp_res = await db.execute(cp_stmt)
        checkpoint = cp_res.scalar_one_or_none()
        if not checkpoint:
            results.append(CheckinResultItem(
                id=item.id,
                status="invalid",
                valid=False,
                invalid_reason=f"Checkpoint ID {item.checkpoint_id} not found.",
                server_ts=now
            ))
            invalids += 1
            continue

        if checkpoint.route_id != group.route_id:
            results.append(CheckinResultItem(id=item.id, status="invalid", valid=False, invalid_reason="Checkpoint is on another route", server_ts=now))
            invalids += 1
            continue

        if user and user.route_scope and user.route_scope != checkpoint.route_id:
            raise HTTPException(403, "Checkpoint outside staff route scope")
        if item.source == 'volunteer' and user.role not in ('admin','volunteer','rescue'):
            raise HTTPException(403, 'Volunteer, rescue or admin role required for confirmed check-ins')
        item.volunteer_id = user.id if user and item.source == 'volunteer' else None
        from app.services.journey import members_for, apply_event
        members = await members_for(db, group)
        selected_ids = item.member_ids or ([m.id for m in members] if item.headcount == group.size else [])
        reason = None
        if len(set(selected_ids)) != len(selected_ids) or len(selected_ids) != item.headcount or not set(selected_ids) <= {m.id for m in members}:
            reason = 'Select exactly the members present; partial-group events require member IDs'
        first_cp = (await db.execute(select(Checkpoint).where(Checkpoint.route_id == group.route_id).order_by(Checkpoint.seq))).scalars().first()
        if item.direction == 'exit' and checkpoint.id != first_cp.id:
            reason = 'Final exit is recorded only at the first checkpoint (Hadsar)'
        if reason:
            results.append(CheckinResultItem(id=item.id,status='invalid',valid=False,invalid_reason=reason,server_ts=now))
            invalids += 1
            continue
        # 4. Physical Signed QR Verification
        is_qr_valid, scanned_cp_id, error_msg = verify_checkpoint_qr(
            item.signed_qr,
            checkpoint.qr_key_version
        )
        if not is_qr_valid or scanned_cp_id != checkpoint.id:
            reason = error_msg or f"QR signed for CP {scanned_cp_id} but submitted for CP {checkpoint.id}"
            invalid_checkin = Checkin(
                id=item.id,
                group_id=group.id,
                checkpoint_id=checkpoint.id,
                source=item.source,
                volunteer_id=item.volunteer_id,
                headcount=item.headcount,
                client_ts=item.client_ts,
                server_ts=now,
                clock_skew_s=item.clock_skew_s,
                lat=item.lat,
                lon=item.lon,
                valid=False,
                invalid_reason=reason
            )
            db.add(invalid_checkin)
            results.append(CheckinResultItem(
                id=item.id,
                status="invalid",
                valid=False,
                invalid_reason=reason,
                server_ts=now
            ))
            invalids += 1
            continue

        corrected = item.client_ts.replace(tzinfo=timezone.utc) if item.client_ts.tzinfo is None else item.client_ts
        corrected -= timedelta(seconds=item.clock_skew_s)
        if abs(item.clock_skew_s)>300 or corrected>now+timedelta(minutes=5):
            results.append(CheckinResultItem(id=item.id,status='invalid',valid=False,invalid_reason='Device clock is unreliable; correct the clock and rescan',server_ts=now))
            invalids+=1
            continue
        item.client_ts=corrected
        # 5. Valid Check-in Creation
        new_checkin = Checkin(
            id=item.id,
            group_id=group.id,
            checkpoint_id=checkpoint.id,
            source=item.source,
            volunteer_id=item.volunteer_id,
            headcount=item.headcount,
            client_ts=item.client_ts,
            server_ts=now,
            clock_skew_s=item.clock_skew_s,
            lat=item.lat,
            lon=item.lon,
            valid=True,
            invalid_reason=None, direction=item.direction, member_ids=selected_ids
        )
        db.add(new_checkin)

        await apply_event(db, group, new_checkin, members)
        results.append(CheckinResultItem(
            id=item.id,
            status="accepted",
            valid=True,
            invalid_reason=None,
            server_ts=now
        ))
        accepted += 1

    await db.commit()
    from app.services.pipeline import evaluate_all
    from app.services.sse import sse_hub
    await evaluate_all(db)
    await sse_hub.broadcast("checkin", {"accepted": accepted})

    return CheckinBatchResponse(
        results=results,
        processed_count=len(payload.events),
        accepted_count=accepted,
        duplicate_count=duplicates,
        invalid_count=invalids
    )
