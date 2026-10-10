# Verification — corrected hackathon build, 10 October 2026

## Executed here
- Backend pytest suite: **51 passed** (SQLite test database).
- Frontend Vitest suite: **12 passed** across 4 files.
- TypeScript compilation and Vite production/PWA build: **passed**.
- Live API: admin, health, police, rescue and volunteer logins and session lookup: **passed**. Dashboard summary/groups, poster generation, analytics and incident list returned 200. Registration returned 201 and the generated pass code could be retrieved.
- Chromium browser smoke test on development build: **passed**.
- Chromium browser smoke test on production preview: **passed**, including:
  - Opening page, admin sign-in and control-room map.
  - Signed checkpoint poster endpoint.
  - Complete three-step registration, visible/decoded QR image and pass page.
  - Pilgrim map and checkpoint entry.
  - Browser offline mode: local scan save, reconnect, batch sync and verification of the last checkpoint on the server.
  - Volunteer sign-in and redirect away from control-room routes.
  - 390px mobile page without horizontal document overflow.
  - No uncaught browser page errors during the tested flows.
- Desktop/mobile screenshots visually inspected; elevation labels adjusted to avoid overlap.

## Reproduce
Start the app using `scripts/start.py --preview`. In `api`, run `../.venv/bin/python -m pytest tests -q` (use the Windows venv equivalent on Windows). In `web`, run `npm test`, `npm run build`, and `npm run test:smoke` after installing Playwright Chromium with `npx playwright install chromium`. Smoke tests create simulated records and capture screenshots under `web/test-results`.

The verification environment was Linux, Python 3.12 and Node.js 24. The Windows launcher was reviewed but was not executed on a Windows machine. Browser testing used Chromium 134 after newer browser binary downloads failed in this environment.

## Boundaries
Not tested here: PostgreSQL deployment, physical phone camera scans, real-device GPS, actual mountain connectivity, external emergency messaging, or field navigation. Basemap tiles are externally served; the checkpoint layer/overview remains available without tiles. Map coordinates are indicative demo seed data. This report does not certify production or field safety. Earlier audit JSONs in docs/audits belong to the incoming project and are not evidence for this revision.
