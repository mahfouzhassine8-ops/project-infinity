# INFINITY GROUP #1 — VERTICAL CONTINUE WATCHING CHOOSER + TASK #19 LIFECYCLE FORENSICS

**Date:** 2026-10-19. **Group #1 status: IN PROGRESS, NOT COMPLETE.** This receipt reports only **source-only staging and host tests**. No new, merged, installed, or permanently signed APK; no physical Samsung Fold test; no user sign-off; no final lock.

## Protected parent and hard boundary

Original signed developmental 2103390 SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`. Original 7,430 APK members and immutable 2103384 shutdown fallback preserved. Cobra, shutdown / Essential-First, native Kodi GUI/player and installed device were **not edited**. Skipped SlyGuy and Lyrics work stays skipped; no third-party provider or user data mutation.

## Task #03 additional source fix STAGED (not Fold-qualified)

Root source: original Home panels 8830 and 8831 are native horizontal directory-backed Continue Watching rails; default unified Fold item geometry was separately corrected in prior checkpoint. Their built-in Resume/Play chooser is owned by Kodi's `CVideoSelectActionProcessor` and `DialogSelect`; changing that global dialog may affect Cobra.

The new **first-party-only experimental** approach:

- `repairs/2103390-bugfixes/group1/continue_choice_patch.py`, source commit `bed9bd932edd5b9ed0643b6a3c3ec55a11641518`, verified Git blob `b5775c1597d603c3b53757be334cb8321f9ff458`.
- Strict SHA-guarded patch of original `assets/addons/script.infinity.uirepair/runtime.py` plus exactly **two `<onclick>` actions in each of the original 14 `skin.infinity.diggz/*/Home.xml` variants**, targeting Movies ID 8830 and TV ID 8831. Each action is conditional on first-party UI Repair availability; original native click remains the fallback if that addon is unavailable. Does not edit other Home controls or other view types.
- Reuses existing `script.infinity.uirepair/popup.py:choose()` and `InfinityItemOptions.xml` with **vertical 78-pixel touch rows**: `Resume from M:SS` / `Play from beginning`; native Kodi `DialogSelect` and Cobra remain unchanged. Back cancels the modal.
- Selected key is validated against `hub.KEY_RE` and original `hub.entry_identity`. The original Command Center `_target` and `_list_item` retain source identity, video info, artwork and watched state. The live item is reread after modal dismissal; changed source/identity/progress fails closed instead of playing stale data. No provider searches, link guesses, history write, watched reset or preference mutation.
- Action uses Kodi's documented `xbmc.Player().play(target, listitem)` with original ListItem and `StartOffset`/`ResumeTime` set to saved position or zero. **This dispatch route is NOT byte-for-byte the same as original native PlayMedia(resume/noresume); physical provider/Kodi tests are REQUIRED to prove no duplicate native chooser, correct stream resolution and correct resumed position before any acceptance.** If it fails on Fold, reject the candidate; preserve original APK. Source staging alone does not prove user-visible repair.

## Task #03 tests — host only

- `repairs/2103390-bugfixes/group1/test_continue_choice_patch.py` commit `7fc82b6e42052bdea7e3850b3fcd33656fbcaa62`: **12/12** targeted local cases (original signed parent and 14 Home variants, two-click-line isolation, strict executable runtime delta, malformed/reapply refusal, unchanged unrelated components, movie/TV saved offset, begin-at-zero, cancel, stale route, changed progress, invalid key and unavailable safe message). Kodi/UI mocks for player calls; **no physical Fold playback**.
- New full virtual scope test committed at `repairs/2103390-bugfixes/group1/test_group1_scope_apk_29.py`, commit `51b0f661b8141512c28b14efc528f737d3600d56`. Independently executed local member-by-member signed parent test: **1/1 PASS**, matching all expected exact staged Group #1 transformations. The committed integration guard imports the previously staged patch scripts for the equivalent checks; it was not separately run in a GitHub CI checkout in this checkpoint.

**Exact virtual Group #1 candidate member inventory: 29 of original 7,430 members proposed changed, 7,401 unchanged.** Breakdown: 14 existing Home XML variants, 10 existing Home-orb include XML variants, 2 Command Center controller sources (`plugin.py` TV; `resume_hub.py` movie), 2 first-party controller source-integrity JSON manifests (only the two expected CC hashes in each), 1 existing `script.infinity.uirepair/runtime.py` implementing only the scoped Home chooser. **No APK members added or removed; no Cobra, native library, Essential-First shutdown, Version Check, third-party plugin, UI Repair popup artwork or watchedbridge executable modified.** Prior 12-, 14-, and 15-member dry-run receipts are historical and superseded for the proposed candidate; no newly packaged APK exists.

## Task #19 — diagnostic only, still NOT FIXED

Native Kodi Omega's `CGUIBaseContainer::UpdateVisibility` ordinarily preserves hidden provider items; a `CDirectoryProvider` refresh may instead come from URL change, `INVALIDATED` announcements or full Home reset. Exact source review also showed Home's existing `infinity_continuity.py` publishes a changing `Infinity.Continuity.HomeLoad` marker on Home initialization and aggregates state in its in-app `continuity.json`. This is a useful **existing** diagnostic; do not add a new runtime monitor or write in the shutdown path.

- New **offline-only** `group1/home_reload_correlation.py` commit `c1546bd9e49264d003c2c3cfae08bcfccfbad58f`; test `group1/test_home_reload_correlation.py` commit `a1ae517749f922aa52304ed2ad01566b03b654bd`. **4/4 synthetic tests PASS** for reinitialized Home markers, repeated jobs without false cause, no privacy leaks and missing export sections.
- It reads an existing user-exported diagnostic ZIP and reports bounded aggregate Home load changes / Continue Watching directory starts, without printing saved paths, user identity, titles or source URL. **A changed HomeLoad confirms window reinitialization, NOT the event that caused it.**
- The previously measured real Fold diagnostic has 20 Continue Watching directory jobs over ~49.6 seconds with unchanged revision (all 20 cache_hit=0); it does not yet include a proved cause-correlated native invalidation/URL + visibility trace available to this session. The precise cause of BOTH Umbrella latest releases and Command Center Continue Watching blanking is still unproven. **Do not suppress legitimate refresh or cache third-party media blindly; #19 still red.**

## Executed combined host evidence

Local `python -m unittest -q test_continue_choice_patch test_integrated_scope_29 test_home_reload_correlation`: **17/17 pass** in about 4.5 seconds with the exact signed 2103390 parent; Python/mock tests and deterministic virtual APK comparison only. `test_integrated_scope_29` is the locally executed independent virtual equivalent of the committed `test_group1_scope_apk_29.py`. Previous 19/19 and 17/17 host batches were separate; do not falsely describe a single combined full suite or runtime Android CI result.

## REQUIRED BEFORE CHECKING OFF GROUP #1

1. Verify original failing TV episodes resolve (and genuinely unavailable episodes fail safely) on the user's actual Fold.
2. Verify real Insidious records represent same movie and durable progress updates one existing card.
3. On both Fold displays, verify swipe vs tap, poster selection and scroll offset; vertical two-choice popup resume/start behavior, cancellation/back and audio/video source continuity. If Python playback changes original semantics, correct or reject source patch.
4. Verify clock/orb non-overlap across rotation and themes.
5. Prove cause and fix #19 no blank/reload for **both** Umbrella latest-release and Command Center Continue Watching while legitimate updates still refresh. No unproved native or provider modification.
6. Perform strict unchanged Cobra/shutdown audit and real combined signed APK install-over + physical Fold validation only under separately authorized Group #7 packaging gate. No premature lock.

**Status: 0/7 complete groups, Group #1 not complete, source tests only.**
