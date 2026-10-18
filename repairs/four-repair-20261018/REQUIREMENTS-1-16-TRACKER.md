# Infinity — binding 1–16 completion tracker

**Status:** IMPLEMENTATION TRACKER. **Current step:** #5 targeted repair complete; await instruction for #6. **Individual implementations complete:** 5/16. **Final all-in-one APK and Fold acceptance:** NOT DONE.
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
- An item gets `[x]` once **its individual implementation and targeted regression/preservation checks pass**. This does NOT certify the integrated APK or physical Fold: those must pass the strict final #16/binding audit before release. A failure during final acceptance reopens the affected item; no shortcuts.
- Complete **one numbered step at a time**, in order, **except when the user explicitly directs advancing with an earlier step still unchecked**. This does not waive or check off that earlier step; it must be completed before release. Stop and ask approval for any shared-component conflict rather than touching Cobra.
- Only after **all 16** checkmarks and the full binding audit may the approved work be packaged into **one** permanently signed install-over APK. Signing, testing, and user final lock are separate gates. User must approve final lock.

## Live checklist

- [x] **1.** Player Rotate button; white Follow Device / cyan Infinity-controlled; Playback Display Mode removed; all unrelated playback preserved — **INDIVIDUAL IMPLEMENTATION COMPLETE:** Work Rotate handler reused, 13 alternate layout cyan corrections made in skin 1.0.5.228; all 14 layouts checked; exact approved binary delta proved; final Fold/integrated APK acceptance PENDING.
- [x] **2.** Home Continue Playing context menu; complete actions and persistence without normal-tap regression — **INDIVIDUAL IMPLEMENTATION COMPLETE:** Work's original Home movie/episode actions preserved; helper 0.1.1 fixes a reproducible stale-action data integrity bug; targeted original-writer/host/source/package tests green; final integrated APK + Fold acceptance PENDING.
- [x] **3.** Video Sources exact first-tap select / second-tap launch / selected-hold menu; both columns and focus — **INDIVIDUAL IMPLEMENTATION COMPLETE:** existing approved two-tap/hold behavior retained; native opt-in Video Sources identity mismatch fail-closed correction and C++ host tests GREEN; final signed APK/physical Fold acceptance PENDING.
- [x] **4.** Exact approved context menu order and relevant actions; Hide is reversible and never Disable — **INDIVIDUAL IMPLEMENTATION COMPLETE:** same-ID helper 0.1.2 enforces selected-tile identity and live option capability before every action, and again after an explicit Disable confirmation; host/CI tests passed. Conditional external integrations require proven support; final APK/Fold acceptance pending.
- [x] **5.** Universal blue watched indicators, Resume Hub and Watchlist/Collection correctness; durable identity — **INDIVIDUAL IMPLEMENTATION COMPLETE:** existing approved native/skin blue-badge presentation and exact provider contracts retained; Watched Bridge 1.0.1 now guards stale movie/episode watched, Watchlist, and Collection actions using original CC writer; host regression/preservation tests passed. Final signed APK, true Fold, universal supported-provider parity and Close/reopen acceptance PENDING.
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


## #1 ACTUAL TARGETED CORRECTION — 2026-10-18 (implementation checkmark)

**Defect found beyond the previous Work review:** Work's 1.0.5.227 unified VideoOSD already showed white FFFFFFFF / cyan FF00D9FF, but thirteen alternate OSD layouts still used theme-dependent $VAR[InfinityPaletteFocus] for the *rotation-enabled* state. This does not meet the fixed cyan requirement across all existing layouts.

**Fix implemented, not merely audited:** \`item1_rotate_cyan_228.py\` builds a fail-closed, forward-only **1.0.5.228 #1 isolated staging skin** from the exact already-implemented Work 1.0.5.227 ZIP (SHA-256 \`cc07fe41ccef2b9eca52b8b273ac5ad9a6c1f498a008d64ac0526a7e62dbe699\`). Changes exactly **13 alternate VideoOSD.xml image color attributes**, plus required \`addon.xml\` version and protected manifest. It does not rewrite the unified OSD, player handler, Playback menu, other skin controls, Command Center, Rails, Kodi native engine, or the Cobra add-on.

**Reproducible corrected output:** \`skin.infinity.diggz-1.0.5.228-Rotate-Cyan-Isolated-TEST.zip\`, SHA-256 \`39f8f041376748fbe209868a33ef51e1cfd59082ee6ebb8ad095e6f85336bdef\`. The ZIP preserves all **3,072 existing members** in the exact order; **3,057 members are byte-identical** to the protected .227 parent. There are **no deletions**, **no Cobra-named file changes**, and the Home Continue Playing/Video Sources integration files remain byte-identical.

**Independent local evidence:** \`test_item1_rotate_cyan_228.py\` passed 3 targeted positive/negative unit tests, checked the real ZIP member-by-member, validated all **14** OSD layouts show correct white/cyan rotation states, required approved Android rotation actions, no Repeat in the Rotate slot, and no redundant Playback \`Display Mode\`. A second complete deterministic build produced the same SHA-256. The original signed **2103384** \`classes.dex\` contains both Android rotation actions; 2103384 and the earlier 2103386 native engines are not byte-identical because of previously approved input changes; **#1 did not modify either**. Three preexisting Cobra APK files are byte-identical in those two references.

**Scope:** only the named Rotate color defect and necessary metadata, plus the already-approved Work Rotate/Display Mode correction reused unchanged. The deliberately separate Repeat command under \`PlayerControls.xml\` remains untouched. Original Work Android17 run [39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633) witnessed actual rotation toggle/reset; its overall Essential-First Close FAILED and remains red.

**Final release gates still required:** integrate this exact hash-pinned skin change into the single final APK later, test actual native rotation, Light/Dark/OLED, folded/unfolded, player controls, Cobra runtime, PiP/background, preserved user data, protected Close/reopen and Fold acceptance. No APK was produced or device changed for #1. No final lock authorized.


## #2 ACTUAL TARGETED FIX — IMPLEMENTATION COMPLETE (GitHub 2026-10-18)

**Reproduced defect:** Original Work helper 0.1.0, when a long-press menu read `Add to Watchlist`, would call the unguarded toggle even if a concurrent background writer had already added the same item, unexpectedly **removing** it. The pre-fix executable reproduction confirmed `concurrent_add_still_present=false` and `unintended_remove=true`.

**Actual correction:** same-ID `script.infinity.uirepair` **0.1.1** committed at [fcaf1505ddcc8f3c3a24f49c7d4824ec3c3e71bd](https://github.com/mahfouzhassine8-ops/project-infinity/commit/fcaf1505ddcc8f3c3a24f49c7d4824ec3c3e71bd). It rechecks the exact selected original Command Center context-menu label/operation under the **same protected writer scope**. When the menu becomes stale or its item is no longer a current Continue Playing entry, it **does not mutate anything** and offers the user a brief retry message. Mark Watched, Reset Progress, and Remove from Continue reject a changed playback clock/occurrence; ordinary Resume/Play taps and original Command Center data/save owners remain unchanged.

**Exact production scope:** GitHub commit changed only five files: `addon/controller_access.py`, `addon/runtime.py`, `addon/addon.xml` (version only), `build.py` (helper output name only), `test_resume.py` (six real CC writer regression tests). No player engine, skin, Cobra, Compatibility service, Rails, watched bridge, profile, provider, essential-shutdown code, or other files changed. [1-parent GitHub scope comparison](https://github.com/mahfouzhassine8-ops/project-infinity/compare/8286c0a9e57511830a4293e5a88ccfd37f1673be...fcaf1505ddcc8f3c3a24f49c7d4824ec3c3e71bd).

**Exact reproducible GitHub build:** [run39153079012](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39153079012) **GREEN**; **22/22 original CC Resume/durability tests** (16 inherited/previous + 6 specific guards), **8/8 Add-on menu tests**, authenticated package and skin asset checks. Signed 2103384 baseline [guard39153079053](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39153079053) **GREEN** (source/host safeguard, not new Fold proof).

**Exact CI-created helper** from Actions artifact ID **12145394887**, internal ZIP `script.infinity.uirepair-0.1.1-TEST.zip`, SHA-256 **`07fa26f3eb8136c97263f9e67575fd804a8afba76b31bac970c1c590b095a06c`**. Compared member-by-member against Work's original 0.1.0 ZIP SHA-256 `792154bc91f3a2839dec29b6c560c854105913df6d78a79d39cb253207f947d7`: **9/9 original members retained; exactly three #2-related files changed; six identical; no deleted/added members**. Original CC source hash manifest, Video Sources plugin, favourites/rails menu model, popup layout and input unchanged. Independently executed 13 focused state/menu tests **all PASS** on this exact Github-built ZIP (including watched/episode identity, rating removal, stale Watchlist/Collection/rating, new playback clocks, removed item, protected writer denial, no unintended writes). The local prototype package SHA differs from the CI-built source; the *authoritative* #2 artifact is the exact CI-created SHA above.

**#1 preservation:** GitHub #2 code did not edit the pinned #1 corrected skin 1.0.5.228, native playback/OSD, or its source. #2 staged helper is for eventual approved integrated APK only; not a separate required user installation.

**Final acceptance still pending:** A complete signed upgrade containing #1 and #2 plus all other fixes, preserving installed Diggz/user data, stable Cobra runtime, Android17/Fold long-press, current provider state, full Essential-First Close and restart. This is an **individual implementation** checkmark, not a release/physical Fold pass, and no final APK is claimed.

## #3 ACTUAL TARGETED FIX — IMPLEMENTATION COMPLETE (2026-10-18)

**Prior Work contract retained:** One tap selects, next tap on same tile opens the selected add-on, select+hold opens that tile's options, left/right columns and scroll-state preserved. The earlier [Android 17 UI trace 39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633) contained 18/18 matched grid/scroll cases and 12/12 matching opened add-on identities across synthetic cover/inner sizes and Light/Dark/OLED. That overall run **FAILED at Essential-First Close**, not a final release pass.

**New genuine defect reproduced:** The old native `OnInfinityUiTouch()` accepted a plugin-projected item with `Infinity.UI.Token` disagreeing with `Addon.ID`. In the compiled negative control, two taps on that mismatched Video Sources tile reached an ordinary `OnClick(ACTION_SELECT_ITEM)` and could launch the *different* add-on named by `Addon.ID`. Its long-press also improperly swallowed the event after arming the inconsistent token. This contradicted the exact selected-tile identity requirement.

**Only scoped production correction:** [commit 6d7c315592793d09dee840680666b2e23e5ef769](https://github.com/mahfouzhassine8-ops/project-infinity/commit/6d7c315592793d09dee840680666b2e23e5ef769) inserts 13 lines into **`repairs/four-repair-20261018/native_patch.py`** inside the existing `browse` scope (`WINDOW_HOME + 1193`, control `50`, only explicit `Infinity.UI.Version=1` and `Infinity.UI.Kind=addon`). This fails closed on an unsafe or mismatched token, clears only that input's arm state, restores previous selection, and consumes that malformed touch so it cannot fall through to Kodi's direct launch. It does not change normal valid Video Sources behavior or any other input path. The entire previous native source is reproduced **byte-for-byte** when this one insertion is removed.

**Compiling, regression and preservation proof:** New [host-only workflow 39154244497](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39154244497) **GREEN**:
- Original `test_native.py` compiled/ran original left/right, second-tap, long-press, scrolled/Fold transforms, first popup tap selection, normal Resume path, unrelated window fallthrough. PASS.
- `test_item3_video_source_identity.py` compiled the previous exact pinned production C++ method and reproduced unsafe second-tap wrong-ID action. It compiled the corrected method and confirmed that malformed first/second taps, malformed holds, and tokens changing *after* initial arming **do not activate**; valid exact IDs still select first/open second; independent Home Resume, popup, native fallthrough preserved. PASS.
- Protected locked 2103384 shutdown source guard [39154244499](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39154244499) **GREEN**.
- Exact change-scope comparison [583d08cb..94aba881](https://github.com/mahfouzhassine8-ops/project-infinity/compare/583d08cb683dcc866e824b1551f0cfb96cce878b...94aba881292bba91fc4dc975b966e0e701af9d8a) contains **one 13-line production native source addition**, one new target test, one new host-only CI workflow. **No Cobra source, assets, dependencies, skin, Item Options 0.1.1 (#2), skin 1.0.5.228 (#1), player code, or shutdown source modified.**
- First run [39154158075](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39154158075) failed in a test-only overly broad whole-file assertion before compiling new negative controls; this test assertion was corrected (no production change) and the exact next run passed. That historical failure is retained.

**No new APK:** The correction is checked in as a protected *native build input* for eventual one-APK integration, not yet in any signed APK. Physical Fold/Android17 firmware, full Cobra functional preservation, install-over, Essential-First Close/reopen and final user lock remain **not accepted**, and must be independently tested at #16. The individual #3 implementation checkmark does not waive them.


## #4 ACTUAL TARGETED FIX — IMPLEMENTATION COMPLETE (2026-10-18)

**Prior Work structure preserved:** The previously approved seven ordered top-level Video Sources actions remain exact: Open; Add-on Information; Add-on Settings *when supported*; Add to Favourites; Add to Infinity Rails *when supported*; Hide from This View; More / Manage Add-on. The menu is not a generic Kodi context dump. Normal first-select, second-open, selected-hold, original popup XML/focus, Video Sources provider routes, and standalone Restore Hidden Video Sources remain unchanged.

**Reproduced dangerous defect, before fix:** Work's `script.infinity.uirepair` **0.1.1** checked the current tile identity only in **Add-on Information**. Other actions used the captured old `aid` without checking whether native container 50 still selected the same add-on. Independently running the *actual original helper archive*, with a harmless fixture tile changed from `plugin.video.fixture` to `plugin.video.unrelated` while its popup was open, showed the old helper executed `set_hidden('plugin.video.fixture', True)`. That is a wrong-item Hide, not the approved behavior.

**Narrow corrective implementation:** same-ID Item Options helper **0.1.2** at [commit 6afe2eca](https://github.com/mahfouzhassine8-ops/project-infinity/commit/6afe2ecaf07ad83b12dfa5d500670367fa2aa750):
- `ensure_selected_addon(aid)` is invoked only by Video Sources `addon_menu` and `manage`. It requires current custom Browse window `11193` and both `Container(50).ListItem.Property(Addon.ID)` and `Infinity.UI.Token` equal the original valid add-on ID.
- Recheck before opening the popup, **after** the popup selection and **again after** an explicit management Disable confirmation. No Open, Information, Favourites, Rails, Settings, Hide or Disable action is permitted for an old/different tile.
- Reevaluate actual conditional `Add-on Settings` and `Add to Infinity Rails` availability after the popup. If capability disappeared, report that options changed instead of silently doing nothing. Existing same-name supported actions preserve their exact original handlers.
- Hide continues to call only `Skin.SetBool(Infinity.VideoSources.Hidden.<id>)`, with `Skin.Reset(...)` for restoration. Hide **never calls** `Addons.SetAddonEnabled`, and Disable exists **only inside More / Manage Add-on** behind explicit confirmation. Existing protected Infinity navigation/recovery exclusions remain intact.
- AutoWidget and Super Favourites are not offered without a verified installed integration/action contract. Do **not** introduce speculative no-op commands or touch those external add-ons; qualifying live-device adapters must be confirmed during final optional-integration acceptance where installed.
- No Cobra code, files or settings touched. No change to Home Continue Playing `resume_menu`, guarded Command Center writer, Video Sources first/second-tap native routing, playback, Rails source, skin or shutdown components.

**Exact source/file delta** [5f911c1e...6afe2eca](https://github.com/mahfouzhassine8-ops/project-infinity/compare/5f911c1e1130992ed0a2ac797af92ed291087e9e...6afe2ecaf07ad83b12dfa5d500670367fa2aa750): exactly **four source files**: `addon/runtime.py`, `addon/addon.xml` (0.1.2 version), `build.py` (helper ZIP filename), and `test_menu.py` (added targeted regressions). No source files removed; all #1–3 corrective files byte-identical to the previous commit.

**GitHub targeted verification:** [run39155208245](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39155208245) **GREEN** with **22/22 Continue Playing/Command Center tests** (#2 preserved), **15/15 Add-ons menu tests** (previous 8 plus 7 additional safety/positive tests), authentic skin asset checks, skin XML checks and exact helper package produced. Locked 2103384 protection [run39155208368](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39155208368) **GREEN** (source only). Tests cover stale first menu selection, stale token after popup, current-window mismatch, stale settings/Rails support, changed tile during Disable confirmation, Hide/Restore isolation, preserved native Information/Rails actions, proper Favourites/Disable consent and first-party protected navigation controls.

**Independently validated exact GitHub artifact:** Workflow artifact **12146632893**, internal `script.infinity.uirepair-0.1.2-TEST.zip`, SHA-256 **`48142c960d5a49f79989e3614d4d12255603b3c9c07e2d70755be8f21d0c0d7a`**. Compared full nine-member helper ZIP against original #2 GitHub 0.1.1 artifact **`07fa26f3eb8136c97263f9e67575fd804a8afba76b31bac970c1c590b095a06c`**: **9/9 members retained in original order**, **exactly 2 changed** (`addon.xml` and `runtime.py`), **7 byte-identical** (`controller_access.py`, `plugin.py`, popup/menu, asset XML and others), **zero members added/deleted**. Independently executed the actual old/runtime helper and new/runtime helper under the same mocked selection-change fixture: **old helper mutated wrong tile; new helper raised a selected-tile-changed error with zero writes**.

**Release gates outstanding:** This is **an individually verified implementation**, not an installed app/APK, physical Fold or Cobra runtime acceptance. Later final signed single-APK integration must combine this exact 0.1.2 helper with #1 skin, #3 input and subsequent requirements, pass fresh/upgrade Android17, physical Fold menus across themes/fold states, data/permission preservation and Essential-First Close/reopen, and repeat binding/Cobra regression audit. Missing supported optional integrations require re-opening #4 before final acceptance; no final lock is authorized.

## #5 ACTUAL TARGETED FIX — IMPLEMENTATION COMPLETE (2026-10-18)

**Original approved watched/resume functionality retained:** Source files `repairs/watched-bridge-20261017/addon/bridge_state.py`, `service.py`, `provider_contracts.py`, native `InfinityWatchedIndex.h`/`InfinityWatchedPresentation.h`, and prior blue-badge skin artwork/layout are **unchanged** by this #5 correction. The bridge only presents verified, typed movie/episode watched identities; a title-only guess or unverified provider/episode numbering must remain unknown. Existing Command Center watched, progress, Watchlist, Collection and saved `continue-watching.json` storage remain authoritative. Positive watched/unwatched indicators, no autoplay, resume progress, underlying player, provider routes and approved #1-4 changes are preserved.

**Genuine defect corrected:** Old Watched Bridge 1.0.0's `context.main()` displayed `Add to Watchlist` or `Add to Collection` and called the existing CC toggles *after* the user selected, without checking whether an asynchronous writer had already added the item. The old popup could reverse a user's newer state or mark a title based on a stale watched-state row. This was **not** covered by existing UI-only menu checks and must be guarded before calling the existing writer.

**Scoped production change:** Same-ID `script.infinity.watchedbridge` version **1.0.1**, [commit 5046a0f996e93fce95ff8d6f4375c05ad8725df4](https://github.com/mahfouzhassine8-ops/project-infinity/commit/5046a0f996e93fce95ff8d6f4375c05ad8725df4). `context.py` captures the exact typed, view-local watched/Watchlist/Collection state shown in the provider popup. `controller.py` accepts this optional intent and, **inside the original Command Center persistence scope**, re-resolves the same canonical saved identity and verifies only the selected action's relevant present state. If the watched state/list membership changed during a popup, it returns `False` with **no data write**, leaving saved progress, watched state, lists and Kodi sync queue intact. Other existing `controller.apply` callers lacking an intent retain their previous original behavior; the main provider popup passes intent. No new background service, database, account integration, provider code or core Kodi hooks were added. `addon.xml` and `build.py` change only the helper version to 1.0.1.

**Actual GitHub test evidence:** [host-only run 39156538395](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39156538395) **GREEN**: `test_state.py` **13/13**, `test_contracts.py` **2/2**, `test_actions.py` **32/32** (all older CC behavior inherited plus six targeted safety tests, movie and vetted episode provider; verifies actual `context.main()` wiring, stale membership/watched prevention, explicit actions/save/reload, ambiguous identity/no-write, original checkpoint admission). **47/47** total. Locked user-approved 2103384 source/host preservation gate [39156538210](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39156538210) **GREEN**.

**Exact package preservation:** The GitHub workflow created [artifact 12146674934](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39156538395), containing `script.infinity.watchedbridge-1.0.1-TEST.zip`, SHA-256 **`dbc913459c148052ce46b30241d77c4a2c7d29bea45fddcad82496ebe9ad0029`** (13,052 bytes). Independently opened the actual artifact ZIP and checked 9/9 internal members, no duplicates/broken ZIP, correct package naming. GitHub CI compared each source member against exact previous protected commit **3dec3461723ae5dd0ce2c667d591217998653871** and found only three modified add-on files: `addon.xml`, `context.py`, `controller.py`; **six members byte-for-byte identical**, none removed. [Exactly scoped source diff](https://github.com/mahfouzhassine8-ops/project-infinity/compare/3dec3461723ae5dd0ce2c667d591217998653871...5046a0f996e93fce95ff8d6f4375c05ad8725df4) includes these three, one pinned helper builder version, tests, and one host-only workflow. **Cobra and #1–4 code/assets/native sources were NOT changed.**

**Preexisting broader watched presentation evidence and open integration limits:** Real Kodi before/after renderer runs [39006084978](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39006084978) and [39007979797](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39007979797) passed on older watched-badge implementation, retained byte-for-byte here. However, actual Android compiled native-row tests [39006400078](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39006400078) and [39006924487](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39006924487) previously **FAILED**, and no new physical Galaxy Fold test has been performed. Those failures remain red and MUST be resolved in the integrated acceptance phase; do not call source/host pass a native Android fix. Provider versions outside the exact hashed Umbrella/POV episode contracts, including unverified Otaku episode numbering, are intentionally withheld from confident cross-provider matching pending proof, not marked verified or silently inferred.

**Release boundary:** #5 is a **verified individual implementation** but is NOT installed as a new APK, not Fold-certified, not evidence that *all* providers show blue badges, not an Essential-First Close success and not a final lock. During final packaging, integrate the hash-pinned Watched Bridge 1.0.1 along with #1–4 and the future fixes; prove native Android/Fold watched badges, historical failure resolution, original CC/progress/watchlist durability, Cobra functional immutability, full install-over and Close/reopen before any release approval. Any unmet requirement reopens #5 rather than silently waiving it.
