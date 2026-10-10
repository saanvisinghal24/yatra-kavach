> Historical input-repository document. Not current acceptance evidence. Read root TEST_REPORT.md, IMPLEMENTATION_STATUS.md and HANDOVER.md for this delivery.

# Yatra Kavach - Tech Stack Selection Rationale

Every tool in the Yatra Kavach stack was chosen deliberately for high-reliability, offline capability, low operational overhead, and speed of delivery.

## 1. Frontend
- **React 18 + Vite + TypeScript:** Fast compilation, strict type safety for mission-critical domain entities, and instant HMR.
- **vite-plugin-pwa (Workbox):** Service worker precaching of application shell, fonts, and active trail configuration. Guarantees 100% functionality in airplane mode.
- **Dexie (IndexedDB):** ACID transactions inside the browser. Scans and registrations persist across app reloads, cold starts, and device battery shutdowns.
- **qr-scanner & qrcode:** High-performance, low-latency WASM-based camera QR scanning and lightweight client-side QR generation.
- **Hand-written SVG for Altitude Profiles:** Eliminates heavy map tile libraries from the pilgrim mobile bundle. Provides high-contrast, beautiful topographic elevation profiles readable in glare.
- **Leaflet (Code-Split Chunk):** Dedicated exclusively to the Control Room desktop dashboard for spatial trail visualization without polluting the pilgrim bundle.
- **Design Tokens & Plain CSS / CSS Modules:** No heavy UI frameworks (Tailwind, MUI). Pure CSS custom properties for instant rendering and high contrast.

## 2. Backend
- **Python 3.11+ & FastAPI:** High-throughput async endpoints, native Pydantic v2 validation, and built-in Server-Sent Events (SSE) support for the control room.
- **SQLAlchemy 2 & Alembic:** Full declarative model definitions, rock-solid schema migrations, and clean PostgreSQL 16 JSONB support.
- **PostgreSQL 16:** Relational integrity for groups and members combined with JSONB flexibility for dynamic checkpoint facilities and rules configuration.
- **Astral:** Deterministic sunset and twilight calculations for high-altitude latitude/longitude coordinates to warn pilgrims of nightfall.
- **Slowapi:** Rate-limiting to safeguard public registration and sync endpoints against abuse.
- **pyjwt & argon2-cffi:** Cryptographically secure, modern authentication for control room operators and field volunteers.

## 3. Operations & Reliability
- **Docker Compose:** Predictable reproducible environment orchestrating PostgreSQL, FastAPI, and Vite web client.
- **Deterministic Rules Engine:** Pure functional programming with zero external I/O or network LLM dependencies in the safety evaluation loop.
- **Console & Telegram Notifier:** Pluggable notification adapter pattern enabling instant dispatch of urgent alerts to rescue team channels.
