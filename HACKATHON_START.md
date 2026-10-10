# Start here — corrected hackathon build

## Windows
1. Extract the entire ZIP into a **new folder**. Do not copy an old `.env`, `.venv`, database or `node_modules` into it.
2. Install Python **3.12** and Node.js **22 or 24** if needed.
3. Double-click **START_WINDOWS.cmd**. First run installs dependencies and needs internet; wait for setup and the frontend build to finish.
4. Open **http://localhost:5173**. Keep the command window open. Use this exact address, not port 8000 or a file opened directly.
5. Open **LOCAL_CREDENTIALS.txt**, created during setup, for your private staff passwords. Admin opens the control room; volunteer opens the station page. Health, police and rescue also have control-room access.

If an older version is still displayed: close the old server terminal, open a fresh browser profile or clear this site's cached application data, then reopen the address. Clearing site data removes locally queued scans, so sync them first.

## Demo order
- Home: select **Pilgrim**, then **Register your group**.
- Enter departure and a later return time, accept consent, complete leader/contact and member details. Use simulated details.
- Generate the pass. The QR appears on the next screen; download PNG or print it.
- Open **Live Trail View** to see the Manimahesh checkpoint map, journey information and scan controls.
- Use **Staff / Control room** and the admin credentials. Open **Terrain Map**, **Groups Registry**, analytics and incident desk.
- Admin → **Print posters** generates signed checkpoint QRs. Volunteer mode accepts these station QRs and a pilgrim pass/code.
- To exercise alerts, expand admin **Demo mode · Staff controls** and choose a scenario. These are simulated records.
- Test offline operation only after opening the production app online and downloading/verifying resources. Offline scans are local until sync succeeds.

## What changed
- Sign-in/entry screen at `/` and `/login`; pilgrim registration and existing-pass access; staff sessions and volunteer role redirect.
- Startup uses one root `.env`, migrates and seeds before serving, and proxies to IPv4 explicitly (avoids localhost/IPv6 backend connection failures).
- Private credential file and Windows launcher; no shared passwords embedded in the ZIP.
- Registration displays actual validation failures. A local storage write failure no longer hides a pass successfully created on the server.
- QR download/print and visible generation errors; pass details reload from the server on another browser.
- Manimahesh map at `/map`, on the pilgrim trail and in control room. Markers are fitted to view and safely handle missing status. Offline checkpoint overview works without map tiles.
- Improved opening screen, form controls, mobile layout, footer and sync strip.

## Practical limits
This is a hackathon prototype, not a field-certified emergency system. Map tiles need internet; offline overview uses indicative seeded checkpoint locations, not surveyed walking geometry. Camera/GPS need browser permission. Localhost is suitable on your laptop; a second phone needs a properly configured HTTPS origin. Weather requires its external provider. No SMS/WhatsApp dispatch is promised without a configured provider.

## Other platforms
`python3.12 scripts/bootstrap.py`, then `.venv/bin/python scripts/start.py --preview`.
