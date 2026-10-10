# Implementation status — 9 October 2026

The delivered source is a runnable local prototype with passing API/unit/build checks. It is **not** a claim that every requested browser flow has been demonstrated or that production/field validation is complete. TEST_REPORT.md distinguishes executed checks from blocked ones.

| Requirement | Implementation | Executed evidence | Remaining limit |
|---|---|---|---|
| Registration / pass | Validated API, member slots/age bands, departure/return, consent, short code, QR and print | API registration tests; QR decoding | Native-phone printing/camera not tested; short code is a prototype lookup capability |
| Pilot route | Correct five proposed checkpoints; other routes cannot register | Pilot metadata and planned-route tests | Seed positions/timing are indicative; no reviewed navigation geometry |
| Offline resources | Production PWA precache, explicit resource inspection/download, local pass/roster and API cache | Production build emits worker + 55 precache entries | Current-browser airplane-mode reload/readiness not executed; storage can be evicted |
| Offline queue | IndexedDB first; preserved IDs; batch drain; retry; invalid state; background-sync handler | Six sync unit tests including bulk/retry; API mixed-batch test | Foreground and background concurrent behaviour on real browsers needs execution |
| Signed check-ins | Server-only HMAC, manual/camera input, source/headcount/direction/member selection | Signature/replay/invalid-token API tests; generated PNG roundtrip | Signature does not prove presence; actual camera scanning unverified |
| Member journey | Per-member outbound/returning/self exit pending/staff exit; split groups; final group completion only when all exited | Split/exit and stale outbound regression | No full operator UI to undo erroneous terminal exit; requires audited correction process |
| Time / uncertainty | Visit and receipt separate, clock skew, no missing-person finding from R8 | Delayed fixture and time/rule tests | Corrected visit time is stored with skew; original time reconstructable, no immutable original raw event payload column |
| Volunteer assistance | Staff scan + manual group lookup; registration through normal form on staff device | Role and group API tests | Dedicated offline registration and complex identity recovery not implemented |
| Route pack / GPS | GPX/GeoJSON import, five local versions, source/licence metadata, SVG overview, foreground fix, synthetic test track | Three deviation calculation unit tests | Real GPS/camera, mountain geometry and field deviation unverified; no real-route navigation |
| Weather | Six-hour model forecast request, attribution, retrieval/validity, stale/unavailable; no fabricated readings | Mocked response and outage tests | Live API request blocked by runtime proxy compatibility; issue time unavailable from endpoint |
| Advisories | Persistent scoped observations/staff/source-linked official entries, expiry, withdrawal, UI | Publication/role/expiry/withdraw API regression | Source URL does not authenticate a bulletin; staff must verify it |
| Health / SOS | Minimal concerns, configured triage, queued SOS, server incident, staff acknowledgment status | Health/SOS API tests; restart persistence | Current-browser acknowledgment UI not executed; no real dispatch integration |
| Control room | Role/scope checks, group timeline, member counts, incidents/notes, flags, analytics, CSV, browser print/PDF | API tests; actual restart preserves notes | No dedicated checkpoint-device heartbeat inventory; last receipt is not device health |
| SSE / edits | Refresh stream, reconnect behaviour, dirty incident forms preserved in code | Browser test supplied | Current SSE/unsaved-form browser verification blocked; broadcaster process-local |
| Family | Random expiring share, revoke, minimal checkpoint/time/status, no staff notes/phone | Expiry tests + restart privacy assertions | Sharing consent is UI-mediated; code-holder capability must be protected |
| R1–R10 | Shared rules.yaml; R8 uncertainty wording; return state protected | Rule suite + journey tests | Thresholds, distances, capacities and timings pending rescue/clinical review |
| Retention | Worker removes associated group records/shares; notification cleanup; local clear controls | Existing retention tests | Export/device/backup erasure requires operator action; no remote erasure of downloaded files |
| Demo | Staff-only idempotent reset; delayed/split/SOS/weather/headcount/overdue fixtures | Scenario tests and simulated-only reset | Synthetic weather/GPS not live evidence |
| UI / bilingual | Green/off-white/saffron, self-hosted fonts, practical screens, added bilingual operational text | TS/build; bundled Devanagari fonts | Full Hindi terminology audit, 360×640/desktop visual QA, keyboard/contrast/touch-target audit not executed; some technical labels remain English |
| Local start | Checked versions, private random .env, no overwrite, shared config, supervised API/worker/web | Linux bootstrap reuse and start smoke | Native Windows/PowerShell not executed; clean network-dependent install not reproduced after interruption |
| Production | PostgreSQL/Alembic, HTTPS Caddy, containers, persistent volumes, backup/restore scripts | SQLite migration chain executed | Docker/PostgreSQL/backup restore and deployment blocked; not production-verified |

## Necessary rule changes

R8 retains its API identifier and legacy demo scenario key for compatibility but means extended reporting delay, not an automatic missing-person declaration. Completed is reserved for confirmed member-level final exits; destination arrival cannot trigger it. Older historical check-ins lacking member reconciliation are retained for audit and are not silently treated as evidence of member exit. Return/split journeys require human review of member-level evidence rather than a single forward ETA.

## Remaining software work before a supervised field pilot

Implement a dedicated checkpoint-device heartbeat inventory; strengthen pilgrim ownership beyond a short code; add immutable incident-note edit history and an audited correction workflow for mistaken final exits; enforce expiry consistently for legacy checkpoint status mutations; complete translation and accessible interaction review; execute the supplied browser suite plus broader real-device queue/SOS/split flows. These are software/verification gaps, separate from external permission and clinical review.
