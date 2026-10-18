# Infinity 2103390 — Nine-item integrated experimental APK: signed packaging GREEN

**Date:** 2026-10-18. **This is NOT a final user lock or physical Fold approval.**

## Exact combined scope and source
- Approved integration numbers: **#1, #2, #3, #4, #5, #6, #9, #10, #12** only.
- Explicitly excluded from new work: **#7, #8, #11**. Previously present components remain protected.
- Original shutdown-locked Android APK: **2103384**, SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.
- Original permanent signer certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Fresh source-matched native input compiled/signed and passed its *own* fresh/loaded Android tests: [native run 39169187099](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39169187099), native source commit `b6434fe29d1b78451a4911a2760afa6b36d307e8`; this includes the current #3 identity guard and preserves previously verified #9/#10 native source.
- Final assembly source commit `0efb67a0237c8d05ca066c5f893e6a1713bc5e2d`.

## Combined artifact (ONE APK)
- **VersionCode:** `2103390`
- **Exact file:** `Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk`
- **Signed APK SHA-256:** `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`
- **Result:** [combined workflow 39173982272](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982272) **SUCCESS**, including exact native-parent identity, source ZIP digests, copied parent member preservation, permanent signing, final unsigned-vs-signed binary-delta check, and a fail-closed packaging receipt.
- **GitHub Actions artifact:** [12153970810](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982272/artifacts/12153970810), named `Infinity-2103390-Exact-Nine-Combined-EXPERIMENTAL-NOT-FOLD-QUALIFIED` (artifact container is separate from signed APK).

**Hash-pinned included components:**
- Full skin `skin.infinity.diggz` **1.0.5.228** source ZIP SHA `39f8f041376748fbe209868a33ef51e1cfd59082ee6ebb8ad095e6f85336bdef`.
- `script.infinity.uirepair` **0.1.2** with reviewed Rails .026/.027 compatibility source ZIP SHA `40e89389d624109bba9d9a6a85b90eb656f8e3decdf2d5a96da82e10c0ae277e`.
- `script.infinity.rails` **0.2.7** Mocha repaired source ZIP SHA `e3b8614bc024d25159b64721ec5efe2b26b8c1bf0589dc03a0a33e7a9f02eddf`.
- `script.infinity.watchedbridge` **1.0.1** source ZIP SHA `dbc913459c148052ce46b30241d77c4a2c7d29bea45fddcad82496ebe9ad0029`.
- Original Command Center and required official skin resource dependencies preserved/included under their verified IDs.

## Evidence-backed Compatibility preservation
- Existing signed 2103384 (inherited by 2103385) contains **`service.infinity.compat` 0.7.2**, manifest SHA-256 `aa894dc9678edfb5ba9781de2ef5c7594a2883900291550364675ee4e19f30a9`.
- **It was unregistered** in the original `assets/system/addon-manifest.xml`; original manifest SHA-256 `84f38b810e7c99b1f4e97e44341a63d8d9c0c8bdb06d183ca4d4467c93c681a2`. Actual approved skin .227/.228 does **not** require this service.
- The external 0.8.2 staged version was **NOT integrated**. Combined package preserves the original service **member bytes and original registration state**.
- Read-only proof: [run 39173462632](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173462632). Negative tests reject an unexpected service upgrade, extra file, or newly activating the original service.

## Verification completed (NOT final release)
- [Current nine-item integration host tests 39173982368](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982368): **SUCCESS**.
- [Original locked 2103384 source/shutdown preservation 39173982311](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982311): **SUCCESS** (source-only, NOT a new physical shutdown success).
- [Actual combined APK packaging and permanent signing 39173982272](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39173982272): **SUCCESS**.
- Package gate reports **no deleted prior APK member**, no original Compat or Version Check byte change, no Cobra-named payload change, `libinfinitycrash.so` preserved, native Kodi engine inherited from freshly verified 2103384-derived input delta.
- Earlier failed workflows were evidence and rejection gates. Do NOT reclassify them as passing or distribute older failed experimental APK artifacts.

## Mandatory outstanding #13–16 acceptance
1. The exact **2103390 signed combined APK** must pass fresh/loaded **Android17 API37** runtime activation and original feature UI tests, including .228 Rotate, .012 Continue Playing/Video Sources, .027 Rails menu, .101 watched/Resume/Watchlist/Collection.
2. The exact signed APK must pass genuine Essential-First Close/reopen, 16 essential durable owners, zero blockers, session continuity, background return, fold/unfold and saved state on target Samsung Galaxy Fold; do not weaken original shutdown policy.
3. Verify safe **install-over** without uninstalling/clearing existing Diggz skin, PVR, user data, provider profiles, databases, or currently enabled add-ons.
4. Confirm runtime Cobra untouched, #1–16 binding audit with skips, original native crash diagnostics available and original 00:55 status-139 crash investigation preserved. **Native crash root cause/fix still UNKNOWN**.
5. User explicitly reviews and approves final lock. **Do not label signed experimental output final/install approved** until the above gates are satisfied.

**Status: SINGLE SIGNED EXPERIMENTAL APK AVAILABLE FOR FURTHER TESTING. NO FINAL LOCK.**
