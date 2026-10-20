# Infinity 2103391 — Pro seven-group audit continuation

## Current status — resume here, do not restart

User authorized review and correction of all seven approved groups, including stability and the specifically approved visual polish. No additional features or redesigns. Cobra and all unrelated Infinity behavior are protected. The user resumed after a thinking interruption.

**This is a verified SOURCE-CORRECTION checkpoint, not a completed seven-group repair, corrected APK, Android runtime pass or final LOCK.**

Repository: `mahfouzhassine8-ops/project-infinity`
Audit branch: `work/infinity-2103391-pro-seven-group-audit-20261019`
Verified corrective source commit: `335de7d7e1390abc8486f223997fe05c50dbdfb4`
Successful targeted source-test/save workflow: `39363356305`
Workflow input commit: `41fbb6a36249ee150c848b2a4b033fd40bad2112`
Prior original audit snapshot / rollback: `c04a54c96470117c0bfcc1aae9d4e0d5c0b8bcb0`
Frozen pre-correction classifier reference used by regression tests: `83df773b742dc3f7e576a90157a04c15bc61fdb3`

Do not run the one-shot `apply_source_corrections.py` on the already corrected tree: its exact original-preimage and reapplication guards intentionally reject that. Resume from the saved source and receipts instead.

## Immutable release evidence

Original signed producer: `39348480827`, source `7bd9b1085d598789e9e803b4b76ee1429e1df7e3`.
Matching standalone exporter: `39352426448`, source `6eaf464c1fbc119aa9fd93ff1b0b2b093fb3810f`.
Signed APK: `Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk`.
APK SHA256: `47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151`.
ARM64 libkodi.so SHA256: `dcf227b435256cc974157714c29d9498c52de0fd86d20ee7b8ca9a21af50fe91`.
Permanent signer SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Protected parent 2103390 SHA256: `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`.

Independent original audit workflow `39360977682` verified original signature schemes v1/v2/v3, package/version, CRC and inventory, but failed runtime-component coherence. Integrity is not functional correctness. Original native compilation/signing existed; this Pro correction has NOT been rebuilt into a new Android engine or APK.

The initial audit incorrectly treated every legacy native contract as a simultaneous requirement. That audit error is corrected: complete contract variants are alternatives, and every pin inside a selected variant is mandatory. Inactive Compatibility 0.7.2 remains unregistered and is not a new mismatch to solve by activation.

## Confirmed defects and implemented source corrections

### 1. Native classifier did not recognize final Group1 controller bytes

Three complete Command Center 0.3.5.20 contracts (service/plugin/context entry points) still pinned pre-Group1 versions of `plugin.py` and `resume_hub.py`.

| File | Old native pin | Actual signed Group1 pin |
| --- | --- | --- |
| plugin.py | 11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd | ded5e435f1db7af205869ae33d9e2eab888825d95f5086095bc4615e09b05b4f |
| resume_hub.py | 7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff | 087860b6a551a23fdd8f7f11ab103b367f0ef44be32b5b42cadecf907e548784 |

Actual source correction: append exactly three complete reviewed 13-file Group1 variants to `InfinityScriptCheckpointContracts.cpp`. All original variants and classifier logic remain byte-for-byte intact outside the insertion. The other eleven pins must match. No arbitrary version acceptance, owner-count change, skipped write proof, new owner, or alias bypass.

### 2. Standalone ZIP retagging broke otherwise exact controller dependencies

The exporter changed Command Center's manifest from 0.3.5.20 to 0.3.5.21 without changing the checkpoint runtime's declared 0.3.5.20 identity or either dependent helper's complete manifest preimages. It also retagged UI Repair, Watched Bridge and the skin. Matching non-manifest code alone was insufficient.

Actual source correction: export gate now requires manifest/checkpoint/helper/native identities to agree before any output, and prohibits post-signing version rewrites. Embedded helper preimages already matched the final Group1 code; do not falsely claim those embedded helper files were stale.

**The existing signed 2103391 remains rejected. This gate is not a new installable ZIP set and is not an instruction to downgrade installed add-ons.** Safe coordinated install-over versioning and recovery of already installed 0.3.5.21 remain unfinished.

### 3. Tests and audit reliability

Added `group7/release_coherence.py` and `test_release_coherence.py`. Twelve targeted regressions compile and execute the actual old and corrected C++ classifier with host digest/path test doubles. They reproduce old rejection, accept exactly reviewed bytes, reject every one-file mutation and missing pin, preserve all prior contract variants, reject wrong identities including Cobra/escaped aliases, reproduce manifest-retag incompatibility, and reject export from the unchanged old native binary.

Fixed an invalid Group2 test assertion: additive source patches can retain an original substring inside the exact replacement. The test now verifies exact reconstructed output and unique insertion rather than requiring that preserved substring to vanish. No production browser code changed in this Pro correction.

Restored Group1 fixtures from the exact protected signed parent instead of treating absent files as passes. Temporary runner directory permissions and generated report whitespace were corrected without disabling test or commit gates.

## Latest executed seven-group host results

Source receipt: `audits/2103391-pro/verified-source-checkpoint/seven-group-host-status.json` at the verified corrective commit.

| Group | Scope retained | Latest host result | Still not proved |
| --- | --- | --- | --- |
| 1 | Home, Continue Watching, movie/TV identity, header | 53 tests, zero skips, pass | Task19 category reload remains deferred; actual Fold scroll/touch/resume |
| 2 | Native Add-on Browser actions/focus/ZIP input | 19 passed, 1 skipped | Real native source checkout fixture; Android browser behavior |
| 3 | Approved Option B Home long-press popup | 26 tests, zero skips, pass | Actual long-press dispatch, exact selected poster, Rails fallback on Fold |
| 4 | Existing player icon/actions and three glass menu surfaces | 10 tests, zero skips, pass | Player rendering/materials, original aspect-ratio capability accessibility, audio/subtitle/PiP preservation |
| 5 | Native identity and crash forensics | 10 tests, zero skips, pass | Original SIGSEGV faulting instruction and root cause; this is NOT a crash fix |
| 6 | One System Hub Silent Mode switch and scoped passive toasts | Suite not passing | Two native toast tests require missing `GUIDialogKaiToast.Omega.cpp`; actual toast/dialog/audio isolation |
| 7 | Integration, identities, export, preservation | 22 tests, zero skips, pass, including 12 new regressions | Coherent rebuilt Android binary, installed-profile recovery, signed final package and Fold qualification |

The successful workflow certifies targeted source corrections and saves the complete mixed-result report. It does NOT turn the incomplete Group2/6 fixtures, original release mismatch, or physical behavior green.

## Latest Fold evidence boundary

The existing committed read-only review at `repairs/2103390-bugfixes/receipts/FOLD-2103391-DIAGNOSTICS-20261019-213206-READONLY.md` and the opening of `repairs/2103390-bugfixes/CONTINUE-HERE.md` records the actual 21:32 diagnostic ZIP. During this resumption local Python/container analysis failed; that prior record was re-read, not a fresh raw-ZIP decode.

It records installed APK2103391, skin1.0.5.229 and CC0.3.5.21; helper versions are NOT identified by that diagnostic snapshot. Its two distinct Close failures include `exactly_one_canonical_resident_required` and a later checkpoint deadline with 15 essential owners incomplete. A small advisory blocker count is not complete durability proof.

The recorded native tombstone shows a signal-handler re-raise, not the original faulting instruction. The exit artifact does not establish the crashed APK/native producer identity. Do not attribute that crash to the currently installed binary, a provider, graphics, Python or APK size without further evidence.

## Required next implementation and qualification

1. Preserve this exact source correction; align the next explicitly inventoried install-over controller/helper/manifest/native versions and repair startup/duplicate-resident ownership through its actual cause. Do not rename a manifest alone, whitelist a synthetic duplicate, drop owner requirements, overwrite user databases, or clear data.
2. Restore the genuine pinned native source fixtures for Group2 and Group6 and run their full host tests without skips. Reconcile the native reconstruction/source ledgers with the exact added contract variants; do not bypass the preimage or build manifest checks.
3. Rebuild the real Android ARM64 engine, verify source-to-ELF correspondence, integrate only approved seven-group members, verify complete controller contracts in the resulting package, sign with the permanent key, and compare the exact APK delta. No new APK currently exists for these corrections.
4. Keep the original native SIGSEGV investigation open and obtain usable original-instruction evidence with matched symbols. Preserve diagnostics; never treat a fingerprint or signal re-raise as a root-cause fix.
5. Recheck all required physical Fold behaviors, existing themes, approved menus/materials, Home/Rails/input, original aspect controls, player/audio/subtitles/PiP/background continuity, Silent Mode and complete Essential-First Close/reopen. Group1 task19 remains explicitly open. No user final LOCK until these gates and user approval.

## Saved proof and preservation

Corrective artifact: `12238820300`, run `39363356305`, name `Infinity-2103391-Pro-Corrective-Source-Tests`.
Artifact SHA256: `0d8dbf7668ae8ac5fe977ce52501cf900f2d46daec645214154235e65a3bcfef`.
Saved receipts: `audits/2103391-pro/verified-source-checkpoint/` includes STATUS, source before/after hashes, original-release rejection, all seven group results and the targeted test log.

Comparison from original audit snapshot to verified corrective source contains 16 files: audit workflows/tools/receipts, one test correction, exporter/gate/tests, and the native contract-table insertion. No Cobra source/resources, providers, skin XML, player implementation, user data, or unrelated runtime functionality was modified by this Pro correction. The original signed APK is byte-identical. No installation, uninstall, data clear or final LOCK occurred.
