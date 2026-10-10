# Deployment

## Local PostgreSQL with Docker

Docker Engine/Desktop with Compose is required. Run local bootstrap first to generate private credentials. In `.env`, fill `POSTGRES_PASSWORD` with a random URL-safe password of at least 16 characters. The local Compose file overrides database URLs inside its containers, keeping SQLite separate.

```sh
docker compose -f docker-compose.local.yml up -d --build
cd web
npm run build
npm run preview -- --host 127.0.0.1 --port 5173 --strictPort
```

The container API is at localhost:8000 and the web preview proxies `/api`. Do not run `scripts/start.py` concurrently, as it also binds port 8000. Stop with `docker compose -f docker-compose.local.yml down`; do not add `-v` unless intentionally destroying the disposable database.

## VPS production configuration

1. Set DNS A/AAAA records to the server; publish AAAA only with working IPv6. Install Docker/Compose and allow TCP 80/443 and UDP 443.
2. Copy `.env.example` to a private `.env` **in a separate production checkout**. Fill DOMAIN (hostname only), PUBLIC_ORIGIN (`https://hostname`) and CONTACT_EMAIL (monitored address).
3. Generate distinct secrets locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Fill SECRET_KEY, JWT_SECRET and QR_HMAC_SECRET; generate POSTGRES_PASSWORD separately.
4. Fill PostgreSQL names and URLs: `postgresql+asyncpg://USER:URL_ENCODED_PASSWORD@db:5432/DB` and `postgresql+psycopg://USER:URL_ENCODED_PASSWORD@db:5432/DB`. Keep ENVIRONMENT=production, DEBUG=false. Set DEMO_MODE=true only for a deliberately simulated demo instance.
5. Fill all five STAFF_*_EMAIL/PASSWORD pairs with private accounts. Configure phone/SMS numbers only for a real monitored contact; empty values are intentional defaults. Notifications do not prove dispatch.

```sh
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 api sweep
```

API startup applies migrations then idempotent trail/staff seed. A separate worker runs sweeps. Caddy serves the SPA, proxies API/SSE without buffering, obtains HTTPS certificates and stores them persistently. PostgreSQL is not published on a host port. Verify `/health`, staff sign-in, permissions, live SSE reconnect and a real restart-persistence drill before use.

## QR generation

For a local fixture, after bootstrap and simulated registrations:

```sh
.venv/bin/python scripts/gen_checkpoint_qr.py --allow-local --output qr/local
.venv/bin/python -m pip install zxing-cpp==2.3.0
.venv/bin/python scripts/test_qr_roundtrip.py qr/local
```

Local posters visibly say LOCAL DEMO. They embed tokens signed by that private installation; regenerate after installation or key rotation. They are not production passes. Production generation omits `--allow-local` and requires the real HTTPS PUBLIC_ORIGIN and QR_HMAC_SECRET plus access to the same database. Do not copy local SQLite data or development secrets to production. Authenticated `/admin/posters` also exposes printable posters. `/volunteer-guide` is the bilingual A4 instruction page.

## Render alternative

Provision managed PostgreSQL, a Docker API service from `api/`, and a background worker using the same image and environment with command `python -m app.services.worker`. Use the provider's internal PostgreSQL hostname in both URL drivers. The API listens on port 8000.

Build a Docker web service from `web/` with build arguments VITE_PUBLIC_ORIGIN and VITE_CONTACT_EMAIL. Set API_UPSTREAM to the internal API host and port. Override its command to `caddy run --config /etc/caddy/Caddyfile.render`. Render supplies HTTPS and PORT; configure the custom domain and PUBLIC_ORIGIN consistently. Keep browser requests same-origin through the web proxy. This deployment recipe was not executed against Render in this environment; validate private networking and the service port settings there.

## Release gate

Docker/PostgreSQL and public HTTPS deployment could not be executed in this runtime. Windows native execution, real-phone offline/camera tests, PostgreSQL migrations/restart, backup/restore drills, legal review, route review and clinical/rescue threshold review remain explicit release gates. No public deployment was performed. See TEST_REPORT.md for the checks actually run.
