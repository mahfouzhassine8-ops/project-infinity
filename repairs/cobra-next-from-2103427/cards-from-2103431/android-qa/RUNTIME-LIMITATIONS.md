# Runtime verification limits for delivery

The final existing Android17/API37 emulator baseline run [41010523836](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41010523836) used the unchanged original-key signed2103431 APK. Exact installed bytes/signature, source binding and platform public-class/JAR preflight passed. A20,226-channel synthetic source imported; terminal XML and the inspected PNG show Mobile with video, controls and current/next EPG.

The run stopped during an accessibility root query lasting2867ms: its3426ms readiness phase exceeded the retained2000ms QA budget, so the late result was discarded. No stale press or timeout inflation occurred. Cards was not selected. This is an observation-budget blocker, not a demonstrated native app crash or a failed Cards acceptance test. No fatal/ANR marker appears in the retained finite log; this is not proof of long-running stability.

| Measurement/acceptance | State |
|---|---|
| Cards first usable/card latency | NOT MEASURED |
| Warm/playback return and scrolling/FPS/jank | NOT MEASURED |
| CPU/PSS/memory trend, battery and thermal | NOT MEASURED |
| Android Cards/candidate runtime acceptance | NOT STARTED; no Android PASS claim |
| Physical Fold acceptance | PENDING USER TEST; host/emulator evidence cannot replace it |

The latest user instruction stopped further QA iterations. No further harness change, investigation or run followed. Delivery can report focused host/native/preservation results separately, with no invented Android before/after gain.

Exact official115-file artifact SHA256: af91f837b8a372360114eef2f1f9ac85f8f41993afbd0d6f659548706d3b06da. Inspected terminal PNG SHA256: eef9f3f103f2cb69aeb12fc3d64c72ed7fcc2bc8c8d9c5a66e980c673454e400. Full bindings and per-file hashes: results/signed431-baseline-event-ready/EVIDENCE.json. Prior three failure artifacts remain preserved. No app/native/permission/shutdown change or shutdown test occurred.
