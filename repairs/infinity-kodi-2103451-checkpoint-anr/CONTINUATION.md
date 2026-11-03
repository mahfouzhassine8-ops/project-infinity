# Infinity Kodi 2103451 P0 repair continuation

## Foundation and authorization

Continue on `work/infinity-kodi-2103451-checkpoint-anr-20261103`.
The branch was restored and pushed on 2026-11-03 before further investigation.
Its initial HEAD is `0b3450433adc3349056167a6697dae92dad63d86`, the
`lock/infinity-preview-2103451-user-frozen-20261103` checkpoint.

Protected signed source: `e50e68dad4c50690601bacbe1724507912b70fbd`.
Protected APK version: `2103451`, package `com.projectinfinity.kodi`.
APK SHA-256: `d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399`.
Original certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Signing run: `41568721264`; signed artifact: `13200361701`;
matching component artifact: `13200925524`.

The user's November 3 P0 instruction authorizes only confirmed Infinity Kodi
watched-job persistence/checkpoint and native lifecycle/ANR repairs, with focused
shutdown testing for those failures. It supersedes historical shutdown freezes
only for those targets. Preview, Cobra, chooser/Splash, unrelated Kodi behavior,
data, providers, and unrelated native/shared components remain frozen.

The latest continuation explicitly requires both evidence and execution access
before proceeding with the investigation/implementation. Do not sign until both
repairs and the mandatory verification/preservation requirements are satisfied.
No automatic release lock or promotion is authorized.

## Preserved investigation state

No production file has been changed and no new application/host test has run.
No successor APK has been built or signed for this task.

Before the environment interruption, the actual signed 2103451 archive was read:

- `lib/arm64-v8a/libkodi.so`: 637,890,632 bytes.
- SHA-256: `151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`.
- No GNU BuildId was found in its ELF note sections. Do not invent one for
  attribution or bind historical diagnostic events by installation path alone.
- That SHA matches the recorded final-native build `40287479124`, artifact
  `12636606216`. The final source-map inspection remains outstanding.

Five upstream Kodi 21.3 source files were fetched read-only and their hashes
matched both the before/after entries of the existing
`repairs/android-checkpoint-shutdown/runtime/native/manifest.json`:

| Source | SHA-256 |
| --- | --- |
| `xbmc/video/jobs/VideoLibraryMarkWatchedJob.cpp` | `4acc7acb650dca3b5b99c5ff71ee9c76fc7ccadb162f9fc2f0485b32cd8e1e69` |
| `xbmc/video/jobs/VideoLibraryMarkWatchedJob.h` | `be989bc5d0fca626c5c43d2e3ca9273fad6c0e25162ee2f49399bfbecf7d429d` |
| `xbmc/video/jobs/VideoLibraryJob.cpp` | `67b802726fdbe8501d07069dd7c0daac2ae4df7c2579f7adf807fdc37914a7a2` |
| `xbmc/video/jobs/VideoLibraryJob.h` | `40ae24d0709b6b9a3293ae4d7d6529fc77fb15a8439331c23dc29f54d7eaab49` |
| `xbmc/video/VideoLibraryQueue.cpp` | `7ae1ae19bbf419190c40fe2b45d69be457a91967cf753c4c3c6f0ac62576a0dc` |

Source findings, not a diagnosis of the unavailable November 3 event:

1. `CVideoLibraryMarkWatchedJob::Work` does not check the result of
   `db.CommitTransaction()` before returning `true`. Its class does not provide a
   verified job-completion receipt contract. The checkpoint ledger intentionally
   retains unclassified work after ordinary job completion; a true work result
   is not proof of saved watched/progress state.
2. This job also supports recursive directories, UPnP and PVR recording updates.
   Local SQLite durability cannot certify remote-provider persistence. Do not
   blanket-exempt the class or erase an unresolved obligation based on its name.
3. The Android source overlay synchronously calls
   `surfaceDestroyed -> XBMC_DestroyDisplay -> SendMsg(TMSG_DISPLAY_DESTROY)`.
   The video-player destructor drains its outbound callback queue. These are
   dependencies to trace, not proof of the current ANR's blocked callback, lock,
   worker starvation or a shutdown relationship.
4. Earlier November 1 diagnostic observations belong to a different archive.
   They must not substitute for the November 3 evidence or establish its APK
   producer/version.

## Environment recovery and evidence gate

The previous environment became offline. On resumption, the status tool reported
current `connectivity: connected`; an actual shell command and the branch push
succeeded. This confirms execution access, not Android runtime readiness.

`/workspace/project-infinity` and its pre-existing untracked files survived.
The `/tmp` mount was reset: previous temporary signed archives, source reads and
any incomplete native-artifact download are absent. Their old paths must not be
claimed as accessible evidence. Protected signed releases remain available from
their recorded GitHub artifacts. Verify re-materialized bytes before use.

The previous native-artifact connector failed with `ServerBusy`, "Ingress is
over the account limit"; its fallback transfer did not produce a verified
artifact before the environment interruption. Required artifact identity:

- Artifact `12636606216`, size 184,980,906 bytes.
- Archive SHA-256:
  `98fd817ea50e3a4246903067d6518b43a53aadf9305330737a5ba194265c9b0f`.

During recovery at 12:58 UTC, GitHub authenticated branch push and artifact
metadata reads succeeded. A CLI attempt to restore signed-451 artifact
`13200361701` failed at its redirected Azure Blob download with HTTP Forbidden;
the temporary output was zero bytes. The redirect's reported validity interval
included the current executor time, so expiration was not established as the
cause. No replacement credentials, altered trust, or repeated transfer was
attempted. Do not mistake this artifact-transfer failure for a failed GitHub
branch backup or claim a fresh local signed-baseline copy exists.

The original November 3 Health Center ZIP is still not exposed to this executor.
Bounded workspace/temp/attachment-path searches returned no diagnostics archive;
connected Page searches returned only existing unrelated reference Pages. No
current attachment file ID, path or download reference has been received.
This is an access limitation, not a claim that the user did not supply the file.
Do not request another export, substitute a converter error, guess a file URL,
publish private diagnostics, or claim the archive has been inspected.

## Resume sequence and focused verification

1. Establish a supported local/private reference to the already-supplied original
   November 3 ZIP; verify its ZIP structure/CRC, SHA-256 and readable contents.
   Keep raw diagnostics private and out of the repository.
2. Bind relevant events to timestamps, producer identity where available, native
   symbols and exact source. Distinguish missing receipt from failed writes;
   trace the ANR separately before asserting a common dependency.
3. Before each test execution, record the exact test command and source/APK
   binding under this repair directory. No broad discovery or inherited suites.
4. Select focused host cases from the confirmed mechanism: checked local commit,
   rollback/failure refusal, receipt completion/callback ordering and remote-path
   preservation. For the hang, reproduce the actual dependency with the existing
   callbacks and persistence work intact before implementing a correction.
5. Independently select the authorized Android scenarios: normal shutdown and
   restart; pending watched updates with reopened-database readback; Stop/Back/
   Home; screen-off/on and background/foreground; supported display/Fold lifecycle
   changes; and the combined failure case. Record NOT RUN or exact blockers when
   unavailable. Host simulation is not Android evidence or physical acceptance.
6. Keep shutdown results independent from feature/build orchestration per
   `AGENTS.md`. Do not weaken validation, discard callbacks, add arbitrary timeout
   extensions, or repeat the known native-constructor emulator failure blindly.
7. Enumerate all authorized source/method/APK-member differences against actual
   signed 2103451. Preview, Cobra and every unrelated payload must be unchanged.
   Verify original certificate, package/version, install-over compatibility and
   matching components before delivery. Physical Fold acceptance remains pending.

## Current release status

Execution and branch backup are restored. A separate private reader has now
supplied CRC/hash-verified November 3 observations; see CORROBORATED-EVIDENCE.md.
This executor still has not accessed the original diagnostic archive.

Three bounded source-bound host reproductions and read-only inspection of an
exact-hash retained native member now corroborate the missing-contract and
checkpoint/display-message starvation mechanisms. See MECHANISM-FINDINGS.md and
the bounded evidence JSON. These are BASELINE_DEFECT_REPRODUCED results, not
repaired-runtime passes.

A checkpoint-only lifecycle correction is now implemented as a guarded staging
producer, with exact three-file preimages and a reviewed source patch. Seven
selected host cases passed using actual sender/queue bodies and corrected
application branches, with native-window/EGL boundaries stubbed. Existing sender,
cleanup and normal-dispatch methods plus seven unrelated Application methods
were byte-compared unchanged. This is not full-engine integration or Android
verification. See evidence/LIFECYCLE-HOST-VERIFICATION.json and the reviewed patch.

The bounded local watched-job contract is also implemented as a guarded staging
producer: checked commit, separate-connection readback, actual database write
observation and reviewed callback identity. Fourteen selected host cases pass
against the final source using real SQLite temporary files, with current source
bindings in WATCHED-HOST-VERIFICATION.json. The first compile and fixture-input
failures are retained separately; they were corrected before final cases passed.
Unclassified recursive/UPnP/PVR jobs remain blocking and keep their original
operation results. The original historical job item's route remains unknown.

The exact five-file source union is saved in CONSOLIDATED-STAGING-PLAN.json.
The existing original native producer/overlays, Preview/Cobra payloads and
signature infrastructure remain unmodified. No full native engine was compiled.

**Release blocked:** exact full native source/map and signed-451 artifact access,
full-engine integration, real Kodi/Android verification and complete package
preservation. This executor has no adb, emulator or exposed KVM; do not rerun the
known translated-native constructor failure as if it could verify these changes.
Original diagnostic bytes and historical item-route/producer attribution remain
unavailable here. No successor build/signing or automatic lock is implied.


## 2026-11-03 authenticated recovery and integrated source checkpoint

The earlier asset-access/full-source blockers above are resolved by read-only
Actions run41726452356. It verified the actual signed451 APK/certificate, four
matching components and retained native SHA; restored the full9411 source map
exactly; and integrated only the five reviewed source edits. Both original
compiler transfer tar hashes passed. Source artifact13274901825 was independently
SHA/CRC checked locally, then all9411 candidate source hashes verified after
safe extraction. No production APK or key was changed/accessed.

The sole host-support mismatch was the actual native database barrier's existing
protected-resource predicate. Its write-observation bodies are unchanged. All14
watched cases passed with the actual header, plus one explicit protected-resource
refusal case; the separate provider is a controlled host peer. The seven
lifecycle tests are unchanged and retained. Full CVideoDatabase, callback/final
checkpoint and Android assertions remain NOT RUN. The original historical item
route is UNKNOWN; no reported-case fix is claimed for unclassified remote work.

A separate native-only build is selected in SELECTED-TESTS.md. The original
producer, patch, dependency verifier, NDK installer and inherited shell script
remain byte-identical to the last matching native producer. Only compile_engine
is invoked; its inherited script is cut before APK creation. No behavioral
suite, application run, signing key or release lock is part of this workflow.

Compatible Android runtime remains unproven. The accessible hosted runner is
x86_64; it does not establish an ARM device. The runner inventory API returned
403 Resource not accessible by integration. Do not use alternate credentials,
modify native constructors, repeat known-broken emulators or claim Android PASS.


## Native build request now executing

The selected request commit is765b92bc8af1452ffc2bbb19a03a3de229a90255.
Native-only run41729462691 has passed exact artifact/source/producer/lock gates,
restored original dependency archives and pinnedNDK, and entered complete ARM64
compilation. At this checkpoint it is IN_PROGRESS, not PASS; job126242718633.
Retrieve that existing result once terminal; do not launch another build.
`evidence/NATIVE-BUILD-RUN1.json` records the actual observed step status.
No successor APK has been created/signed or version allocated.

The user explicitly cannot classify the historical watched item. Preserve that
boundary and the old Unknown obligation; see HISTORICAL-JOB-ROUTE.md. A separate
request for an existing authorized ARM64 Android target is pending. See
ANDROID-ACCESS-BLOCKER.md. Do not claim the historical route fixed or Android
ANR clearance from compilation/host evidence, and do not sign prematurely.


## Native integration and available preservation complete; Android BLOCKED

Run41729462691 completed successfully. The full ARM64 engine contains the exact
five reviewed edits over the matching9411 source tree; no reviewed source changed
during compilation. The13 additions are the unchanged producer's generated
configure/toolchain/cache files. Retained native-module ABI and ARM64 ELF checks
passed. Artifact13276398254 archive SHA/CRC and actual native bytes were then
independently checked locally. Engine SHA is
f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674.

The exact signed451 APK also materialized locally through the supported GitHub
artifact broker, matching archive and APK SHA/CRC. Its original certificate
verification remains bound to the identical bytes in41726452356; no replacement
credential, proxy/ACL bypass or signing occurred.

Selected internal unsigned native-only assembly passed:7613 of7614 nonsignature
payload members exact, with only lib/arm64-v8a/libkodi.so changed; all five DEX and
46 other native libraries match baseline byte-for-byte. Full per-member hashes
are saved. This is a baseline-version internal fixture, not a releasable or
installed testing APK. No higher version or matching successor owner ZIPs were
issued. Final versioned/signed/component checks remain NOT RUN.

The user confirms no verified ARM64 self-hosted runner exists and the physical
Fold is not connected. Supported device-farm/ADB options were investigated;
current managed environment has no configured cloud identities, project, device
capability, VPN or TCP grants. See ANDROID-ACCESS-BLOCKER.md. Actual Android
checkpoint/database/display/ANR scenarios are BLOCKED. Do not repeat the known
translated-constructor failure or sign a successor based on compilation alone.
Preserve the native build/tests, Unknown historical job973/token976 and all locks.
