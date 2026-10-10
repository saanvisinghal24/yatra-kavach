> Historical input-repository document. Not current acceptance evidence. Read root TEST_REPORT.md, IMPLEMENTATION_STATUS.md and HANDOVER.md for this delivery.

# Yatra Kavach - Architecture & Design Decisions

This document logs significant architectural decisions, trade-offs, and critical placeholders that require medical or field review.

## ADR-001: Pure Python Deterministic Rules Engine (No LLM in Safety Path)
- **Status:** Locked
- **Context:** High-altitude mountain safety requires 100% explainable, deterministic, zero-hallucination alerts. Network latency or API failure cannot block life-critical evaluations.
- **Decision:** All safety rules (R1 through R10) are pure functions implemented in Python. Alerts contain rule ID, severity, numerical inputs, and exact bilingual strings.
- **Consequence:** Easy unit testing, predictable execution (< 5ms per group), zero external LLM API dependency in emergency workflows.

## ADR-002: Clinical and Rescue Thresholds Review Requirement
- **Status:** Pending Clinical/Rescue Sign-off
- **Context:** Initial thresholds for rules are seeded with standard mountaineering heuristics:
  - R1 Fast Ascent: ascent time < 60% of min segment time above 3000m.
  - R2 Overdue: > 125% of max time (watch), > 175% + 20m grace (urgent).
  - R7 Lake Louise AMS Score: 3-5 mild, 6-9 moderate, 10-12 severe.
  - R8 Missing Window: segment max time + grace window.
  - R10 Sleeping Altitude Gain: > 500m/day above 3000m.
- **Decision:** All thresholds are explicitly marked as placeholders in the codebase.
- **Action Required:** Prior to production deployment with Himachal Pradesh authorities (e.g., SDMA / District Administration), all parameters must be reviewed and calibrated by high-altitude medical specialists and mountain rescue teams (ITBP / NDRF).

## ADR-003: Offline-First Client Architecture (Dexie.js + PWA)
- **Status:** Locked
- **Context:** Mobile coverage may be absent along remote trail segments.
- **Decision:** Pilgrim and volunteer web applications operate as Progressive Web Apps with Workbox precaching and Dexie (IndexedDB) for local scan queues. Every scan is committed locally first before attempting network sync.
- **Consequence:** Full operational capacity in airplane mode. Retries are idempotent via client-generated UUID primary keys.

## ADR-004: Hand-drawn SVG Altitude Profile over Map Tiles for Pilgrims
- **Status:** Locked
- **Context:** Map tile engines (Mapbox, Leaflet, Google Maps) have heavy bundle sizes, consume excessive battery, and require heavy raster/vector tile caching which fails easily offline.
- **Decision:** The primary trail interface for pilgrims is a lightweight, hand-written SVG altitude profile showing checkpoints, current position, cutoff times, and elevation gains. Leaflet is restricted to the Control Room desktop dashboard and code-split into a lazy chunk.
- **Consequence:** Initial pilgrim bundle size stays well within the 250 KB gzipped budget, and battery drain is minimized in cold environments.

## ADR-005: Honest Data & Indicative Seed Labeling
- **Status:** Locked
- **Context:** Exact GPS coordinates, segment distances, and checkpoint altitudes from unofficial sources may be inaccurate in rugged terrain.
- **Decision:** All seeded checkpoints and trail metrics start with `verified: false`. The user interface displays a prominent "Indicative data" note until an authorized administrator verifies the survey coordinates. Simulator data is explicitly flagged as "Demo mode / simulated".

## Dependency Log
| Package | Ecosystem | Rationale |
|---|---|---|
| `fastapi`, `uvicorn` | Backend | High-performance async REST & SSE support |
| `sqlalchemy`, `alembic` | Backend | Type-safe ORM v2 and robust schema migrations |
| `pydantic` | Backend | Runtime schema validation and settings |
| `argon2-cffi`, `pyjwt` | Backend | Secure modern password hashing and JWT staff sessions |
| `slowapi` | Backend | Rate limiting public registration and checkin endpoints |
| `astral` | Backend | Pure Python solar calculations for sunset/night trail alerts |
| `httpx` | Backend | Async HTTP client for Open-Meteo weather fetches |
| `dexie` | Frontend | Ergonomic, transaction-safe IndexedDB wrapper |
| `qr-scanner`, `qrcode` | Frontend | High-performance camera QR scanner and client pass generator |
| `@fontsource/*` | Frontend | Self-hosted typography (Fraunces, IBM Plex, Noto Sans Devanagari) |

## Deployment hardening
- Gunicorn/uvicorn workers behind Caddy; exact-origin CORS and same-site HttpOnly cookies.
- A separate single sweep process prevents per-worker duplicate schedulers. PostgreSQL advisory locks serialize flag updates and event retries.
- SSE sends a one-second refresh event; clients re-query the authoritative DB so multiple workers remain consistent without Redis.
- JSON-subset YAML keeps thresholds and methodology aligned without an extra parser.
- Added gunicorn (production process manager), Pillow/reportlab/qrcode (printable posters), aiosqlite (test fixture engine). Browser/QR audit tools remain optional development tools.
- Clinical thresholds remain unreviewed. No government affiliation, real dispatch, trail verification or legal compliance is claimed.
- Privacy draft reference: https://www.meity.gov.in/data-protection-framework (review applicability and commencement before real use).

- Added development-only @playwright/test and @axe-core/playwright for reproducible browser and accessibility gates.
