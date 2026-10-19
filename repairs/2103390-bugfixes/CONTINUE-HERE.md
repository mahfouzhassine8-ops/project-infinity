# CONTINUE HERE — INFINITY 2103390 POST-BASE BUG-FIX PROJECT

**First file to open when any chat/work session resumes.** User requires saving each completed task, and a new conversation must resume saved work **without asking them to repeat the whole project or restarting old repairs**.

## CONTROLLING FILES — READ IN THIS ORDER

1. **`repairs/2103390-bugfixes/REPAIR-CONTRACT-01-18.md`** — complete verbatim user directives, hard preservation boundaries, precise #01–#18 issues, limited acceptance, and "save every completed task" protocol. This controls task scope.
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

## SAVED STATUS AT HANDOFF

**As of October 19, 2026: TRACKER CREATED; 0/18 NEW TASKS IMPLEMENTED OR COMPLETED.** This handoff created documentation only; no Kodi engine, APK, skin, Cobra or user data was changed.

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
| 16 | CU LRC Lyrics script TypeError | TRIAGE ONLY |
| 17 | TMDb Helper/SlyGuy startup quarantine | TRIAGE ONLY |
| 18 | Selective combined signed APK + strict final physical Fold audit | FINAL GATE NOT STARTED |

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

## WHAT TO DO NEXT

At the moment of this save, **no new task number has been selected for implementation**. The current user requested the entire enumerated contract and persistence/savepoint behavior, and most recently supplied the Playback screenshot for tasks 11–14.

**Next user-facing response:** Show tasks 01–18 succinctly but distinctly, mention the 4 newly added player changes, confirm 0/18 fixes done in this new round, provide direct links to the contract and this handoff. Ask which task number to authorize, then begin **only that one**, with mandatory saved progress after tests. Do not attempt any implementation from this handoff itself.
