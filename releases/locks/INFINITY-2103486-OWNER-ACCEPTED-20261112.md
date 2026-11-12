# 🔒 INFINITY / COBRA — OWNER-ACCEPTED LOCKED BASELINE 2103486

**Recorded:** 2026-11-12  
**Status:** OWNER ACCEPTED — NEW PRESERVATION BASELINE  
**Package:** `com.projectinfinity.kodi`  
**Version code:** `2103486`  
**Approval:** The owner explicitly instructed: "lock everything. And that is our new base. And preserve everything."  
**Scope:** Freeze the complete signed combined APK and all its working behavior. Do not infer that untested functions passed.

## Exact signed artifact — authoritative identity

- Filename: `Infinity-2103486-Combined-Original-Signer.apk`
- APK SHA-256: `550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197`
- Release/signing source: `fe44ec40cd3e43fb5498084dec24c59dd63c3f3a`
- Original-key signing Actions run: `43200317103` — **PASS**
- Signed artifact ID: `13935631408`
- Official signed artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43200317103/artifacts/13935631408
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- APK signature verification: v1, v2, v3 **PASS**.
- Native `libkodi.so` SHA-256: `b75747363c83a548d61463c2fd434be909f27c07d4872fa9d9c61642a3757635`
- Native repair source build checkpoint: `9ce852ebb044a82853ef93af24e34a07ed96daff`; ARM64 build run `43186634362` **PASS**.
- Packaging preservation report: `PASS_ORIGINAL_SIGNED_EXACT83_PRESERVATION`, 7,766 unchanged payload members; Cobra unchanged; Core source/load path unchanged.

### Component identity (preserve exact installed combined build)

- Infinity: `2103486.infinity.startupqa.1` — source `41d9596073e5b7445531105696ede325746ddf5b`
- Chooser shell: `2103486.chooser_shell.startupqa.1` — same source `41d9596073e5b7445531105696ede325746ddf5b`
- Cobra: `2103445.cobra.1` — source `73edb4f25b9e25d67cd8e0c41d44e74931f2b8ef`
- Minimal Android contract: `2103447.minimal_android_contract.1` — source `a5dcae39a49cf44a341f659969bfbee78ba93986`
- Original permanent signing identity preserved; package ID unchanged.

## Physical Galaxy Fold acceptance evidence

Owner reports that Infinity, its menus and Python add-ons load normally; the earlier intermittent empty-shell startup symptom has **not recurred** since its earlier correction. Owner then installed and tested **2103486** on Samsung SM-F976U1, Android 17, and reported successful normal shutdown.

The user's `Infinity-Diagnostics-20261112-053934.zip`, locally read and verified for this checkpoint (only its SHA-256 and selected *non-sensitive* outcomes are recorded; do not publish the raw ZIP), has SHA-256:

`608dd25b290bf5094ae39f7cad7ec7eec4643b6cd32d1a2477d8d7b0fc9a9a55`

The matched `checkpoint/coordinator-receipt.json` states:
- `phase=COMPLETE`; `exit_policy=essential_first_process_exit_v1`
- `exit_kind=essential_verified_process_exit`
- `total_duration_ms=1995` (1.995 seconds)
- All **16 explicitly essential** owners have finished required writes with `COMMITTED` or `ALREADY_DURABLE`.
- Native essential writes: `admission_sealed=true`, `essential_writes_durable=true`, `essential_writes_sealed=true`
- `blocker_count=0`; `active_native_writers=0`
- `authorization_consumed=true`, `process_death_confirmed=true`
- `python_services` was optional and pending; it did not hold final shutdown hostage.
- `whole_package_death_confirmed=false` in this receipt: do not claim that separately.
- Same-profile relaunch **after this particular shutdown** was not expressly reported; it is not marked accepted by inference.

**Acceptance scope:** successful physical Fold startup behavior as owner reported, and a verified **normal essential-safe Kodi process shutdown** on 2103486. The owner explicitly promotes this exact build as the new baseline. Do not repeat unnecessary acceptance tests to justify this owner lock.

## Nonnegotiable preservation rules for all successors

1. **2103486 is the new starting baseline, not 2103483 or diagnostic 2103484.** 2103483 and 2103477 remain untouched historical/recovery references, not the active owner-approved base.
2. Keep the **exact signed 2103486 APK** and original signing certificate identity. Do not overwrite the signed binary, artifact, branch, or approval evidence.
3. Preserve **all** currently working Infinity behavior: Python startup/no empty shell, Essential-only shutdown, Watchlist/tracking, Search, providers, playback/resume, skin/UI/layouts, menus, networking, Command Center, configuration, data, and user profiles.
4. Preserve **all Cobra** functionality, mode layouts, player controls, settings, and UI byte-for-byte unless explicitly separately authorized.
5. Nonessential add-ons including `service.adulthideout.core`, Umbrella, POV, Seren and peers must not hold normal shutdown indefinitely **when essential protected saves have completed**; never grant optional actors permission to modify protected essential data.
6. No factory reset, reinstall from scratch, data deletion, blanket service disabling, silent safety bypass, broad refactoring, or destructive migration.
7. Future change requires **specific owner-approved scope**, source/payload diff against this exact 2103486 binary and component fingerprints, minimal focused checks, original-key install-over signing, and owner acceptance on the actual Fold.
8. Treat this as a **protected milestone**, not authorization for further repairs, diagnostics, or APK publication.
9. A newer version number, GitHub-green build, or another signed artifact does **not** supersede 2103486 without owner approval.
10. This lock records owner acceptance; GitHub branch-protection/enforcement must be managed separately if desired. A GitHub Actions artifact is subject to its retention policy; keep an archival copy of the exact signed APK.

## Separate signed forward-recovery option (NOT the accepted base)

- Version `2103487`, original-key forward recovery, Actions run `43201341671`, artifact `13936225410` — available only if a recovery is later needed and separately authorized.
- https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43201341671/artifacts/13936225410
- **Do not promote or install 2103487 as part of this lock.**

## Historical and source provenance

- Previously protected working 2103483 SHA-256: `0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236`.
- 2103484 was diagnostic only; it is not an accepted repair baseline.
- This lock-branch starts at the exact 2103486 signer/authority commit `fe44ec40cd3e43fb5498084dec24c59dd63c3f3a` and changes only this acceptance record. No production source, engine, manifest, packages, signing keys, or APK bytes are changed by the lock.
