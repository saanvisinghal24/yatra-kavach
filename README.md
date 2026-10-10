# Corrected hackathon build

**Windows: extract into a new folder and double-click `START_WINDOWS.cmd`.**
Open http://localhost:5173. Setup creates private staff credentials in `LOCAL_CREDENTIALS.txt`.
Read [HACKATHON_START.md](HACKATHON_START.md) for the demo steps and fixes.

# Yatra Kavach

Checkpoint-based **simulated hackathon prototype** for Manimahesh, Chamba, Himachal Pradesh. Proposed checkpoints: Hadsar → Dhancho → Sundrasi → Gauri Kund → Manimahesh Lake, then return and final Hadsar exit. These are not confirmed staffed facilities. Other yatras are planned and cannot register.

React/TypeScript/Vite PWA, FastAPI, SQLAlchemy/Alembic and PostgreSQL production configuration. SQLite is a separate local convenience mode. This is not an official emergency service or a field-validated navigation tool.

## Quick start

Install Python **3.11 or 3.12** and Node.js **22 or 24** with npm. Extract the complete ZIP and open a terminal in this folder.

Windows PowerShell:

```powershell
py -3.12 scripts/bootstrap.py
.\.venv\Scripts\python.exe scripts/start.py --preview
```

Linux/macOS:

```sh
python3.12 scripts/bootstrap.py
.venv/bin/python scripts/start.py --preview
```

Open **http://localhost:5173**. `--preview` builds and serves the production PWA for offline tests; omit it for development hot reload. Keep this terminal open; Ctrl+C stops the API, worker and web process together. Use `localhost`, not `127.0.0.1`, in the browser.

Bootstrap generates local random secrets and five staff credentials in private `.env`, creates the local database, migrates, seeds and installs dependencies. Read your own `.env` locally to obtain staff credentials; no fixed shared password is included. An existing `.env` is preserved, including its database selection. Production configuration is refused by local bootstrap. Repeat bootstrap safely; `--skip-deps --skip-web` reuses existing installations.

Staff sign-in: `/control`. Register simulated pilgrims through the public registration form, or use staff Demo mode scenarios. Download offline resources while connected before disconnecting. Pending records stay on that device until uploaded; server receipt and staff acknowledgment are different states. Arrival at the lake does not close the journey.

## Documentation and verification

- [Windows setup](WINDOWS_SETUP.md), [deployment](DEPLOY.md), [operations](OPERATIONS.md)
- [Architecture](ARCHITECTURE.md), [user guide](USER_GUIDE.md), [demo guide](DEMO_GUIDE.md)
- [Sources](DATA_SOURCES.md), [test report](TEST_REPORT.md), [implementation status](IMPLEMENTATION_STATUS.md), [handover](HANDOVER.md)

```sh
cd api
../.venv/bin/python -m pytest tests -q
cd ..
cd web
npm test -- --run
npx tsc --noEmit
npm run build
```

On Windows substitute `.\.venv\Scripts\python.exe` for the Python path. Browser tests require the running app and private staff environment described in the test report.

Offline SOS does not guarantee remote delivery. Forecasts can be stale. Real-route navigation is unavailable without reviewed geometry. The delivered source is a prototype; see executed checks and blocked PostgreSQL/Docker, real-phone and field-validation gates in TEST_REPORT.md.
