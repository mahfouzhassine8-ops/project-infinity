# NUMBERING RECONCILIATION — ONE AUTHORITATIVE REPAIR LIST

**IMPORTANT:** Two documentation-only task lists were added on the same development branch during October 19, 2026. This file prevents accidental work under conflicting number identifiers.

**SOLE CONTROLLING SEQUENCE GOING FORWARD:** tasks **01 through 18** in repairs/2103390-bugfixes/REPAIR-CONTRACT-01-18.md. The corresponding live status and restart instructions are repairs/2103390-bugfixes/TASK-STATUS.json and repairs/2103390-bugfixes/CONTINUE-HERE.md.

**RETIRED DRAFT LABELS:** BF-01 through BF-16 from repairs/bugfix-program-2103390/MASTER-BINDING-TRACKER-BF01-BF16.md are an earlier descriptive grouping and are **not** live execution numbers. The BF document remains archived because it contains valid fine-grained acceptance details, but must never compete with the 18-task status tracker. All new savepoints and user authorization use NUMERIC 01–18. No code change or work acceptance is implied by this mapping.

| Retired BF draft | Definitive task ID(s) | Exact mapped scope |
|---|---|---|
| BF-01 | 01 | TV Shows Continue Watching source resolution |
| BF-02 | 17 | TMDb Helper/SlyGuy startup quarantine investigation |
| BF-03 | 02 | Duplicate Insidious movie progress |
| BF-04 | 03 | Continue Watching horizontal card selection/swipe half |
| BF-05 | 03 | Continue Watching Resume/Play chooser vertical hitbox half |
| BF-06 | 06 | Add-on Browser root screen, instructions and footer |
| BF-07 | 07 and 08 | Add-on Browser My Addons/Updates; Repository/ZIP/Search |
| BF-08 | 05 | Add-on Browser stray blue slash |
| BF-09 | 09 and 10 | Exact approved Option B Movies and TV Shows separately |
| BF-10 | 04 | Header clock and moon overlap |
| BF-11 | 16 | CU LRC Lyrics script error triage only |
| BF-12 | 15 | Native crash exit status 139 root cause |
| BF-13 | 15, diagnostic comparison only | Separate signal 9/OS reclaim classification; not silently a crash fix |
| BF-14 | 18, precombination audit gate | Protect all binding rules |
| BF-15 | 18, combined signed APK stage | Only approved saved fixes |
| BF-16 | 18, physical Fold and final user lock stage | Final verified acceptance |

**ADDITIONAL USER-REQUESTED ITEMS IN THE CONTROLLING 18-TASK LIST:** 11 OSD video/monitor button → Video Settings, 12 remove ONLY duplicate Video Settings row in Playback popup, 13 compact Video Settings popup, and 14 compact Audio & Subtitles popup. These were captured in a separate user-directed handoff with the exact quoted behavior and are not silently implemented by this reconciliation. They require task-specific approval and preservation like any other item.

**Cobra and the 2103384 shutdown base remain absolutely off limits.**

If a user says “fix #03” in a new chat, that means **canonical 03**, covering both rail hitbox and chooser; never interpret “BF-03” as canonical 03. If the user explicitly references “BF-03,” translate to canonical **02** with this table and confirm if needed before changing code.

**Completion status when saved:** all canonical 01–18 OPEN, Option B 09/10 approved as design only, 11–14 user-requested behavior recorded, native status139 unresolved, no new post-2103390 code implemented. User must choose item.

**Only repairs/2103390-bugfixes/TASK-STATUS.json is live machine-readable progress state.**
