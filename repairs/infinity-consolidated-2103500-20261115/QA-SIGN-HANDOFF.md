# Infinity 500 fast QA — signed installer continuation

**Owner authorization:** Produce a fast **QA test APK** containing the **three already implemented/reviewed corrections only**; defer Continue Playing, Otaku → Watchlist and Empty Shell for a later repair. This is **not** release acceptance or proof those deferred issues are fixed.

## Authentic starting point
- Exact original-signed **2103500** APK: SHA-256 `224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40`.
- Permanent original signer certificate: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Final reviewed ARM64 engine: `ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7`, run [43774504911](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43774504911), Astra-reviewed six-file source scope.
- Reviewed updated Cast discovery DEX: `4360efcdf3af08a8388f18846c79353517ab3d7ee6a3c026838b7748c0914c98`, run [43762472390](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43762472390), exactly two Cast class roots changed and 1,035 unchanged.

## Completed QA preparation in this continuation
- Reused the pinned signed500 APK, pinned final ARM64 ELF and pinned two-class Cast DEX. No rebuild, provider edits, reset or user-data access.
- Existing reviewed `.github/workflows/infinity-500-native-integration.yml` staged the selected QA with a strict four-member APK comparison: `lib/arm64-v8a/libkodi.so`, `classes6.dex`, `AndroidManifest.xml` versionCode, `assets/experience-component-updates.properties` version label.
- Workflow [43781637786](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43781637786) — **SUCCESS**, job `fast-qa-stage`. Artifact [14188846231](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43781637786/artifacts/14188846231), digest `sha256:17ba59fb0618489e75c523bf2446c8bfbeedcc014025c39b658d3873290c6dd3`, contains QA-STAGING.json and an **unsigned, NOT INSTALLABLE** APK input.
- The internally staged version **2103502 is provisional only**. **2103501 already belongs to earlier original-signed forward recovery and must not be reused.** Recheck live registry before reservation.
- All 500 user profiles, Search, tracking, startup, provider code, Cast relay/remux, networking, skin and Cobra payload are unchanged by this selected packaging input. The signed package preservation comparison has **not** run because signing has not happened.

## Finish the fast QA installer — mandated trusted route
1. Codex/Astra inspect the unsigned stage's actual QA-STAGING.json, member hashes, source bindings and original signed500 preimages.
2. Reconcile **live** release authority/version issuance and reserve **unused** QA and higher forward-recovery versionCodes through the **existing original-owner authority process**. Do not assume provisional 2103502 is available without checking.
3. Perform the necessary final-ELF full-application Android smoke checks available in CI (Kodi startup, Silent Mode scoped dialog behavior, shutdown and same-profile relaunch). The eight earlier observer Android-bridge cases belong to the earlier observer-only binary, not this final ELF. Preserve uncertainty explicitly.
4. Use **only** the original reviewed signing workflow ID `397702717` and unchanged `repairs/dual-experience-isolation-2103420/assemble.py sign`; preserve original certificate and v1/v2/v3. Do **not** use a disposable test-key APK for the owner's in-place update or bypass signer-policy/owner-authorization gates.
5. Verify the exact allowed APK-member delta relative to signed500, original five DEX unchanged, Cast two-class-only delta, Cobra identical, signed certificate, installation-over-500 preserving UID/dataDir and forward recovery.
6. Publish a real original-signed **installable** QA APK and matching appropriate higher-version recovery, with SHA-256 and link. Until this happens, **no installable QA APK exists**; do not offer the unsigned staging artifact as such.
7. Owner performs one physical Fold acceptance; casting playback remains unverified until a receiver is tested. Deferred three issues stay OPEN, not passed.

**No downgrade. No changed product scope. No invented progress or trusted Otaku IDs. No profile reset. No redoing completed native work.**
