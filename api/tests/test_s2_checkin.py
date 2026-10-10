import pytest
import uuid
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.seed.seed_trails import seed_data
from app.services.qr_signer import compute_checkpoint_hmac, make_checkpoint_qr_payload, verify_checkpoint_qr

def test_qr_signing_and_verification():
    secret = __import__("os").environ["QR_HMAC_SECRET"]
    cp_id = 2
    version = 1

    # Valid QR
    qr_payload = make_checkpoint_qr_payload(cp_id, version, secret)
    assert qr_payload.startswith("YK1:CP:2:")
    is_valid, extracted_id, err = verify_checkpoint_qr(qr_payload, version, secret)
    assert is_valid is True
    assert extracted_id == 2
    assert err == ""

    # Tampered signature
    tampered_qr = f"YK1:CP:2:ffffffff"
    is_valid, extracted_id, err = verify_checkpoint_qr(tampered_qr, version, secret)
    assert is_valid is False
    assert "verification failed" in err

    # Malformed format
    bad_qr = "SOME_RANDOM_TEXT"
    is_valid, _, err = verify_checkpoint_qr(bad_qr, version, secret)
    assert is_valid is False
    assert "Malformed" in err

@pytest.mark.asyncio
async def test_idempotent_checkin_batch_ingest():
    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register a test group
        reg_resp = await client.post("/api/v1/groups", json={
            "consent": True, "yatra_id": 1,
            "route_id": 1,
            "leader_name": "Kiran Thakur",
            "leader_phone": "+919816055555",
            "emergency_name": "Prem Thakur",
            "emergency_phone": "+919816044444",
            "size": 2,
            "planned_start": "2026-08-20T07:00:00Z",
            "members": [
                {"name": "Kiran Thakur", "age_band": "18-40", "note": None},
                {"name": "Reena Thakur", "age_band": "18-40", "note": None}
            ]
        })
        group_code = reg_resp.json()["code"]

        # Valid signed QR for Checkpoint 1 (Hadsar Trailhead)
        valid_qr = make_checkpoint_qr_payload(1, 1, __import__("os").environ["QR_HMAC_SECRET"])
        event_id = str(uuid.uuid4())

        batch_payload = {
            "events": [
                {
                    "id": event_id,
                    "group_code": group_code,
                    "checkpoint_id": 1,
                    "signed_qr": valid_qr,
                    "source": "self",
                    "headcount": 2,
                    "client_ts": datetime.now(timezone.utc).isoformat(),
                    "clock_skew_s": 0.5
                }
            ]
        }

        # First Submission -> accepted
        resp1 = await client.post("/api/v1/checkins/batch", json=batch_payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["accepted_count"] == 1
        assert data1["duplicate_count"] == 0
        assert data1["results"][0]["status"] == "accepted"

        # Replay same submission -> duplicate (idempotent, no error)
        resp2 = await client.post("/api/v1/checkins/batch", json=batch_payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["accepted_count"] == 0
        assert data2["duplicate_count"] == 1
        assert data2["results"][0]["status"] == "duplicate"

        # Submission with forged QR signature -> invalid
        forged_id = str(uuid.uuid4())
        forged_payload = {
            "events": [
                {
                    "id": forged_id,
                    "group_code": group_code,
                    "checkpoint_id": 1,
                    "signed_qr": "YK1:CP:1:deadbeef",
                    "source": "self",
                    "headcount": 2,
                    "client_ts": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        resp3 = await client.post("/api/v1/checkins/batch", json=forged_payload)
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["invalid_count"] == 1
        assert data3["results"][0]["status"] == "invalid"
        assert "verification failed" in data3["results"][0]["invalid_reason"]
