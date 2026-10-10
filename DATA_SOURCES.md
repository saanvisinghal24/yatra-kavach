# Data, provenance and verification

Source acquisition: 8 October 2026. Implementation review: 9 October 2026. This is an independent hackathon prototype; the software pass is not official registration or permission to travel.

| Asset / data | Source | Licence / handling | Verification status |
|---|---|---|---|
| Broad Manimahesh route context | https://hpchamba.nic.in/manimahesh-yatra/ | District-owned page; referenced and paraphrased, photographs not copied | Names Hadsar, Dhanchho, Sundarasi and Gauri Kund support the proposed sequence. Does not validate software checkpoint facilities, coordinates or staffing. |
| Forecast | https://open-meteo.com/en/docs | https://open-meteo.com/en/licence — data CC BY 4.0, attribution required; review service terms for commercial deployment | Six-hour model forecast for approximate checkpoint coordinates, not an observation or safety clearance. Live request success is recorded separately in TEST_REPORT.md. |
| Online control map | https://opentopomap.org/ | Existing OpenTopoMap attribution retained (OpenStreetMap contributors / CC-BY-SA); online display only, no tile prefetch | Approximate separate checkpoint markers; no connected walking route. Provider terms must be reviewed before deployment. |
| Offline map policy | https://operations.osmfoundation.org/policies/tiles/ | Standard public OSM tile service prohibits offline bulk prefetch | No bulk download. Offline overview and imported route packs are separate from online tiles. |
| Pilot checkpoint sequence | User-provided specification | Project configuration | Proposed Hadsar → Dhancho → Sundrasi → Gauri Kund → Manimahesh Lake. Return requires final Hadsar exit reconciliation. |
| Seed coordinates, distances, altitude, timing and capacity | Inherited prototype seed | Unverified configuration | Indicative only. Not a surveyed or approved walkable route; do not infer shelters, staffing or medical facilities. |
| Imported GPX / GeoJSON | User supplied with source/licence/version metadata | Importer must hold redistribution/offline rights | Import does not establish field review. Real-route navigation remains unavailable. |
| Controlled test track | Software-created fixture | Project fixture, simulated | Demonstrates foreground GPS/deviation calculation only; never Manimahesh navigation evidence. |
| Icons / typography | Lucide, fontsource packages; bundled Noto and DejaVu fonts | Retain package and bundled OFL / DejaVu notices | Self-hosted build assets. |
| Existing branding / social images | Input repository | Original authorship not independently established | No government emblem intended; permission audit remains owner responsibility. |

The district page separates official registration from general route information. Its published season information is not live operational clearance. Consult the current district notices directly before any field use. No current official advisory is fabricated or silently seeded as a real bulletin.

Provider retrieval timestamps are UTC ISO-8601. `issue_time` is null because the selected forecast response does not provide a model issuance timestamp; `valid_from` and `valid_until` describe the hourly forecast window. Missing arrays or null values produce unavailable status, never fabricated temperatures. Cached data becomes stale after fetch failure; offline clients cannot obtain fresh forecasts.

No reviewed, licensed Manimahesh GPX/GeoJSON was supplied or established during this work. The delivered route representation is an indicative overview. Field geometry, facility verification, local language review, route permissions and rescue/clinical review are external requirements.
