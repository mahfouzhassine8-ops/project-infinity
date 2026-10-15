# Cobra 2103281 — user-authorized lock

Locked at the user's explicit “Lock” instruction on 2026-10-01 (America/Detroit).
This records approval to preserve this build as the baseline; it does not invent a physical-device pass or declare the full audit complete.

## Exact identity
- Approved candidate/report commit: `27b06cef01c7b9883de5dd502790eb478cd465e6`.
- Build/runtime source commit: `85126e37c322067718b6309e11246697b29ccd2e`.
- Prior locked baseline: `ad18f93633ecc3ec74d121acf50bda873cd33cd0` (2103280), unchanged.
- APK: `Infinity-2103281-Remaining-Audit-RC1.apk`.
- Version: 2103281 / `1.0.9-Remaining-Audit-RC1`.
- Bytes: 93,536,543.
- SHA-256: `4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5`.
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Build/runtime run: 36823023157, successful.
- APK artifact: 11144128927; source/regression artifact: 11144069407; runtime artifact: 11144740658.
- Lock branch: `locked-infinity-cobra-2103281-remaining-audit-user-approved-20261001`.

## Verified scope
522 regression tests passed; 20 protected renders byte-identical; emulator install/update from 2103280 and three Sports runtime scenarios passed. The baseline audit recorded 12/14 additional scenarios passing, with the two stale Sports callbacks repaired and replayed successfully in 2103281. Native libraries, assets and Android resources remain unchanged.

## Outstanding scope
Physical Fold/window transitions, authenticated provider and external add-on outcomes, physical calls, sustained hardware performance/thermals, and exhaustive remaining settings/control combinations are not certified. See `cobra-2103281-remaining-audit.md` and `cobra-2103281-candidate-verification.json` for the bounded evidence. Their candidate/unlocked flags describe pre-lock validation and are superseded only for lock status by this record.

This commit adds this lock record only. No APK rebuild or product-source change. Future repairs must use a forward branch and preserve this lock and previous locks.
