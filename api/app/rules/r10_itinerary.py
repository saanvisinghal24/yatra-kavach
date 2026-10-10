from app.rules.settings import RULES
from typing import List, Dict, Any, Optional

def evaluate_r10_itinerary(
    planned_stops: List[Dict[str, int]],
    checkpoints_by_id: Dict[int, Any]
) -> List[Dict[str, Any]]:
    """
    R10: Itinerary Advisory Rule.
    Trigger: Planned sleeping altitude gain > 500 m/day above 3000 m.
    Severity: info (registration advisory).
    Pure function, no I/O.
    
    NOTE: 500 m/day threshold is a standard mountaineering heuristic placeholder.
    Requires clinician and rescue-team review (see docs/DECISIONS.md ADR-002).
    """
    advisories = []
    if len(planned_stops) < 2:
        return advisories

    sorted_stops = sorted(planned_stops, key=lambda s: s["day"])
    for i in range(1, len(sorted_stops)):
        prev_stop = sorted_stops[i - 1]
        curr_stop = sorted_stops[i]
        
        prev_cp = checkpoints_by_id.get(prev_stop["checkpoint_id"])
        curr_cp = checkpoints_by_id.get(curr_stop["checkpoint_id"])
        
        if not prev_cp or not curr_cp:
            continue
            
        prev_alt = prev_cp.altitude_m if hasattr(prev_cp, "altitude_m") else prev_cp["altitude_m"]
        curr_alt = curr_cp.altitude_m if hasattr(curr_cp, "altitude_m") else curr_cp["altitude_m"]
        
        day_diff = max(1, curr_stop["day"] - prev_stop["day"])
        
        # Calculate altitude gain above 3,000m threshold
        gain_above_threshold = max(0, curr_alt - max(prev_alt, RULES["R10"]["altitude_m"]))
        gain_per_day = gain_above_threshold / day_diff
        
        # Trigger condition: sleeping above 3000m and gaining > 500m/day above 3000m
        if curr_alt >= RULES["R10"]["altitude_m"] and gain_per_day > RULES["R10"]["sleep_gain_m"]:
            prev_name = getattr(prev_cp, 'name_en', None) or (prev_cp.get('name_en', 'Day start') if isinstance(prev_cp, dict) else 'Day start')
            curr_name = getattr(curr_cp, 'name_en', None) or (curr_cp.get('name_en', 'Day end') if isinstance(curr_cp, dict) else 'Day end')
            advisories.append({
                "rule_id": "R10",
                "severity": "info",
                "message_en": (
                    f"Planned sleep altitude gain of {int(gain_per_day)} m/day from "
                    f"{prev_name} ({prev_alt} m) to "
                    f"{curr_name} ({curr_alt} m) "
                    "exceeds the recommended 500 m/day above 3,000 m. Allow an acclimatization day."
                ),
                "message_hi": (
                    f"3,000 मीटर से ऊपर प्रतिदिन {int(gain_per_day)} मीटर की ऊंचाई वृद्धि अनुशंसित 500 मीटर/दिन से अधिक है। "
                    "ऊंचाई की बीमारी (AMS) से बचाव के लिए एक दिन का अनुकूलन (acclimatization) विश्राम लें।"
                ),
                "altitude_gain_m": int(gain_per_day),
                "details": {
                    "from_checkpoint_id": prev_stop["checkpoint_id"],
                    "to_checkpoint_id": curr_stop["checkpoint_id"],
                    "from_altitude_m": prev_alt,
                    "to_altitude_m": curr_alt,
                    "gain_above_threshold_m": gain_above_threshold,
                    "days": day_diff
                }
            })

    return advisories
