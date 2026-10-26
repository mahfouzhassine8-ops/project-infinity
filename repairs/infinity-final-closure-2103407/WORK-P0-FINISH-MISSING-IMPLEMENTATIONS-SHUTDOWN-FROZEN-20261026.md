# INFINITY — USER P0 COMPLETION DIRECTIVE: FIX ONLY INCOMPLETE ITEMS, FREEZE WORKING SHUTDOWN, SIGN APK

**Explicit user authorization / highest priority — October 26, 2026.**
**Repository:** mahfouzhassine8-ops/project-infinity  
**Branch:** work/infinity-final-corrective-from-2103407-20261025  
**Current examined signed candidate:** 2103419 / run 40396544415, source a24db78554da7bc40a2a0b658ba441793f1c1605, APK SHA256 0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a.  
**Immutable historical reference:** protected 2103407 and physical Fold working installed 2103410.  
**User's new instruction:** Everything else works. Whatever is missing, incomplete, incorrectly integrated or unresolved in the original approved seven-workstream brief becomes the highest-priority repair. Finish it and produce a newly signed install-over APK with exact matching ZIPs. **Shutdown is working perfectly: PRESERVE IT and DO NOT REQUIRE OR RUN ANY NEW SHUTDOWN TEST. Do not make shutdown verification a dependency for producing or signing this corrective APK.**

This document is a **targeted implementation/delivery directive**, not a generic audit or an authorization to redesign already working features. The original seven-workstream brief and protection requirements remain in force except that the user's explicit latest instruction supersedes their old requirement for *new repetitive or real-device shutdown tests* as a pre-signing gate. It does not waive genuine data safety or native write-fence requirements. Work must fetch and use this directive rather than blindly following an older continuation statement demanding fresh shutdown cycles.

## A. HIGHEST PRIORITY — DIRECTLY CONFIRMED INCOMPLETE SIGNED-APK INTEGRATION

**P0-1: Repair Latest Releases context-menu relocated-helper reference.**

- In the signed APK: `assets/addons/script.infinity.commandcenter/context.py`, around lines 546–560, for `plugin://plugin.infinity.latestreleases/`, resolves `script.infinity.uirepair/latest_identity.py`.
- That original-root file is **absent** from the signed APK and matching UI Repair ZIP. The correct authenticated decoder exists at `assets/addons/script.infinity.commandcenter/infinity_modules/uirepair/latest_identity.py`. Its actual hash matched the trusted literal in the old caller (SHA256 `225ac23336701db63715583ca8b6716afa96bb9b738b4b99750d9a5bbd8ab223`).
- Correct the caller to the authentic signed migrated Command Center module, preserve exact identity/path/hash validation and action behavior, and avoid copying a redundant untrusted shim or disabling checks. Keep first-tap/second-tap/hold and verified-title selection behavior unchanged.
- Closure: signed APK contains the correct caller AND decoder, manifest re-signed, matching component ZIP, no reference to missing old decoder in this route.

**P0-2: Repair Health Center read-only component-source inventory.**

- In the signed APK: `assets/addons/script.kodihealthcenter/infinity_runtime_identity.py`, around lines 15–25, still scans original top-level file paths for `script.infinity.uirepair`, `script.infinity.watchedbridge` and `script.infinity.rails` that were intentionally relocated into `script.infinity.commandcenter/infinity_modules/...`.
- It can falsely label the authentic live consolidated modules as `MISSING_OR_UNVERIFIED`. Update the inventory to validate the correct signed module locations plus genuine installed extension-point shims, preserving original signature/source-digest checks and read-only behavior. Do not bypass verification, mutate Health Center saved data, or re-add obsolete original-root scripts.
- Closure: shipped Health Center checks the actually packaged paths and reports their authentic identities, not phantom missing items. Matching APK/package member and helper ZIP audit.

## B. HIGHEST PRIORITY — ACTUAL UNFINISHED PERFORMANCE, LOADING, CONTINUE PLAYING, REFRESH

**P0-3: Finish first-usable Home + Continue Playing/Continue Watching speed and correctness.**

The existing signed package DOES contain several narrow improvements; **keep them**:
- Local Resume Hub snapshot/revision invalidation (Command Center `resume_hub.py`).
- Per-render signed source-contract memoization (`experience.py` / `plugin.py`).
- Bounded Search query/result cache introduced in 2103418 (`infinity_search.py`), with existing source/lease/TTL checks.
- Earlier Home helper de-duplication and optional refresh/skin publisher cache.
- 2103419 skin 1.0.5.246 conditional PlaylistBrowser invocation when installed; the previously observed absent helper job took 24.163 seconds.

But these **are not the entire original loading/refresh optimization**. User's physical Fold 2103410 reference recorded Continue/Resume first-card delays around 0.55s, 1.68s and **10.23s**. The slow operation spent ~10.17s in native directory fetch, with 41–42 jobs queued, and another observation exceeded 100 queued (up to 114). Source read memoization measured mere milliseconds; do not represent it as an instant-Home fix.

Work required:
1. Trace real cold/warm icon→experience decision→Kodi usable→Home first usable→Continue first REAL selectable card→artwork→live refresh. Separate cold native startup from warm same-session return and the user's chooser dwell.
2. Make verified per-profile local saved Continue cards **actually visible and actionable in the first Home viewport** without waiting unnecessarily for providers/non-visible image/metadata rescans. Retain exact movie/TV/season/episode IDs, saved resume position, watched/finished rules, provider capability validation, optional Trakt, and **no autoplay**. A placeholder is not an implementation.
3. Reduce demonstrated native directory queue contention and redundant Home invocations: coalesce identical jobs, prioritize first viewport, avoid offscreen artwork on critical path, safely cancel stale invisible work, don't duplicate provider refresh, avoid full-window reconstruction on Stop/Back→Home; preserve Kodi/Command Center owned leases and Essential-First write protection.
4. Finish correct prompt refresh after playback progress/Stop/Back, watched/unwatched, list/Watchlist/Favorites/Save for Later, provider enable/disable/install, Latest Releases updates. Current local snapshot must never overwrite fresher watched/progress/source state or use a stale unsupported provider route.
5. Make browsing, scrolling, transitions, card selection, touch-to-visible response and fold/rotation rendering visibly smooth with correct image reuse, bounded caches and memory/CPU/worker growth. Respect Android effective refresh-rate and Power Saving; don't force 120Hz, stretch/recolor video or disturb other sessions. Preserve player PiP/background behavior and Light/Dark/OLED design.
6. Record honest before/after local-first Home, Continue card, native fetch, poster, queue, memory/jank timings where technically possible. Do not confuse elapsed proof/capture time with actual first paint; no invented sub-second startup claim. The mission is **a real speed fix in the signed runtime**, not another test-only optimization or stress suite.

**P0-4: Complete any other demonstrably missing pieces from the ORIGINAL brief, with minimum touched code.**

- Compare the original seven groups against the **actual 2103419 signed APK + five ZIPs** and identify any truly absent or misrouted feature. Fix **confirmed missing or incomplete implementation**, not something that merely lacks an artificial repetition count.
- Specifically scrutinize original Infinity Movies/TV/Latest Releases first-tap select, deliberate second-tap launch, exact press-and-hold options, provider-independent Save for Later, Watchlist, Favorites, Collection, watched/unwatched, correct popup focus/scroll and preserved source identity; repair only a real missing/incorrect route. Preserve already working Otaku, WatchNixtoons2 and other providers.
- Check only originally approved Option B synopsis/details/scroll, popup clipping/overlap, skin themes/logo/clock and player OSD Rotate/Play-Pause/seek/time corrections; fix a missing or stale coded feature, **do not redesign working screens**.
- Check the original health export/diagnostic action is still present and wired (apart from P0-2), and Command Center remains unified, authenticated and source-pin correct. Leave real working operations alone.
- Provider compatibility: handle only actually evidenced, verifiable installed provider routes; never guess plugin actions, substitute a similar title, invent unsupported routes, or exempt a provider from universal media-identity/data safety.
- Provide a concise requirement→actual APK member→disposition ledger: `INCLUDED_PRESERVE`, `P0_FIXED_AND_INCLUDED`, `UNRESOLVED_WITH_EXACT_REASON`. An unobserved physical interaction is NOT proof that code was omitted. Avoid vague “tests not verified” in the implementation inventory.

**Conditional nonblocking issue:** Signed 2103419 currently has 46/47 ARM64 ELF libraries with 4KiB PT_LOAD alignment, incompatible with a strict 16KiB-page environment; APK ZIP page alignment alone doesn't change ELF alignment. The user's physical Fold page size was not checked, while the existing installed Infinity physically closes successfully. **Do not overhaul shared native or touch Cobra to appease a synthetic 16KiB emulator**, and do not let unrelated strict-16KiB emulator runs block this scoped signed APK. Truthfully disclose the compatibility limitation. If the actual target Fold requires 16KiB, report as a real compatibility blocker requiring separate safe, Infinity-only solution; no silent omission or unsafe waiver.

## C. ABSOLUTE FREEZE: ESSENTIAL-FIRST SHUTDOWN IS WORKING — DO NOT TOUCH OR RE-TEST

**User's highest-priority instruction: no new shutdown test for this APK and NO shutdown-testing dependency for APK signing.**

- **Freeze** production Power→Close behavior, authenticated native owner inventory, all 16 essential saves, Java/native coordinator/receipt/seals/termination, late protected-write fences, timeout/unknown-writer fail-closed policy, and the 2103419 signed shutdown runtime binaries/helpers/manifest-specific owned semantics. Freeze saved Infinity/Cobra/Ask/Just This Time launch preferences and Samsung Home/Recents policy; Cobra is 100% off limits.
- Preserve historical results as already adequate for this scoped freeze: signed 2103419 **three visible real Power Close/reopen passes**, run **40397618519**, 16 owners/native/two-Java/engine+coordinator/actual external zero-UID PIDs/SQLite/preferences/source/Continue state. Independently, unsafe shared-writer veto and native-image handling passed run **40397718606**. Earlier 2103418/417/411 results also exist. **Do not repeat any of these tests or add new shutdown test scenarios.**
- **Do not invoke** existing shutdown workflow as a new signing, packaging, upload, code change, or release prerequisite; do not create a new Android shut-down fixture, three-cycle scene, opaque-writer test, alternate termination requirement or synthetic stress run. Do not run new tests just because a build version or non-shutdown module changes.
- Use an **unchanged-member/source-hash comparison only**, against the signed 2103419 parent, to demonstrate shutdown binary/Java/Python/Power-route ownership wasn't modified (allow listed rebinding of non-shutdown first-party signed manifests to match genuinely modified code, with authenticated hash checks retained). A changed hash in manifest due solely to separately authorized code updates is not a shutdown redesign. Ensure the original signing checks and preserved data flows remain enforced.
- **If a proposed P0 fix would require modifying a shutdown-owned component or a shared Cobra path, stop that part and report the specific conflict rather than changing the working shutdown.** The rest of the approved APK can still be built and signed independently, with exact uncompleted-item disclosure. Never fake the absence of a genuine persistence risk.
- No clean install, uninstall, data wipe, broken signing identity or forced experience choice.

## D. BUILD/DELIVERY CONTRACT — NO MORE AUDIT-ONLY OUTPUT

1. Continue from current correct signed 2103419 source; retain protected 2103407, installed user data and all known good 2103419/418 features. **Do not restart the project or open new workstreams.**
2. Implement and integrate P0-1, P0-2 and P0-3, plus any genuinely absent original-brief P0-4 item, into production APK members and matching signed Command Center / skin / helper component archives as applicable.
3. Full original-key signing, exact APK/ZIP member digest and module manifest verification, Android install-over packaging compatibility, ABI, and checksums remain required. **Signing happens when integration files are ready; no new shutdown test gate, no 50/30/20 stress-loop gate, and no physical Fold pre-signing gate.** A compiled artifact is not automatically declared accepted on the Fold.
4. Do a SMALL, meaningful non-shutdown walkthrough for changed behavior (Latest Releases title context; Health Center inventory; local-first Home/Continue Playing movie & TV; refresh after Stop/Back; one realistic Search→title→save/list→Home journey). Tests must not overwrite original user data. Report genuine UI outcomes and remaining limitations; do not hold signing hostage to unrelated emulator startup/stress configurations.
5. Deliver the **actual signed install-over APK and exact matching component ZIPs**, full SHA256, successful build run, version/source, simple install instructions. User performs the final physical Fold acceptance when ready. **No fictitious all-features pass claim, no extra diagnostic-only APK, no new shutdown test.**

**Release decision: The user wants working behavior and completed implementation—not repeated artificial loops. Prioritize unfinished code, integrate, SIGN and DELIVER, while leaving the proven shutdown completely unchanged.**
