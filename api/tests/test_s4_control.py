import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.seed.seed_trails import seed_data
from app.models.safety import RiskFlag
from app.db import AsyncSessionLocal
from sqlalchemy import select, delete

@pytest.mark.asyncio
async def test_staff_auth_and_control_room_operations():
    await seed_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Origin":"http://localhost:5173"}) as client:
        # 1. Staff Login
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": __import__("os").environ["STAFF_ADMIN_EMAIL"],
            "password": __import__("os").environ["STAFF_ADMIN_PASSWORD"]
        })
        assert login_resp.status_code == 200
        auth_data = login_resp.json()
        assert "access_token" in auth_data
        assert auth_data["role"] == "admin"
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get Profile
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == __import__("os").environ["STAFF_ADMIN_EMAIL"]

        # 3. Get Dashboard Summary
        summary_resp = await client.get("/api/v1/dashboard/summary")
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        assert "active_groups" in summary_data
        assert "urgent_alerts" in summary_data
        assert "control_status" in summary_data

        # 4. Create and Resolve a Flag
        async with AsyncSessionLocal() as session:
            await session.execute(delete(RiskFlag).where(RiskFlag.group_id == 1, RiskFlag.rule_id == "R_TEST"))
            flag = RiskFlag(
                group_id=1,
                checkpoint_id=2,
                rule_id="R_TEST",
                severity="watch",
                message_en="Test slow flag",
                message_hi="परीक्षण विलंब फ्लैग",
                data={},
                status="open"
            )
            session.add(flag)
            await session.commit()
            flag_id = flag.id

        # Patch flag to resolve
        resolve_resp = await client.patch(f"/api/v1/flags/{flag_id}?action=resolve", headers=headers)
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resolved"

        # 5. Admin Verify Checkpoint
        verify_resp = await client.post("/api/v1/admin/checkpoints/2/verify", headers=headers)
        assert verify_resp.status_code == 200
        assert verify_resp.json()["verified"] is True

        # 6. Export Audit CSV
        csv_resp = await client.get("/api/v1/admin/report.csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["Content-Type"]
        assert "Checkin_UUID" in csv_resp.text
