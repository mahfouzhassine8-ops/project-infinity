# Current device identity — sanitized read-only Health Center evidence

**Evidence:** User-provided `Infinity-Diagnostics-20261106-134146.zip`, captured 2026-11-06 18:41 UTC. This summary contains ONLY curated package/source identities. Never commit raw private diagnostics, full device paths, URLs, queries, or settings.

## Confirmed installed source
- APK package: `com.projectinfinity.kodi`.
- APK versionCode: **2103462** (report header `1.0.9-Final-Corrections-TEST0011 (2103462)`).
- APK member `lib/arm64-v8a/libkodi.so` SHA256: `fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d` — exactly matches the published 2103462 engine.
- Inspected installed skin: `skin.infinity.diggz` **1.0.5.262**, addon.xml SHA256 `f72125c39115f2d108e25cdf2b12ebd35220a6f726c55bffa56be8c1c6054e7e`.
- Inspected installed Command Center: `script.infinity.commandcenter` **0.3.5.61**, addon.xml SHA256 `922ac8d332bbef8ccd70a194f664536f0b789ffbe451ff402736f9fa696090a2`.
- Command Center `default.py` SHA256: `6ecfa94ca3256d20d9605d016b7585a9e587c8cb4dd87ada8bbe0dcbacd47cc4`.
- Command Center `infinity_search.py` SHA256: `245e599843b817bfa7f06b1db212502790a2dca13d229e21367060beb1fa9b6c`.
- Skin `unified/DialogVideoInfo.xml` SHA256: `3e1323aec4af3121d4283d55bcb77f5b1d05dd892593854835e36e7b64b51460`.
- Skin `unified/Custom_1198_InfinityNav.xml` SHA256: `15da2e0b3e3779f08018a624d20d72f8aef4a0d412a559fb679c64fd1858dfde`.
- These observed hashes match the original-signed 2103462 / 1.0.5.262 delivered code. **They establish copied file identity, NOT selected active runtime origin.** All inspected `component_locations[].runtime_active` are **UNKNOWN**.
- Health Center observed: `script.kodihealthcenter` **2.5.26**.

## Precise remaining evidence
- No `runtime-component-identity.json` and no `environment-now.json` in this ZIP, so selected/loaded Kodi skin, resolved component paths and authenticated module manifest digest are still **UNVERIFIED**.
- `unified/Includes_InfinityMediaLists.xml` and actual active XML contents are not exported, only some sampled skin file hashes.
- No current `kodi.log` or `INFINITY_SEARCH_STATE` / `state_changed` entries are included. Thus the Crew / Nixtoons provider-heading navigation regression **cannot be attributed from this ZIP**.
- `crash/native-crash-last.txt` is empty; repeated Search native crash remains **UNTESTED**, not PASSED.
- Snapshot of addon quarantine does not list Crew/Nixtoons. This does not establish their working result status.
- `state: DIFFERENT` within `corrective_2103395` compares with a legacy snapshot; it is **not** evidence of installed 2103462 code corruption.

## Immediate next action for 6.1
**Do not ask the user to identify/reinstall the APK again.** Installed version and inspected script/skin file generations are now confirmed. Restrict the remaining read-only collection to (1) Kodi's selected/active skin path and full authenticated Command Center manifest digest + relevant runtime XML identity, and (2) the first current failing Crew/Nixtoons activation plus `INFINITY_SEARCH_STATE` reason/status/count and Kodi navigation error lines. Avoid sensitive values in published evidence.

Preserve physical **PASS #1 Power, #2 Movies, #3 TV, #5 Downloads** and the user-liked browser art/Cast. Repair **P0 #7 actual provider results**, then #9 Play/Trailer, #8 watched action/check, #4 white curve ONLY in Downloads Files. #6 repeated Search crash remains UNTESTED. No source, user data or device state was modified by this diagnostic review. The prepared skin patch remains unapplied until this binding is resolved.
