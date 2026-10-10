> Historical input-repository document. Not current acceptance evidence. Read root TEST_REPORT.md, IMPLEMENTATION_STATUS.md and HANDOVER.md for this delivery.

# Validation — simulated hackathon build

## Executed
- API: `python -m pytest -q` — 41 passed (SQLite fixtures), one dependency deprecation warning.
- Web: `npm test` — 9 passed; `tsc && vite build` passed with VITE_PUBLIC_ORIGIN set to the local test origin.
- Playwright: four browser tests passed, including incident creation/notes across reload and pilgrim status, live incident arrivals and unsaved-note preservation during SSE refresh, health-role admin-action rejection, Hindi staff sign-in/analytics with axe and full registration wizard, group pass, service-worker offline page reload, scan queue, reconnect and sync at 360×640 — passed.
- Browser audit: 18 public/staff/pilgrim screens, no page errors, no horizontal page overflow; axe WCAG A/AA violations corrected and final audit clean.
- Lighthouse: performance 86, accessibility 100, best practices 100 on local production build.
- Current Lighthouse has no PWA score category. Manifest, service-worker control, cached navigation and offline reconnect were checked directly.
- QR generation: five Manimahesh checkpoint posters + five demo passes; all 10 PNGs decoded with zxing-cpp and checkpoint HMACs verified.
- A4 English/Hindi volunteer guide and poster PDFs rendered and visually inspected.
- PostgreSQL Alembic upgrade SQL compiled successfully; no live PostgreSQL connection was available.
- Actual API process restart: write → stop API → start API → read passed on SQLite test storage, including staff assignment/notes/ack and pilgrim/family views.
- SSE connected and refresh events observed on real HTTP during the restart test.
- Shared limiter exercised: auth returns 429 after ten attempts; origin rejection and HSTS/nosniff verified.
- Five scenarios loaded through the API, repeated idempotently; reset preserved staff and non-simulated records. Retention deletion tested.

- Backup script: shell syntax and mocked pg_dump success/failure tests passed; partial files removed and dumps restricted to mode 0600. This does not verify a real PostgreSQL backup.
- Render proxy config now forwards /health to the API and shares VPS security headers; Caddy execution remains unverified.

- Bulk foreground reconnect: 123 queued check-ins drained in 50/50/23 batches; overlapping sync calls coalesced; network failure retains pending events.

## Feature evidence
| Flow | Evidence |
|---|---|
| Registration, pass and R10 | API tests + browser wizard; URL pass QR format test |
| Offline check-ins and headcount | Per-event signatures survive IndexedDB; duplicate replay; browser offline/online flow |
| R1–R10 | Existing table tests plus persisted R1/R9/R7/SOS and scenario R2/R5/R8 tests |
| Volunteer | Authenticated scan source and route restriction; shared queue; persisted checkpoint endpoint |
| Trail, family, control actions | Both-direction API integration test and restart script |
| Incidents, analytics, CSV | Real saved DB rows; endpoint tests and browser page audit |
| PDF | Browser Print / Save PDF for analytics and guide; generated poster PDFs |
| Weather and solar | Cached Open-Meteo client with unavailable/stale state; Astral per-coordinate sunrise/sunset |
| Trust pages | Bilingual privacy/terms, methodology from rules.yaml, empty facts hidden, planned roadmap |

## Not verified here
- Docker/Caddy image execution, ACME certificate issuance, Render, PostgreSQL concurrency/restore and production deployment.
- No Docker executable was present; PostgreSQL initdb refused this root-only runtime. No bypass attempted.
- No production domain or production HMAC secret was supplied. Included `/qr/` files are LOCAL fixtures, not venue-ready posters.
- Real phone camera scanning, Android install prompts, iOS install sheet/SMS behavior and true cellular airplane-mode transitions.
- Live Open-Meteo and Telegram delivery from the deployment network.
- Full linguistic, clinical/rescue and legal review. Some administrative status/technical labels remain English.
- No statutory compliance, official affiliation, real rescue dispatch or verified trail geography is claimed.

## Run on your host
1. Follow DEPLOY.md and start all four services.
2. Run scripts/verify_persistence.py write, restart only API, then run read against PostgreSQL.
3. Run scripts/simulate.py; inspect all five groups and R8 search evidence.
4. Regenerate posters with production DB/origin/secret and run scripts/test_qr_roundtrip.py.
5. Configure Playwright environment: PUBLIC_ORIGIN, STAFF_ADMIN_EMAIL, STAFF_ADMIN_PASSWORD; run npm run test:browser.
6. Run daily backups, a restore drill, and real-phone checks before judging.
