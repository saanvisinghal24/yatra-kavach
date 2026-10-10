# Operations

## Ownership and daily checks

Assign a named operator for the control room, incident acknowledgments and monitored contact details before any real pilot. Acknowledgment is a staff action, not dispatch confirmation. Inspect queue delay, last server receipt, expired advisories and overdue-report evidence. A dedicated checkpoint-device heartbeat inventory is not implemented. Connectivity delay must not be interpreted as proof that someone is missing or safe.

```sh
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 api sweep web
```

Avoid publishing logs, exports, `.env`, database dumps or browser storage. Healthchecks cover API HTTP availability, PostgreSQL readiness and worker heartbeat. Investigate an unhealthy worker even when the UI still loads. Do not erase offline storage before unsent events are reconciled.

## Backups and recovery

```sh
sh scripts/backup.sh
sh scripts/restore.sh backups/REPLACE_WITH_ACTUAL_FILE.dump yatra_restore_drill
```

Backup creates a private custom-format PostgreSQL dump atomically. Restore creates a **new** database and fails if it already exists; it never drops production. Review the restored database and test an API instance against it before a planned cutover. Schedule backups externally, encrypt copies before off-host transfer and restrict access. These scripts require Docker/PostgreSQL and have not been exercised here; a real restore drill is a release gate.

RETENTION_DAYS controls application cleanup through the worker: a group is eligible only when both its creation time and the yatra season end are older than the configured cutoff. This is not a simple fixed interval after registration. Backup retention is separate: use an operator-managed 30-day expiry or an approved policy, and ensure restoration does not silently resurrect erased records. Exports downloaded to staff devices require their own deletion policy. The project cannot remotely remove a previously downloaded CSV/PDF.

## Credentials and signing-key rotation

Keep `.env` out of version control and distribute it only through an approved secret manager. Generate new distinct random values locally. JWT_SECRET changes invalidate issued sessions. SECRET_KEY changes can invalidate cryptographic state. QR_HMAC_SECRET changes invalidate existing checkpoint posters: generate and replace every affected poster, then test scans online before resuming. Record the deployment time and notify staff of replacement materials.

Staff seeding is idempotent and does not overwrite existing passwords automatically. Changing STAFF_*_PASSWORD in `.env` alone is not a password-reset workflow for existing accounts; arrange an explicit controlled account update with the administrator. Never reset the database to rotate credentials.

## Local recovery

Stop the launcher with Ctrl+C, preserve `.env` and `local.sqlite3`, and rerun `scripts/start.py --preview`. Bootstrap may be repeated without replacing credentials. Retain a copy before manual database repairs. Only disposable demo databases may be recreated; do not stamp failed migrations or delete data merely to suppress errors.

## Updates

Back up first, review migration changes and test against a restored disposable database, then rebuild containers. Check the worker, auth, family expiry, offline upload and member-level exit accounting after rollout. A previous application image may not support an upgraded database; rollback needs a tested migration/restore plan, not just an old container tag.
