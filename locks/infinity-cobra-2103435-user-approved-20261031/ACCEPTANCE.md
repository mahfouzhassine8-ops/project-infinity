# Infinity + Cobra 2103435 — user-approved signed release lock

**User approval:** October 31, 2026 — direct instruction **"Okay lock 35"** after physical Galaxy Fold evaluation. Treat this as an explicit release-lock instruction, not authorization for more feature changes or a statement that all unmeasured functionality passed every possible test.

## Exact frozen release identity

| Field | Value |
|---|---|
| Combined package | `com.projectinfinity.kodi` |
| Locked combined versionCode | **2103435** |
| Signed APK file | `Infinity-2103435-Combined-Original-Signer.apk` |
| SHA256 | `dc83faed4a8eb1d2e2e116914cf15f2f1c27cc2a8653813fd6701ba300234442` |
| Original signing certificate SHA256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Exact signed source commit | `e0c6153588992001d84076d33fdf8f0d676c0d00` |
| GitHub Actions signing run | [41125367621](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41125367621) — SUCCESS |
| Original-key signed APK artifact | [13011191050](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41125367621/artifacts/13011191050) |
| Matching owner ZIPs artifact | [13009774373](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41125367621/artifacts/13009774373) |
| Signed-source lock branch | `lock/infinity-cobra-2103435-user-approved-20261031` → exactly `e0c6153588992001d84076d33fdf8f0d676c0d00` |

**Component ZIP SHA256 values from original signed delivery verification:**

- `CHOOSER_SHELL.zip` — `30589df7f2459a133b8fdd34f0bc56f8a5dc363d4f36accbb523a7ae47185f14`
- `COBRA.zip` — `e67dd28dab95206dcda8cb88903828453da57670468c532a32cd1db077663893`
- `INFINITY.zip` — `a99e7bb789a0817fdfc9cc10b4e1649d52a2c78f0e3375f0735c55f4a91a0336`
- `MINIMAL_ANDROID_CONTRACT.zip` — `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`

Verified upstream evidence: `repairs/cobra-next-from-2103427/cards-from-2103431/consolidated435/DELIVERY435.md`, `SHA256SUMS`, independent downloaded archive/owner verification, and original-key signing logs.

## Lock rules

1. **Freeze this exact signed release and component contents** as the new **user-approved recovery/working baseline** for both experiences. No editing the signed source snapshot branch, replacing original APK artifacts, rebasing the lock, or signing a different payload under this lock name.
2. Do **not** alter any existing protected 2103427, 2103431, 2103432, or 2103433 references and archived APKs. Rejected 2103434 remains historical failure evidence; do not call it accepted.
3. Preserve original 2103435 Cobra and Infinity behavior byte-for-byte in the lock, including all provider settings/data, currently accepted UI, player controls, PiP, and Essential-First shutdown. Keep signing identity, source-authentication and owner gates unchanged.
4. This release's successful CI and chosen Android checks are recorded in upstream delivery evidence; physical user approval is grounded only in user's explicit instruction to lock. **Do not infer broader untested Fold conditions as automated PASS**.
5. Any future correction starts a **separate engineering branch from this locked commit**, modifies only the specifically approved owner/feature, passes focused preservation tests, and creates a separately versioned, originally signed install-over APK. Do not silently merge concurrent Cobra and Infinity feature experiments; one owner per feature release unless user explicitly reauthorizes.
6. This is a Git source **snapshot/lock branch**, not proof of GitHub repository branch-protection enforcement. A signed archive has separate GitHub retention settings; retain copies for durable recovery. Locking does not perform any action on the installed Android device and does not affect its user data.

**Lock creation verification target:** the branch must resolve to `e0c6153588992001d84076d33fdf8f0d676c0d00` and comparing that branch to the signed source commit must yield zero changed files. This acceptance record belongs on the engineering branch, not inside the source snapshot, so signing source identity remains exact.

**Status:** USER-APPROVED 2103435 LOCKED SOURCE SNAPSHOT. No new app build, signing, or installed-device operation was requested or performed by the lock action.
