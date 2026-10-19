# GROUP #1 — CRITICAL SIGNED-BASE COMPATIBILITY CHECKPOINT (2026-10-19)

**Source-only correction and executed test; no new APK, CI signed build, device installation, physical Fold pass, or user lock. Group #1 remains IN PROGRESS.**

## Newly proven integration defect in signed 2103390

The original 2103390 Android APK (SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`) contains BOTH first-party controllers:

- `assets/addons/script.infinity.uirepair/controller_access.py`: `load()` refuses to load Command Center unless every source SHA in its `CONTROLLER-PREIMAGES.json` matches.
- `assets/addons/script.infinity.watchedbridge/controller.py`: `verify()` likewise refuses compatibility/actions unless the same 13 Command Center file hashes match.

Their original contract JSON bytes are IDENTICAL (SHA-256 `f091b91bc4c8a62c06327348fa3f57d4411ecce58e44c883ff4aa888fe9edebf`). Both explicitly pin the ORIGINAL `plugin.py` and `resume_hub.py`. The separately staged Group #1 TV resolver and movie-identity fixes change exactly those two file contents. **Without this compatibility correction, the shipped Continue Watching rail's selected uirepair provider can return an empty/error directory, and the watched bridge can reject its original operations. The previous 12-member virtual APK scope check therefore was NOT sufficient for a working integrated Group #1.**

## Surgical source-only correction staged and committed

- `repairs/2103390-bugfixes/group1/cc_preimage_contract_patch.py` committed **`9d6bc1845e3f392cbe48ed86aa96eb73cc79d681`**.
- `repairs/2103390-bugfixes/group1/test_cc_preimage_contract_patch.py` committed **`0bf2be94fcbfa22e64344ca9b8105f7614708c13`**.
- The patch derives the two NEW SHA-256 values from the previously approved, exact-hash protected Group #1 patch functions; it refuses unknown inputs, an out-of-contract original controller, a mutated contract JSON or re-patching.
- Original `plugin.py` SHA: `11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd`. Staged: `ded5e435f1db7af205869ae33d9e2eab888825d95f5086095bc4615e09b05b4f`.
- Original `resume_hub.py` SHA: `7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff`. Staged: `087860b6a551a23fdd8f7f11ab103b367f0ef44be32b5b42cadecf907e548784`.
- Exactly two expected hash STRINGS change inside each of the two existing `CONTROLLER-PREIMAGES.json` files. **All other 11 Command Center source-file trust pins remain byte-identical; neither `controller_access.py` nor `controller.py` nor their behaviors change.** No source identity, authorizations, error paths, or write/admission gates are widened.

## Executed verification (real signed APK bytes, host only)

Command from the saved Group #1 scripts with original Actions artifact mounted:

```
cd repairs/2103390-bugfixes/group1
python -m unittest -v test_cc_preimage_contract_patch
```

**5/5 tests PASSED** locally in ~3.59 seconds:

1. Confirm real signed APK and both consumers' 13-file pin maps match every original Command Center file.
2. Prove both original maps reject the newly corrected controller files and both narrowly amended maps accept all 13 exact staged/original files.
3. Prove tampered original contract, plugin/hub files, or attempting to re-patch fail closed.
4. Prove immutable original files and two explicitly staged JSON copies, no write to original.
5. Full original **7,430-member** signed APK in-memory comparison of ALL staged Group #1 changes: exactly **14 proposed changed members**, **7,416 unchanged**. The exact list: **10** `skin.infinity.diggz` Home status-orb include variants, **1** Command Center TV `plugin.py`, **1** Command Center movie `resume_hub.py`, and **2** first-party dependent contract JSON files. No members added/removed. **Cobra, native libraries, Essential-First shutdown, Version Check, third-party providers, UI Repair and Watched Bridge executable logic unchanged in this simulation.**

Local test source Git blob SHA `bcdec3434e2194275756dda1ad582371526577c4` matched fetched committed file; two original staged Group #1 modules and clock patch matched their committed Git blobs too. These tests do NOT establish that installed external add-on copies, actual directory provider focus, or app startup/reopen will work on the Galaxy Fold.

## Next acceptance gates (still RED)

Task **01** user-specific TV failing episode must play with real verified route; **02** real Insidious identity/progress must update one card; **03** reliable real horizontal swipe/selected poster and spacious VERTICAL Resume/Play chooser; **04** physical Fold clock/orb clearance; **19** actual cause-isolated no blank/reload on rapid Movies ↔ TV Shows; theme/orientation/persistence regressions and no Cobra changes. Preserve full original 2103390 base; no combined APK until Group #7 authorized.

This checkpoint supplements, and corrects the integration assumptions of, the historical `test_group1_scope_apk_12.py` receipt. **Do not ship a candidate that changes only 12/7430 and omits the two pinned consumers.**
