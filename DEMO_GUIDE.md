# Guided demonstration

Use invented names and `0000000000` contacts only. The app is independent of official registration. Do not dial 112/108 or send real SMS during the demo.

## Prepare

Run the README bootstrap/start commands with `--preview`. Read generated staff credentials privately from `.env`; there is no shared committed password. Use separate browser profiles for a pilgrim, volunteer and admin laptop. Separate physical phones require trusted HTTPS and a reachable server; laptop localhost alone does not supply this. Real-device HTTPS setup was not executed here.

Sign in as admin, open Demo mode, and load the named scenarios. They are idempotent until reset. Reset removes only simulated groups and their associated records. It does not reset real groups or rotate accounts. Generated development credentials and the local database must not be uploaded with the source.

## Ten-minute script

1. **Register:** On the pilgrim browser register two simulated members. Show the pass and member roster. Explain that the QR has no openly embedded name/phone.
2. **Prepare offline:** Use Download & verify. Wait for the production service worker, reload, then repeat the check. Show actual blockers rather than claiming readiness. Keep the pass and roster on that same device.
3. **Delayed upload:** Disable networking. Save a signed checkpoint scan. Show local-only queue status. Re-enable networking, sync, and compare visit time to server receipt time on the control room. No remote update should be claimed before receipt.
4. **Group separation:** Have the volunteer select one of the two members, direction return/exit, at Hadsar. Show split state; the other member remains on route. Confirm the remaining member separately before claiming complete return.
5. **Late record:** Use the delayed-sync fixture or a queued earlier outbound event. Confirm a late upload does not reverse a recorded return/exit.
6. **SOS:** Use the simulated SOS scenario or app button with an invented concern. Show pending versus server receipt. A staff member acknowledges the SOS flag. Explain that none of these states means emergency-service dispatch.
7. **Incident:** Create/assign an assistance incident, save a note, reload and show persistence. Keep an unsaved note open during an update to demonstrate the intended draft-preservation behaviour; see TEST_REPORT for browser verification status.
8. **Advisory:** Publish a clearly simulated, scoped, expiring advisory. Compare it to a volunteer observation and model forecast. Do not fabricate an official bulletin.
9. **Family:** Create a consented share, inspect its limited contents in a separate browser, revoke it and verify it becomes unavailable.
10. **Map:** Show the proposed checkpoint overview. Load the separate controlled test track and simulate an off-track fix. State explicitly that this is a synthetic software demonstration, not Manimahesh field GPS evidence.

## Fixtures

Demo controls include fast ascent, overdue report, headcount mismatch, simulated thunderstorm threshold, extended reporting delay (legacy API name `missing-group`), delayed sync, SOS and split return. The legacy name does not label a person missing.

`qr/local/` contains locally signed sample posters and passes generated during verification. They are installation-specific and will not validate against your newly generated secret. Regenerate locally:

```sh
.venv/bin/python scripts/gen_checkpoint_qr.py --allow-local --output qr/local
.venv/bin/python scripts/test_qr_roundtrip.py qr/local
```

Windows: replace `.venv/bin/python` with `.\.venv\Scripts\python.exe`. The QR decoder requires `zxing-cpp==2.3.0` (install with your venv pip if absent). Print the bilingual `/volunteer-guide` page at A4. Existing legacy QR fixtures are excluded from the consolidated delivery to avoid stale checkpoint labels.

## Honest presentation close

Explain tested software behaviour separately from unexecuted browser/hardware/PostgreSQL checks. Route review, staff ownership, emergency-service arrangements, legal approval and clinical/rescue threshold review remain external requirements. Do not describe this as a deployed rescue service.
