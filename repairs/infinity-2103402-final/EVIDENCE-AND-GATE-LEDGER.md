# Infinity 2103402 — Initial Evidence and Repair Gate Ledger

**Date:** 2026-10-24. **Status:** Scope locked; work branch created; no signed candidate exists.

**Protected source:** `1738478709cd8881f7ad4a524e7abbbc82b5d79c` (2103401), build `40089463702`. **Branch:** `work/infinity-2103402-final-stabilization-20261024`. Never modify protected `lock/infinity-2103401-signed-qa-20261024`.

## Non-public evidence retained outside GitHub

| Evidence | SHA-256 | Handling |
|---|---|---|
| `19999.mp4` physical Fold recording | `4fdbb41477688d5e37828476cb23a368226dd6ff6d37e82a40e16b62c258e1b4` | **Do not commit raw video to a public repository** |
| `Infinity-Diagnostics-20261024-152230.zip` | `8dd22eab912c7eb93993cfccb0b7feaa2d353e48daa69ec4d7ac79ab9b9fb232` | **Do not commit raw logs, tokens or private profile data** |
| `skin.infinity.diggz-1.0.5.242.zip` | `a3c0998afc7367910968c7cd5ccb6dff4728403a4099543f875717b7b888e20b` | Exact pinned OSD source input; 14 VideoOSD variants |

**Observed evidence:** Search History restores `relationship rehab` and app later exits. Android historic exit record: `2026-10-24 15:22:18`, process `com.projectinfinity.kodi:kodi`, `Reason: signal; Status: 7`. `crash/native-crash-last.txt` in supplied archive is empty; cause remains unverified. Poster rails blank on initial entry and warm playback return (around 45 seconds on return). Clock becomes `3:21…`/`3:22…` after return/reflow. Option B has unused right-side scroll tracks and excessive empty area; chooser truncates Cancel, prints `[/B]` and occupies excessive height. Seek-time labels are too dark. Heavy near-opaque Play/Pause backdrop appears. Selected-poster focus return is suspect.

**Do not reopen earlier repairs without a reproduced regression:** the supplied diagnostic also contains an older `Essential-First COMPLETE` Close receipt, `total_duration_ms: 4043`, `authorization_consumed: true`, `engine death: confirmed`, `blocker_count: 0`; this is not proof that the recorded Search termination was a failed Close.

## Nine-row execution ledger

| # | Owner / authorized problem | Evidence status | Implementation status | Targeted tests | Android 17 integration | Physical Fold candidate PASS |
|---|---|---|---|---|---|---|
| 1 | Search/native signal process exit | Original OS bugreport confirms SIGBUS; all32 text/32 protobuf tombstones lack this PID/date | No speculative Search fix; older aborts kept separate | Capture/analyzer host checks PASS; Search runtime NOT RUN | NOT RUN | NOT RUN |
| 2 | Home blank loading/re-entry restoration | Visibly reproduced; native-owned geometry invalidation identified | Scoped native-owned revision-trigger correction STAGED; complete warm Home delay still unresolved | 4 host tests + CI PASS for changed path | NOT RUN | NOT RUN |
| 3 | Clock suffix clipped after reflow | Visibly reproduced | Clock bounding-width correction STAGED in unified Home only | 3 host tests + CI PASS | NOT RUN | NOT RUN |
| 4 | Option B scrollbars and oversized plot space | Forced one-page bars and unused short-plot area confirmed | Track hiding and short-synopsis geometry correction STAGED; physical scrolling not accepted | 4 new host geometry tests + prior XML source checks PASS | NOT RUN | NOT RUN |
| 5 | Provider chooser size/label issues | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 6 | Player seek-time contrast | Unified variant uses theme ink over video; other13 already white | Unified white text/black shadow staged; other13 time controls unchanged | Scoped source/package tests PASS | NOT RUN | NOT RUN |
| 7 | Play/Pause heavy dark styling regression | 14 exact XML source preimages identified | **Isolated source-only prototype staged** | **4 local unittest cases PASS; 14 variants parsed** | NOT RUN | NOT RUN |
| 8 | Post-Information focus restoration | Suspected visually; needs identity proof | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 9 | Health Center diagnostics reliability | Signed exporter gaps and native re-raise context loss confirmed; original abort registers partly recovered from older tombstones | Partial Python export, Java exit/resource metadata and isolated native context forwarding STAGED; candidate DEX/ARM64 integration pending | Python5 retained; Java2 updated PASS; native5 and analyzer4 PASS | NOT RUN | NOT RUN |

**OSD prototype limitation:** `osd_playpause_scope.py` makes only two texture tag opacity changes inside existing control `202` in the exact 14 `VideoOSD.xml` members. Its source tests independently assert byte-exact invariance of all other control text/behavior, exact input SHA-256, strict fail-closed baseline mismatches, XML parse and no source archive mutation. It is a **staged experiment, not the final approved look, not a component ZIP, not signed, not physically tested**. Reference the user's approved clean/translucent appearance before final packaging; replace the prototype only if needed by documented physical result, always within control 202.

## Gate policy

- Test broadly, edit only authorized nine workstreams and indispensable narrow dependencies.
- Cobra and every unrelated Infinity component remain SHA-identical and behavior-preserved.
- Trace root cause before any native Search fix or Home performance rewrite. Do not block unrelated scoped fixes while tracing.
- Do not start final signed packaging until the candidate is integrated, code/host/Android17 checks pass, and member-delta receipts are complete.
- New physical acceptance is required for 2103402. Old 2103401 user acceptance is a retained rollback baseline, not advance acceptance of this new candidate.

## Continuation checkpoint — source only

Protected baseline APK hash and diagnostic APK-native hash match build40089463702.
The new archive has no faulting stack. Signal7 remains unassigned to a function;
no pure-virtual/Scudo attribution or speculative Search fix was made. Video
samples show at least40 seconds of blank Home after playback return; no measured
readiness target has passed. Directory reset, announcement invalidation and
provider re-listing paths are identified, but the complete runtime owner chain
still needs attribution before a native cache change.

`FILE-AUTHORIZATION-LEDGER.json` was recorded before the respective staged edits.
`visual_scope.py` and its four new checks preserve every non-target byte and
reject both a reintroduced Play/Pause matte and seek-text regression in package
fixtures. Existing Play/Pause prototype and its prior passing tests remain.
`health_export_scope.py` compiles the actual revised methods in its host harness;
Android interfaces are controlled fixtures, not an Android test. Signed DEX
identity/preservation and actual API37 export integration are still required.
The Health export source adapter remains fail-closed to its exact preimage.
Initial failures are retained separately from the passing results.

## Single-install continuation from Astra checkpoint 8ed595fb

The latest remote checkpoint and its 17 passing host checks from run40132316838
were retained before editing. Delivery remains one integrated, permanently
signed 2103402 candidate. Internal test builds are allowed; no diagnostic APK
installation has been requested, and no candidate has been promoted.

The supplied archive's native/critical logs contain PIDs27962 and30115 from
08:11 and06:49 America/Detroit, with zero rows for Search incident PID9097 at
15:22:18. They cannot identify this Search fault. `SEARCH-LOG-COVERAGE.json`
records these boundaries. Existing-baseline OS bugreport/ADB capture remains
viable and NOT RUN; it is not exhausted. `NON-APK-EVIDENCE.md` and the tested,
read-only `capture_baseline.py` support that route without installing anything.

Read-only disassembly of the signed APK confirms the two staged Java exporter
defects. `HEALTH-DEX-BASELINE-REVIEW.json` pins the DEX and method instructions,
records the sole external caller in Splash's Infinity export action, and lists
existing compiler-generated shared API helpers that must remain untouched.
This is targeted original-bytecode review, not candidate DEX equivalence or ART
execution. Candidate integration remains blocked on those separate checks.

The exact signed Health Center Python exporter was also shown to discard an
otherwise useful report when optional collection throws. The scoped correction
retains existing evidence, writes unavailable statuses without exception text,
reports empty source files honestly, and preserves fatal archive-write errors.
Five focused checks pass against the real exporter; no lifecycle, persistence,
provider or shutdown policy changed. Three capture-tool host checks and an
exact 19-member staging gate also pass. All required Android/Fold cycles remain
NOT RUN. Home latency, chooser ownership, focus restoration and actual visual
rendering remain unresolved acceptance gates.

The source-only workflow now includes these nine new checks and explicitly
allows the existing takeover handoff document. It does not add runtime,
shutdown or packaging triggers. See `CONTINUATION-HOST-RESULTS.json` for the
current source-only receipt. No raw diagnostics were committed.

No signed2103402 artifact has been produced. No workflow, signing, provider,
TrackIt, database, persistence or Cobra source was edited. The only revised
existing repository document is this ledger; candidate XML and Java are isolated
under this repair directory. No personal recording or diagnostic archive was
committed. Required50 Search,30 playback-return,20 rotation and separate Close/
reopen cycles are all NOT RUN. This session has no attached Android device, adb
or emulator acceleration, and no GitHub workflow-dispatch action. These gates
remain blocked; no sign-in request or workflow authorization bypass was used.


## Continuation — source-level corrections and gated CI

- Signed 2103401 baseline remains the only accepted package; no 2103402 APK or component ZIP is signed.
- Found a concrete unnecessary reload trigger: under native-owned `app-` display reflow, Command Center previously incremented `Infinity.WidgetReloadRevision` for a geometry-only change. Home Latest Releases URLs contain that revision, creating an avoidable new directory request. The 2103402 overlay changes only this branch; native layout updates still run, with older fallback code unchanged. This corrects one identified invalidation, **not yet the observed 40–45 second return delay as a whole**.
- Extended the existing unified Home clock box from left 72% / width 26% to left 64% / width 34%, retaining the original 98% right edge and every other Home control.
- Corrected Option B's fixed short-synopsis reservation while retaining full metadata text, the long-plot scrollable bound, existing textbox controls and action buttons. Existing one-page scrollbar hiding remains staged separately.
- The actual signed CC35/skin242 preimages were rehashed and their full staged overlay members inverse-compared byte-for-byte. Focused local tests: **4 Home reflow + 3 clock + 4 Option B geometry = 11 PASS**. Earlier 2103402 visual/Health tests remain independent.
- GitHub CI run `40131873559` succeeded against the exact 2103401 signed ZIPs, with full-history source preservation checking. Later CI incorporating Option B is selected separately; do not infer Android/physical acceptance. An initial run `40131428226` failed because checkout was shallow; preserved the failure and repaired the test checkout by fetching full history without relaxing the diff guard.
- `FILE-AUTHORIZATION-LEDGER.json` now includes exact preimage/candidate SHA-256 and negative regressions for the three new scoped member overlays. Private user recording/log data remain outside the public repository.
- **Still open:** Search SIGBUS faulting stack/root cause, full Home warm-return timing, native/Android17 end-to-end acceptance, chooser owner and Cancel/formatting, selected-title focus restoration, broader Health/DEX integration, and a user-approved signed final release. No suspected cause is being treated as fixed merely because a source test passes.

## Original Android bugreport continuation from e66371a0

The new original bugreport was verified against SHA256
`938f1859648fcbf1c7118646e3896de0c721c5a4c2d9f0b037446e0d186af0c9`.
`ANDROID-BUGREPORT-EVIDENCE.json` and `ANDROID-BUGREPORT-FINDINGS.md` record
the separated incident findings and actual limitations. All32 text and32
protobuf tombstones were inspected; none matches the Oct24 Search SIGBUS.
The two Oct23 tombstones contain partial original register buffers recoverable
from displayed memory, but not the original caller stack. The Scudo snapshot's
65685 VMAs/29749 secondary regions are a mapping-pressure lead, not a proven
allocation-owner fix or evidence that today's Search has the same cause.

The exact recorder source and signed executable establish a downstream-context
loss: re-raising creates a syscall PC rather than forwarding the original one.
An isolated native source repair passes5 host signal/ownership/preservation
checks, including a real SIGBUS baseline/candidate comparison. Main is the sole
literal library load site in signed DEX, and the signed manifest assigns Main
to :kodi; an additional exact-process constructor guard enforces that boundary.
No Kodi engine, Cobra, original recorder binary or baseline APK was edited.
Android17/ART/debuggerd and ARM64 compilation remain NOT RUN. The candidate
source is not eligible for final integration until those checks pass.

The staged Java exporter now also preserves OS RSS/PSS/importance metadata,
with honest unavailable values and isolated getter failures. Its2 existing host
checks pass with added cases;4 parser/privacy tests pass. Earlier26 host passes
(run40137879262) and all19 addon overlays remain retained. See
`BUGREPORT-HOST-RESULTS.json`; source CI is selected for the expanded35 checks.
No interim installation requested, no signed2103402 package, and no Search/Home/
rotation/Fold performance or stability PASS claimed. Raw diagnostics remain
private. All other approved workstreams and physical release gates remain open.
