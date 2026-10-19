# GROUP #1 — ORIGINAL 03 HORIZONTAL RAIL, ORIGINAL APK PAYLOAD SCOPE — HOST EVIDENCE

**Status:** SOURCE-ONLY/READ-ONLY VERIFIED, **NO CHANGE TO SIGNED APK**, NOT INSTALLED OR PHYSICAL FOLD-PASSED. Do not mark full Group #1 complete.

## Tests saved and actual base

- Exact signed 2103390 APK source: `Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk`, SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`.
- Original source asset skin `skin.infinity.diggz` version 1.0.5.228.
- Read-only layout regression `repairs/2103390-bugfixes/group1/test_home_rail_contract.py`, real source Git blob `a012fc816766c96217ccc91638f8e65785777282`; saved source commit `cf1b3c577a2e7561bafe492b4157efe38f2e0da0`. **Host PASS.**
- Read-only whole-APK member-scope guard `repairs/2103390-bugfixes/group1/test_group1_scope_apk.py`, Git blob `63a83137517575d7a0af91ec5d08b281164c202c`; saved commit `1a1802ac95310409061eb222a5f9705ded1febaa`. **Host PASS.**
- Combined local command (working directory group1 stage): `python -m unittest -v test_clock_orb_patch test_movie_identity_patch test_home_rail_contract test_group1_scope_apk`. **9/9 tests PASS**, `Ran 9 tests in 6.887s — OK`. Source-only unit/layout/virtual APK patch-diff tests, **not** Android/Fold UI tests. Applies only to exact 2103390 preimage.

## HORIZONTAL Continue Watching — precise evidence

Inspect every actual `skin.infinity.diggz/{16x9|fallback|responsive variants|unified}/Home.xml` from exact APK-derived source ZIP:

- **14 / 14 `Home.xml` variants** have BOTH panel IDs 8830 (Movies → Continue Watching) and 8831 (TV Shows → Continue Watching) defined as original Kodi **`control type="panel"`**.
- Both have explicit `<orientation>horizontal</orientation>`, `<scrolltime>150</scrolltime>`, different original category visibility properties and `InfinityCompactContinueMoviesPath` / `InfinityCompactContinueTVPath` existing Command Center destinations.
- No panel relayout or replacement is necessary or authorized solely to keep horizontal orientation. **Original source passes static orientation gate.**
- **This does NOT certify touch gesture responsiveness, correct poster selection after swiping, or selected horizontal offset retention on Fold.** User's recording `19042.mp4` shows difficulty and a separate vertical `Resume from [time] / Play from beginning` chooser. Task03 remains **OPEN FOR PHYSICAL INPUT WORK**. Do not change shared Android touch, native input, Cobra or global Kodi `DialogSelect` without proof and exclusive scoping.

## Exact original 7,430-member APK delta firewall (in-memory only)

A read-only test opens the signed APK from its original GitHub Actions artifact, iterates **all 7,430 members** of the real installed base, and calculates an **in-memory, SHA-guarded** candidate using ONLY the two separately saved stage patches:
- 10 existing skin `Includes_InfinityHomeUnified.xml` status-orb variants (the exact task04 health-orb/clock overlap correction), no new controls.
- 1 existing `assets/addons/script.infinity.commandcenter/resume_hub.py` verified movie duplicate identity/presentation logic (task02), no data wipes/third-party addons.
- **Potential changed source members: exactly 11 / 7,430**. All remaining **7,419 members** unchanged in memory, including Cobra resources, libs, native code, Version Check, compatibility service and shutdown files. No member added or removed.
- **This is a virtual change inventory, NOT evidence of a signed 2103391 APK, build success, or actual install.** Tests refuse unknown source SHA, changed input, nonsupported APK member counts or out-of-scope edits.
- Signed source base unchanged. No user data or installed device modified.

## Additional Group1 red gates still remaining

- **01 TV episode resolver:** User-specific failing and working episode verified saved source/series IDs absent from supplied diagnostics. Current original Command Center route policy may reject unverified show IDs or expired nonstable route. A root cause cannot be assigned to any particular episode without actual identity/source evidence; NO provider patch yet. Skipped independent SlyGuy and TMDb startup-error task17 remains SKIPPED.
- **02 Insidious duplicate:** 5 synthetic host tests pass with fully verified identical IDs; actual user Insidious ID equality and durable playback update not yet proven. No saved data changed/deleted.
- **03 horizontal swiping and vertical chooser:** Static orientation passes; touch precision, no accidental launches, vertical picker touch target and scroll offset on real Fold not physically tested; no patch to shared dialog.
- **04 clock/orb overlap:** 2 targeted source unit tests pass, source-only patch staged; actual Fold visual/cutout/theme proof missing.
- **19 Movies/TV content staying populated:** User recording `19049.mp4` shows repeat blanks; actual Kodi source includes category-gated visible panels and external plugin content. Exactly which cache invalidation/removal mechanism causes reload **has not been proved**, so no unsafe global native cache or addon edits.
- Group #1 overall: **NOT DONE** until all targeted fix and real Fold proof requirements pass. Group #2–7, other Infinity features and Cobra completely off limits.

**Never claim source-host green equals working production behavior. Save this evidence with the group tracker and continuation handoff.**
