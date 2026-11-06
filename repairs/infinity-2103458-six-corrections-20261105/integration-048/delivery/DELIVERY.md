# 2103460 controlled navigation/UI test and 2103461 forward recovery

This is a testing handoff, not completion or acceptance of all six correction groups. Signed 2103458 remains the immutable working reference. Nothing was installed, promoted or locked. Android/Fold execution, installation and physical recovery are **NOT RUN / PENDING**.

## Downloads

GitHub repository access is required. Each APK link downloads an artifact ZIP containing the named APK and build/preservation evidence. Component artifacts contain the matching four owner ZIPs and catalog.

| Purpose | APK artifact | Matching components |
|---|---|---|
| **2103460 testing** | [Original-key APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42146650003/artifacts/13470392498) | [Component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42146650003/artifacts/13470921726) |
| **2103461 forward recovery** | [Original-key APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42147263793/artifacts/13471121076) | [Component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42147263793/artifacts/13470727803) |

APK SHA-256 (the extracted APK, not its download ZIP):

- 2103460: `226911966c1d27d1246cd0ecfcd864c722df48f9be07167bd4b15ad1e73560af`
- 2103461: `ffd95188504357a093070aa7d064aa2c3fafec6b6eed176b3db0685857ff1a16`

Original permanent certificate SHA-256, both APKs:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

Both use `com.projectinfinity.kodi`, ARM64, higher version codes, original APK v1/v2/v3 signatures and the existing installer/authentication protections. CI verified 16 KiB ZIP alignment. Package/signature/version compatibility supports an install-over test; it is not evidence of an actual Android install. See `SHA256SUMS` for all component hashes and the per-artifact archive-verification JSON files for ZIP hashes.

## Exact source and integration

- Approved patch: `04806da44330e5db4a795bf291625e72abded128`.
- Application-source integration: `3f3f47bdf9b0f14f9ac3b42fcff6f8710ceeda05`.
- Prepared payload source: `6ddd9a3b35a31637dd41e424f78d49510f4b6263`.
- 2103460 signing source: `a4c1d751c32b3a978ee86ab4ed9a7b38783956dc`.
- 2103461 signing source: `04947a46172b172f49a3867a792cbda9cf27da9a`.
- Immutable signed 2103458 source: `b740fc6f2f987c83b9a67617bfae82a34bd307d2`; original APK SHA-256 `eb2c5121b6a0173dc3848eda93ea0d640d1db9245de5b5985933312d56e951fd`.

The reviewed navigation failure mechanism is the existing built-in same-start-folder handling and Videos initialization restoring a retained child directory for a return-style activation. The correction routes only the two existing library actions through the existing helper's JSON-RPC parameter vector. For Android, the actual Infinity skin, the exact two unchanged title-library URLs and the exact explicit-entry flag, `GUIWindowVideoNav.cpp` sets the requested path before original initialization. Original directory loading, error handling and Back/history remain in charge. This is source/compiled evidence, not a claim that a historical export establishes the active device skin.

The latest patch changes exactly the approved native file, the two helper actions and their two drawer bindings. Retained earlier authorized corrections add the Info Back/Trailer control IDs, Details Up targets and visual refinements. The cumulative functional source inventory against signed 2103458 is:

1. `xbmc/video/windows/GUIWindowVideoNav.cpp` — explicit Infinity library entry only.
2. `assets/addons/script.infinity.commandcenter/library_navigation.py` — two library actions.
3. `assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml` — retained drawer changes and two library bindings.
4. `assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml` — retained approved visual and Back/Trailer corrections.
5. `assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml` — retained visual and Details-navigation corrections.
6. `assets/addons/skin.infinity.diggz/unified/Variables.xml` — retained presentation fallback.

The sole original-key workflow received only exact candidate/recovery routing and authority registrations. Original signing, ownership, source, artifact, authentication and preservation guards remained enabled. No provider, Search runtime, playback, shutdown, Preview or Cobra source change was added in this integration.

## Verification and preservation

| Check | Result and limit |
|---|---|
| Exact approved patch integration | **PASS**, 16 source checks; original native input untouched |
| Prior focused navigation evidence | Reused the unchanged 53 compiled-fragment/mock checks; not Android execution |
| Prior changed-control/visual evidence | Reused 23 static and 58 Linux checks; not physical visual acceptance |
| Full Android ARM64 compile/link | **PASS**, run [42143297475](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42143297475) |
| Native source comparison | **PASS**, 9,410 of 9,411 mapped files unchanged; only approved `GUIWindowVideoNav.cpp` differs |
| Native target/strong ABI compatibility | **PASS**; binary not executed on Android |
| Focused packaging checks | **PASS**, 11 cases in preparation run [42145501182](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42145501182) |
| Original-key module authentication and recovery | **PASS**, 19 host checks; disposable profile/sentinel, no real user data accessed |
| Official artifact/authority review | **PASS**, run [42146199256](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42146199256) |
| Signed APK preservation | **PASS**, original signer plus post-sign member comparisons for both versions |
| Download verification | **PASS**, full artifact ZIP SHA/CRC checks, all 7,622 APK payload hashes, original certificate identity, component hashes/payloads and all DEX ordering |
| Android runtime, install-over and Fold rendering/recovery | **NOT RUN**; no connected compatible target |
| Required Search acceptance | **2 FAIL retained**, not disabled or waived |

2103460 changes exactly **14 existing non-signature APK members**, adds none and preserves **7,608** existing members byte-for-byte. The 14 are the five skin/helper members above, `lib/arm64-v8a/libkodi.so`, Android version metadata and seven authenticated module/skin/component metadata members. All five DEX files and 46 other native libraries are unchanged. See `2103460-APK-PRESERVATION.json` for every member and hash.

The compiled candidate engine SHA-256 is `febf0e0ed95ef33e906999b4a92c46e6b79bae1c555eaa89b4954d0b74fb3e41`. The native source comparison, rather than an impossible identical whole-library claim after compilation, establishes the narrow source scope.

2103461 restores **every functional 2103458 payload member**, including its original engine `9f77b092899b51850928007578e0fbf91bad38c05f147a308f3ac0cf5c036638`. Exactly eight existing metadata members differ; **7,614** are identical, including all five DEX files and all 47 native libraries. No new files are added. See `2103461-APK-PRESERVATION.json`.

Cobra and Minimal Android Contract component ZIP hashes are identical to the frozen references. Preview DEX/resources and all other non-allowlisted payloads are unchanged. User data was not accessed or migrated. Recovery locks and accepted-baseline pointers were not modified.

The first preparation dispatch was skipped because its new workflow branch routing contained a version substitution error; the recorded correction changed no application code. The successful preparation performed the consolidated checks. The first local raw component comparison stopped on `AndroidManifest.xml`; reproducing the existing assembler's versionCode-only stamping and DEX ordering made the exact downloaded comparison pass. Neither issue was suppressed, and neither required a production payload change.

## Remaining boundaries

- Downloads-only filtering is **not implemented**: trustworthy positive provider-source identities are unavailable; ambiguous and user-added sources remain intact. No guessed classifier or unauthorized native filter was inserted.
- Both required Search result-validation failures remain open. No meaningful-configuration, cancellation, ownership, interpreter-lifetime or source-security guard was weakened. The Crew attribution and repeated native Search crash remain unresolved. No synthetic 30-cycle result is represented as an Android crash fix.
- Scudo OOM remains separate and unresolved.
- Browser design and the device's active installed-skin resolution require physical verification. Host checks do not prove the reference is rendered correctly.

## Coordinated Fold test and forward recovery

Keep both downloaded APKs and their hashes before testing. Use **2103460** for the correction test; **2103461 is recovery only**. Do not install the component ZIPs manually. No automatic installation is authorized or performed.

Follow [FOLD-TEST-PLAN.md](../packaging/FOLD-TEST-PLAN.md): test both Library drawer entries from Home and retained child directories, switch libraries, Back/focus/history, other Movies/TV provider routes, drawer height/Power/removals, Info Back/Trailer/Details, artwork/synopsis and existing touch/playback in Light/Dark, cover/inner displays and orientations. Record actual outcomes and Search/Downloads limitations honestly.

If the testing candidate needs recovery, use the original-key **2103461 install-over APK**, which has higher authenticated module and skin generations while restoring 2103458 functional code. Do not install a lower version over it, uninstall, clear storage or overwrite an unknown modified module. The unchanged installer deliberately rejects unrecognized local modifications and invalid signatures; stop on that rejection rather than reset user data. Host recovery passed, but actual Android recovery and active-skin replacement are pending. Recovery cannot restore unsaved in-memory data or waive unresolved durability obligations. After recovery, any further testing APK must have a version code above 2103461.

Only the user can accept the physical result. No new lock, baseline promotion or claim of complete six-group correction is made.
