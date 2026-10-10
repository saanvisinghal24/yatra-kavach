from app.rules.settings import RULES
from datetime import datetime, timezone, time, timedelta
from typing import List, Dict, Any, Optional
import math

class RuleFlag:
    def __init__(
        self,
        rule_id: str,
        severity: str,
        message_en: str,
        message_hi: str,
        checkpoint_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.message_en = message_en
        self.message_hi = message_hi
        self.checkpoint_id = checkpoint_id
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message_en": self.message_en,
            "message_hi": self.message_hi,
            "checkpoint_id": self.checkpoint_id,
            "data": self.data
        }

def evaluate_r1_fast_ascent(
    last_checkin: Dict[str, Any],
    prev_checkin: Dict[str, Any],
    curr_checkpoint: Dict[str, Any]
) -> Optional[RuleFlag]:
    """
    R1: Fast Ascent
    Trigger: Segment elapsed time < 60% of min_minutes AND checkpoint altitude >= 3000 m.
    Severity: watch
    NOTE: Placeholder threshold; requires clinician and rescue-team review (ADR-002).
    """
    alt = curr_checkpoint.get("altitude_m", 0)
    min_mins = curr_checkpoint.get("min_minutes", 0)
    if alt < RULES["R1"]["altitude_m"] or min_mins <= 0:
        return None

    t1 = prev_checkin["client_ts"]
    t2 = last_checkin["client_ts"]
    elapsed_minutes = (t2 - t1).total_seconds() / 60.0

    threshold = RULES["R1"]["fraction"] * min_mins
    if 0 < elapsed_minutes < threshold:
        return RuleFlag(
            rule_id="R1",
            severity="watch",
            checkpoint_id=curr_checkpoint["id"],
            message_en=(
                f"Ascent too rapid: completed segment to {curr_checkpoint['name_en']} ({alt} m) in "
                f"{int(elapsed_minutes)} min (minimum expected {min_mins} min, threshold {int(threshold)} min). "
                "Risk of Acute Mountain Sickness (AMS). Rest and monitor breathing."
            ),
            message_hi=(
                f"अत्यधिक तीव्र चढ़ाई: {curr_checkpoint['name_hi']} ({alt} मी) तक का मार्ग मात्र {int(elapsed_minutes)} मिनट "
                f"में पूरा किया (सामान्य न्यूनतम {min_mins} मिनट)। ऊंचाई की बीमारी (AMS) का जोखिम है। विश्राम करें।"
            ),
            data={
                "elapsed_minutes": elapsed_minutes,
                "min_minutes": min_mins,
                "threshold_minutes": threshold,
                "altitude_m": alt
            }
        )
    return None

def evaluate_r2_slow_overdue(
    last_checkin: Dict[str, Any],
    next_checkpoint: Dict[str, Any],
    now: datetime,
    grace_minutes: int = RULES["R2"]["grace_minutes"]
) -> Optional[RuleFlag]:
    """
    R2: Slow / Overdue
    Trigger:
      - Elapsed > 125% of max_minutes -> watch
      - Elapsed > 175% of max_minutes + grace -> urgent
    """
    max_mins = next_checkpoint.get("max_minutes", 0)
    if max_mins <= 0:
        return None

    last_ts = last_checkin["client_ts"]
    if last_ts.tzinfo is None and now.tzinfo is not None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    elif last_ts.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    elapsed_mins = (now - last_ts).total_seconds() / 60.0

    urgent_threshold = (RULES["R2"]["urgent_factor"] * max_mins) + grace_minutes
    watch_threshold = RULES["R2"]["watch_factor"] * max_mins

    if elapsed_mins > urgent_threshold:
        return RuleFlag(
            rule_id="R2",
            severity="urgent",
            checkpoint_id=next_checkpoint["id"],
            message_en=(
                f"Critically overdue towards {next_checkpoint['name_en']}: {int(elapsed_mins)} min elapsed "
                f"(max expected {max_mins} min, critical threshold {int(urgent_threshold)} min)."
            ),
            message_hi=(
                f"{next_checkpoint['name_hi']} की ओर गंभीर रूप से विलंबित: {int(elapsed_mins)} मिनट बीत चुके हैं "
                f"(अधिकतम अपेक्षित {max_mins} मिनट)।"
            ),
            data={
                "elapsed_minutes": elapsed_mins,
                "max_minutes": max_mins,
                "urgent_threshold": urgent_threshold
            }
        )
    elif elapsed_mins > watch_threshold:
        return RuleFlag(
            rule_id="R2",
            severity="watch",
            checkpoint_id=next_checkpoint["id"],
            message_en=(
                f"Segment progress slow towards {next_checkpoint['name_en']}: {int(elapsed_mins)} min elapsed "
                f"(expected maximum {max_mins} min)."
            ),
            message_hi=(
                f"{next_checkpoint['name_hi']} की ओर धीमी प्रगति: {int(elapsed_mins)} मिनट बीत चुके हैं "
                f"(अपेक्षित अधिकतम {max_mins} मिनट)।"
            ),
            data={
                "elapsed_minutes": elapsed_mins,
                "max_minutes": max_mins,
                "watch_threshold": watch_threshold
            }
        )
    return None

def evaluate_r3_cutoff(
    last_checkin: Dict[str, Any],
    curr_checkpoint: Dict[str, Any],
    next_checkpoint: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None
) -> Optional[RuleFlag]:
    """
    R3: Cutoff Rule
    Trigger: Arrived after cutoff time OR projected arrival is after cutoff time.
    Severity: watch
    """
    # Check if arrived after cutoff at current checkpoint
    cutoff_str = curr_checkpoint.get("cutoff_time")
    if cutoff_str:
        h, m = map(int, cutoff_str.split(":"))
        checkin_time = last_checkin["client_ts"].time()
        cutoff_time = time(h, m)
        if checkin_time > cutoff_time:
            return RuleFlag(
                rule_id="R3",
                severity="watch",
                checkpoint_id=curr_checkpoint["id"],
                message_en=(
                    f"Arrived at {curr_checkpoint['name_en']} after cutoff ({cutoff_str}). "
                    "Do not proceed further in deteriorating light. Take shelter here."
                ),
                message_hi=(
                    f"{curr_checkpoint['name_hi']} पर कटऑफ समय ({cutoff_str}) के बाद पहुंचे। "
                    "अंधेरे में आगे न बढ़ें, यहीं विश्राम स्थल में रुकें।"
                ),
                data={"cutoff_time": cutoff_str, "arrival_time": checkin_time.strftime("%H:%M")}
            )

    # Check projected cutoff at next checkpoint
    if next_checkpoint and next_checkpoint.get("cutoff_time") and now:
        n_cutoff_str = next_checkpoint["cutoff_time"]
        nh, nm = map(int, n_cutoff_str.split(":"))
        next_cutoff_time = time(nh, nm)
        expected_arrival = (now + timedelta(minutes=next_checkpoint.get("min_minutes", 60))).time()
        if expected_arrival > next_cutoff_time:
            return RuleFlag(
                rule_id="R3",
                severity="watch",
                checkpoint_id=next_checkpoint["id"],
                message_en=(
                    f"Projected to miss cutoff at {next_checkpoint['name_en']} ({n_cutoff_str}). "
                    "Pace is insufficient before nightfall."
                ),
                message_hi=(
                    f"{next_checkpoint['name_hi']} पर कटऑफ समय ({n_cutoff_str}) चूकने की संभावना है।"
                ),
                data={"next_cutoff": n_cutoff_str, "projected_arrival": expected_arrival.strftime("%H:%M")}
            )
    return None

def evaluate_r4_night_on_trail(
    last_checkin: Dict[str, Any],
    next_checkpoint: Dict[str, Any],
    now: datetime,
    sunset_time: time
) -> Optional[RuleFlag]:
    """
    R4: Night on Trail
    Trigger: Projected movement on trail after calculated sunset time (Astral).
    Severity: watch
    """
    est_duration_mins = next_checkpoint.get("max_minutes", 60)
    projected_finish = (now + timedelta(minutes=est_duration_mins)).time()

    if projected_finish > sunset_time and now.time() < sunset_time:
        return RuleFlag(
            rule_id="R4",
            severity="watch",
            checkpoint_id=next_checkpoint["id"],
            message_en=(
                f"Nightfall hazard: estimated arrival at {next_checkpoint['name_en']} is after sunset "
                f"({sunset_time.strftime('%H:%M')}). Walking high ridges at night carries hypothermia risk."
            ),
            message_hi=(
                f"सूर्यास्त के बाद मार्ग पर रहने का जोखिम: {next_checkpoint['name_hi']} तक पहुंचने का समय सूर्यास्त "
                f"({sunset_time.strftime('%H:%M')}) के बाद होगा। रात में ठंड और मार्ग भटकने का गंभीर खतरा है।"
            ),
            data={
                "sunset_time": sunset_time.strftime("%H:%M"),
                "projected_finish": projected_finish.strftime("%H:%M")
            }
        )
    return None

def evaluate_r6_congestion(
    segment_key: str,
    people_in_segment: int,
    capacity_hint: Optional[int],
    checkpoint_id: int
) -> Optional[RuleFlag]:
    """
    R6: Congestion
    Trigger: People currently in segment > capacity_hint
    Severity: watch
    """
    if not capacity_hint or capacity_hint <= 0:
        return None

    if people_in_segment > capacity_hint:
        return RuleFlag(
            rule_id="R6",
            severity="watch",
            checkpoint_id=checkpoint_id,
            message_en=(
                f"Trail bottleneck: {people_in_segment} pilgrims currently in segment "
                f"(safe capacity hint: {capacity_hint}). Expect heavy delays."
            ),
            message_hi=(
                f"मार्ग पर अत्यधिक भीड़: इस खंड में वर्तमान में {people_in_segment} तीर्थयात्री हैं "
                f"(सुरक्षित क्षमता: {capacity_hint})। कृपया धैर्य रखें।"
            ),
            data={"people_in_segment": people_in_segment, "capacity_hint": capacity_hint}
        )
    return None

def evaluate_r8_missing(
    last_checkin: Dict[str, Any],
    next_checkpoint: Dict[str, Any],
    now: datetime,
    grace_minutes: int = RULES["R8"]["grace_minutes"]
) -> Optional[RuleFlag]:
    """
    R8: Extended reporting delay; follow-up required
    Trigger: No check-in past expected window + extended grace.
    Outputs: last checkpoint and precise search window between CP N and N+1.
    Severity: urgent
    """
    max_mins = next_checkpoint.get("max_minutes", 60)
    missing_threshold = (RULES["R8"]["factor"] * max_mins) + grace_minutes

    last_ts = last_checkin["client_ts"]
    if last_ts.tzinfo is None and now.tzinfo is not None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    elif last_ts.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    elapsed_mins = (now - last_ts).total_seconds() / 60.0

    if elapsed_mins > missing_threshold:
        search_window_start = last_checkin["client_ts"] + timedelta(minutes=max_mins)
        return RuleFlag(
            rule_id="R8",
            severity="urgent",
            checkpoint_id=next_checkpoint["id"],
            message_en=(
                f"Extended reporting delay: {int(elapsed_mins)} min since last scan. Connectivity delay is possible; missing status is not established. "
                f"Last reported segment between {last_checkin.get('checkpoint_name', 'CP')} and {next_checkpoint['name_en']}. "
                f"Expected arrival was {search_window_start.strftime('%H:%M')}."
            ),
            message_hi=(
                f"रिपोर्ट में देरी: अंतिम स्कैन से {int(elapsed_mins)} मिनट। नेटवर्क में देरी संभव है; लापता होना सिद्ध नहीं है। "
                f"तलाशी क्षेत्र: {last_checkin.get('checkpoint_name', 'CP')} और {next_checkpoint['name_hi']} के बीच।"
            ),
            data={
                "elapsed_minutes": elapsed_mins,
                "missing_threshold": missing_threshold,
                "last_checkpoint_id": last_checkin.get("checkpoint_id"),
                "search_segment_from": last_checkin.get("checkpoint_name"),
                "search_segment_to": next_checkpoint["name_en"],
                "search_window_start": search_window_start.isoformat(),
                "search_window_end": now.isoformat()
            }
        )
    return None

def evaluate_r9_headcount_drop(
    current_headcount: int,
    previous_headcount: int,
    unresolved_duration_mins: float = 0.0,
    checkpoint_id: Optional[int] = None
) -> Optional[RuleFlag]:
    """
    R9: Head Count Drop
    Trigger: Count at checkpoint < previous count.
    Severity: watch, escalated to urgent if unresolved for 30 minutes.
    """
    if current_headcount < previous_headcount:
        dropped = previous_headcount - current_headcount
        severity = "urgent" if unresolved_duration_mins >= RULES["R9"]["urgent_minutes"] else "watch"
        return RuleFlag(
            rule_id="R9",
            severity=severity,
            checkpoint_id=checkpoint_id,
            message_en=(
                f"Headcount drop detected: party size reduced from {previous_headcount} to {current_headcount} "
                f"({dropped} member(s) separated). "
                + ("URGENT: Separation unresolved for > 30 minutes!" if severity == "urgent" else "Verify stragglers immediately.")
            ),
            message_hi=(
                f"दल के सदस्यों की संख्या में कमी: संख्या {previous_headcount} से घटकर {current_headcount} हुई "
                f"({dropped} सदस्य पीछे छूटे)। "
                + ("अति-आवश्यक: 30 मिनट से अधिक समय से सदस्य लापता हैं!" if severity == "urgent" else "तुरंत जांच करें।")
            ),
            data={
                "current_headcount": current_headcount,
                "previous_headcount": previous_headcount,
                "dropped_count": dropped,
                "unresolved_duration_mins": unresolved_duration_mins
            }
        )
    return None

def calculate_median_eta(
    checkpoint_a_id: int,
    checkpoint_b_id: int,
    historical_durations: List[float],
    min_minutes: int,
    max_minutes: int
) -> tuple[int, int]:
    """
    ETA Calculation:
    Median of past segment durations for that checkpoint pair (minimum sample of 5),
    falling back to min_minutes - max_minutes range.
    """
    if len(historical_durations) >= 5:
        sorted_d = sorted(historical_durations)
        mid = len(sorted_d) // 2
        median = sorted_d[mid] if len(sorted_d) % 2 != 0 else (sorted_d[mid - 1] + sorted_d[mid]) / 2.0
        # Show as +/- 15% range around median
        return int(median * 0.88), int(median * 1.15)
    return min_minutes, max_minutes
