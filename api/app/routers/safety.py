from app.rules.settings import RULES
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal
from fastapi import Request, APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.services.receipt import replay, finish
from app.models.group import Group
from app.models.trail import Checkpoint
from app.models.checkin import Checkin
from app.models.safety import SymptomReport, RiskFlag, Incident, ShareToken
from app.services.weather import get_checkpoint_weather
from app.services.sse import sse_hub
from app.notify.notifier import get_notifier

router = APIRouter(tags=["Safety, Health, SOS & Family Share"])

# --- Schemas --- #
class SymptomReportRequest(BaseModel):
    group_code: str
    checkpoint_id: Optional[int] = None
    headache: int = Field(..., ge=0, le=3)
    stomach: int = Field(..., ge=0, le=3)
    fatigue: int = Field(..., ge=0, le=3)
    dizziness: int = Field(..., ge=0, le=3)
    red_flags: List[Literal['confusion', 'ataxia', 'breathless_at_rest', 'wet_cough']] = Field(default_factory=list, max_length=4)  # e.g. 'confusion', 'ataxia', 'breathless_at_rest', 'wet_cough'

class SymptomReportResponse(BaseModel):
    id: int
    score: int
    advice_level: Literal["normal", "mild", "moderate", "severe"]
    guidance_en: str
    guidance_hi: str
    emergency_contact_needed: bool
    red_flags_detected: List[str]

class SOSRequest(BaseModel):
    group_code: str
    checkpoint_id: Optional[int] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    reason: Optional[str] = Field("Emergency assistance requested", max_length=1000)

class FamilyShareResponse(BaseModel):
    status: str
    last_checkpoint: Optional[str] = None
    last_seen_time: Optional[str] = None
    eta_range: Optional[str] = None
    advisory_note: str

# --- Endpoints --- #

@router.post("/symptom-reports", response_model=SymptomReportResponse)
async def submit_symptom_report(payload: SymptomReportRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Evaluate Lake Louise Acute Mountain Sickness (AMS) score and red flags.
    Strictly provides GUIDANCE, never diagnosis.
    Red flags immediately escalate to urgent control room flag and rescue alert.
    """
    key=request.headers.get('Idempotency-Key')
    if key and len(key)>64:raise HTTPException(422,'Invalid event identifier')
    previous=await replay(db,key)
    if previous:return previous
    res = await db.execute(select(Group).where(Group.code == payload.group_code))
    group = res.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group code not found.")

    if payload.checkpoint_id is not None:
        checkpoint = await db.get(Checkpoint, payload.checkpoint_id)
        if not checkpoint or checkpoint.route_id != group.route_id: raise HTTPException(422, "Checkpoint outside group route")
    score = payload.headache + payload.stomach + payload.fatigue + payload.dizziness
    has_red_flags = len(payload.red_flags) > 0

    if has_red_flags or score >= RULES["R7"]["severe"]:
        advice_level, emergency_needed = "severe", True
    elif score >= RULES["R7"]["moderate"]:
        advice_level, emergency_needed = "moderate", True
    elif score >= RULES["R7"]["mild"]:
        advice_level, emergency_needed = "mild", False
    else:
        advice_level, emergency_needed = "normal", False
    guidance_en = ("Urgent staff follow-up requested. Contact medical help; call 112 / 108 for an emergency. " if emergency_needed else "Seek medical advice if unwell. ") + "This unreviewed screening rule is not a diagnosis or fitness-to-continue assessment. No warning threshold does not rule out illness."
    guidance_hi = ("कर्मचारी से शीघ्र संपर्क आवश्यक। चिकित्सा सहायता लें; आपात स्थिति में 112 / 108 पर कॉल करें। " if emergency_needed else "अस्वस्थ होने पर चिकित्सा सलाह लें। ") + "यह समीक्षा-लंबित नियम निदान या आगे बढ़ने की अनुमति नहीं है। सीमा पार न होना स्वस्थ होने का प्रमाण नहीं है।"

    # Persist report
    report = SymptomReport(
        group_id=group.id,
        checkpoint_id=payload.checkpoint_id,
        score=score,
        red_flags=payload.red_flags,
        advice_level=advice_level
    )
    db.add(report)

    # Escalate to control room if moderate or severe
    if advice_level in ["moderate", "severe"]:
        severity = "urgent" if advice_level == "severe" else "watch"
        stmt = select(RiskFlag).where(
            RiskFlag.group_id == group.id,
            RiskFlag.rule_id == "R7",
            RiskFlag.status == "open"
        )
        existing_flag = (await db.execute(stmt)).scalar_one_or_none()
        if existing_flag:
            existing_flag.severity = severity
            existing_flag.message_en = f"Medical Advisory (Score {score}/12): {guidance_en}"
            existing_flag.message_hi = f"चिकित्सा सलाह (स्कोर {score}/12): {guidance_hi}"
            existing_flag.data = {"score": score, "red_flags": payload.red_flags, "advice_level": advice_level}
            existing_flag.checkpoint_id = payload.checkpoint_id
        else:
            flag = RiskFlag(
                group_id=group.id,
                checkpoint_id=payload.checkpoint_id,
                rule_id="R7",
                severity=severity,
                message_en=f"Medical Advisory (Score {score}/12): {guidance_en}",
                message_hi=f"चिकित्सा सलाह (स्कोर {score}/12): {guidance_hi}",
                data={"score": score, "red_flags": payload.red_flags, "advice_level": advice_level},
                status="open"
            )
            db.add(flag)
        # Notify
        notifier = get_notifier()
        await notifier.send_alert(
            title=f"AMS Health Flag ({advice_level.upper()})",
            message="A health concern was recorded; authenticated staff should review the dashboard.",
            severity=severity
        )
        await sse_hub.broadcast("new_flag", {"group_code": group.code, "rule_id": "R7", "severity": severity})

    await db.flush()
    result = SymptomReportResponse(
        id=report.id,
        score=score,
        advice_level=advice_level,
        guidance_en=guidance_en,
        guidance_hi=guidance_hi,
        emergency_contact_needed=emergency_needed,
        red_flags_detected=payload.red_flags
    )
    return await finish(db,key,group.id,result.model_dump())

@router.post("/sos")
async def trigger_emergency_sos(payload: SOSRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Emergency SOS trigger with automatic control room escalation.
    Creates urgent Incident and RiskFlag.
    """
    key=request.headers.get('Idempotency-Key')
    if key and len(key)>64:raise HTTPException(422,'Invalid event identifier')
    previous=await replay(db,key)
    if previous:return previous
    res = await db.execute(select(Group).where(Group.code == payload.group_code))
    group = res.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if payload.checkpoint_id is not None:
        checkpoint = await db.get(Checkpoint, payload.checkpoint_id)
        if not checkpoint or checkpoint.route_id != group.route_id: raise HTTPException(422, "Checkpoint outside group route")
    # Create or update Urgent Flag
    stmt = select(RiskFlag).where(
        RiskFlag.group_id == group.id,
        RiskFlag.rule_id == "SOS",
        RiskFlag.status == "open"
    )
    flag = (await db.execute(stmt)).scalar_one_or_none()
    if flag:
        flag.severity = "urgent"
        flag.message_en = f"EMERGENCY SOS: Group {group.code} ({group.leader_name}) triggered distress alarm! {payload.reason}"
        flag.message_hi = f"आपातकालीन एसओएस: दल {group.code} ({group.leader_name}) ने सहायता का अनुरोध किया है!"
        flag.data = {"lat": payload.lat, "lon": payload.lon, "reason": payload.reason}
        flag.checkpoint_id = payload.checkpoint_id
    else:
        flag = RiskFlag(
            group_id=group.id,
            checkpoint_id=payload.checkpoint_id,
            rule_id="SOS",
            severity="urgent",
            message_en=f"EMERGENCY SOS: Group {group.code} ({group.leader_name}) triggered distress alarm! {payload.reason}",
            message_hi=f"आपातकालीन एसओएस: दल {group.code} ({group.leader_name}) ने सहायता का अनुरोध किया है!",
            data={"lat": payload.lat, "lon": payload.lon, "reason": payload.reason},
            status="open"
        )
        db.add(flag)
    await db.flush()

    # Create Incident
    incident = Incident(
        group_id=group.id,
        flag_id=flag.id,
        type="emergency_sos",
        status="open",
        notes=payload.reason
    )
    db.add(incident)
    await db.flush()

    # Dispatch Alert
    notifier = get_notifier()
    await notifier.send_alert(
        title="EMERGENCY DISTRESS SOS",
        message="An SOS was recorded; authenticated staff should review the dashboard.",
        severity="urgent"
    )
    await sse_hub.broadcast("sos_alert", {"group_code": group.code, "checkpoint_id": payload.checkpoint_id})

    return await finish(db,key,group.id,{
        "status": "server_received",
        "server_received_at": datetime.now(timezone.utc).isoformat(),
        "staff_acknowledged": False,
        "incident_id": incident.id,
        "emergency_dispatch": "Server received the request. Staff acknowledgment and emergency dispatch are not confirmed. Call 112 / 108 if able."
    })

@router.get("/weather/{checkpoint_id}")
async def get_weather(checkpoint_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve 30-min cached weather and R5 status for a checkpoint."""
    res = await db.execute(select(Checkpoint).where(Checkpoint.id == checkpoint_id))
    cp = res.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found.")
    from astral import Observer
    from astral.sun import sun
    from zoneinfo import ZoneInfo
    solar=sun(Observer(cp.lat,cp.lon),date=datetime.now(ZoneInfo('Asia/Kolkata')).date(),tzinfo=ZoneInfo('Asia/Kolkata'))
    result=await get_checkpoint_weather(cp.id, cp.lat, cp.lon, cp.name_en)
    return {**result,'sunrise':solar['sunrise'].isoformat(),'sunset':solar['sunset'].isoformat()}

@router.post("/share/generate/{code}")
async def generate_family_share_token(code: str, db: AsyncSession = Depends(get_db)):
    """Generate a privacy-preserving 128-bit random token for family sharing."""
    res = await db.execute(select(Group).where(Group.code == code))
    group = res.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    token = secrets.token_hex(16)  # 128-bit random hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    st = ShareToken(
        group_id=group.id,
        token=token,
        expires_at=expires_at
    )
    db.add(st)
    await db.commit()
    return {"token": token, "share_url": f"/share/{token}", "expires_at": expires_at.isoformat()}

@router.get("/share/{token}", response_model=FamilyShareResponse)
async def get_family_share_status(token: str, db: AsyncSession = Depends(get_db)):
    """
    Privacy-minimal public family viewer.
    Zero live GPS. Only displays last verified checkpoint, timestamp, and segment ETA range.
    """
    st_res = await db.execute(
        select(ShareToken)
        .where(ShareToken.token == token)
        .options(selectinload(ShareToken.group))
    )
    share = st_res.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Family share link is invalid or expired.")

    exp = share.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Family share link is invalid or expired.")

    group = share.group
    latest_incident=(await db.execute(select(Incident).where(Incident.group_id==group.id).order_by(Incident.created_at.desc()))).scalars().first()
    # Fetch last checkin
    chk_res = await db.execute(
        select(Checkin)
        .where(Checkin.group_id == group.id, Checkin.valid == True, Checkin.state_applied == True)
        .order_by(Checkin.client_ts.desc())
    )
    last_checkin = chk_res.scalars().first()

    last_cp_name = None
    last_seen = None
    eta_range = None
    if last_checkin:
        cp_res = await db.execute(select(Checkpoint).where(Checkpoint.id == last_checkin.checkpoint_id))
        cp = cp_res.scalar_one_or_none()
        if cp:
            last_cp_name = cp.name_en
            last_seen = last_checkin.client_ts.replace(tzinfo=timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %H:%M IST")
            next_cp=(await db.execute(select(Checkpoint).where(Checkpoint.route_id==cp.route_id,Checkpoint.seq>cp.seq).order_by(Checkpoint.seq))).scalars().first()
            eta_range=f"{next_cp.min_minutes} – {next_cp.max_minutes} min" if next_cp else 'Destination report; final return reconciliation pending' 

    return FamilyShareResponse(
        status=group.status.upper(),
        last_checkpoint=last_cp_name or "Trailhead base",
        last_seen_time=last_seen or "Pending first scan",
        eta_range=None,
        advisory_note="Last reported checkpoint only; reports may be delayed. No live GPS or assurance of safety." + (" Simulated demo data." if group.simulated else "")
    )

@router.delete("/share/{token}")
async def revoke_family_share(token: str, group_code: str, db: AsyncSession = Depends(get_db)):
    share = (await db.execute(select(ShareToken).join(Group).where(ShareToken.token == token, Group.code == group_code))).scalar_one_or_none()
    if not share: raise HTTPException(404, "Share not found")
    await db.delete(share)
    await db.commit()
    return {"revoked": True}
