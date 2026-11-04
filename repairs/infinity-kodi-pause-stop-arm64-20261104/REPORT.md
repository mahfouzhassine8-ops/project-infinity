# Pause/Stop/Play ARM64 integration — Android verification pending

The exact `7f2c93f94c7372679b756091d5b2666a7d909fd0` source candidate compiled successfully against the preserved 2103452 native inputs. The integrated host checks, source comparison, ABI comparison and focused ARM64 instruction review passed. This supports preparing a controlled physical-test candidate after separate packaging authorization. It does **not** establish that the ANR is fixed on Android or the Galaxy Fold.

No APK was built, signed or installed. No release or recovery lock was changed.

## Build and input identity

- Isolated branch: `work/infinity-kodi-452-pause-stop-arm64-20261104`.
- Build source: `24c6eeb30a6fbc65546a9945a87ca19500694f31`.
- Successful [Actions run 41778685295](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41778685295), 2026-11-04 05:20:51–05:40:46 UTC.
- [Native engine and producer evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41778685295/artifacts/13298763260), artifact `13298763260`, **internal native output, not an installable APK**. GitHub currently retains it until 2027-02-02.
- Downloaded artifact: 184,643,302 bytes, SHA-256 `1fdcdce88a031d60c48421535cc0be69b0e54f79331f7c860be0f87cde6e8b85`; local ZIP CRC verification passed.
- Exact original compiler recipe retained: SHA-256 `d4f5a12673404c077ee2aec34a9e8323537fa94257b5e8aa32dc65f722289d52`, pinned Android NDK `21.4.7075529` and preserved dependency artifacts. No alternate signer or native dependency was introduced.

| Native engine | Bytes | SHA-256 |
| --- | ---: | --- |
| Preserved 2103452 unstripped engine | 638,038,440 | `f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674` |
| Integrated ARM64 engine | 637,989,448 | `d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98` |

The integration wrapper stops at native compilation. The workflow has no APK packaging, installation or signing step and no signing-secret access. `ENGINE-PROOF.json` records zero changed or missing reviewed source files after compilation.

## Exact source scope

The complete 9,411-file source map matches the established 2103452 inputs except **`xbmc/messaging/ApplicationMessenger.cpp`**. All other 9,410 mapped files are identical, including the existing watched-persistence and display-lifecycle corrections.

- Before: `c565bf9dad1f5dcbdca3d81a6d3dc5a42c4d8fd8151dac2f20766caaeb4ef0c8`.
- After: `f53c09ca57fe3b4e8e575b4f51e2f3108dc77836b35c4498dbb859f61c866f8b`.
- The after bytes and original host harness remain identical to the acknowledged `7f2c93f9` checkpoint.

This stage adds only the compile-only workflow, integration/comparison tools and evidence in this repair folder. It makes no further native production edit. Generated configure/cache files are individually enumerated in `ENGINE-PROOF.json`; none replaced a reviewed source file.

## What the actual ARM64 output establishes

Direct inspection of the compiled engine confirms:

1. The selective pump still requires Kodi's process thread and an active checkpoint. Its queue population bound, retained FIFO, existing display messages, stop flag and locking remain present.
2. The new helper checks the complete envelope: GUI action `0x08000005`, application target `9999`, second parameter `-1`, zero third parameter, non-null action and empty string/vector parameters. Its compiled ID comparison accepts only Pause `12`, Stop `13` or Play `79`.
3. The real GUI receiver still calls `CApplication::OnAction`. Its existing active-checkpoint branch returns before action dispatch, player work or persistence work. It then destroys the action payload. The selective pump sets the wait event only after that receiver returns, destroys the message, then reacquires its queue lock.
4. `SendMsg` retains its default result of `-1`. The GUI-action branch does not set a success result. `OnAction` returning `true` means handled/refused here; it does not mean playback changed. Native `onPause`, `onStop`, `onResume` and audio-focus callers do not convert the result into a successful playback notification.

The existing `onPause` resume flag records an intent, not proof of an actual pause. `onResume` independently checks real playing/video/paused state. During a failed checkpoint the guard remains active, so a resume-time Play request is also refused and acknowledged. Android observation of this behavior is still required.

The purpose is to let the Android sender finish after the **existing refusal**, without weakening that refusal. It does not make Pause or Stop execute while a checkpoint prohibits playback actions, grant a write receipt, discard a pending obligation or authorize termination.

## Exact binary comparison and its limits

Both files are ELF64 AArch64 shared objects. The complete dynamic-symbol contract and protected `InfinityCommandCenterIdentityV1` export are unchanged. All 37 sections and all function records were inventoried and hashed.

- 203,143 paired function records have exactly equal raw bytes.
- 104,126 comparison records differ or are added/removed; raw differences include link addresses. These must not be described as 104,126 source changes or as byte-identical code.
- The selective pump is the **only existing non-linker function whose size changes**, from 468 to 460 bytes. The new admission helper is 156 bytes. The remaining additions/removals are the linker's `e843419@...` erratum stubs: 21 added and 38 removed.
- The 46 selected unchanged symbols include Android callers, both message receivers, normal dispatch/cleanup, `OnAction`, checkpoint pumping, write guards and termination authorization, plus their selected template helpers. Their instruction counts and opcodes match. The 5,824 instructions comprise 4,275 exact instructions, 565 unchanged named branch/call targets, 717 unchanged intra-function target offsets, and 267 unchanged allocated-section page offsets. No selected difference remained unclassified.

`BINARY-COMPARISON.json` retains exact section and selected-function hashes. `FUNCTION-SIZE-AND-LINKER-SYMBOL-CHANGES.json` enumerates every size/addition/removal entry. The separate full comparison ZIP contains both complete ELF inventories, every function comparison row and selected disassemblies; its digest and member hashes are in `FULL-BINARY-EVIDENCE-ARCHIVE.json`.

This is a full raw-byte inventory and a focused instruction comparison, **not** a proof of whole-engine semantic equivalence. The 2,587 duplicate local symbol names are explicitly counted and paired by address order. No blanket normalization of arbitrary constants or data was used to declare a pass.

## Focused verification

**20 host cases passed against the integrated source:** the existing 15 control/lifecycle cases and five existing watched-durability cases. Earlier failing-before evidence is retained without rerunning it.

The control cases cover Pause/Stop/Play, native callback bodies using host peers, repeated interruptions, receiver-before-acknowledgement ordering, display ordering, negative GUI envelopes, retained FIFO, wrong-thread rejection, normal dispatch, bounded reentrant events, checkpoint activation after enqueue, durability fences and stopped-queue cleanup. Player commands remain unexecuted while the checkpoint is active; pending writes and failure obligations remain blocking.

The five watched cases cover commit failure, close failure, unknown native ownership, owner callback failure and unknown PVR ownership. They use real temporary SQLite commit/reopen operations with declared host adapters; they do not identify the historical watched route or certify device shutdown. One initial fixture compilation failed because its established protected-resource adapter option was missing. That failure is retained. Restoring the existing option allowed the five selected cases to run; no production source or assertion was changed and the 15 passing control cases were not rerun.

## Preservation and next gate

The original signed 451 recovery APK and signed 452 testing APK were rehashed unchanged. No new APK exists, so this stage cannot claim a candidate APK-member gate. Preview 451, Cobra, chooser, signing identity, user data and recovery locks were not modified. The original isolated source/proof branches remain preserved. Settings-owner retirement stays blocked; Scudo memory exhaustion, Continue Playing and Home loading remain unresolved separate scopes.

**Android/Fold verification: NOT RUN / pending.** No authorized compatible ARM64 device is connected. Cross-compilation, instruction inspection and host fixtures are not JNI, real codec/surface or physical Fold testing.

A controlled physical-test candidate is justified by the completed integration evidence, subject to separate authorization and the existing exact APK-member, signer and install-over gates. Its mandatory device tests are listed in [ANDROID-VERIFICATION-PENDING.md](ANDROID-VERIFICATION-PENDING.md): real audio-focus Pause/Stop branches, resume-time Play, repeated interruptions, failed and pending checkpoints, actual surface destruction/recreation, normal playback/shutdown and Fold transitions. Verify real player state and failure receipts rather than treating callback return as playback success.

This correction still depends on the application thread reaching the selective pump and the real receiver returning. It does not fix independent EGL/codec teardown, callback/worker stalls, activity destruction or memory exhaustion. Any such stall must retain its own evidence and protection boundary. No ANR-fixed, physical-acceptance or release-approval claim is made.
