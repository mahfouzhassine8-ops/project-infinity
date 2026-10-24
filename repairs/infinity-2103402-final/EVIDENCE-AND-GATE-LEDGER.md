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
| 1 | Search/native signal process exit | Observed; stack unavailable | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 2 | Home blank loading/re-entry restoration | Visibly reproduced; native-owned geometry invalidation identified | Scoped native-owned revision-trigger correction STAGED; complete warm Home delay still unresolved | 4 host tests + CI PASS for changed path | NOT RUN | NOT RUN |
| 3 | Clock suffix clipped after reflow | Visibly reproduced | Clock bounding-width correction STAGED in unified Home only | 3 host tests + CI PASS | NOT RUN | NOT RUN |
| 4 | Option B scrollbars and oversized plot space | Forced one-page bars and unused short-plot area confirmed | Track hiding and short-synopsis geometry correction STAGED; physical scrolling not accepted | 4 new host geometry tests + prior XML source checks PASS | NOT RUN | NOT RUN |
| 5 | Provider chooser size/label issues | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 6 | Player seek-time contrast | Unified variant uses theme ink over video; other13 already white | Unified white text/black shadow staged; other13 time controls unchanged | Scoped source/package tests PASS | NOT RUN | NOT RUN |
| 7 | Play/Pause heavy dark styling regression | 14 exact XML source preimages identified | **Isolated source-only prototype staged** | **4 local unittest cases PASS; 14 variants parsed** | NOT RUN | NOT RUN |
| 8 | Post-Information focus restoration | Suspected visually; needs identity proof | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 9 | Health Center diagnostics reliability | Signal metadata omitted; empty snapshot falsely available; read failure abort risk | Bounded partial-read and exit-metadata fixes staged; signed DEX binding and broader integration pending | 2 focused tests PASS, including compiled actual Java methods with controlled interfaces | NOT RUN | NOT RUN |

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
