# Controlled testing delivery — 2103456 and forward recovery 2103457

The actual combined APKs are signed, downloadable and verified below. **2103456 is a partial testing candidate, not an accepted release.** No installation, promotion or lock was performed. Android/Fold execution and physical recovery remain **NOT RUN**. The two required Search failures, incomplete browser design and unconfirmed Favorites attribution remain visible.

## Downloads

GitHub artifact links require access to the private repository. Download and extract the artifact ZIP to obtain the named APK or the four individual component ZIPs. These links contain the actual binaries, not source-only reports. Both APK artifacts and both component artifacts were downloaded independently and their complete CRC/SHA checks passed.

| Artifact | Download | Actual APK SHA-256 |
|---|---|---|
| Testing APK, versionCode **2103456** | [Infinity-2103456-Combined-Original-Signer.apk](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41988386798/artifacts/13397163155) | `81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696` |
| Matching 2103456 components | [INFINITY, COBRA, CHOOSER_SHELL, MINIMAL_ANDROID_CONTRACT](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41988386798/artifacts/13397307616) | [Individual checksums](SHA256SUMS-2103456.txt) |
| Forward recovery, versionCode **2103457** | [Infinity-2103457-Combined-Original-Signer.apk](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41989110830/artifacts/13397403046) | `cbba67441055492e2bd83558e7e65ad95396aefc1381d2e9e7809e180e8eb212` |
| Matching 2103457 components | [Recovery component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41989110830/artifacts/13397408243) | [Individual checksums](SHA256SUMS-2103457.txt) |

Testing APK size: 778,576,464 bytes. Recovery APK size: 778,596,097 bytes. Artifacts have the workflow's 90-day retention; no GitHub Release or accepted-release pointer was created.

## Identity, source and build evidence

Both APKs retain package `com.projectinfinity.kodi` and the original permanent RSA signing certificate, SHA-256 **`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`**. Actual `apksigner verify` in the original trusted signing workflow passes v1, v2 and v3 with one original signer. The independently downloaded APK hashes match those verified files. No local-device install or local `apksigner` execution is implied. The pre-existing v1 META-INF version-entry warnings are retained in the signature transcripts; v2/v3 verification passes.

| Stage | Exact source | Successful Actions run |
|---|---|---|
| Full ARM64 engine | `a6722c3848e12e58c4c0fbef360629e922c4ece6` | [41983648377](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41983648377) |
| Component/module preparation | `451a4f5204b11019b281ba8e7077ad3e0cfd4db7` | [41986609531](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41986609531) |
| Testing APK signing | `9c77703eb847d3482441091da94bdbee272a2ee3` | [41988386798](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41988386798) |
| Recovery APK signing | `feec0ee1c8c450c52a21b3d93877e97502cc2652` | [41989110830](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41989110830) |

The source candidate continues checkpoint `4c4094918845bd42649f50bcb094d2ba334a51bc` on `work/infinity-master-testing-from-2103451-20261105`. Frozen reference APK2103451 SHA-256 is `d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399`. The current installed phone version and last physical acceptance remain unverified. Official version availability was checked before each issuance: 2103456 and 2103457 were unused and exceed the previous issued 2103455.

## Included corrections and boundaries

- The complete ARM64 engine is frozen2103451 plus only `xbmc/input/InputManager.cpp` and `xbmc/guilib/GUIBaseContainer.cpp`. The existing Infinity touch controller provides first-tap selection, second-tap activation and the existing hold/context path while preserving direct-action controls. All 9,409 other reviewed native inputs are unchanged. Final engine SHA-256: `9f77b092899b51850928007578e0fbf91bad38c05f147a308f3ac0cf5c036638`.
- The existing 12-member master source overlay is preserved: fresh Search-response validation/diagnostic work; guarded direct Umbrella Movies/TV, SportHD and native Favorites routing; Browse Files correction; drawer height with preserved rows and landscape scrolling; global view preference, first-entry List/refresh/View Options corrections; and the completed thumbnail bindings. No provider source is replaced. Actual installed provider compatibility remains a runtime check.
- Search still rejects identical settings rewrites and Nixtoons' own history writes in the two required failing cases. The Crew's actual device state delta remains unconfirmed. No source-verification, meaningful configuration, cancellation, concurrency or request-ownership guard was disabled.
- The full locked browser mockup is **not implemented**. Its exact PNG bytes have not been accessible here for SHA/visual verification. Favorites' missing-item cause is **unconfirmed**; its read-only diagnostic was not run against user data.
- Scudo/OOM, the separate prior ANR/loading investigations and blocked settings-owner retirement are unchanged. This engine does not silently include the unaccepted2103452/2103453 P0 native changes.

## Exact preservation

[Exact changed-member inventory with before/after hashes](EXACT-MEMBER-ALLOWLIST.json) and the full signed per-member inventories below enumerate the complete differences. Counts exclude the three ZIP signature members; those and the APK signing blocks are necessarily regenerated and verified separately.

| Compared with signed2103451 | 2103456 testing | 2103457 recovery |
|---|---:|---:|
| Changed existing payload members | 14 | 8, authenticated/version metadata only |
| New payload members | 7 | 0 |
| Existing payload members byte-identical | 7,600 | 7,606 |
| DEX files byte-identical | All 5 | All 5 |
| Native libraries byte-identical | 46; only approved `libkodi.so` replacement differs | All 47, including original451 engine |

Cobra's complete component ZIP and the minimal Android contract ZIP remain byte-identical. Preview's compiled payload is unchanged. Chooser/routing code, permissions, icons, playback and shutdown source, providers and other add-on payloads remain preserved; chooser-component versionCode metadata is advanced by the original assembler. No real profile, database, settings or media file was opened or changed. All 19 existing recovery-lock refs and the accepted registry pointer remain unchanged.

- Testing: [preservation result](signed456-evidence/signed-combined/preservation/APK-PRESERVATION.json), [every payload member hash](signed456-evidence/signed-combined/preservation/ALL-APK-MEMBER-HASHES.json), [original-certificate verification](signed456-evidence/signed-combined/preservation/SIGNATURE.txt).
- Recovery: [preservation result](signed457-evidence/signed-combined/preservation/APK-PRESERVATION.json), [every payload member hash](signed457-evidence/signed-combined/preservation/ALL-APK-MEMBER-HASHES.json), [original-certificate verification](signed457-evidence/signed-combined/preservation/SIGNATURE.txt).
- Actual download checks: [testing APK](DOWNLOADED-SIGNED456-VERIFIED.json), [testing components](DOWNLOADED-COMPONENTS456-VERIFIED.json), [recovery APK](DOWNLOADED-SIGNED457-VERIFIED.json), [recovery components](DOWNLOADED-COMPONENTS457-VERIFIED.json).

Only the existing sole original-key signing workflow signed these APKs. Exact-branch authority, versions, artifact/source authentication and preservation remained mandatory. Engineering authority generations42/43 were issued for these testing artifacts; accepted-release authority and recovery locks were not moved. The build-only workflows have no original-key access. No alternate signer or bypass was introduced.

## Verification and recovery

| Check | Result and evidence |
|---|---|
| Existing exact touch host comparison | Reused **59 assertions PASS**; baseline30 contract failures retained in the prior source evidence. [Touch results](../infinity-native-touch-2103451-20261105/RESULTS.md). |
| Full ARM64 compile/link and all9,411 native source bindings | **PASS**. [Verified engine](NATIVE-CONTROLLED-ENGINE-VERIFIED.json). ELF64/AArch64, same SONAME/dependencies and all71,211 strong exports; actual original/candidate ELF comparison performed. |
| New focused packaging/security contracts | **11 PASS** in actual preparation CI. [Completed-job excerpt](CI-PACKAGING-CHECKS.txt). Earlier local disk-space fixture failure is retained; the corrected bounded negative fixture and actual ABI check pass. |
| Original-key authenticated module and recovery checks | **20 PASS**, host POSIX/JCA adapters executing the original installer/verifier algorithm. [Checks and limits](SIGNED456-RECOVERY-VERIFICATION.json). Interrupted writes, retry, bad signature/source, retained-helper refusal and a disposable data sentinel were checked. |
| Actual signed APK/component preservation, permanent cert, version and module authentication | **PASS** for both actual downloads. [Consolidated evidence](FINAL-VERIFICATION.json). |
| Required Search acceptance cases | **2 FAIL**, retained and disclosed. No provider test was reclassified as PASS. |
| Full browser/Favorites attribution | **INCOMPLETE / UNCONFIRMED**. |
| Android/Fold render, gestures, provider network behavior, install-over and physical recovery | **NOT RUN**: no supported connected Android target. Compilation/host fixtures are not device acceptance. |

Recovery2103457 restores exact2103451 functional source and native engine at a higher Android versionCode. Module generations0.3.5.57→0.3.5.58 and skin1.0.5.254→1.0.5.255 are authenticated using the original trust mechanisms. Candidate-only retained helpers are refused by the restored module contract and restored routes do not invoke them; no destructive cleanup is used. Actual Android skin-generation/install behavior remains pending.

Before any user-controlled test, verify the phone's installed package, original certificate and version; an unexpected signer or version2103456 or higher requires reassessment. Recovery must occur at an existing safe persistence/close point. Do not force-kill Kodi or bypass an unresolved checkpoint. An APK cannot recover unsaved in-memory writes, and recovery from an already hung process with unresolved obligations is not guaranteed. Follow the [focused Fold and recovery procedure](FOLD-AND-RECOVERY-PROCEDURE.md).

No automatic installation, uninstall, data clearing, downgrade, promotion, acceptance or lock occurred. Final physical acceptance remains the user's.
