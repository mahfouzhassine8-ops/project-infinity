# Infinity + Cobra 2103438 — USER-APPROVED WORKING LOCK WITH ONE OPEN ISSUE

**Direct user instruction (October 31, 2026):** "Lock recent but needs 1 fix"

**Decision:** The most recent successfully original-key signed APK in the authorized Cobra-only development task is **2103438**. The user explicitly requests to LOCK that release **as it stands**, while acknowledging ONE **unspecified** outstanding issue. This is a **working/provisional acceptance with an open issue**, NOT a claim of full defect-free approval, completion of the next repair, or authority to modify/rebuild anything.

## EXACT immutable signed release identity

| Item | Exact value |
|---|---|
| Package | `com.projectinfinity.kodi` |
| Combined Android versionCode | **2103438** |
| Signed APK filename | `Infinity-2103438-Combined-Original-Signer.apk` |
| Actual APK SHA256 | `a1907acbcb3a36f5b2312f8a11cd4e38d8fcdbed2f435b6ab45d369adc8e9f35` |
| Original signing certificate SHA256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Exact signing-source commit | `a5f721578c53e026a26cf21d929fbdad530f6d17` |
| Successful original-key signing workflow | [41250066560](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560) |
| Signed APK archive artifact | [13061405460](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560/artifacts/13061405460) |
| Matching component ZIPs artifact | [13060877683](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560/artifacts/13060877683) |
| Immutable-by-convention source lock | `lock/infinity-cobra-2103438-user-approved-pending-one-fix-20261031` → EXACT `a5f721578c53e026a26cf21d929fbdad530f6d17` |

**Exact component archive SHA256 hashes**

- `COBRA.zip`: `2229274553616f4febb7ef80925eddc23f6f2346bddf4eeabee18e819158399e`
- `INFINITY.zip`: `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` (**EXACT INFINITY 2103437, unchanged**)
- `MINIMAL_ANDROID_CONTRACT.zip`: `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`
- `CHOOSER_SHELL.zip`: `145c0639a6387659391fa312e646c533a681f6d7e98c0f823d787477a6691266` (truthful Cobra version metadata; executable/UI unchanged).

## Accepted baseline scope and evidence

The signed438 update brings existing **Cobra Cards appearance compatibility** with the current native Dark/Light/OLED theme resolver. The original signed437 behavior remains frozen outside the authorized Cards palette changes.

Original-key signing and verification passed in run41250066560. The independent signed437-versus-signed438 actual artifact comparison shows only **seven changed APK ZIP members** (two Cobra DEX members, one typed versionCode manifest, one truthful chooser version property, and three original-key signature metadata members), none added/removed; 7,610 nonsignature members unchanged. Infinity’s owner assets/DEX and ZIP are byte-identical to signed437; all 47 native libraries, launcher resources, minimal/shared runtime, chooser executable/UI and unrelated components are unchanged. Method-level evidence reports 7,160 unchanged original Cobra class definitions; only 7 Cards styling classes plus necessary component-version literal changed, and two palette-adapter classes were added. Full source and evidence: `repairs/cobra-2103437-cards-theme/DELIVERY.md`, `evidence/delivery438/STATUS.json`, `SHA256SUMS`, `COMPLETE-APK-DELTA.json` on the engineering branch.

**Physical acceptance qualification:** The signed APK had no full physical Fold runtime/stream/decoder or Android 17 acceptance within CI. User says "Lock recent but needs 1 fix"—treat it as user approval to retain this working build, not proof that every scenario is flawless. The ONE outstanding issue has **not been described** in the current request. Do NOT infer which widget, theme, mode, player, device configuration or control is defective. Do not pre-approve a fix based on speculation.

## LOCK rules — no code change and no automatic corrective work

1. **Preserve the exact 2103438 signed APK and all matching component ZIPs, source SHA, original signer certificate and this frozen lock**. Never rebuild, replace, rebase or advance the signed baseline branch.
2. Preserve original approved 2103437 signed source `31d55543e3a01a37975c396c0291ff26d98cc4b8` and lock `lock/infinity-cobra-2103437-user-approved-20261031`, plus 2103436 and all earlier backups/recovery locks. 2103438 is working baseline; 2103437 remains a prior recovery.
3. **Infinity 2103437 remains fully frozen** in the combined 2103438 APK, including its loading system, skin, providers, playback/persistence, shutdown and data. **All unrelated Cobra behavior remains frozen**: Mobile, Compact, Grid, Pro/Pro Sports, Multi-View, Cards geometry/controls/playback/drawer, PiP/More, user settings and guide data. No additional modification by this lock request.
4. The **single outstanding issue is OPEN / UNSPECIFIED / NOT AUTHORIZED FOR IMPLEMENTATION**. Await the user’s actual description, reproduction media and explicit correction scope before investigation or development. Do not assume that the open item is theme-related simply because this was the last themed release.
5. When the issue is described and a corrective scope is approved, start a NEW Cobra-only branch **from the exact signed 2103438 commit**, not from later engineering/report commits. Make only the single authorized change; prove full 2103438 source/member preservation for every other owner and system. Produce a separately versioned signed install-over *testing candidate* only after relevant gates pass and await user Fold approval before a later lock.
6. Do not uninstall/clear app data, change databases, run shutdown stress, automatically promote release authority or push unrelated changes. Original Android key/package `com.projectinfinity.kodi` stays unchanged.
7. This GitHub branch is a source reference preserved by convention, **not a guarantee of GitHub branch-protection enforcement**. Actions download artifacts may expire under retention settings; preserve external backups of the original APK and ZIPs.

**STATUS: EXACT SIGNED 2103438 USER-APPROVED WORKING SOURCE LOCK CREATED; ONE UNSPECIFIED FIX PENDING. NO NEW APK, CODE PATCH, SIGNING OR DEVICE CHANGE FOR THIS LOCK.**
