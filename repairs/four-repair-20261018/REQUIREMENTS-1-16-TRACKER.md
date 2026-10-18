# Infinity — binding 1–16 completion tracker

**Status:** OPEN. **Current step:** #3 at the user's explicit direction. **#1 and #2:** verification deferred, both unchecked. **Fully completed:** 0/16.
**Repository:** `mahfouzhassine8-ops/project-infinity`.
**Development branch:** `work/infinity-post-2103384-feature-restoration`.
**Protected user-approved APK:** 2103384, SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.
**Locked skin:** 1.0.5.223; preserve user's later installed 1.0.5.225 and all data.
**Final acceptance device:** Samsung Galaxy Fold, One UI 9, Android 17/API37.

## Governing no-exceptions instructions

- Fix **only** the specific numbered requirement under examination; use verified prior implementation rather than recreate it.
- **Cobra is off limits:** no changes to Cobra code, features, player path, assets, settings, dependencies or runtime behavior, including via shared services. Any unapproved Cobra impact blocks the item.
- No unrelated changes, regressions, silently removed APK files, feature deletions, compatibility downgrades, redesigns, rollback, uninstall, data clear, or false success.
- Test change scope against exact protected versions **before** claiming an item complete. Preserve signed/native identities and produce exact source and artifact checksums.
- Green host checks and generic emulator checks are limited evidence; do not claim Fold acceptance without physical testing. A failed Close or missing crash cause remains failed/open.
- An item gets `[x]` **only when all its explicit functional, preservation, and required acceptance gates pass**. Partial work stays `[ ]`; write progress separately. After checking an item, report “#N COMPLETE” and show the updated list.
- Complete **one numbered step at a time**, in order, **except when the user explicitly directs advancing with an earlier step still unchecked**. This does not waive or check off that earlier step; it must be completed before release. Stop and ask approval for any shared-component conflict rather than touching Cobra.
- Only after **all 16** checkmarks and the full binding audit may the approved work be packaged into **one** permanently signed install-over APK. Signing, testing, and user final lock are separate gates. User must approve final lock.

## Live checklist

- [ ] **1.** Player Rotate button; white Follow Device / cyan Infinity-controlled; Playback Display Mode removed; all unrelated playback preserved — **DEFERRED BY USER to proceed to #2; source evidence saved, physical Fold acceptance outstanding, NOT COMPLETE.**
- [ ] **2.** Home Continue Playing context menu; complete actions and persistence without normal-tap regression — **DEFERRED BY USER to proceed to #3; prior host/emulator evidence saved, physical acceptance and successful Close/reopen outstanding; NOT COMPLETE.**
- [ ] **3.** Video Sources exact first-tap select / second-tap launch / selected-hold menu; both columns and focus — **IN PROGRESS: existing Work native gesture path, selected-add-on identity and exact Android 17 evidence; physical Fold pending.**
- [ ] **4.** Exact approved context menu order and relevant actions; Hide is reversible and never Disable
- [ ] **5.** Universal blue watched indicators, Resume Hub and Watchlist/Collection correctness; durable identity
- [ ] **6.** Home Movie/TV rails long-press, touch parity and correct options with no black ghost popup
- [ ] **7.** Safe add-on recovery and physical Otaku re-enable with all settings retained
- [ ] **8.** Full approved Infinity skin refinement, themes, Fold layouts, animation, ZIP preview and navigation
- [ ] **9.** Native stability / OnJobComplete deadlock correction / background return, screensaver, PiP, session continuity
- [ ] **10.** Essential-First Close and durable save-state; zero blocked essential writers; genuine exit and reopen
- [ ] **11.** Android Version Check correction; preserve service and strict native writer safeguards
- [ ] **12.** Original abnormal native exit status 139; evidence-grounded root-cause fix and regression proof
- [ ] **13.** Preserve ALL existing Infinity and Cobra behavior; Cobra completely off-limits; shared components unchanged unless approved
- [ ] **14.** Include every required hash-pinned component in one APK with original dependency/compatibility parity
- [ ] **15.** Install-over activation and preservation of user data, installed Diggz build, settings, add-ons and skin
- [ ] **16.** All sixteen acceptance gates + binding preservation audit; Android17 and physical Fold verification; final user-approved lock only

## Proof required before checking #1

- Pin **exact existing** signed APK/skin identities; reuse Work's already implemented rotation patch from the exact .225 source. Verify the white/cyan state and the actual platform orientation actions rather than a cosmetic icon swap.
- Preserve correct player OSD controls, original independent Repeat functionality outside Rotate (where approved), Video Settings, zoom/aspect, audio/subtitles, PiP/background, and all **Cobra** assets/code and dependencies byte-for-byte.
- Verify only approved player OSD and Playback-menu skin entries differ; no unrelated XML/navigation or shared-service changes. An unanticipated difference blocks acceptance.
- Require direct Android 17 gameplay tests and Fold orientation/fold/unfold evidence before the final #1 checkmark. Generic emulator is not the user's One UI firmware.
- No candidate build or signed APK promotion at this stage. The rest of the list remains unchecked.

## #1 source/package verification — 2026-10-18 (NOT a full checkmark)

**Verified without changing APKs or the skin payload:**
- Read the actual GitHub implementation in `repairs/full-system-20261017/player_rotate_226.py` and `repairs/four-repair-20261018/build.py`, plus exact host test `test_skin.py`.
- Read two existing hash-pinned full skin artifacts from the *previously completed* UI producer: 1.0.5.226 SHA-256 `48a889cf3181d181da81431d56562fd1165d6ab6cb32da0142190948d728b6c9`; 1.0.5.227 SHA-256 `cc07fe41ccef2b9eca52b8b273ac5ad9a6c1f498a008d64ac0526a7e62dbe699`. Both match their producer receipt.
- All **14** `VideoOSD.xml` XML payloads are byte-for-byte identical across .226 and .227; `Display Mode` entry absent from each. Unified control `263` uses `PLAYER_ROTATION_UNLOCKED` and `PLAYER_ROTATION_FOLLOW_DEVICE` with approved white/cyan visible states; the Rotate slot does not invoke Repeat.
- The exact two skin archives contain 3,071 and 3,072 members respectively: **no old member deleted**, one newly added `unified/InfinityItemOptions.xml`. From .226 to .227, only `addon.xml`, the protected metadata, and three approved UI/helper integration XML members change; **no Cobra-named file in that delta**.
- Saved Work Android17 UI evidence for signed 2103386: `UI-INTERACTIONS.json` has 89 successful interactions, including `rotate-first-state` (rotation true, focus 263), `rotate-returned-state` (rotation false, focus 263), and `playback-without-display-mode`. See [API37 Work full UI run 39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633). **This entire run FAILED at Essential-First Close** and therefore is not a release success.
- The two saved skin builds and these preexisting Work/host artifacts were **inspected read-only**. These checks do not constitute a new build, physical Fold result, or a Cobra functional proof.

**Remaining before #1 can be marked [x]:**
- Actual physical Galaxy Fold: rotate action affects orientation, white/cyan state matches requested modes, fold/unfold/portrait/landscape survive, and repeat no longer occupies Rotate slot.
- Confirm playback Video Settings/aspect/zoom, audio, subtitles, PiP/background and Stop remain functional on Fold; no Cobra regression. Do not alter Cobra.
- Keep #1 **unchecked** until the required physical acceptance can be recorded without exposing personal diagnostics.

## Current factual context (not a completed-item claim)

- Work's skin `1.0.5.227` implements the approved Rotate/Playback layout and has source and emulator evidence; that **does not** establish physical Fold parity.
- Locked 2103384 remains protected. Previously attempted all-in-one 2103388 has unapproved Compatibility-service file loss and is **rejected** as a final candidate.
- Original native crash, Essential-First Close and complete single-APK install-over remain **OPEN**. Source-only 2103389 is not a verified signed build.

**Updating rule:** Add dated source/CI/device receipts under the relevant numbered item when evidence passes; keep remaining checkboxes unchecked. Do not turn a risk, assumption, or source-only assertion into a checkmark.

## #2 investigation start — 2026-10-18 (NOT a checkmark)

- User explicitly instructed **Move on to number two**. #1 remains open, with its Fold acceptance deferred; it is not treated as passing.
- **Narrow scope only:** Home Continue Playing movie/episode card holds open the original item-specific menu, without replacing ordinary Resume/Play tap, bypassing the existing Command Center writer or changing unrelated add-ons/rails/Cobra.
- Menu actions: Mark Watched/Unwatched, Reset Progress, Watchlist/Collection add/remove, Rate/Change/Remove Rating where original supports it, Custom List, and Remove from Continue Playing.
- Demand source hashes, menu selection behavior, correct movie/episode identity, guarded mutations, restart persistence, and preservation of current progress/unrelated items.
- Existing `controller_access.py`, `addon/runtime.py`, `addon/plugin.py`, `native_patch.py`, `test_resume.py`, saved Android17 `android_interactions.py` evidence and original protected Command Center are the starting evidence; **no complete result or Fold proof claimed**.
- Need passing targeted tests and physical device before #2 can be checked; any need to modify shared code triggers Cobra impact review and fail-closed approval, not unrelated changes.

## #2 verified existing implementation — 2026-10-18 (NOT a checkmark)

**Read-only proof, no production file or Cobra edits:**

1. The unchanged pinned Work helper `script.infinity.uirepair` version `0.1.0` delegates to the original `script.infinity.commandcenter` v`0.3.5.20` menu, persistence scope and saved-state writer. It does not introduce a background service, secondary progress database or new provider route.
2. Independently compared **all 13** Command Center file SHA-256 preimages in the helper against the already-signed 2103388 APK bundle. **13/13 match**. This proves internal bundle identity, **not** the user's live installed add-on hashes or approval of 2103388.
3. Independently diffed exact hash-pinned skin 1.0.5.226 vs 1.0.5.227 `unified/Includes_InfinityHomeUnified.xml`. The *only* difference in that file is one conditional helper directory value for Movies and one for TV, both retaining the original Command Center fallback with the original `Infinity.ContinueWatchingRevision` query. No unrelated Home visual control changes in this file.
4. [Work host package run 39114438060](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39114438060) completed successfully. The exact source job log has **16 ResumeTests PASSED**, including movie and episode mutations and reload from saved data; rejection of closed write admission, identity mismatch and stale progress; and **8 contextual menu tests PASSED**. This is host evidence, not Fold evidence.
5. Independently inspected the actual [Android17 signed 2103386 UI evidence artifact from run 39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633): `UI-INTERACTIONS.json` reports 89 successful UI records. Both `continue-movie-context` and `continue-tv-context` displayed the original seven top-level rows; both `continue-*-watchlist-saved` observations returned to Home with the correct control focus. **The overall CI run then FAILED Essential-First Close**, so post-restart durability is **not certified** by that Android run.
6. Native source/host harness explicitly sends the Home 8830/8831 long-press to the opt-in Resume context; ordinary taps fall through to the original Resume/Play action, and popup selection never invokes the row on the first tap. This is source/controlled-Android evidence only, not proof on the Fold.

**Remaining #2 blockers:**
- Actual Fold long-press on a saved movie and episode, normal tap Resume/Play unaffected, correct focused card and same scroll position after dismissal. Verify all applicable menu actions, including removing a rating and removing an entry, on harmless user-approved test content.
- Confirm **current installed** Command Center preimages before any helper installation; runtime must fail safely rather than overwrite/downgrade a differently configured controller. The bundled signed 2103388 is independently rejected for unrelated Compatibility-service preservation violations and MUST NOT be used as #2 Fold test delivery.
- Require actual approved single-APK upgrade, normal Essential-First Close/reopen and untouched unrelated progress, watched history, Watchlist and Collection. No physical-device connection or permitted integrated qualified candidate is available yet.

**#2 verdict:** source and controlled emulator functionality substantially verified; **unchecked** due to physical and full persistent-install acceptance still missing. No reproduction, guesswork, source edits or APK builds started for #2.

## #3 investigation start — 2026-10-18 (NOT a checkmark)

- At the user's explicit direction, work has advanced to **#3**, while #1 and #2 remain deferred/unverified, neither approved nor checked.
- Scope is restricted to `All Add-ons → Video Sources` **first tap selects**, **second tap on same tile launches**, and **select then long-press opens contextual menu for that same tile**, across both columns, scrolling and active Fold geometry. Correct initial focus without launching/back-navigation workaround; dismiss restores current selection and scroll.
- Audit existing native `OnInfinityUiTouch` and `OnInfinityUiContextMenu` and opt-in scope, existing custom `Custom_1193_InfinityBrowse.xml`, `script.infinity.uirepair` directory projection, and tested Android gestures. D-pad, unrelated Kodi input, Cobra, and all shared services are **untouchable** except where explicitly approved with proof of no impact.
- #4's menu actions and Hide/Disable semantics remain a separate numbered workstream, not authorization to change #4 while verifying #3.
- No source/native/skin/APK implementation changes or builds authorized by this tracker update. Missing physical Galaxy Fold testing cannot be reclassified as a passing result.

## #3 verified existing Video Sources touch implementation — 2026-10-18 (NOT a checkmark)

**Scope unchanged:** Only `All Add-ons → Video Sources` tile gesture/focus behavior. Do not modify Cobra, Command Center, player/OSD, shared Compatibility service, native shutdown, or other numbered repairs.

**Inspected existing production sources and historical runtime data:**

- `repairs/four-repair-20261018/native_patch.py`: `OnInfinityUiTouch` uses the exact custom Browse window `WINDOW_HOME + 1193` / container `50` and requires a verified opt-in item token. First touch only selects; second on the same focused tile invokes one original activation; selected hold routes through `OnInfinityUiContextMenu`. A different tile cannot immediately launch. `DISPATCH` also requires skin ID `skin.infinity.diggz`, one-finger tap/hold and a valid native window. D-pad and unrelated windows retain their original paths. These are source-scope protections; **Cobra physical behavior is not asserted tested**.
- `build.py` and `test_skin.py`: the active custom Browse XML directs Video Sources to the opt-in helper via an isolated conditional URL with the original non-Video-Sources provider as fallback. Original grid geometry and right/left layouts are preserved in source checks. The helper emits actual installed add-on IDs, not generic context targets.
- `test_native.py` contains compiled C++ method cases for left/right initial tap, second tap, hold on changed tile, scroll offsets, coordinate transforms, nonselected item, invalid token and nonopt-in fallthrough; no stock Kodi/Cobra rewrite.
- [Previously signed 2103386 native CI run 39121637251](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39121637251) signed the real candidate and passed exact protected native-source, fresh and loaded Android cases; this was before later API37 full application Close failure. This does NOT certify the complete candidate.
- Independently reopened the **actual saved** `UI-INTERACTIONS.json` produced by [Android17 run 39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633) for signed 2103386. It has 89 recorded UI observations with `passed=true`, `physical_fold_verified=false`.
- **18 of 18 historical runtime trace comparisons matched**: 2 emulated display sizes (1080×2400 cover and 1800×1440 inner) × 3 themes (Light/Dark/OLED) × (left, right, scrolled). For each, menu state opened and dismissal restored the exact selected token and page; menu was anchored to a selected item, never an independent unrelated tile. **12/12 left/right opened-provider folder paths** matched the exact add-on IDs selected by first tap. Both right-side and left-side real item activation observations were recorded.
- Every one of the six emulated display/theme cases exercised a scrolled tile hold; selection and current page were still retained on dismissal. These are synthetic emulator sizes, **not** a physical hinge/fold test.
- Historical full Android17 workflow **FAILED Essential-First Close** with a Version Check writer-ownership blocker, despite the separate UI evidence `passed=true`. Its overall failure remains red; no Close or final-release approval inferred.

**Still required before #3 gets `[x]`:**

1. **Physical Galaxy Fold Android17/One UI9** with live Diggz profile: left and right first tap select; same second tap launches; hold on selected tile opens correct popup without directly launching; tapping different tile only selects, across scrolling, fold/unfold/rotation.
2. Normal Back/outside dismissal preserves selection and scroll, UI does not trap focus, no black ghost popup, no shortcut suddenly executes.
3. Actual installed Cobra and unrelated input/playback behavior prove unaltered; **no Cobra edits allowed**. Shared native input path is reviewed only, not newly changed here.
4. Full final signed one-APK install-over, data persistence and required guarded shutdown are separate later steps and cannot be falsely presumed passed.

**#3 result:** **Source and controlled Android17 UI behavior verified; physical/integrated release acceptance OPEN. #3 remains UNCHECKED.** No new APK/native/skin/helper code or test workflow was modified or built for #3. Changes in this step are restricted to this tracker record.
