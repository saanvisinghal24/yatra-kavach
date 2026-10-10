import pytest
from datetime import datetime, timezone, time, timedelta
from app.rules.engine import (
    evaluate_r1_fast_ascent,
    evaluate_r2_slow_overdue,
    evaluate_r3_cutoff,
    evaluate_r4_night_on_trail,
    evaluate_r6_congestion,
    evaluate_r8_missing,
    evaluate_r9_headcount_drop,
    calculate_median_eta
)
from app.services.sweep import upsert_risk_flag, run_safety_sweep_cycle
from app.models.group import Group
from app.models.trail import Checkpoint
from app.models.checkin import Checkin
from app.models.safety import RiskFlag
from app.seed.seed_trails import seed_data
from app.db import AsyncSessionLocal
from sqlalchemy import select

# ----------------- TABLE DRIVEN TESTS ----------------- #

@pytest.mark.parametrize("elapsed_mins,altitude_m,min_minutes,expected_flag", [
    (140.0, 3000, 130, False),  # Normal ascent (140 mins for 130 min expected min)
    (50.0, 3000, 130, True),    # Fast ascent (50 mins < 60% of 130 = 78 mins, alt >= 3000m)
    (30.0, 2100, 70, False),    # Fast ascent below 3000m -> R1 does not trigger
])
def test_r1_fast_ascent_cases(elapsed_mins, altitude_m, min_minutes, expected_flag):
    t0 = datetime(2026, 8, 20, 8, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=elapsed_mins)
    prev_checkin = {"client_ts": t0}
    last_checkin = {"client_ts": t1}
    cp = {"id": 2, "name_en": "Dhancho", "name_hi": "धंचो", "altitude_m": altitude_m, "min_minutes": min_minutes}

    flag = evaluate_r1_fast_ascent(last_checkin, prev_checkin, cp)
    if expected_flag:
        assert flag is not None
        assert flag.rule_id == "R1"
        assert flag.severity == "watch"
        assert "Ascent too rapid" in flag.message_en
    else:
        assert flag is None

@pytest.mark.parametrize("elapsed_mins,max_minutes,expected_severity", [
    (100.0, 170, None),       # Normal progress
    (220.0, 170, "watch"),    # Elapsed > 125% of 170 (212.5m) -> watch
    (330.0, 170, "urgent"),   # Elapsed > 175% of 170 + 20 grace (317.5m) -> urgent
])
def test_r2_slow_overdue_cases(elapsed_mins, max_minutes, expected_severity):
    t0 = datetime(2026, 8, 20, 8, 0, 0, tzinfo=timezone.utc)
    now = t0 + timedelta(minutes=elapsed_mins)
    last_checkin = {"client_ts": t0}
    next_cp = {"id": 2, "name_en": "Dhancho", "name_hi": "धंचो", "max_minutes": max_minutes}

    flag = evaluate_r2_slow_overdue(last_checkin, next_cp, now, grace_minutes=20)
    if expected_severity:
        assert flag is not None
        assert flag.rule_id == "R2"
        assert flag.severity == expected_severity
    else:
        assert flag is None

@pytest.mark.parametrize("checkin_hour,checkin_minute,cutoff_str,expected_flag", [
    (14, 30, "15:00", False),  # Arrived at 14:30, cutoff 15:00 -> ok
    (15, 0, "15:00", False),   # Exactly at 15:00 cutoff -> ok
    (15, 30, "15:00", True),   # Arrived at 15:30, cutoff 15:00 -> watch
])
def test_r3_cutoff_cases(checkin_hour, checkin_minute, cutoff_str, expected_flag):
    chk_ts = datetime(2026, 8, 20, checkin_hour, checkin_minute, 0, tzinfo=timezone.utc)
    last_checkin = {"client_ts": chk_ts}
    cp = {"id": 2, "name_en": "Dhancho", "name_hi": "धंचो", "cutoff_time": cutoff_str}

    flag = evaluate_r3_cutoff(last_checkin, cp)
    if expected_flag:
        assert flag is not None
        assert flag.rule_id == "R3"
        assert flag.severity == "watch"
        assert "after cutoff" in flag.message_en
    else:
        assert flag is None

@pytest.mark.parametrize("start_hour,est_duration,sunset_hour,expected_flag", [
    (13, 120, 19, False),  # Finish at 15:00, sunset 19:00 -> ok
    (17, 180, 19, True),   # Finish at 20:00, sunset 19:00 -> Night hazard
    (11, 240, 18, False),  # Finish at 15:00, sunset 18:00 -> ok
])
def test_r4_night_on_trail_cases(start_hour, est_duration, sunset_hour, expected_flag):
    now = datetime(2026, 8, 20, start_hour, 0, 0, tzinfo=timezone.utc)
    last_checkin = {"client_ts": now}
    next_cp = {"id": 3, "name_en": "Gaurikund", "name_hi": "गौरीकुंड", "max_minutes": est_duration}
    sunset = time(sunset_hour, 0)

    flag = evaluate_r4_night_on_trail(last_checkin, next_cp, now, sunset)
    if expected_flag:
        assert flag is not None
        assert flag.rule_id == "R4"
        assert flag.severity == "watch"
        assert "Nightfall hazard" in flag.message_en
    else:
        assert flag is None

@pytest.mark.parametrize("people,capacity,expected_flag", [
    (200, 400, False),  # Under capacity
    (400, 400, False),  # At capacity
    (550, 400, True),   # Congested -> watch
])
def test_r6_congestion_cases(people, capacity, expected_flag):
    flag = evaluate_r6_congestion("seg_1_2", people, capacity, checkpoint_id=2)
    if expected_flag:
        assert flag is not None
        assert flag.rule_id == "R6"
        assert flag.severity == "watch"
        assert "Trail bottleneck" in flag.message_en
    else:
        assert flag is None

@pytest.mark.parametrize("elapsed_mins,max_minutes,grace_minutes,expected_flag", [
    (120, 150, 40, False),  # Still within segment max
    (250, 150, 40, False),  # Overdue (R2 territory, not yet R8 missing)
    (380, 150, 40, True),   # Missing: > (2.0 * 150 + 40 = 340 mins) -> R8 urgent
])
def test_r8_missing_cases(elapsed_mins, max_minutes, grace_minutes, expected_flag):
    t0 = datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc)
    now = t0 + timedelta(minutes=elapsed_mins)
    last_checkin = {"client_ts": t0, "checkpoint_id": 2, "checkpoint_name": "Dhancho"}
    next_cp = {"id": 3, "name_en": "Gaurikund", "name_hi": "गौरीकुंड", "max_minutes": max_minutes}

    flag = evaluate_r8_missing(last_checkin, next_cp, now, grace_minutes=grace_minutes)
    if expected_flag:
        assert flag is not None
        assert flag.rule_id == "R8"
        assert flag.severity == "urgent"
        assert "missing status is not established" in flag.message_en
        assert flag.data["search_segment_from"] == "Dhancho"
        assert flag.data["search_segment_to"] == "Gaurikund"
    else:
        assert flag is None

@pytest.mark.parametrize("curr_cnt,prev_cnt,unresolved_mins,expected_severity", [
    (4, 4, 0.0, None),        # No change
    (3, 4, 10.0, "watch"),    # Drop from 4 to 3 -> watch
    (3, 4, 35.0, "urgent"),   # Drop unresolved > 30m -> escalated to urgent!
])
def test_r9_headcount_drop_cases(curr_cnt, prev_cnt, unresolved_mins, expected_severity):
    flag = evaluate_r9_headcount_drop(curr_cnt, prev_cnt, unresolved_mins, checkpoint_id=2)
    if expected_severity:
        assert flag is not None
        assert flag.rule_id == "R9"
        assert flag.severity == expected_severity
        assert "Headcount drop detected" in flag.message_en
    else:
        assert flag is None

def test_calculate_median_eta():
    # Fallback to min-max when sample < 5
    eta_min, eta_max = calculate_median_eta(1, 2, [135, 140, 150], 120, 170)
    assert eta_min == 120
    assert eta_max == 170

    # Calculated from median when sample >= 5
    samples = [140.0, 145.0, 150.0, 155.0, 160.0]  # Median = 150
    m_min, m_max = calculate_median_eta(1, 2, samples, 120, 170)
    assert m_min == int(150 * 0.88)
    assert m_max == int(150 * 1.15)

@pytest.mark.asyncio
async def test_stalled_group_produces_r2_then_r8_and_deduplicates():
    import uuid
    from app.services.code_gen import generate_group_code
    await seed_data()

    code = generate_group_code(6)
    chk_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        # Create an active group with one checkin at Hadsar (CP 1)
        group = Group(
            code=code,
            yatra_id=1,
            route_id=1,
            leader_name="Devendra Paul",
            leader_phone="+919816077777",
            emergency_name="Rita Paul",
            emergency_phone="+919816088888",
            size=2,
            planned_start=datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc),
            started_at=datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc),
            status="active"
        )
        session.add(group)
        await session.flush()

        checkin1 = Checkin(
            id=chk_id,
            group_id=group.id,
            checkpoint_id=1,
            headcount=2,
            client_ts=datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc),
            server_ts=datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc),
            valid=True
        )
        session.add(checkin1)
        await session.commit()

        # Step 1: Advance time to 220 mins (Dhancho max_minutes = 170 mins).
        # Elapsed 220m > 125% of 170 (212.5m) -> Trigger R2 (Slow/Overdue)
        time_overdue = datetime(2026, 8, 20, 9, 40, 0, tzinfo=timezone.utc)
        await run_safety_sweep_cycle(session, now=time_overdue)

        flags_overdue = (await session.execute(
            select(RiskFlag).where(RiskFlag.group_id == group.id, RiskFlag.status == "open")
        )).scalars().all()
        assert len(flags_overdue) == 1
        assert flags_overdue[0].rule_id == "R2"
        assert flags_overdue[0].severity == "watch"

        # Step 2: Running sweep again at the same time does NOT create duplicate flags (deduplication check)
        await run_safety_sweep_cycle(session, now=time_overdue)
        flags_dedup = (await session.execute(
            select(RiskFlag).where(RiskFlag.group_id == group.id, RiskFlag.status == "open")
        )).scalars().all()
        assert len(flags_dedup) == 1  # Still exactly 1 open flag!

        # Step 3: Advance time to 400 mins -> R8 Missing triggers (> 2.0*170 + 40 = 380m)
        time_missing = datetime(2026, 8, 20, 12, 40, 0, tzinfo=timezone.utc)
        await run_safety_sweep_cycle(session, now=time_missing)

        flags_missing = (await session.execute(
            select(RiskFlag).where(RiskFlag.group_id == group.id, RiskFlag.status == "open")
        )).scalars().all()
        # R8 missing is present with search window
        r8 = next(f for f in flags_missing if f.rule_id == "R8")
        assert r8.severity == "urgent"
        assert "missing status is not established" in r8.message_en
        assert r8.data["search_segment_from"] == "Hadsar"
        assert r8.data["search_segment_to"] == "Dhancho"
