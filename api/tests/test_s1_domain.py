import pytest
from datetime import datetime, timezone, timedelta
from app.services.code_gen import generate_group_code, ALPHABET, make_pass_token
from app.rules.r10_itinerary import evaluate_r10_itinerary

def test_group_code_format_and_entropy():
    code = generate_group_code(6)
    assert len(code) == 6
    for char in code:
        assert char in ALPHABET
    # Ensure look-alike characters (0, O, 1, I, L) are never generated
    for bad_char in ["0", "O", "1", "I", "L"]:
        assert bad_char not in code

    pass_token = make_pass_token(code)
    assert pass_token == f"YK1:{code}"

def test_r10_itinerary_triggers_on_excessive_ascent():
    # Day 1: Base (2100m) -> Day 2: High camp (3850m) => Gain of 1750m in 1 day above 3000m
    checkpoints = {
        1: {"id": 1, "name_en": "Base", "altitude_m": 2100},
        2: {"id": 2, "name_en": "Dhancho", "altitude_m": 3000},
        3: {"id": 3, "name_en": "Gaurikund", "altitude_m": 3850}
    }
    stops = [
        {"checkpoint_id": 1, "day": 1},
        {"checkpoint_id": 3, "day": 2}
    ]
    advisories = evaluate_r10_itinerary(stops, checkpoints)
    assert len(advisories) == 1
    assert advisories[0]["rule_id"] == "R10"
    assert advisories[0]["severity"] == "info"
    assert advisories[0]["altitude_gain_m"] == 850
    assert "exceeds the recommended 500 m/day" in advisories[0]["message_en"]
    assert "अनुकूलन" in advisories[0]["message_hi"]

def test_r10_itinerary_passes_safe_schedule():
    # Safe ascent: Base (2100m) -> Day 2: Dhancho (3000m) -> Day 4: Gaurikund (3850m)
    # Gain from 3000m to 3850m over 2 days = 425m/day (below 500m/day)
    checkpoints = {
        1: {"id": 1, "name_en": "Base", "altitude_m": 2100},
        2: {"id": 2, "name_en": "Dhancho", "altitude_m": 3000},
        3: {"id": 3, "name_en": "Gaurikund", "altitude_m": 3850}
    }
    stops = [
        {"checkpoint_id": 1, "day": 1},
        {"checkpoint_id": 2, "day": 2},
        {"checkpoint_id": 3, "day": 4}
    ]
    advisories = evaluate_r10_itinerary(stops, checkpoints)
    assert len(advisories) == 0

@pytest.mark.asyncio
async def test_register_group_api_and_status():
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.seed.seed_trails import seed_data

    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Fetch Yatras
        resp = await client.get("/api/v1/yatras")
        assert resp.status_code == 200
        yatras = resp.json()
        assert len(yatras) >= 3
        manimahesh = next(y for y in yatras if y["slug"] == "manimahesh")
        route_id = manimahesh["routes"][0]["id"]
        checkpoints = manimahesh["routes"][0]["checkpoints"]

        # 2. Register Group with Itinerary
        reg_payload = {
            "consent": True, "yatra_id": manimahesh["id"],
            "route_id": route_id,
            "leader_name": "Vikram Negi",
            "leader_phone": "+919816012345",
            "emergency_name": "Sunita Negi",
            "emergency_phone": "+919816098765",
            "size": 3,
            "planned_start": "2026-08-20T06:00:00Z",
            "members": [
                {"name": "Vikram Negi", "age_band": "18-40", "note": "Group Leader"},
                {"name": "Amit Sharma", "age_band": "18-40", "note": None},
                {"name": "Ramesh Kumar", "age_band": "41-60", "note": "Mild asthma"}
            ],
            "planned_stops": [
                {"checkpoint_id": checkpoints[0]["id"], "day": 1},
                {"checkpoint_id": checkpoints[3]["id"], "day": 2}  # Base to Gaurikund in 1 day (R10 trigger)
            ]
        }
        post_resp = await client.post("/api/v1/groups", json=reg_payload)
        assert post_resp.status_code == 201
        group_data = post_resp.json()
        assert len(group_data["code"]) == 6
        assert group_data["pass_token"] == f"YK1:{group_data['code']}"
        assert len(group_data["advisories"]) == 1
        assert group_data["advisories"][0]["rule_id"] == "R10"

        # 3. Retrieve Group Status
        code = group_data["code"]
        get_resp = await client.get(f"/api/v1/groups/{code}")
        assert get_resp.status_code == 200
        status_data = get_resp.json()
        assert status_data["code"] == code
        assert status_data["leader_name"] == "Vikram Negi"
        assert status_data["next_checkpoint"]["name_en"] == "Hadsar"
        assert len(status_data["open_advice"]) == 1
