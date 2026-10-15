# Cobra 2103279 — user-approved locked baseline

Locked at the user's explicit request on 2026-10-01 (America/Detroit): "Please lock recent end to end apk".

This freezes the already delivered End-to-End Repair RC1 APK. It is a baseline approval, not a claim that every item in the full audit brief has been verified.

## Exact approved package

- APK: `Infinity-2103279-End-to-End-Repair-RC1.apk`
- Version code: `2103279`
- Version name: `1.0.9-End-to-End-Repair-RC1`
- Size: `93536543` bytes
- SHA-256: `cf7aedadded921e5ddc023ba08161638d8f6207dd7002f3258daf178073679cd`
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`

## Source and evidence

- Approved candidate source/report commit: `950a22593ecadba6e28a6dd46a8a99ffd03e3a36`
- Successful build/test source commit: `92dbd3bb9547e1afe03cfda382abdad6773d7a14`
- Product/runtime source commit: `7c91b569ccb3056ea33439434707c2c52d2bd828`
- Build/test run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36810766190
- Package artifact ID: `11139469019`; archive SHA-256: `6cc48019b9965e2a592408be1af8c9f744f8dad4fc1dfb8c90eee6d4324356f9`
- 519 tests passed and 20 protected render comparisons were byte-identical.
- 21 emulator runtime scenarios passed on the exact same APK hash in Android runtime job `110198831557` of run `36808284951`. That overall run failed a unit fixture check later fixed in the successful build/test run; its Android runtime job passed.
- No APK rebuild or application source change accompanies this lock.
- The previous 2103278 locked branch and rollback snapshot remain unchanged.

## Open audit work

The remaining work is still authorized and must proceed on a new forward candidate, never by changing this locked branch.

- Physical Galaxy Fold inner/cover display, fold/unfold and Samsung split-screen/pop-up/live-resize verification.
- Actual affected user channels, authenticated providers, Sports/Watch Live and external add-ons.
- Recording permissions/destinations/results, YouTube/trailers/casting.
- Sustained decode capacity, memory, frame rate, battery and thermals.
- Exhaustive settings persistence, subtitle/audio formats and languages, phone-call handling and process recovery.
- Remaining Multi-View/PiP return and detailed control/focus/touch checks.

Open items are unverified, not declared broken or passed. Historical candidate-only reports predate this user-approved lock; this record is authoritative for lock status.
