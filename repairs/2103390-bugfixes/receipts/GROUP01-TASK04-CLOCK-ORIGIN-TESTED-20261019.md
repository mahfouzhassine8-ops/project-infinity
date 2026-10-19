# GROUP #1 / ORIGINAL TASK 04 — CLOCK/ORB OVERLAP TARGETED CHECKPOINT

**Status:** SOURCE CORRECTION STAGED, TARGETED HOST TESTS GREEN, **NOT PACKAGED/INSTALLED/FOLD-VERIFIED**, GROUP #1 OVERALL STILL IN PROGRESS.

## Specific verified cause

Actual signed 2103390 APK under `assets/addons/skin.infinity.diggz/16x9/Includes_InfinityHomeUnified.xml` (and corresponding exact fallback/responsive/unified skin variants) defines `InfinityHomeStatusCluster` with BOTH the pulsating health/status orb icon and the clock label sharing `$PARAM[timeleft]`. When the live text `12:06 AM` or `11:52 PM` occupies this left edge, the orb collides with the clock. Real user screenshot `19035.jpg` shows the collision.

**Exactly approved fix:** Reposition ONLY the existing health/status orb's left anchor from `$PARAM[timeleft]` to `708` (clock left remains `742`) to create a 16px gap between the 18px orb and the clock left edge. Do not change text, weather data, date, fonts, buttons, theme, header graphics, focus or native runtime. All responsive skin include variants carry the same minimal edit, no extra controls.

## Saved source/tests

- Preimage exact signed 2103390 build source: `0efb67a0237c8d05ca066c5f893e6a1713bc5e2d`.
- Staged patch source: `repairs/2103390-bugfixes/group1/clock_orb_patch.py`; GitHub blob SHA `12225afea1dd77275443506e51ae29d54b48c29e`.
- Automated exact-skinned archive conservation tests: `repairs/2103390-bugfixes/group1/test_clock_orb_patch.py`; GitHub blob SHA `1f931e5f5c3d8af458432fa3240f7cff88321f39`.
- Source file commit `d78f95445342651703f70031df51777cd3a05142`; test file commit `9d52bbc17364234e7733b99f4618b567940b1b57`.
- Original signed APK member list: 7,430 total APK entries (no native changes from this patch). Exact source skin has 3,072 ZIP members including 10 status-cluster variants.
- SHA of conversation-exported skin ZIP (recompressed, *not original signed build package*): `d1a6dab62e59ec9f44ee7b5840343407596452eff27326f1ab15413d1c2363ca`. All **10 original status-cluster file bytes independently matched those in the original signed 2103390 APK**.
- Candidate PATCHED SOURCE-ONLY skin archive SHA: `24df313e6964088953ddf4701900bea008032fdec58bc5fdd72511e06358993d`. **Not a tested/final installable user release, not signed APK, not user-approved APK.**
- Changed ZIP members: exactly **10** `Includes_InfinityHomeUnified.xml` variants (16x9, fallback, seven responsive widths, unified); **3,062 other skin members byte-for-byte identical** to 2103390 source asset ZIP. Exact counts tested in code. No Cobra assets or code inspected for modifications because none were altered.

## Tests actually run (local Python, real APK-derived skin)

Command from staged `group1` directory: `python -m unittest -v test_clock_orb_patch`.

- `test_does_not_modify_original_source_or_add_controls` — PASS.
- `test_only_orb_anchor_moves_in_all_variants` — PASS.
- Result: `Ran 2 tests in 6.170s — OK`.
- Exact original unmodified source remains unchanged; running patch twice is rejected by the original asset SHA guards; same-path in-place overwrite is rejected.

## Remaining before acceptance

- No physical Fold screenshot/test yet. Must compare at 11:52 PM/12:06 AM, time/date/weather font scaling, both Fold displays and supported Light/Dark/OLED/Night Cinema themes.
- No Android runtime test, installed over APK/skin package, permanent signing, or combined Group1 APK.
- The other Group #1 faults 01 (episode route), 02 (verified duplicate movie identities), 03 (horizontal swipe and vertical chooser touch), 19 (category reload), are still **OPEN**. SlyGuy/TMDb startup task 17 and CU LRC Lyrics task 16 were **explicitly skipped as independent repairs**, never patched.
- Original protected shutdown 2103384, signed 2103390 and Cobra remain unchanged. Never mark Group #1 complete until ALL accepted group tasks and Fold gates have passed.

**NEXT ACTION:** Continue Group #1 ONLY, with evidence-driven scoped fixes and GitHub saved/tested checkpoints after each milestone. Do not modify unrelated Infinity functions or Cobra.
