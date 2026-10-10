import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.seed.seed_trails import seed_data
from app.services.weather import evaluate_r5_weather, get_checkpoint_weather

@pytest.mark.asyncio
async def test_symptom_report_lake_louise_and_red_flags():
    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register a group
        reg = await client.post("/api/v1/groups", json={
            "consent": True, "yatra_id": 1,
            "route_id": 1,
            "leader_name": "Rohan Verma",
            "leader_phone": "+919816099999",
            "emergency_name": "Pooja Verma",
            "emergency_phone": "+919816088888",
            "size": 2,
            "planned_start": "2026-08-20T06:00:00Z",
            "members": [
                {"name": "Rohan Verma", "age_band": "18-40", "note": None},
                {"name": "Pooja Verma", "age_band": "18-40", "note": None}
            ]
        })
        code = reg.json()["code"]

        # Case 1: Normal Vitals (score 1)
        resp1 = await client.post("/api/v1/symptom-reports", json={
            "group_code": code,
            "checkpoint_id": 2,
            "headache": 1,
            "stomach": 0,
            "fatigue": 0,
            "dizziness": 0,
            "red_flags": []
        })
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["score"] == 1
        assert d1["advice_level"] == "normal"
        assert d1["emergency_contact_needed"] is False

        # Case 2: Moderate Score (score 7) -> emergency option shown
        resp2 = await client.post("/api/v1/symptom-reports", json={
            "group_code": code,
            "checkpoint_id": 2,
            "headache": 2,
            "stomach": 2,
            "fatigue": 2,
            "dizziness": 1,
            "red_flags": []
        })
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["score"] == 7
        assert d2["advice_level"] == "moderate"
        assert d2["emergency_contact_needed"] is True

        # Case 3: Red Flag (Ataxia / Unsteady walking) -> Severe emergency guidance
        resp3 = await client.post("/api/v1/symptom-reports", json={
            "group_code": code,
            "checkpoint_id": 2,
            "headache": 1,
            "stomach": 0,
            "fatigue": 1,
            "dizziness": 0,
            "red_flags": ["ataxia"]
        })
        assert resp3.status_code == 200
        d3 = resp3.json()
        assert d3["advice_level"] == "severe"
        assert d3["emergency_contact_needed"] is True
        assert "not a diagnosis" in d3["guidance_en"]
        assert "112 / 108" in d3["guidance_en"]

@pytest.mark.asyncio
async def test_emergency_sos_dispatch():
    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Trigger SOS
        sos_resp = await client.post("/api/v1/sos", json={
            "group_code": "TEST01",
            "checkpoint_id": 2,
            "lat": 32.3812,
            "lon": 76.6231,
            "reason": "Severe hypothermia and exhaustion"
        })
        assert sos_resp.status_code == 200
        d = sos_resp.json()
        assert d["status"] == "server_received"
        assert "emergency dispatch are not confirmed" in d["emergency_dispatch"]

@pytest.mark.asyncio
async def test_weather_r5_rule_and_silent_degradation():
    # Severe Weather (Thunderstorm code 95)
    severe_data = {
        "rain_max_mm": 2.0,
        "wind_gusts_max_kmh": 35.0,
        "temp_min_c": 4.0,
        "weather_codes": [95, 80]
    }
    flag = evaluate_r5_weather(severe_data, "Gaurikund")
    assert flag is not None
    assert flag["rule_id"] == "R5"
    assert flag["severity"] == "urgent"
    assert "Thunderstorms" in flag["message_en"]

    # Heavy rain >= 5mm/h -> watch
    rain_data = {
        "rain_max_mm": 6.5,
        "wind_gusts_max_kmh": 20.0,
        "temp_min_c": 8.0,
        "weather_codes": [61]
    }
    flag_rain = evaluate_r5_weather(rain_data, "Dhancho")
    assert flag_rain is not None
    assert flag_rain["severity"] == "watch"

    # Silent degradation on network failure (lat=0, lon=0)
    res = await get_checkpoint_weather(999, 0.0, 0.0, "Test CP")
    assert res is not None
    assert res["status"] in ("active", "stale", "unavailable")
    # Should not produce crash or false alarm
    assert res["r5_flag"] is None

@pytest.mark.asyncio
async def test_family_share_token_flow():
    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate share token
        gen_resp = await client.post("/api/v1/share/generate/TEST01")
        assert gen_resp.status_code == 200
        token = gen_resp.json()["token"]
        assert len(token) == 32  # 128-bit hex string

        # Access share view
        view_resp = await client.get(f"/api/v1/share/{token}")
        assert view_resp.status_code == 200
        vd = view_resp.json()
        assert "group_code" not in vd and "leader_name" not in vd
        assert "reports may be delayed" in vd["advisory_note"]
        assert "GPS" in vd["advisory_note"]
