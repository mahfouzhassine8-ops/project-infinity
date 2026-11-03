# Preview fullscreen and Display — verification boundary

Protected signed2103450 remains the recovery baseline. Production changes are
limited to Preview Activity UI/window state, Chrome.Control's Fullscreen drawing
and the new private Display Dialog. No engine, resume database, URI routing,
Kodi, Cobra, shared/native, skin/resource, launcher or shutdown changes.

| Selected requirement | Evidence | Result |
|---|---|---|
| Fullscreen entry, reveal, exit, Back-first-exits | Real View input plus real API37.1 decoder/window/pixel observations | PASS available automation |
| Temporary proportional crop and previous-mode restore |11 entries;16/16 edge points each; BestFit/Fill/Stretch radio restored | PASS available automation |
| Cover/inner portrait/landscape equivalents |1080x2520@420,1600x1680@320,2520x1080@420,1680x1600@320 | PASS emulator viewport changes; physical hinge/OneUI pending |
| Actual decoding and scale | Wide, portrait and square synthetic media; decoded square marker ratios0.96 Fit,1.00465 Fill,8.64 Stretch | PASS; optional Stretch alone distorts |
| Light/Dark Display, Appearance, Done and row scrolling | Native screenshots/input and14 host cases, including short windows | PASS available automation |
| Playback continuity, resume and source return | Same request/engine in host; real native frame progression, Resume/Start Over and final decoder release | PASS selected cases; unchanged underlying engine/resume classes |
| Retained controls/call policy |14 host checks plus exact protected source/method/class comparison; prior450 evidence retained | PASS scoped checks; no new physical-call claim |
| Approved PNG and cover recording comparison | Original media bytes unavailable to this executor; frozen written design read in full | UNVERIFIED; no exact visual-parity claim |
| Physical Fold acceptance | User's device | PENDING; checklist in FOLD-ACCEPTANCE.md |
| Shutdown | Frozen source/payload; no new suite | NOT RUN |

Selected Android run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41560863335
Source:8db52e19a32ce014a92b7f7c8bb8f9649571c44d.232 recorded observations are not
232 separate test cases. Largest hidden-chrome response0.6043s; this is observed
emulator timing for the new action, not a physical Fold performance improvement.

Fourteen focused host tests use real Activity/View input and native Canvas with
a decoder terminal spy. They do not prove real video decoding. The selected
Android run separately provides real media decoding, public OS input, screenshots,
window state and frame counters. Its exact source/DEX/class/artifact bindings and
raw result are in final-evidence. Six focused release-protocol tests pass,
including rejection of frozen-owner tampering, wrong baseline/version/DEX and
incomplete runtime evidence. All unsuccessful attempts are retained as FAIL or
CANCELLED and are not included as a successful full journey.

The actual signed candidate must still pass original-certificate and every-member
comparison against signed450 before delivery. Required exceptions are classes3.dex,
app versionCode and truthful component-version labels, plus signature metadata.
All other APK members must be identical. Signing/registration does not promote
or lock the candidate. Final physical acceptance remains the user's.
