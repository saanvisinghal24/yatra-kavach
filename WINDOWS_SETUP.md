# Windows setup

Install Python 3.12 (include the Python launcher) and Node.js 22 or 24 LTS. Reopen PowerShell. Extract the ZIP to a writable folder. In that folder:

```powershell
py -3.12 --version
node --version
npm --version
py -3.12 scripts/bootstrap.py
.\.venv\Scripts\python.exe scripts/start.py --preview
```

Open http://localhost:5173. `--preview` builds the real service worker; the development server alone is not an offline demonstration. No virtual-environment activation or PowerShell execution-policy change is necessary. The `.ps1` wrappers are optional.

The local `.env` contains generated staff emails/passwords. Keep it private. Bootstrap never replaces it or silently rotates passwords. Use `/control` to sign in. Stop all services with Ctrl+C before relaunching. Data survives a normal stop/restart in `local.sqlite3`.

Common errors:

- `py` missing: repair the Python installation with the launcher enabled. If using Python 3.11, replace `py -3.12` with `py -3.11`.
- Unsupported Node/Python: use one of the versions above. The launcher validates them before installation.
- Dependency download failure: restore internet/proxy access and rerun bootstrap. Do not use skip options unless dependencies are already installed.
- Port 8000 or 5173 busy: stop your previous project terminal; identify the owner before terminating another process.
- Existing production `.env`: local bootstrap refuses it. Preserve it elsewhere privately and use a separate extracted project for a local demo.
- Database already contains tables but Alembic reports no migration: do not stamp a real database blindly. For an expendable local demo, stop servers, preserve the SQLite file under another name, and rerun bootstrap. Never apply this to production data.
- Camera denied: allow camera permission. A second phone needs a trusted HTTPS deployment; localhost on the laptop is not localhost on the phone. Manual code entry remains available.
- Old PWA after upgrade: reconnect, reload and accept the new version. Preserve/sync the queue before clearing site storage, as clearing storage deletes unsent records.

Windows commands are supplied and reviewed, but this delivery was exercised on Linux; native PowerShell and real Windows camera tests remain user-owned checks.
