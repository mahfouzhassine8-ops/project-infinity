# CURRENT PRIMARY HANDOFF — SEVEN WORK GROUPS, GROUP #6 SILENT MODE

## GROUP #1 LATEST: SCOPED RESUME CHOOSER EXPERIMENT, 29-MEMBER SOURCE-ONLY SCOPE, #19 NOT FIXED

**Date:** 2026-10-19. **Latest user authorization:** “Fix and complete” **Group #1 only**. This does not authorize Cobra, native-wide UI, Essential-First shutdown, third-party provider modifications, unrelated Groups #2–#7 or auto-locking. **CURRENT GROUP #1 REMAINS IN PROGRESS / RED**, NOT completed. Source-only stage and local tests below: **no APK build/sign/install, no Fold pass, no user acceptance**.

**Signed original unchanged:** Infinity 2103390, SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`, exactly 7,430 APK members.

**New Group #1 original task 03 experiment—first-party vertical Resume/Play chooser:** The original horizontal Home Continue Watching panel IDs 8830 Movies and 8831 TV use Kodi's CDirectoryProvider native click. Its resume prompt uses shared native VideoSelectActionProcessor / DialogSelect, which might change Cobra if edited globally. Instead source-stage a direct **Infinity Home panel-only** conditional click into the existing first-party `script.infinity.uirepair/runtime.py` and `popup.py:choose()` WindowXMLDialog. It displays vertical touch rows `Resume from M:SS` and `Play from beginning`, 78px-tall native rows, reuses Command Center verified identity/source/ListItem/saved playback position, rechecks record/source/progress after the modal, and cancels cleanly. It invokes `xbmc.Player().play(original_verified_route, original_listitem)` with original saved offset or 0. **CAVEAT:** This Python playback call does *NOT* equal the original Kodi native `PlayMedia(...,resume/noresume)` and absolutely requires physical provider playback verification (avoid second dialog/wrong source or position); DO NOT treat synthetic mocks as that proof or install as final. The fallback native click is preserved only if UI Repair is disabled. No popup artwork, player engine, third-party addons or stored progress were edited.

- SHA-guarded patch `group1/continue_choice_patch.py` commit **`bed9bd932edd5b9ed0643b6a3c3ec55a11641518`**, Git blob **`b5775c1597d603c3b53757be334cb8321f9ff458`**.
- `group1/test_continue_choice_patch.py` commit **`7fc82b6e42052bdea7e3850b3fcd33656fbcaa62`**, **12/12 PASS source/host mocked-player** including 14 actual signed Home variants, only 2 conditional Home clicks per variant, exact single first-party runtime handler, tab/media identity, 0 vs saved resume seconds, Back/cancel and stale media refusals.
- New virtual full original-APK combination `group1/test_group1_scope_apk_29.py`, commit **`51b0f661b8141512c28b14efc528f737d3600d56`**. Separately executed equivalent independent local 7,430-member scope gate **1/1 PASS**: 14 existing Home XML, 10 clock orb includes, 2 Command Center source files, 2 first-party pinned controller JSON, 1 UI Repair runtime; **exactly 29 potentially changed members, 7,401 unchanged**. No files added/removed, Cobra/native/shutdown/Version Check/provider unchanged. Historical 12/14/15-member checks are superseded; no candidate APK packaged.
- **Local combined host regression:** `python -m unittest -q test_continue_choice_patch test_integrated_scope_29 test_home_reload_correlation` = **17/17 PASS** (12 + 1 + 4) in ~4.5s on original signed base, no Android CI. Earlier host 17/17 and 19/19 were **separate runs**; don't total them as one suite. Full signed APK SHA verified. Host scripts/receipt in `repairs/2103390-bugfixes/receipts/GROUP01-CONTINUE-CHOICE-29MEMBER-HOST-20261019.md`, commit **`f436c0e9f79066803f9dd98fa2c453dff7f32f82`**.

**Original task 19 still RED, no runtime fix.** Native source audit confirms hiding a panel does not automatically reset DirectoryProvider items; refresh may instead result from URL, invalidation or Home reset. Existing `infinity_continuity.py` already marks Home reinitialization with `Infinity.Continuity.HomeLoad`. New read-only offline diagnostic collector `group1/home_reload_correlation.py` source commit **`c1546bd9e49264d003c2c3cfae08bcfccfbad58f`**, tests `group1/test_home_reload_correlation.py` commit **`a1ae517749f922aa52304ed2ad01566b03b654bd`**, **4/4 synthetic host PASS**. It only aggregates HomeLoad tokens and Continue Watching starts from existing user-owned in-app ZIP export. Earlier actual user diagnostic had **20** Continue Watching jobs in ~49.6 seconds under one revision; **exact per-tab native invalidation reason still unknown**. Umbrella supplies the top latest-release widgets; Command Center/UI Repair supplies Continue Watching; do not conceal real updates with a blind CC cache or alter Umbrella. **A real no-reload correction has NOT been coded or proved.** Do not falsely mark task 19 complete.

**Tracker now saved at commit `fea428d1c49298c2c228f7968089ea10d2868e06`. Latest commit after this handoff will be newer; query live HEAD before next edit.**

**Next mandatory gates before ANY Group #1 completion/checkbox:** true selected horizontal swipe/accurate tap/scroll restoration; actual working vertical chooser/correct saved position vs restart under real Kodi/Fold provider; actual failing TV episode route, real duplicate Insidious stored identities/progress, clock orb across Fold/themes, true cause-isolated #19 Movies↔TV Home rail persistence with legitimately refreshed progress/provider, strict unchanged Cobra/Essential-First/shutdown and signed install-over physical Fold validation. If evidence shows this staged Python playback is incompatible, reject/repair it instead of shipping. **No full Group #1 completion, no APK, no LOCK at this checkpoint.**

---



## NEWEST GROUP #1 SOURCE CHECKPOINT — OCT 19 NUMERIC CONTINUE CARD AND NAVIGATION AUDIT

**USER AUTHORIZATION: CONTINUE GROUP #1 ONLY.** Cobra ABSOLUTELY off limits; likewise Essential-First shutdown, other Infinity work groups, third-party plugins and installed user data. **GROUP #1 STILL IN PROGRESS, NOT COMPLETE.** Current actual original signed APK `2103390` remains unchanged. **NO new signed APK**, no install/Fold pass, no user lock.

**NEW TASK #03 SOURCE CHANGE — DEFAULT FOLD HORIZONTAL POSTER TOUCH DIMENSIONS**
- Exact original signed 2103390 default skin is `skin.infinity.diggz` 1.0.5.228, with default `<res width="1080" height="2400" aspect="9:20" default="true" folder="unified"/>`.
- In ORIGINAL default `unified/Home.xml`, Continue Watching Movies panel ID `8830` and TV Shows ID `8831` have `<itemlayout width="auto" height="97.619048%" aspectratio="0.561219512">` and identical focused layout dimensions. Kodi upstream reads numeric list item width/height with `QueryFloatAttribute`; invalid width can default to the entire parent width, misaligning poster touch cell and horizontal scrolling. **Other 13 original Home layout variants ALREADY use correct numeric 230.1 × 410 card dimensions.**
- **SOURCE PATCH COMMITTED:** `repairs/2103390-bugfixes/group1/continue_horizontal_touch_patch.py` commit `d6ba53d7317e379044a23062434ff128f5b39cf2`, verified Git blob `47c2b02ed6cd96a65453be6270cab01ab5243829`. Exact immutable unified Home preimage SHA-256 `61fe23defed0536ce24f7c6d2d9b6beed5c0f3b8d04a33809a929a6b1f2532be`. Only **four layout tags** change: the item/focused dimensions of panels 8830 and 8831 to `width="230.1" height="410"`. All other existing Home item art, playback routes, visibility, navigation, formatting and XML remain byte-equivalent. No other 13 Home files changed.
- **TESTS COMMITTED** `group1/test_continue_horizontal_touch_patch.py` at `bd0ecbf5c608b649e5dcedbd8546174ab1e3f59b`, **6/6 host PASS**. Separate `group1/test_group1_scope_apk_15.py` at `a07b7840ed835e98c54e5c389ce347f07dd9d946`, **1/1 full real signed APK virtual scope PASS**.
- **CURRENT VIRTUAL APK SCOPE: 15 of 7430 MAY CHANGE, 7415 UNCHANGED.** The 15: previously staged 10 Home orb include XML, 1 Command Center TV `plugin.py`, 1 movie `resume_hub.py`, 2 first-party UI Repair/Watched Bridge expected SHA JSON, plus 1 default `unified/Home.xml` for both narrow touch fixes. No file deletion/addition, no Cobra, no native, no shutdown, no provider, no guarded controller *executable* logic change. Previous 14- and 12-member virtual checks are HISTORICAL and MUST NOT be used for future combined packaging.
- **NO PHYSICAL INPUT PROOF.** This corrects a tangible source-level layout defect; real one-finger swipe/accurate tapped poster/no accidental tap-on-drag/offset restoration on actual Fold are still **RED**. The VERTICAL compact Resume from [time] / Play from beginning chooser is **NOT FIXED**; do NOT globally change Android touch/Kodi native/DialogSelect without an exact first-party-only scope proof.
- Source receipt: `repairs/2103390-bugfixes/receipts/GROUP01-TASK03-DEFAULT-FOLD-HORIZONTAL-15MEMBER-20261019.md`, saved at commit `6613f6dbed514bdbaaafb1b96c66a138b9fad663`.

**NEW TASK #19 READ-ONLY NAVIGATION/FETCH INVESTIGATION — NOT A FIX**
- Exact original signed Home (all 14 variants) shows category selector ID 9000: **focus/selection** changes `Container(9000).ListItem.Property(section)` and show/hide of corresponding widget panels. But **click activation** is originally `ActivateWindow(Videos,...)`, which leaves Home and may legitimately lead to window reinit on return. Neither source proves which event the user's Fold video shows; do not remove these existing navigation actions.
- Movie and TV normal latest-release panels 8101/8102 are **Umbrella-owned**. Movies and TV Continue Watching panels 8830/8831 are **Infinity first-party UI Repair/Command Center**. The original retains distinct revision properties. The previous in-app diagnostics confirmed 20 new Continue Watching jobs under one stable data revision over ~49.584 seconds (not a proven invalidation reason). Fixing only CC snapshot cache or deleting Umbrella refresh is not supported.
- Read-only audit `group1/home_category_contract.py` source commit `6dcb0ce4d1003e4e7cda4352f8b9fcc72ee33f8c`; tested `group1/test_home_category_contract.py` commit `52c1840810dee5e74419101c1fab499226f6cfbf`, **5/5 host PASS**. No source/provider behavior changed for #19.
- Receipt: `repairs/2103390-bugfixes/receipts/GROUP01-TASK19-HOME-SELECT-VS-ACTIVATE-20261019.md`, saved `7e341678e337405b4f646bf08ddcff5d778c34f6`. #19 RED: need cause-correlated Fold visibility/URL/provider reset/Window activation trace, user changes refresh correctness, and both Umbrella+CC rail retention.

**LAST EXECUTED COMBINED HOST RUN**:
```
cd repairs/2103390-bugfixes/group1
python -m unittest -v test_home_category_contract test_continue_horizontal_touch_patch test_group1_scope_apk_15 test_cc_preimage_contract_patch
```
**17/17 PASS** using original signed 2103390 locally: five navigation read-only audits, six #03 layout tests, one 15-member virtual APK firewall, five first-party pinned controller compatibility tests. The earlier **19/19** host run is a separate historical run: DO NOT claim 36 distinct tests or a single 36/36 run.

**STATUS TRACKER** `TASK-STATUS.json` updated by commit `edeaf2db13a84d24b90a0fb0e2dbcd4e1f97a68e`. SOURCE ONLY, no combined/signed APK, no Fold; all prior validated source patches preserved.

**NEXT GROUP #1 work**: narrowly scoped vertical Resume/Play chooser without global dialogs, real swipe and focused selection physical proof, #19 root-cause isolation and source correction for category blanking, TV user episode evidence, actual duplicate Insidious identity, clock/orb physical proof. #01/#02/#04 still source-staged only. SlyGuy/Lyrics work stays USER-SKIPPED. After all Group #1 gates, user authorizes any Group #7 combined build/final lock separately. Older handoff paragraphs below listing 12 or 14 members or "task03 not started" are historical and superseded by THIS section.

---



## DUAL CONTROLLER-CONSUMER COMPATIBILITY — NEWEST VERIFIED GROUP #1 CHECKPOINT (2026-10-19)

**THIS CHECKPOINT SUPERSEDES THE PREVIOUS `12 OF 7,430` POTENTIAL-APK MEMBER ASSUMPTION.** User's latest authorization remains **CONTINUE GROUP #1 ONLY**. No new signed APK, no package modification, no Fold proof, no user lock; **Group #1 STILL RED**. Cobra, Essential-First shutdown, all other Infinity groups and third-party add-ons remain untouchable.

The genuine signed 2103390 APK was recovered (original SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`). Its `script.infinity.uirepair/controller_access.py` (which serves **Home Continue Watching** through `script.infinity.uirepair/?action=continue`) and `script.infinity.watchedbridge/controller.py` BOTH require exact SHA matches to 13 Command Center source files. The three previously staged behavior patches include TV `plugin.py` and movie `resume_hub.py`, so applying only the prior 12 member changes would leave both consumers verifying OLD pinned hashes and rejecting the newly corrected modules. This is a **proven first-party integration defect in the previous virtual candidate**, NOT proof of the user's original TV playback or category reload root cause.

**NEW REAL SOURCE STAGING — COMPLETE AT HOST LEVEL:**
- New `group1/cc_preimage_contract_patch.py` source commit: `9d6bc1845e3f392cbe48ed86aa96eb73cc79d681`. Patches **only two expected hashes** in each of the two original `CONTROLLER-PREIMAGES.json` maps; the other **11 pins per map and all runtime guard logic are unchanged**. Exact original source + staged patch hash proofs; refuses unknown versions, double apply or mutated contracts.
- New `group1/test_cc_preimage_contract_patch.py` test commit: `0bf2be94fcbfa22e64344ca9b8105f7614708c13`. Executed against original signed APK bytes: **5/5 tests passed**, signed base SHA verified, both consumer guard maps verified, fail-closed tamper negatives, original file preservation, full simulated APK member inventory.
- **Corrected Group #1 virtual packaging scope: 14 of 7,430 members** may differ: original 10 skin clock-orb include variants, original 1 Command Center TV `plugin.py`, original 1 Command Center movie `resume_hub.py`, plus **2 first-party preimage JSON maps**. Other **7,416 members remain original** in the simulation. NO Cobra/native/shutdown/provider/code-guard changes. This 14-member allowlist is now mandatory for any later approved integration. **DO NOT ship historical 12-member candidate.**
- Immutable verification receipt: `repairs/2103390-bugfixes/receipts/GROUP01-CONTROLLER-CONSUMER-14MEMBER-20261019.md`, commit `c3cc7181fef5781f329f12a1a49195c4095b3684`.
- Master status committed `33fb53e782fa1b971e2370950718cd4ce029e714`; prior **19/19** Group #1 host checks and new **5/5** compatibility checks were performed in **SEPARATE runs**, so do not misrepresent a single full 24-check run.

**Still RED and next work**: prove user-specific TV episodes actually resolve; verify real saved Insidious identity/upsert; **task 03** physically reliable Movies AND TV horizontal poster swipe, correct tapped card, retained offset, and VERTICAL touch-friendly Resume/Play choices; **task 19** first isolate exact Movies↔TV category invalidation/blanking trigger affecting BOTH Umbrella latest-release and Continue Watching rails (20 repeat directory jobs same state revision, but trigger not yet confirmed); verify clock/orb on Fold. Do not touch shared GUI input/Kodi DialogSelect, native DirectoryProvider, Cobra, startup SlyGuy/TMDb, Lyrics, shutdown, or other groups. No combined APK without Group #7 user authorization.

---



## LIVE WORK STATUS — GROUP #1 ACTIVE, THREE SCOPED SOURCE PATCHES STAGED, 19/19 HOST CHECKS

**LATEST USER INSTRUCTION:** “Continue” during the specifically authorized **Group #1** repair. Do NOT mistake old handoff text below saying no group selected for current truth. Group #1 is **ACTIVE/AUTHORIZED**. STOP and ask before changing anything beyond this group. The separate SlyGuy/TMDb startup-error and CU LRC Lyrics bug repairs are USER-SKIPPED, not part of this group. No changes to third-party addons, Cobra, shutdown, any other Infinity feature, or other Groups #2–#7.

**Current live branch:** `work/infinity-2103390-targeted-bugfixes`; query live HEAD immediately before next edit. Last verified source-only receipt checkpoint: **5cb853ccf6b4b09058945f82212a39d0cdef3bae**. Current master TASK-STATUS.json records the latest precise committed statuses; never assume latest checkpoint equals current HEAD after documentation commits.

**ACTUAL COMPLETED SOURCE-HOST MILESTONES (NOT PHYSICAL REPAIRS):**
- Original #04 Home clock/status-orb overlap: exact-hash protected source-only 10 Home include XML anchor reposition, **2/2 tests passed**, 3062 unchanged skin ZIP members. Receipt `receipts/GROUP01-TASK04-CLOCK-ORIGIN-TESTED-20261019.md`. Not installed, not fold verified.
- Original #02 verified duplicate movie progress/card: original CC Resume Hub source-only change to reuse newest **mutually verified movie identity**, display one confirmed duplicate without deleting records, **5/5 tests passed**. User's actual Insidious stored IDs not yet confirmed; no data touched. Receipt `receipts/GROUP01-TASK02-VERIFIED-MOVIE-KEY-STAGED-20261019.md`.
- Original #01 TV episode source route: original CC plugin.py source-only patch, **TV-only preferred/stable route fallback**, legacy pre-verified SHOW identity fallback, rejected episode-ID guess and two-failure bypass; **9/9 fixture tests passed**. Movies retain ORIGINAL preference precedence exactly. Source commit narrowed at `9ef345369b999694c944334385b4d77aaefc18f5`, test commit `65e27c93079507895bc88113389b0b786a608a9b`. Receipt `receipts/GROUP01-TASK01-EPISODE-SAVED-ROUTE-19HOST-20261019.md`. User's actual TV item identities and Fold proof unknown.
- Original #03 horizontal rails: real signed 2103390 skin has Movies 8830 and TV 8831 panel `orientation=horizontal`, `scrolltime=150`, **14/14 Home layouts**. This is static orientation only; real touch focus/drag and **vertical Resume/Play dialog** remain uncorrected and not Fold-tested. Receipt `receipts/GROUP01-RAIL-AND-SIGNED-APK-SCOPE-AUDIT-20261019.md`. No global Kodi DialogSelect/native input edits.
- Original #19 no repeated Movies↔TV Shows reload: in-app diagnostic confirms **20 fresh Continue Watching directory jobs over ~49,584 ms under one constant revision**, 20/20 `cache_hit=0` (9 movie/11 TV) in ONE collected session. Code `group1/category_load_diagnostic.py` read-only aggregate, no private raw data committed. Exact visibility/URL/native invalidation cause not yet proven. NO #19 fix staged. Receipt `receipts/GROUP01-TASK19-REPEAT-LOAD-TRACE-20261019.md`. Do NOT touch native DirectoryProvider, Cobra, Umbrella or invent a new global cache without isolated proof.

**LATEST VERIFIED FULL HOST TEST:** `python -m unittest -v test_clock_orb_patch test_movie_identity_patch test_home_rail_contract test_group1_scope_apk test_tv_episode_route_patch test_group1_scope_apk_12`, **19/19 PASS** (Python local, ~8.44s). Strict **simulation** of potential signed APK changes: **12 of 7430** original signed 2103390 members permitted (10 Home status-orb variants, 1 CC `resume_hub.py`, 1 CC `plugin.py`), **7418 unchanged**, Cobra, native engine, shutdown, VersionCheck, services unchanged. This is NOT a signed APK/CI/Fold result. All patch scripts use exact original SHA guards, fail closed on mismatched source and never edit original/device.

**STILL REQUIRED FOR GROUP #1 ACCEPTANCE:** Real/failing TV episode route evidence and playback, actual Insidious identity/durable progress, reliable horizontal swipe/selected poster/focus, touch-friendly vertical two-choice Resume dialog scoped to Infinity only, actual cause-based solution for category-switch blank/reload (top Umbrella + Continue Watching, including genuine updates), proper fold/rotation/themes/screensaver, and final strict unchanged-Cobra/shutdown/source/Android regression tests. No combined APK; no final lock. **0/7 full groups completed.**

**MANDATORY SAVING:** Every new source/test correction must be GitHub committed with receipt, then TASK-STATUS.json and THIS handoff updated before moving beyond the checkpoint. Never claim 2103390 base was modified or that a Fold test passed when not performed.

---

## LATEST USER HARD FREEZE AND GROUP #1 HORIZONTAL SCROLL — OVERRIDES ANY OLDER GENERIC GUIDANCE

User explicitly states **Cobra and EVERYTHING ELSE INSIDE INFINITY outside exact Groups #1–#7 are OFF LIMITS**. No unapproved new buttons, menus, options, actions, source changes, removal/hiding/reordering of any existing feature, global GUI/native rebuild/refactor, opportunistic fixes or layout redesign. Protect all behavior that is not the minimum specifically named edit of the current authorized group. For even a possible shared Cobra side-effect or need to change outside the current group, **STOP AND REQUEST USER APPROVAL**. Before edits and after builds: exact file/source/APK member allowlist + before/after SHA + untouched inventory + negative regression proofs. No silently “necessary” related extras. Full directive and examples preserved in `GROUPED-01-07-BINDING-CONTRACT.md` section “HIGHEST-PRIORITY USER SCOPE FREEZE.”

User additionally requires **Group #1** to have **fully functional HORIZONTAL swipe/scroll** in BOTH **Movies → Continue Watching** and **TV Shows → Continue Watching/Resume Hub** poster rails. This is **MANDATORY PASS/FAIL**, not a future option or vertical list. Swipe left/right, choose the actual tapped card reliably without accidental launch on swipe, preserve selected poster/horizontal offset when returning or dismissing an action and retain saved progress/source identity. Separately, `Resume from [time] / Play from beginning` is a **VERTICAL** touch chooser. Verify EACH category independently on actual Galaxy Fold. If either rail does not horizontally scroll, do not mark Group 1 green.

**Precise current state:** Seven groups scoped, **0 of 7 groups actually implemented**, no bugfix source changes or APK built. Group #6 = new **Silent Mode** in System Hub (old lyrics repair skipped); Group #4 translucent glass menu material approved; Group #3 Option B design approved. No implementation group specifically authorized yet. Last edits to this note and trackers are **documentation only**. Original signed 2103390 baseline and locked 2103384 shutdown remain immutable.

**SAVE RULE:** After every tested in-group milestone and finished group commit real source/tests + immutable receipt and update TASK-STATUS.json plus THIS handoff before next task. Read current source SHA in live GitHub; do not rely on stale hardcoded HEAD.

**READ THIS FIRST.** Current approved work UNIT numbers are **GROUP #1–#7**, with detailed requirements from the existing original tasks 01–19 retained for testing. Read `repairs/2103390-bugfixes/GROUPED-01-07-BINDING-CONTRACT.md` FIRST and this handoff and `repairs/2103390-bugfixes/TASK-STATUS.json` next. Read `REPAIR-CONTRACT-01-19.md` only as the detailed subrequirement index. No renumbering of original tasks took place.

**USER'S LAST CONFIRMATION:** “Silent mode will be #6.” That unequivocally means **WORK GROUP #6 = the NEW System Hub Silent Mode On/Off setting**, NOT the original Add-on Browser subrequirement task 06 (which remains under Group #2). The previously proposed sixth work GROUP, CU LRC Lyrics bug repair (original task 16), is **SKIPPED BY USER**. Do not uninstall, disable, reinstall or repair Lyrics; future user may manage it, not authorized here.

**SEVEN ACTIVE GROUPS:**
1. Home / Continue Watching / episode resolver / movie duplicates / horizontal touch & vertical choice / clock and no MOVIES↔TV SHOWS reload (original 01,02,03,04,17,19).
2. Add-on Browser end-to-end root, submenu, menus, ZIP picker, Search and stray blue slash (original 05,06,07,08).
3. User-approved EXACT Option B long-press Movie and TV details modal (09,10).
4. Player video-icon route, Playback rows, translucent glass Video Settings + Audio & Subtitles (11,12,13,14). Glass material design **user-approved “Prefect bite to bite”**, saved at `PLAYER-GLASS-MENUS-APPROVED-20261019.md`; actual Sacrifice player controls preserved.
5. Native status139 physical Fold investigation/evidence-based correction (15).
6. **NEW System Hub Silent Mode** — Off/On suppression of unsolicited on-screen Kodi/Infinity/third-party notification banners/toasts (e.g. CU LRC Lyrics and Trakt) via safe Infinity-only presentation gate, preserve scripts and diagnostics, no forced dismissal of interactive/essential prompts.
7. Exact saved, approved group repairs only → full binding audit → new permanently signed APK → physical Fold acceptance and user final LOCK (18).

**STATUS NOW: 0/7 GROUPS IMPLEMENTED OR TESTED; 0/19 ORIGINAL TASKS IMPLEMENTED IN THIS NEW ROUND; ONE ORIGINAL TASK (16) SKIPPED.** Neither design approval nor docs count as code. This is NOT authorization to touch other groups. Wait for a specific “Fix/Proceed Group #N.” This grouping records full scopes and acceptance checks; **NO COBRA WORK EVER**, no 2103390/2103384/Essential-First changes unless expressly authorized in a confined item and proven safe.

**PERMANENT SAVE CONTRACT:** Before any group: record exact branch SHA and scoped file allowlist. After any verified in-group subtask and group completion: SAVE real GitHub code/tests commit, tests/receipts and exact rollback SHA, update GROUP statuses + detailed subrequirement statuses in TASK-STATUS.json, update THIS handoff, confirm saved URLs before moving on. Do not say “complete” for host proof alone or claim a Fold pass not performed. Do not combine until Group #7 user-authorized.

---

# CONTINUE HERE — INFINITY 2103390 POST-BASE BUG-FIX PROJECT

**First file to open when any chat/work session resumes.** User requires saving each completed task, and a new conversation must resume saved work **without asking them to repeat the whole project or restarting old repairs**.

## CONTROLLING FILES — READ IN THIS ORDER

1. **`repairs/2103390-bugfixes/REPAIR-CONTRACT-01-19.md`** — complete verbatim user directives, hard preservation boundaries, precise #01–#19 issues, limited acceptance, and "save every completed task" protocol. This controls task scope.
2. **`repairs/2103390-bugfixes/TASK-STATUS.json`** — machine-readable current state/actual completed numbers and exact commits/artifacts, which tasks are still open, last evidence, user sign-off.
3. **`repairs/baselines/INFINITY-2103390-PROVISIONAL-BUGFIX-BASE.md`** — exact signed 2103390 source/hash and immutable locked 2103384 shutdown fallback.
4. **`repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md`** — approved **exact Option B** movie and TV top-rail long-press pop-up design. Do not substitute Option A or redesign existing Infinity Home.

**Repository:** `mahfouzhassine8-ops/project-infinity`.  
**Working branch:** `work/infinity-2103390-targeted-bugfixes`.  
**Original source of signed provisional base:** `0efb67a0237c8d05ca066c5f893e6a1713bc5e2d`.  
**Base APK SHA-256:** `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`, versionCode `2103390`.  
**Signed base artifact:** [GitHub Actions run 39173982272](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982272) / artifact `12153970810`.  
**Protected locked prior shutdown:** `2103384`, SHA `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.  
**Permanent signing certificate:** `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

## ABSOLUTE NON-NEGOTIABLES

- **COBRA SHALL NOT BE TOUCHED AT ALL. NO REASON TO TOUCH IT.** Do not write Cobra files/resources/configs or a shared path that might change Cobra; STOP for separately explicit approval rather than expanding any task.
- **Only fix the item explicitly authorized by NUMBER.** Nothing else. Preserve every feature, previous correction, native playback, PiP, background behavior, player controls, skin identity and user data.
- Preserve fully working Essential-First shutdown and all protected write safeguards, and original crash reporter. No clean install, uninstall, data wipe, package/signing ID change, provider delete, baseline overwrite or speculative native crash fix.
- New post-base **tasks #01–18** are distinct from previous original **1–16** repaired/skipped gates. Do not re-open previous #1–16 tasks, rewrite fixes, or add new unrequested features. #09/10 (Option B) are **DESIGN-APPROVED ONLY**, no code implementation. #11–14 player OSD/Video Settings/Audio & Subtitles are user-requested behavior, not yet implemented.
- Every progress report must separate **source implemented, host tests GREEN, integrated Android GREEN, physical Fold verified, user-approved**. Do not check off unproven stages or claim a production lock.

## NUMBERING RECONCILIATION AND LATEST PLAYER GLASS VISUAL REQUEST

**Single controlling task IDs are 01 through 18.** Current authoritative scope: `repairs/2103390-bugfixes/REPAIR-CONTRACT-01-19.md`. Only live machine-readable completion statuses: `repairs/2103390-bugfixes/TASK-STATUS.json`. The earlier BF-01 through BF-16 descriptive draft is archived and must NOT override, renumber or compete with tasks 01–18; detailed alias map: `repairs/bugfix-program-2103390/DRAFT-BF-ALIAS-TO-CANONICAL-01-18.md`.

**Important new user wording:** “Also, for the video icon and the subtitle icon, they should be glass to where the video still can be seen through them to a sense. So if you want to mock that so we can approve it, we can do that.” Then user clarified: “I'm referring to the menu, that is.” and “If anything, playback menu should follow the same.”

**Correct scope:** MENU PANELS, not the tiny OSD icon artwork: the **Playback options popup**, **Video Settings popup**, and **Audio & Subtitles popup** all use actual Infinity liquid-glass **semi-transparent** panels so live video is visible THROUGH the panels; compact Video/Audio menus slightly smaller than original Playback; Light/Dark/OLED/Night Cinema and original player controls preserved. Original Playback's true actions are `Now Playing`, `Audio & Subtitles`, `Video Settings` (only redundant row to be removed under task12 after task11 works), `Chapters & Bookmarks`, `Playlist`, `Go To Time`, `Player Settings`, `Playback Info`, `Close Player`. AI-generated mock rows such as `Play/Pause` / `Repeat Mode` are illustrative, **NOT APPROVED ACTIONS**.

**Visual reference/spec saved:** `repairs/2103390-bugfixes/PLAYBACK-GLASS-MENUS-VISUAL-PROPOSAL.md`; latest mock shown in current conversation. **User has NOT yet approved exact opacity/layout of new glass menu mock.** Proposal only, 0/19 detailed tasks implementations remain complete, Cobra still absolutely OFF-LIMITS. If a future chat is asked to implement canonical task 11/12/13/14, read and obtain any missing user visual approval first. Do not interpret the mock as permission to change controls.

## SAVED STATUS AT HANDOFF

**As of October 19, 2026: TRACKER UPDATED TO #19; 0/19 NEW TASKS IMPLEMENTED OR COMPLETED.** This handoff created documentation only; no Kodi engine, APK, skin, Cobra or user data was changed.

**Compact task map:**

| Number | Scope | State |
|---|---|---|
| 01 | TV Shows Continue Watching unresolvable episode source | OPEN |
| 02 | Duplicate Insidious/movie Continue Watching records | OPEN |
| 03 | Continue Watching horizontal touch and Resume/Play choice popup | OPEN |
| 04 | Home moon/weather icon overlapping upper-right clock | OPEN |
| 05 | Add-on Browser stray blue slash in header | OPEN |
| 06 | Add-on Browser root hierarchy/nav/instructions | OPEN |
| 07 | Browser My Add-ons/Available Updates/Recently Updated | OPEN |
| 08 | Browser Repository/ZIP picker/Search subpages | OPEN |
| 09 | Movies top rail — EXACT approved Option B long-press details | DESIGN LOCK ONLY |
| 10 | TV top rail — SAME exact Option B long-press details | DESIGN LOCK ONLY |
| 11 | Video/monitor-looking OSD button opens Video Settings | OPEN / USER-REQUESTED |
| 12 | Remove ONLY redundant "Video Settings" row from Playback popup | OPEN / USER-REQUESTED |
| 13 | Dedicated compact Video Settings modal, smaller than Playback | OPEN / USER-REQUESTED |
| 14 | Dedicated compact Audio & Subtitles modal, smaller than Playback | OPEN / USER-REQUESTED |
| 15 | Native engine exit 139 missing traceback / root cause | OPEN / DIAGNOSTICS FIRST |
| 16 | CU LRC Lyrics script TypeError | SKIPPED BY USER — NOT A REPAIR |
| 17 | TMDb Helper/SlyGuy startup quarantine | TRIAGE ONLY |
| 18 | Selective combined signed APK + strict final physical Fold audit (run after accepted #19 if user authorizes) | FINAL GATE NOT STARTED |
| 19 | Movies↔TV Shows show retained populated rails immediately on each navigation, no reload after initial startup | OPEN / USER-REPORTED |

## EVIDENCE TO REUSE (PRIVATE USER UPLOADS; NEVER COMMIT RAW)

- `19021.jpg` and `19028.jpg`: TV Continue Watching unavailable source dialog.
- `19035.jpg`: actual Infinity Home, double Insidious cards and moon overlapping clock. **Authoritative Home visual layout reference**.
- `19042.mp4`: Continue Watching touch selection and Resume/Play vertical choice.
- `19032.mp4`, Add-on Browser screenshot `1792383561650.jpeg`: browser menu issues and stray header slash.
- `19043.jpg` stock Kodi title-detail concept; `19045.mp4` actual Infinity top Home rail; `infinity_ui_interaction_options_mockup.png` approved option B visually.
- **NEW screenshot `1792386488186.jpeg`**: Playback popup over `Sacrifice`, includes `Now Playing`, `Audio & Subtitles`, `Video Settings`, `Chapters & Bookmarks`, `Playlist`, `Go To Time`, `Player Settings`, `Playback Info`, `Close Player`. Bottom OSD video/monitor-looking button is user-reported inert; user requests it open Video Settings, remove only redundant Playback popup Video Settings entry, and make Video Settings and Audio & Subtitles smaller compact popups.
- `Infinity-Diagnostics-20261019-000835.zip`, `Kodi_Diagnostics_20261019T042154Z-2eaea0ee.zip` and earlier diagnostics (user-owned; private) for installed components, TV route and add-on script exceptions. Avoid copying sensitive logs to public repo.
- Earlier original 12:55 EDT Oct 18 status139 and native crash evidence review in `repairs/full-system-20261017/CONSOLIDATED-THREE-UI-AND-NATIVE-EXIT-BRIEF.md` and `repairs/four-repair-20261018/STOP-TRACE.md`.

## REQUIRED TASK WORKFLOW IN EVERY FUTURE CHAT

1. Read controlling files and the latest GitHub commits; identify the **one user-authorized exact task number** and its current status.
2. Do NOT skip user authorization or silently revise original task definitions.
3. Save before modifying source: exact prechange SHA + unchanged baseline + task scope/allowed paths.
4. Reproduce, make the narrow actual correction, add targeted positive + fail-closed negative tests.
5. After each numbered task, **COMMIT ALL SOURCE + TESTS + STATUS/HANDOFF UPDATE** to GitHub. Record exact git SHA, changed files, test run IDs, APK/ZIP hashes if any, open failures, physical test evidence, rollback anchor, next number.
6. Update **both `TASK-STATUS.json` and this `CONTINUE-HERE.md`**, so if chat closes a different assistant can resume from the last saved task without recreating it or inventing successes.
7. Only combine completed user-accepted numbers when user orders combination. Independently preserve all other files/native libraries/add-ons and Cobra; fail closed if any gate red.
8. Final full fold test + original 2103384 working Close and no data loss, then user alone approves final lock.


## NEW USER REQUEST — #19 MOVIES/TV SHOWS STAY POPULATED AND GLASS MENU CLARIFICATION

**Verbatim #19:** “If you look at the video, how we can go from movies to TV shows, and it would be as if, like, they would have to reload going from movies and TV shows. It should not be that way because as soon as I start up Kodi, or I mean Infinity, and everything populates, everything should be there at all times. Unless, obviously, I shut down Infinity and it comes back, and I turn it back on and it reloads, which is fine, but that should not happen.”

**Recording:** `19049.mp4` (approx. 76.9s). Switching into TV Shows briefly shows already-populated category/add-on tiles but blank Umbrella Latest Releases/Continue Watching. Those appear later in the same running app. Root cause/provider lifecycle **unverified**. Requirement is to retain ready Movies and TV content while session runs and not visibly reload on each tab switch; a true cold startup or Close/reopen may load normally. No permanent stale data, provider bulk refetch or RAM leak.

**Verbatim #12–14 visual direction:** “Also, for the video icon and the subtitle icon, they should be glass to where the video still can be seen through them to a sense. So if you want to mock that so we can approve it, we can do that.” “I'm referring to the menu, that is.” “If anything, playback menu should follow the same.”

**Explicit corrected object:** This is about the semi-transparent **MENU PANELS**: existing Playback list (#12), smaller Video Settings modal (#13), smaller Audio & Subtitles modal (#14). Not about changing the OSD toolbar icon appearance. Video OSD icon functionality remains task #11. The background video should be partially perceivable through the glass, respecting Light/Dark/OLED/Night Cinema and reduced/off motion. All original functional rows and their handlers remain intact except the separately approved redundant Video Settings row removal in #12. Do not substitute conceptual mockups' movie names or different menu rows for the user's actual `Sacrifice` player screenshot. Exact glass material **APPROVED BITE FOR BITE** (see new approved glass contract); generated concepts are not code or an approved runtime screenshot.

**Status after saving:** This changed **documentation only**. 0/19 new fixes implemented, original signed 2103390 base intact, 2103384 shutdown locked, COBRA NEVER TOUCHED.

## WHAT TO DO NEXT

At this savepoint, **no work group has been selected for implementation**. Work unit selection uses Group #1–#7. The user just added task #19 with recording `19049.mp4` and clarified that existing Playback, Video Settings and Audio & Subtitles menu SURFACES should be translucent glass, not toolbar icons. These are specifications, not completed fixes.

**Next user-facing response:** Show GROUPS #1–#7, emphasizing GROUP #6 = NEW System Hub Silent Mode, old Lyrics repair skipped; mention glass menu design saved/approved and original tasks 01–19 retained as subrequirements. Confirm 0/7 groups implemented. Ask which GROUP to authorize, then implement ONLY that group, saving every tested milestone and complete group to GitHub. No code changes from this documentation alone.
