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
| 2 | Home blank loading/re-entry restoration | Visibly reproduced; owner unknown | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 3 | Clock suffix clipped after reflow | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 4 | Option B scrollbars and oversized plot space | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 5 | Provider chooser size/label issues | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 6 | Player seek-time contrast | Visibly reproduced | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 7 | Play/Pause heavy dark styling regression | 14 exact XML source preimages identified | **Isolated source-only prototype staged** | **4 local unittest cases PASS; 14 variants parsed** | NOT RUN | NOT RUN |
| 8 | Post-Information focus restoration | Suspected visually; needs identity proof | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |
| 9 | Health Center diagnostics reliability | Explicit user authorization; missing native crash snapshot | NOT STARTED | NOT RUN | NOT RUN | NOT RUN |

**OSD prototype limitation:** `osd_playpause_scope.py` makes only two texture tag opacity changes inside existing control `202` in the exact 14 `VideoOSD.xml` members. Its source tests independently assert byte-exact invariance of all other control text/behavior, exact input SHA-256, strict fail-closed baseline mismatches, XML parse and no source archive mutation. It is a **staged experiment, not the final approved look, not a component ZIP, not signed, not physically tested**. Reference the user's approved clean/translucent appearance before final packaging; replace the prototype only if needed by documented physical result, always within control 202.

## Gate policy

- Test broadly, edit only authorized nine workstreams and indispensable narrow dependencies.
- Cobra and every unrelated Infinity component remain SHA-identical and behavior-preserved.
- Trace root cause before any native Search fix or Home performance rewrite. Do not block unrelated scoped fixes while tracing.
- Do not start final signed packaging until the candidate is integrated, code/host/Android17 checks pass, and member-delta receipts are complete.
- New physical acceptance is required for 2103402. Old 2103401 user acceptance is a retained rollback baseline, not advance acceptance of this new candidate.