import asyncio
from datetime import date
from sqlalchemy import select
from app.db import async_engine, AsyncSessionLocal, Base
from app.models.trail import Yatra, Route, Checkpoint
from app.models.user import User
from app.config import get_settings
from argon2 import PasswordHasher

ph = PasswordHasher()

async def seed_data():
    settings = get_settings()
    if settings.ENVIRONMENT != "production":
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Yatra).where(Yatra.slug == "manimahesh"))
        if result.scalar_one_or_none():
            from sqlalchemy import update
            await session.execute(update(Yatra).where(Yatra.slug != "manimahesh").values(status="planned"))
            await session.commit()
            print("Database already seeded with trails.")
            return

        print("Seeding initial Himalayan pilgrim trails (Indicative data, verified: false)...")

        # 1. Manimahesh Yatra
        yatra_manimahesh = Yatra(
            slug="manimahesh",
            name_en="Manimahesh Yatra",
            name_hi="मणिमहेश यात्रा",
            district="Chamba",
            season_start=date(2026, 8, 15),
            season_end=date(2026, 9, 15),
            description_en="Sacred high-altitude pilgrimage in the Pir Panjal range to Lake Manimahesh (4,080 m).",
            description_hi="पीर पंजाल श्रृंखला में पवित्र मणिमहेश झील (4,080 मी) की उच्च-पर्वतीय यात्रा।",
            status="active"
        )
        session.add(yatra_manimahesh)
        await session.flush()

        route_manimahesh = Route(
            yatra_id=yatra_manimahesh.id,
            name="Hadsar to Manimahesh Dal Lake",
            type="trek",
            total_distance_km=13.0,
            base_altitude_m=2100,
            max_altitude_m=4080,
            rules_config={
                "min_ascent_rate_m_min": 15,
                "grace_minutes": 20,
                "high_altitude_threshold_m": 3000
            },
            verified=False
        )
        session.add(route_manimahesh)
        await session.flush()

        cp_mm = [
            Checkpoint(
                route_id=route_manimahesh.id, seq=1,
                name_en="Hadsar", name_hi="हड़सर",
                lat=32.3685, lon=76.6041, altitude_m=2100,
                dist_from_prev_km=0.0, min_minutes=0, max_minutes=0,
                cutoff_time="14:00", capacity_hint=600,
                facilities={},
                has_network=True, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_manimahesh.id, seq=2,
                name_en="Dhancho", name_hi="धंचो",
                lat=32.3812, lon=76.6231, altitude_m=3000,
                dist_from_prev_km=6.0, min_minutes=130, max_minutes=170,
                cutoff_time="15:00", capacity_hint=400,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_manimahesh.id, seq=3,
                name_en="Gaurikund", name_hi="गौरीकुंड",
                lat=32.3920, lon=76.6380, altitude_m=3850,
                dist_from_prev_km=5.5, min_minutes=150, max_minutes=210,
                cutoff_time="16:30", capacity_hint=250,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_manimahesh.id, seq=4,
                name_en="Manimahesh Lake", name_hi="मणिमहेश झील",
                lat=32.3982, lon=76.6434, altitude_m=4080,
                dist_from_prev_km=1.5, min_minutes=45, max_minutes=75,
                cutoff_time="17:30", capacity_hint=500,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            )
        ]
        cp_mm[2].seq = 4
        cp_mm[2].name_en = "Gauri Kund"
        cp_mm[2].dist_from_prev_km = 3.0
        cp_mm[2].min_minutes = 90
        cp_mm[2].max_minutes = 130
        cp_mm[3].seq = 5
        cp_mm.insert(2, Checkpoint(route_id=route_manimahesh.id, seq=3,
            name_en="Sundrasi", name_hi="सुंदरासी", lat=32.3866, lon=76.6305,
            altitude_m=3350, dist_from_prev_km=2.5, min_minutes=60, max_minutes=80,
            cutoff_time="16:00", capacity_hint=150, facilities={},
            has_network=False, status="open", qr_key_version=1, verified=False))
        session.add_all(cp_mm)

        # 2. Kinner Kailash Yatra
        yatra_kinner = Yatra(
            slug="kinner-kailash",
            name_en="Kinner Kailash Yatra",
            name_hi="किन्नर कैलाश यात्रा",
            district="Kinnaur",
            season_start=date(2026, 7, 1),
            season_end=date(2026, 8, 15),
            description_en="Tough circumambulation trek in Kinnaur reaching the 79-foot vertical rock Shivling (4,650 m).",
            description_hi="किन्नौर में 79 फीट ऊंचे प्राकृतिक शिवलिंग (4,650 मी) की दुर्गम तीर्थ यात्रा।",
            status="planned"
        )
        session.add(yatra_kinner)
        await session.flush()

        route_kinner = Route(
            yatra_id=yatra_kinner.id,
            name="Tangling to Kinner Kailash Shivling",
            type="trek",
            total_distance_km=19.5,
            base_altitude_m=2000,
            max_altitude_m=4650,
            rules_config={"grace_minutes": 25, "high_altitude_threshold_m": 3000},
            verified=False
        )
        session.add(route_kinner)
        await session.flush()

        cp_kk = [
            Checkpoint(
                route_id=route_kinner.id, seq=1,
                name_en="Tangling", name_hi="तांगलिंग",
                lat=31.5204, lon=78.2711, altitude_m=2000,
                dist_from_prev_km=0.0, min_minutes=0, max_minutes=0,
                cutoff_time="11:00", capacity_hint=300,
                facilities={},
                has_network=True, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_kinner.id, seq=2,
                name_en="Malling", name_hi="मलिंग",
                lat=31.5342, lon=78.2915, altitude_m=2900,
                dist_from_prev_km=5.0, min_minutes=140, max_minutes=200,
                cutoff_time="14:00", capacity_hint=200,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_kinner.id, seq=3,
                name_en="Ganesh Park", name_hi="गणेश पार्क",
                lat=31.5451, lon=78.3120, altitude_m=3800,
                dist_from_prev_km=6.0, min_minutes=180, max_minutes=260,
                cutoff_time="16:00", capacity_hint=150,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_kinner.id, seq=4,
                name_en="Parvati Kund", name_hi="पार्वती कुंड",
                lat=31.5560, lon=78.3305, altitude_m=4300,
                dist_from_prev_km=4.5, min_minutes=150, max_minutes=210,
                cutoff_time="17:00", capacity_hint=100,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            ),
            Checkpoint(
                route_id=route_kinner.id, seq=5,
                name_en="Shivling Summit", name_hi="शिवलिंग दर्शन",
                lat=31.5645, lon=78.3418, altitude_m=4650,
                dist_from_prev_km=4.0, min_minutes=120, max_minutes=180,
                cutoff_time="18:00", capacity_hint=150,
                facilities={},
                has_network=False, status="open", qr_key_version=1, verified=False
            )
        ]
        session.add_all(cp_kk)

        # 3. Shrikhand Mahadev Yatra
        yatra_shrikhand = Yatra(
            slug="shrikhand-mahadev",
            name_en="Shrikhand Mahadev Yatra",
            name_hi="श्रीखंड महादेव यात्रा",
            district="Kullu",
            season_start=date(2026, 7, 7),
            season_end=date(2026, 7, 25),
            description_en="Extreme Himalayan pilgrimage in Kullu ascending over 3,300 vertical meters to 5,160 m.",
            description_hi="कुल्लू में 3,300 मीटर से अधिक की सीधी चढ़ाई वाली अति-दुर्गम 5,160 मीटर की तीर्थ यात्रा।",
            status="planned"
        )
        session.add(yatra_shrikhand)
        await session.flush()

        route_shrikhand = Route(
            yatra_id=yatra_shrikhand.id,
            name="Jaon to Shrikhand Summit",
            type="trek",
            total_distance_km=32.0,
            base_altitude_m=1850,
            max_altitude_m=5160,
            rules_config={"grace_minutes": 30, "high_altitude_threshold_m": 3000},
            verified=False
        )
        session.add(route_shrikhand)
        await session.flush()

        cp_sk_data = [
            (1, "Jaon", "जाओं", 31.4281, 77.4981, 1850, 0.0, 0, 0, "10:00", 400, True),
            (2, "Singhgad", "सिंहगाड", 31.4410, 77.5112, 2100, 3.0, 60, 90, "12:00", 300, True),
            (3, "Thachru", "थाचडू", 31.4580, 77.5320, 3200, 7.0, 240, 330, "16:00", 250, False),
            (4, "Kali Ghati", "काली घाटी", 31.4710, 77.5450, 3650, 3.0, 90, 140, "17:30", 150, False),
            (5, "Bhim Talai", "भीम तलाई", 31.4820, 77.5580, 3500, 2.5, 60, 90, "18:30", 200, False),
            (6, "Bhim Dwar", "भीम द्वार", 31.5020, 77.5810, 4100, 8.0, 220, 300, "15:00", 250, False),
            (7, "Parvati Bagh", "पार्वती बाग", 31.5150, 77.5950, 4400, 3.5, 120, 180, "16:30", 150, False),
            (8, "Shrikhand Summit", "श्रीखंड शिखर", 31.5300, 77.6100, 5160, 5.0, 180, 240, "17:30", 100, False),
        ]
        for seq, ne, nh, lat, lon, alt, dist, mn, mx, co, cap, net in cp_sk_data:
            session.add(Checkpoint(
                route_id=route_shrikhand.id, seq=seq,
                name_en=ne, name_hi=nh, lat=lat, lon=lon, altitude_m=alt,
                dist_from_prev_km=dist, min_minutes=mn, max_minutes=mx,
                cutoff_time=co, capacity_hint=cap,
                facilities={},
                has_network=net, status="open", qr_key_version=1, verified=False
            ))

        for slug, en, hi, district, lat, lon in [
            ("naina-devi", "Naina Devi", "नैना देवी", "Bilaspur",31.306,76.536),
            ("chintpurni", "Chintpurni", "चिंतपूर्णी", "Una",31.805,76.102),
            ("jwalaji", "Jwalaji", "ज्वालाजी", "Kangra",31.875,76.321)]:
            y = Yatra(slug=slug,name_en=en,name_hi=hi,district=district,season_start=date(2026,1,1),season_end=date(2026,12,31),status="planned",description_en="Indicative crowd-mode seed; Navratri operations planned",description_hi="सांकेतिक भीड़ मार्ग; नवरात्रि संचालन नियोजित")
            session.add(y); await session.flush()
            r = Route(yatra_id=y.id,name=en+" queue",type="crowd",total_distance_km=0,base_altitude_m=0,max_altitude_m=0,rules_config={},verified=False)
            session.add(r); await session.flush()
            for seq, label, hindi in [(1,"Entry","प्रवेश"),(2,"Exit","निकास")]:
                session.add(Checkpoint(route_id=r.id,seq=seq,name_en=en+" "+label,name_hi=hi+" "+hindi,lat=lat,lon=lon,altitude_m=0,dist_from_prev_km=0,min_minutes=0,max_minutes=0,capacity_hint=100,facilities={},has_network=False,status="open",qr_key_version=1,verified=False))
        for obj in session.new:
            if isinstance(obj, Checkpoint) and not obj.verified:
                obj.facilities = {}
        await session.commit()
        print("Trail seed completed successfully.")

async def main():
    from app.seed.staff import seed_staff
    await seed_data()
    await seed_staff()

if __name__ == "__main__":
    asyncio.run(main())
