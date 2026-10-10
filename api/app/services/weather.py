from app.rules.settings import RULES
import time
from typing import Dict, Any, Optional
import httpx
from app.config import get_settings

settings = get_settings()

_weather_cache: Dict[int, Dict[str, Any]] = {}

def evaluate_r5_weather(weather_data: Dict[str, Any], checkpoint_name: str) -> Optional[Dict[str, Any]]:
    """
    R5: Weather Rule
    Next checkpoint, next 6 h:
      - Rain >= 5 mm/h -> watch
      - Thunderstorm (codes 95, 96, 99) OR Wind Gusts >= 50 km/h OR Temp <= 0 °C on exposed stretch -> urgent
    """
    if not weather_data:
        return None

    rain_max = weather_data.get("rain_max_mm", 0.0)
    wind_gusts_max = weather_data.get("wind_gusts_max_kmh", 0.0)
    temp_min = weather_data.get("temp_min_c", 10.0)
    weather_codes = weather_data.get("weather_codes", [])

    is_thunderstorm = any(code in RULES["R5"]["codes"] for code in weather_codes)
    is_freezing = temp_min <= RULES["R5"]["temp_c"]
    is_high_winds = wind_gusts_max >= RULES["R5"]["gust_kmh"]

    if is_thunderstorm or is_high_winds or is_freezing:
        reason_parts = []
        if is_thunderstorm: reason_parts.append("Thunderstorms (Codes 95/96/99)")
        if is_high_winds: reason_parts.append(f"High Gusts ({wind_gusts_max} km/h)")
        if is_freezing: reason_parts.append(f"Sub-zero ({temp_min} °C)")

        return {
            "rule_id": "R5",
            "severity": "urgent",
            "message_en": (
                f"Severe weather warning at {checkpoint_name}: {', '.join(reason_parts)}. "
                "Forecast threshold reached; request current advice from staff. Shelter locations and route safety are not verified by this app."
            ),
            "message_hi": (
                f"{checkpoint_name} पर गंभीर मौसम की चेतावनी: {', '.join(reason_parts)}। "
                "पूर्वानुमान सीमा पार हुई; कर्मचारियों से वर्तमान सलाह लें। ऐप आश्रय या मार्ग की सुरक्षा सत्यापित नहीं करता।"
            ),
            "data": {
                "rain_max_mm": rain_max,
                "wind_gusts_max": wind_gusts_max,
                "temp_min_c": temp_min,
                "weather_codes": weather_codes
            }
        }
    elif rain_max >= RULES["R5"]["rain_mm"]:
        return {
            "rule_id": "R5",
            "severity": "watch",
            "message_en": (
                f"Heavy rain expected at {checkpoint_name} ({rain_max} mm/h). "
                "Forecast threshold reached; seek current local advice. This is not a route safety assessment."
            ),
            "message_hi": (
                f"{checkpoint_name} पर भारी वर्षा ({rain_max} मिमी/घंटा) की संभावना। "
                "रास्ता फिसलन भरा है, सावधानी से चलें।"
            ),
            "data": {"rain_max_mm": rain_max}
        }

    return None

async def get_checkpoint_weather(checkpoint_id: int, lat: float, lon: float, checkpoint_name: str) -> Dict[str, Any]:
    """Six-hour model forecast; unavailable fields never become invented readings.

    Provider does not supply model issuance time in this endpoint. Retrieval time
    is explicitly separate and the server cache is process-local (browser saves
    downloaded responses for offline use).
    """
    from datetime import datetime, timezone, timedelta
    import math
    now_ts = time.time()
    cached = _weather_cache.get(checkpoint_id)
    if cached and now_ts - cached["timestamp"] < settings.WEATHER_CACHE_TTL_SECONDS:
        return cached["data"]
    params = {"latitude": lat, "longitude": lon,
              "hourly": "temperature_2m,precipitation,weather_code,wind_gusts_10m",
              "forecast_hours": 6, "timezone": "UTC"}
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(settings.OPEN_METEO_API_URL, params=params)
            resp.raise_for_status()
            hourly = resp.json().get("hourly", {})
            names = ("temperature_2m", "precipitation", "wind_gusts_10m", "weather_code")
            arrays = [hourly.get(name, [])[:6] for name in names]
            times = hourly.get("time", [])[:6]
            if not times or any(len(a) != len(times) for a in arrays):
                raise ValueError("Incomplete forecast")
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for a in arrays for x in a):
                raise ValueError("Unavailable forecast values")
            temps, rains, gusts, codes = arrays
            start = datetime.fromisoformat(times[0]).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(times[-1]).replace(tzinfo=timezone.utc) + timedelta(hours=1)
            retrieved = datetime.now(timezone.utc).isoformat()
            summary = {"checkpoint_id": checkpoint_id, "temp_current_c": temps[0],
                       "temp_min_c": min(temps), "rain_max_mm": max(rains),
                       "wind_gusts_max_kmh": max(gusts), "weather_codes": codes,
                       "status": "active", "fetched_at": retrieved, "retrieved_at": retrieved,
                       "issue_time": None, "issue_time_note": "Not supplied by provider",
                       "valid_from": start.isoformat(), "valid_until": end.isoformat(),
                       "source": "Open-Meteo", "source_url": "https://open-meteo.com/",
                       "licence": "CC BY 4.0", "forecast_timezone": "UTC",
                       "hourly": hourly, "is_observation": False}
            summary["r5_flag"] = evaluate_r5_weather(summary, checkpoint_name)
            _weather_cache[checkpoint_id] = {"timestamp": now_ts, "data": summary}
            return summary
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        pass
    if cached:
        return {**cached["data"], "status": "stale", "r5_flag": None}
    return {"checkpoint_id": checkpoint_id, "status": "unavailable", "r5_flag": None,
            "issue_time": None, "retrieved_at": None, "source": "Open-Meteo"}
